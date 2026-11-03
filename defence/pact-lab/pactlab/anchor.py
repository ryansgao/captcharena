"""MoLE Anchor (PACT's vouching role): grants EC-IHAT Endorsements to Clients it has a reason to vouch for.

Grant per draft-jms-mole-protocols §EC-IHAT Grant: two HTTP exchanges on one grant URI, four messages
(GrantRequest -> GrantCommitments, GrantChallenges -> GrantResponses), a random session_id that is claimed
atomically and tombstoned, a per-subject budget. Whom to vouch for is the Anchor's policy, a plug-in: a demo
account in good standing, a passed process check (C7), or anything else that is scarce for an attacker.
"""
from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from ec_ihat import protocol as ihat
from ec_ihat import wire as ihat_wire
from fastapi import APIRouter, Request, Response

from . import wire

MEDIA_REQ = "application/mole-endorsement-request"
MEDIA_RES = "application/mole-endorsement-response"


class GrantError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


@dataclass
class _Batch:
    states: list
    expires: float
    claimed: bool = False


@dataclass
class Anchor:
    """One Anchor key, one issuance epoch (ctx_iss)."""

    name: str
    grant_uri: str
    issuance_epoch: bytes
    # policy(request) -> (subject, max_endorsements) or None if this Anchor will not vouch for the caller
    policy: Callable[[Request], Optional[tuple[str, int]]]
    budget_per_subject: int = 5
    session_ttl: float = 120.0
    keypair: tuple = field(default_factory=lambda: ihat.G.GenerateKeyPair())
    now: Callable[[], float] = time.time

    def __post_init__(self):
        self.skA, self.pkA = self.keypair
        self._batches: dict[bytes, _Batch] = {}
        self._spent: dict[str, int] = {}
        self._lock = threading.Lock()
        self.granted = 0

    @property
    def key_bytes(self) -> bytes:
        return ihat.G.SerializeElement(self.pkA)

    def configuration(self) -> dict:
        return {
            "grant-uri": self.grant_uri,
            "endorsement-type": wire.ENDORSEMENT_EC_IHAT,
            "ciphersuite": "P256-SHA256",
            "anchor-key": wire.b64e(self.key_bytes),
            "issuance-epoch": wire.b64e(self.issuance_epoch),
            "name": self.name,
        }

    def _gc(self):
        t = self.now()
        for sid in [s for s, b in self._batches.items() if b.expires < t]:
            del self._batches[sid]

    def start(self, subject: str, allowed: int, count: int) -> bytes:
        """GrantRequest -> GrantCommitments."""
        if count < 1:
            raise GrantError(400, "count must be at least 1")
        with self._lock:
            self._gc()
            left = min(allowed, self.budget_per_subject - self._spent.get(subject, 0))
            n = min(count, left)
            if n < 1:
                raise GrantError(403, "endorsement budget used up for this epoch")
            self._spent[subject] = self._spent.get(subject, 0) + n  # every granted session counts against the budget
            states, commits = [], []
            for _ in range(n):
                st, cm = ihat.Commit(self.issuance_epoch)
                states.append(st)
                commits.append(ihat_wire.EncodeCommitMessage(cm))
            sid = secrets.token_bytes(32)
            self._batches[sid] = _Batch(states, self.now() + self.session_ttl)
        return wire.encode_grant_commitments(sid, commits)

    def finish(self, body: bytes) -> bytes:
        """GrantChallenges -> GrantResponses. The session id is claimed atomically; a tombstone stays until expiry."""
        sid, challenges = wire.decode_grant_challenges(body)
        with self._lock:
            batch = self._batches.get(sid)
            if batch is None or batch.claimed or batch.expires < self.now():
                raise GrantError(400, "no open grant session with this id")
            batch.claimed = True
            states, batch.states = batch.states, []
        if len(challenges) != len(states):
            raise GrantError(400, "challenge count differs from the batch")
        try:
            responses = [
                ihat_wire.EncodeResponseMessage(ihat.Respond(self.skA, st, ihat_wire.DecodeChallengeMessage(ch)))
                for st, ch in zip(states, challenges)
            ]
        except Exception as e:  # any Respond failure discards the whole batch
            raise GrantError(400, f"respond failed: {e}") from e
        self.granted += len(responses)
        return wire.encode_grant_responses(responses)

    def router(self, prefix: str = "") -> APIRouter:
        r = APIRouter()
        anchor = self

        @r.get(prefix + "/.well-known/mole-anchor")
        def config():
            return anchor.configuration()

        @r.post(prefix + "/mole/grant")
        async def grant(request: Request):
            ctype = request.headers.get("content-type", "").replace(" ", "").lower()
            if ctype != f"{MEDIA_REQ};type=0002":
                return Response("content-type must be application/mole-endorsement-request; type=0002", 415)
            body = await request.body()
            try:
                if len(body) == 2:  # first exchange: a GrantRequest
                    who = anchor.policy(request)
                    if who is None:
                        return Response("this Anchor does not vouch for you", 401, {"WWW-Authenticate": 'Mole endorse-0002=""'})
                    out = anchor.start(who[0], who[1], wire.decode_grant_request(body))
                else:
                    out = anchor.finish(body)
            except GrantError as e:
                return Response(str(e), e.status)
            except (wire.WireError, ValueError) as e:
                return Response(f"malformed grant message: {e}", 400)
            return Response(out, 200, media_type=f"{MEDIA_RES}; type=0002", headers={"Cache-Control": "no-store"})

        return r


def bearer_accounts(accounts: dict[str, str], per_account: int = 5):
    """Demo policy: an account in good standing (a bearer token naming it) may get `per_account` Endorsements."""

    def policy(request: Request):
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer ") and auth[7:].strip() in accounts:
            return accounts[auth[7:].strip()], per_account
        return None

    return policy
