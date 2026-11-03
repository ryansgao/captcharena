"""MoLE Client, for a user or for an agent acting for one (the "agent lane").

A Wallet holds Endorsements (per Anchor key and epoch) and Credentials (per Moderator). It serialises to JSON, so a
user can hand their wallet to an agent: the agent then carries the user's Credentials and the user bears the
consequences of what the agent does (MoLE architecture §2.2 "User Agents Acting Under Delegation"). MoleClient
drives the HTTP flows with any httpx client: grant at an Anchor, Redeem & Issue on a 401 challenge, present on every
request, finalize the Update the Moderator returns.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Optional

import httpx
from ec_act import protocol as act
from ec_act import wire as act_wire
from ec_ihat import protocol as ihat
from ec_ihat import wire as ihat_wire

from . import wire
from .moderator import L


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


@dataclass
class Wallet:
    endorsements: list[dict] = field(default_factory=list)  # {anchor_key, epoch, endorsement} (b64)
    credentials: dict[str, dict] = field(default_factory=dict)  # moderator key_id (b64) -> {credential, context, key, issuance_uri}

    def to_json(self) -> str:
        return json.dumps({"endorsements": self.endorsements, "credentials": self.credentials})

    @classmethod
    def from_json(cls, text: str) -> "Wallet":
        d = json.loads(text)
        return cls(d["endorsements"], d["credentials"])

    def balance(self, key_id_b64: str) -> Optional[int]:
        c = self.credentials.get(key_id_b64)
        return act_wire.DecodeCredential(wire.b64d(c["credential"])).c if c else None


class MoleError(Exception):
    pass


class MoleClient:
    def __init__(self, wallet: Wallet, http: httpx.Client, grease_rate: float = 0.0, report_maker=None):
        self.wallet = wallet
        self.http = http
        self.grease_rate = grease_rate
        self.report_maker = report_maker  # (moderator_config, anchor_index) -> report bytes, for C2
        self.last_spend: Optional[dict] = None  # pending presentation, for recovery
        self.challenges: dict[str, bytes] = {}  # site -> last EC-ACT challenge

    # --- grant ---------------------------------------------------------------------------------------------------
    def get_endorsements(self, anchor_config_url: str, count: int = 1, auth: Optional[str] = None) -> int:
        cfg = self.http.get(anchor_config_url).json()
        pkA = ihat.G.DeserializeElement(wire.b64d(cfg["anchor-key"]))
        ctx_iss = wire.b64d(cfg["issuance-epoch"])
        hdrs = {"Content-Type": "application/mole-endorsement-request; type=0002"}
        if auth:
            hdrs["Authorization"] = auth
        r1 = self.http.post(cfg["grant-uri"], content=wire.encode_grant_request(count), headers=hdrs)
        if r1.status_code != 200 or r1.headers.get("content-type", "").replace(" ", "") != "application/mole-endorsement-response;type=0002":
            raise MoleError(f"grant refused: HTTP {r1.status_code} {r1.text[:120]}")
        sid, commits = wire.decode_grant_commitments(r1.content)
        if len(commits) > count:
            raise MoleError("Anchor sent more commitments than asked for")
        states, challenges = [], []
        for cm in commits:
            st, ch = ihat.Challenge(pkA, ctx_iss, wire.CTX_RED, ihat_wire.DecodeCommitMessage(cm))
            states.append(st)
            challenges.append(ihat_wire.EncodeChallengeMessage(ch))
        r2 = self.http.post(cfg["grant-uri"], content=wire.encode_grant_challenges(sid, challenges), headers={"Content-Type": hdrs["Content-Type"]})
        if r2.status_code != 200:
            raise MoleError(f"grant failed at the second exchange: HTTP {r2.status_code}")
        responses = wire.decode_grant_responses(r2.content)
        if len(responses) != len(states):
            raise MoleError("response count differs")
        endorsed = [ihat.Finalize(pkA, st, ihat_wire.DecodeResponseMessage(rs)) for st, rs in zip(states, responses)]
        for e in endorsed:  # all or nothing: Finalize raised above if any failed
            self.wallet.endorsements.append({"anchor_key": cfg["anchor-key"], "epoch": cfg["issuance-epoch"], "endorsement": wire.b64e(ihat_wire.EncodeEndorsement(e))})
        return len(endorsed)

    # --- moderator flows ---------------------------------------------------------------------------------------
    def _config(self, base: str) -> dict:
        return self.http.get(base.rstrip("/") + "/.well-known/mole-moderator").json()

    def redeem_and_issue(self, cfg: dict, redemption_context: bytes) -> str:
        ck = cfg["credential-keys"][0]
        pkM = act.G.DeserializeElement(wire.b64d(ck["credential-key"]))
        if ck["balance-width"] != L:
            raise MoleError("balance width differs from this implementation's")
        ctx = wire.b64d(ck["credential-context"])
        ctx_cred = ctx + bytes([L])
        key_id = sha256(wire.b64d(ck["credential-key"]))
        # find an Endorsement from an Anchor in an accepted set
        chosen = None
        for entry in cfg["endorsements"]:
            if entry["endorsement-type"] != wire.ENDORSEMENT_EC_IHAT:
                continue
            for i, e in enumerate(self.wallet.endorsements):
                if e["epoch"] == entry["issuance-epoch"] and e["anchor_key"] in entry["anchor-set"]:
                    chosen = (entry, i, e)
                    break
            if chosen:
                break
        if not chosen:
            raise MoleError("no Endorsement from an Anchor this Moderator accepts")
        entry, i, e = chosen
        anchor_set = [ihat.G.DeserializeElement(wire.b64d(k)) for k in entry["anchor-set"]]
        index = entry["anchor-set"].index(e["anchor_key"])
        redemption = ihat.Redeem(anchor_set, index, ihat_wire.DecodeEndorsement(wire.b64d(e["endorsement"])),
                                 wire.b64d(entry["issuance-epoch"]), wire.CTX_RED, sha256(redemption_context))
        state, request = act.IssueRequest()
        params = {
            "redeem-0002": ihat_wire.EncodeRedemption(redemption),
            "credential-request-0001": wire.encode_issuance_request(key_id[-1], ctx, request),
        }
        r = self.http.post(cfg["issuance-uri"], headers={"Authorization": wire.mole(params)})
        if r.status_code != 200:
            raise MoleError(f"Redeem & Issue refused: HTTP {r.status_code} {r.text[:120]}")
        self.wallet.endorsements.pop(i)  # recorded by the Moderator; never reuse (it would link)
        mc = wire.typed_params(wire.parse_auth_params(r.headers["mole-credential"]))
        response = wire.decode_issuance_response(mc[("response", wire.CREDENTIAL_EC_ACT)])
        cred = act.FinalizeIssue(pkM, ctx_cred, state, response)
        kid = wire.b64e(key_id)
        self.wallet.credentials[kid] = {"credential": wire.b64e(act_wire.EncodeCredential(cred)), "context": ck["credential-context"],
                                        "key": ck["credential-key"], "issuance_uri": cfg["issuance-uri"], "anchor_index": index,
                                        "anchor_epoch": entry["issuance-epoch"]}
        return kid

    def fetch(self, url: str, base: str) -> httpx.Response:
        """GET a Moderator-protected URL, presenting a Credential (getting one first if needed). The EC-ACT
        challenge is learned from the first 401 and cached per site (policy-scoped challenges can be reused)."""
        r = self.http.get(url, headers=self._presentation_headers(base))
        if r.status_code == 401 and "mole" in r.headers.get("www-authenticate", "").lower():
            self._process_update(r)
            challenges = {k: v for scheme, ps in wire.split_challenges(r.headers["www-authenticate"]) if scheme.lower() == "mole" for k, v in wire.typed_params(ps).items()}
            if ("challenge", wire.CREDENTIAL_EC_ACT) in challenges:
                self.challenges[base] = challenges[("challenge", wire.CREDENTIAL_EC_ACT)]
            cfg = self._config(base)
            kid = wire.b64e(sha256(wire.b64d(cfg["credential-keys"][0]["credential-key"])))
            if kid not in self.wallet.credentials and ("redeem", wire.ENDORSEMENT_EC_IHAT) in challenges:
                self.redeem_and_issue(cfg, challenges[("redeem", wire.ENDORSEMENT_EC_IHAT)])
            r = self.http.get(url, headers=self._presentation_headers(base))
        self._process_update(r)
        return r

    def _presentation_headers(self, base: str) -> dict:
        challenge_bytes = self.challenges.get(base)
        if not self.wallet.credentials or challenge_bytes is None:
            return {}
        if self.grease_rate and random.random() < self.grease_rate:  # protocols §Greasing
            g = random.choice(sorted(wire.GREASE))
            return {"Authorization": wire.mole({f"presentation-{g:04x}": random.randbytes(64)})}
        kid, entry = next(iter(self.wallet.credentials.items()))
        ctx = wire.b64d(entry["context"])
        ch = wire.ActChallenge.decode(challenge_bytes)
        if ch.credential_context != ctx:
            return {}
        cred = act_wire.DecodeCredential(wire.b64d(entry["credential"]))
        if cred.c < ch.spend_amount:
            del self.wallet.credentials[kid]  # cannot cover the spend: Redeem & Issue again
            return {}
        state, spend = act.ProveSpend(cred, ctx + bytes([L]), ch.spend_amount, ch.max_top_up, sha256(challenge_bytes))
        payload = wire.encode_presentation(wire.b64d(kid), spend)
        del self.wallet.credentials[kid]  # Spent: invalid whether or not the presentation is answered
        self.last_spend = {"kid": kid, "entry": entry, "state": state, "payload": payload, "spend": spend}
        headers = {"Authorization": wire.mole({"presentation-0001": payload})}
        if self.report_maker:
            headers["PACTLab-Anchor-Report"] = wire.b64e(self.report_maker(entry))
        return headers

    def _process_update(self, r: httpx.Response):
        if self.last_spend is None or "mole-credential" not in r.headers:
            return
        mc = wire.typed_params(wire.parse_auth_params(r.headers["mole-credential"]))
        upd = mc.get(("update", wire.CREDENTIAL_EC_ACT))
        pending, self.last_spend = self.last_spend, None
        if upd is None or upd == b"":
            return  # NoUpdate: the chain ended
        entry = pending["entry"]
        pkM = act.G.DeserializeElement(wire.b64d(entry["key"]))
        cred = act.FinalizeRefund(pkM, wire.b64d(entry["context"]) + bytes([L]), pending["state"], wire.decode_update(upd))
        self.wallet.credentials[pending["kid"]] = {**entry, "credential": wire.b64e(act_wire.EncodeCredential(cred))}

    def recovery_handle(self) -> bytes:
        p = self.last_spend
        return wire.b64d(p["kid"]) + act.G.SerializeScalar(p["spend"].k) + sha256(p["payload"])
