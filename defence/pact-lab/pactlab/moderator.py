"""MoLE Moderator (PACT's per-site role): redeems Endorsements for EC-ACT Credentials and meters every request.

Implements draft-jms-mole-protocols §Credential Protocols / §EC-ACT and the `Mole` HTTP scheme of
draft-jms-mole-http-transport-01: configuration, the two challenges (redeem-0002 and challenge-0001) on 401,
Redeem & Issue in the documented step order (key/context, IssueRequest proof, FinalizeRedeem, IssueResponse, atomic
replay record), presentation steps 1-4 with an atomic nullifier record and the recorded result on every response,
409 for duplicates, and recovery by handle.

Policy (what a request costs, when to end a chain) is the site's. Default: every request spends 1 credit, refunds
0, so an Endorsement buys `initial_balance` requests; a request the site judges abusive gets NoUpdate, which ends
the chain and its remaining balance (the "dynamic revocation" of EC-ACT). The policy-scoped challenge profile is used
(request_context empty), so a presentation is a one-use bearer authorization (protocols §Challenge Binding).
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from ec_act import protocol as act
from ec_act import wire as act_wire
from ec_ihat import protocol as ihat
from ec_ihat import wire as ihat_wire
from fastapi import APIRouter, Request, Response

from . import wire

L = act.L  # the reference code fixes the balance width at 8 bits


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


@dataclass
class Record:
    digest: bytes
    ctx_cred: bytes
    refund: Optional[bytes]  # None = NoUpdate
    recorded_at: float
    retained: bool = True


@dataclass
class Outcome:
    status: int  # 0 = run the protected operation; otherwise answer with this status
    headers: dict
    message: str = ""
    fresh: bool = False
    decision: str = ""  # "refund" | "no-update" | ""


@dataclass
class Moderator:
    origin: str
    issuance_uri: str
    anchor_sets: dict[bytes, list[bytes]]  # ctx_iss -> ordered list of SerializeElement(pkA)
    credential_context: bytes = b"pactlab-v1"
    initial_balance: int = 20
    spend_amount: int = 1
    result_retention: int = 300
    # judge(request_info) -> True if the request is abusive (the chain ends with NoUpdate)
    judge: Callable[[dict], bool] = lambda info: False
    # reporter(report_bytes, abusive) receives the client's private Anchor report (C2), if any
    reporter: Optional[Callable[[bytes, bool], None]] = None
    keypair: tuple = field(default_factory=lambda: act.G.GenerateKeyPair())
    secret: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    window_seconds: int = 600
    now: Callable[[], float] = time.time

    def __post_init__(self):
        if not 0 < self.initial_balance < 2**L:
            raise ValueError("initial balance must fit the balance width")
        self.skM, self.pkM = self.keypair
        self.key_bytes = act.G.SerializeElement(self.pkM)
        self.key_id = sha256(self.key_bytes)
        self.ctx_cred = self.credential_context + bytes([L])
        self.redeemed: set[tuple[bytes, bytes]] = set()  # (ctx_iss, nf)
        self.results: dict[bytes, Record] = {}  # key_id || k
        self._lock = threading.Lock()
        self._anchor_points = {ctx: [ihat.G.DeserializeElement(k) for k in keys] for ctx, keys in self.anchor_sets.items()}
        self.stats = {"issued": 0, "accepted": 0, "revoked": 0, "duplicates": 0, "rejected": 0}

    # --- configuration and challenges ------------------------------------------------------------------------
    def configuration(self) -> dict:
        return {
            "issuance-uri": self.issuance_uri,
            "endorsements": [
                {"endorsement-type": wire.ENDORSEMENT_EC_IHAT, "ciphersuite": "P256-SHA256",
                 "issuance-epoch": wire.b64e(ctx), "anchor-set": [wire.b64e(k) for k in keys]}
                for ctx, keys in self.anchor_sets.items()
            ],
            "credential-keys": [
                {"credential-type": wire.CREDENTIAL_EC_ACT, "credential-key": wire.b64e(self.key_bytes),
                 "ciphersuite": "P256-SHA256", "balance-width": L,
                 "credential-context": wire.b64e(self.credential_context), "result-retention": self.result_retention}
            ],
        }

    def redemption_context(self, window: int) -> bytes:
        """Stateless: an authenticated encoding of origin, policy and time window (protocols §Challenge Binding)."""
        return hmac.new(self.secret, f"{self.origin}|{self.credential_context.hex()}|{window}".encode(), "sha256").digest()

    def _window(self) -> int:
        return int(self.now() // self.window_seconds)

    def act_challenge(self) -> wire.ActChallenge:
        return wire.ActChallenge(self.spend_amount, 0, self.credential_context, b"")

    def www_authenticate(self) -> str:
        return ", ".join([
            wire.mole({"redeem-0002": self.redemption_context(self._window())}),
            wire.mole({"challenge-0001": self.act_challenge().encode()}),
        ])

    # --- Redeem & Issue ----------------------------------------------------------------------------------------
    def redeem_and_issue(self, params: dict[tuple[str, int], bytes]) -> Outcome:
        if ("recovery", wire.CREDENTIAL_EC_ACT) in params:
            return self.recover(params[("recovery", wire.CREDENTIAL_EC_ACT)])
        keys = set(params)
        if keys != {("redeem", wire.ENDORSEMENT_EC_IHAT), ("credential-request", wire.CREDENTIAL_EC_ACT)}:
            return Outcome(400, {}, "Redeem & Issue needs exactly redeem-0002 and credential-request-0001")
        try:
            tkid, ctx, request = wire.decode_issuance_request(params[("credential-request", wire.CREDENTIAL_EC_ACT)])
        except Exception:
            return Outcome(400, {}, "malformed IssuanceRequest")
        # 1. key and context
        if tkid != self.key_id[-1] or ctx != self.credential_context:
            return Outcome(401, {"WWW-Authenticate": self.www_authenticate()}, "unknown key or credential context")
        # 2. the IssueRequest proof (IssueResponse verifies it; nothing is released before step 4 records)
        try:
            response = act.IssueResponse(self.skM, self.ctx_cred, self.initial_balance, request)
        except Exception:
            return Outcome(401, {}, "IssueRequest proof does not verify")
        # 3. FinalizeRedeem
        nf_entry = self._finalize_redeem(params[("redeem", wire.ENDORSEMENT_EC_IHAT)])
        if nf_entry is None:
            self.stats["rejected"] += 1
            return Outcome(401, {"WWW-Authenticate": self.www_authenticate()}, "redemption does not verify under any accepted Anchor set")
        # 4. record the replay id atomically; no response is released if recording fails
        with self._lock:
            if nf_entry in self.redeemed:
                self.stats["rejected"] += 1
                return Outcome(401, {}, "Endorsement already redeemed here")
            self.redeemed.add(nf_entry)
        self.stats["issued"] += 1
        return Outcome(200, {"Mole-Credential": f'response-0001="{wire.b64e(wire.encode_issuance_response(response))}"', "Cache-Control": "no-store"})

    def _finalize_redeem(self, payload: bytes) -> Optional[tuple[bytes, bytes]]:
        w = self._window()
        for window in (w, w - 1):  # adjacent windows
            digest = sha256(self.redemption_context(window))
            for ctx_iss, anchors in self._anchor_points.items():
                try:
                    red = ihat_wire.DecodeRedemption(payload, len(anchors))
                    nf = ihat.VerifyRedemption(anchors, red, ctx_iss, wire.CTX_RED, digest)
                    return (ctx_iss, nf)
                except Exception:
                    continue
        return None

    # --- presentation ------------------------------------------------------------------------------------------
    def present(self, payload: bytes, info: dict, report: Optional[bytes] = None) -> Outcome:
        try:
            key_id, spend = wire.decode_presentation(payload)
        except Exception:
            return Outcome(400, {}, "malformed PresentationAndUpdate")
        if key_id != self.key_id:
            return Outcome(401, {"WWW-Authenticate": self.www_authenticate()}, "unknown credential key")
        rid = key_id + act.G.SerializeScalar(spend.k)
        digest = sha256(payload)
        # 1. nullifier store
        rec = self.results.get(rid)
        if rec is not None:
            if rec.digest == digest and rec.retained and self.now() - rec.recorded_at <= self.result_retention:
                self.stats["duplicates"] += 1
                return Outcome(409, self._update_header(rec), "duplicate presentation: recorded result returned")
            self.stats["rejected"] += 1
            return Outcome(401, {"WWW-Authenticate": self.www_authenticate()}, "credential already spent")
        # 2. the challenge this presentation answers
        ch = self.act_challenge()
        if (spend.s, spend.a) != (ch.spend_amount, ch.max_top_up):
            return Outcome(401, {"WWW-Authenticate": self.www_authenticate()}, "amounts do not match the challenge")
        # 3. verify, decide, record atomically
        try:
            act.VerifySpend(self.skM, self.ctx_cred, sha256(ch.encode()), spend)
        except Exception:
            self.stats["rejected"] += 1
            return Outcome(401, {"WWW-Authenticate": self.www_authenticate()}, "presentation does not verify")
        abusive = bool(self.judge(info))
        refund = None if abusive else wire.encode_update(act.IssueRefund(self.skM, self.ctx_cred, spend, 0))
        with self._lock:
            if rid in self.results:
                return Outcome(401, {}, "credential already spent (race)")
            rec = self.results[rid] = Record(digest, self.ctx_cred, refund, self.now())
        self.stats["revoked" if abusive else "accepted"] += 1
        if report is not None and self.reporter is not None:
            self.reporter(report, abusive)
        # 4. the caller runs the protected operation and must return these headers whatever its status
        return Outcome(0, self._update_header(rec), fresh=True, decision="no-update" if abusive else "refund")

    def _update_header(self, rec: Record) -> dict:
        value = "" if rec.refund is None else wire.b64e(rec.refund)
        return {"Mole-Credential": f'update-0001="{value}"', "Cache-Control": "no-store"}

    def recover(self, handle: bytes) -> Outcome:
        if len(handle) != 32 + 32 + 32:
            return Outcome(400, {}, "malformed recovery handle")
        rid, digest = handle[:64], handle[64:]
        rec = self.results.get(rid)
        if rec is None or rec.digest != digest or not rec.retained or self.now() - rec.recorded_at > self.result_retention:
            return Outcome(404, {}, "no retained result")
        return Outcome(200, self._update_header(rec))


def moderator_app(moderator: Moderator, protected: Callable, prefix: str = ""):
    """FastAPI routes: configuration, Redeem & Issue, and a catch-all protected resource."""
    r = APIRouter()

    @r.get(prefix + "/.well-known/mole-moderator")
    def config():
        return moderator.configuration()

    @r.post(prefix + "/mole/issue")
    async def issue(request: Request):
        try:
            params = wire.parse_mole_authorization(request.headers.get("authorization", ""))
        except wire.WireError as e:
            return Response(f"malformed: {e}", 400)
        out = moderator.redeem_and_issue(params)
        return Response(out.message, out.status, out.headers)

    @r.api_route(prefix + "/{path:path}", methods=["GET", "POST"])
    async def guarded(request: Request, path: str):
        auth = request.headers.get("authorization", "")
        info = {"method": request.method, "path": "/" + path, "headers": dict(request.headers)}
        if auth.lower().startswith("mole "):
            try:
                params = wire.parse_mole_authorization(auth)
            except wire.WireError as e:
                return Response(f"malformed: {e}", 400)
            if ("presentation", wire.CREDENTIAL_EC_ACT) in params:
                report = request.headers.get("pactlab-anchor-report")
                out = moderator.present(params[("presentation", wire.CREDENTIAL_EC_ACT)], info, wire.b64d(report) if report else None)
                if out.status:
                    return Response(out.message, out.status, out.headers)
                resp = await protected(request, info)
                resp.headers.update(out.headers)
                return resp
            # unknown or greased presentation types are treated as absent (protocols §Greasing)
        return Response("A Mole credential is required.\n", 401, {"WWW-Authenticate": moderator.www_authenticate(), "Cache-Control": "no-store"})

    return r
