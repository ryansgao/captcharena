"""Messages of draft-jms-mole-protocols (rev. at MoLE repo 2789337, 2026-11-02) and the `Mole` HTTP authentication
scheme of draft-jms-mole-http-transport-01.

The cryptographic payloads (EC-IHAT CommitMessage, ChallengeMessage, ResponseMessage, Redemption; EC-ACT
IssueRequestMessage, IssueResponseMessage, SpendMessage, RefundMessage) are encoded by the draft authors' own
reference code (`ec_ihat.wire`, `ec_act.wire`). This module adds the protocol layer around them, which had no
implementation: the grant batch, RedemptionChallenge, IssuanceRequest/Response, the EC-ACT Challenge,
PresentationAndUpdate/Update, and the HTTP header syntax.
"""
from __future__ import annotations

import base64
import re
import struct
from dataclasses import dataclass

from ec_act import wire as act_wire
from ec_ihat import wire as ihat_wire
from ec_ihat.ciphersuite import DeserializeError

EncodeLength = ihat_wire.EncodeLength
Reader = ihat_wire.Reader

ENDORSEMENT_NONE = 0x0001
ENDORSEMENT_EC_IHAT = 0x0002
CREDENTIAL_EC_ACT = 0x0001
GREASE = {0x0A0A + 0x1010 * i for i in range(16)}
CTX_RED = b"MOLE-EC-IHAT-ctx_red-v1"


class WireError(ValueError):
    pass


def vec(value: bytes) -> bytes:
    return EncodeLength(len(value)) + value


def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64d(text: str) -> bytes:
    """Canonical unpadded base64url only (http-transport §2: reject noncanonical)."""
    if not re.fullmatch(r"[A-Za-z0-9_-]*", text) or len(text) % 4 == 1:
        raise WireError("not unpadded base64url")
    data = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    if b64e(data) != text:
        raise WireError("noncanonical base64url")
    return data


# --- EC-IHAT grant (protocols §EC-IHAT Grant) ------------------------------------------------------------------

def encode_grant_request(count: int) -> bytes:
    return struct.pack(">H", count)


def decode_grant_request(data: bytes) -> int:
    if len(data) != 2:
        raise WireError("GrantRequest is 2 bytes")
    return struct.unpack(">H", data)[0]


def _encode_batch(session_id: bytes | None, items: list[bytes]) -> bytes:
    return (session_id or b"") + vec(b"".join(items))


def _split(blob: bytes, size: int) -> list[bytes]:
    if size == 0 or len(blob) % size:
        raise WireError("vector is not a whole number of messages")
    return [blob[i : i + size] for i in range(0, len(blob), size)]


COMMIT_SIZE = 2 * 33  # two P-256 compressed elements
CHALLENGE_SIZE = 32
RESPONSE_SIZE = 3 * 32


def encode_grant_commitments(session_id: bytes, commitments: list[bytes]) -> bytes:
    return _encode_batch(session_id, commitments)


def decode_grant_commitments(data: bytes) -> tuple[bytes, list[bytes]]:
    r = Reader(data)
    sid = r.take(32)
    items = _split(r.vector(), COMMIT_SIZE)
    r.finish()
    return sid, items


encode_grant_challenges = encode_grant_commitments


def decode_grant_challenges(data: bytes) -> tuple[bytes, list[bytes]]:
    r = Reader(data)
    sid = r.take(32)
    items = _split(r.vector(), CHALLENGE_SIZE)
    r.finish()
    return sid, items


def encode_grant_responses(responses: list[bytes]) -> bytes:
    return _encode_batch(None, responses)


def decode_grant_responses(data: bytes) -> list[bytes]:
    r = Reader(data)
    items = _split(r.vector(), RESPONSE_SIZE)
    r.finish()
    return items


# --- Redeem & Issue (protocols §Credential Protocols, §EC-ACT Redeem & Issue) -----------------------------------

def encode_issuance_request(truncated_key_id: int, credential_context: bytes, request) -> bytes:
    return bytes([truncated_key_id]) + vec(credential_context) + act_wire.EncodeIssueRequest(request)


def decode_issuance_request(data: bytes):
    r = Reader(data)
    tkid = r.take(1)[0]
    ctx = r.vector()
    rest = data[r.offset :]
    return tkid, ctx, act_wire.DecodeIssueRequest(rest)


def encode_issuance_response(response) -> bytes:
    return act_wire.EncodeIssueResponse(response)


def decode_issuance_response(data: bytes):
    return act_wire.DecodeIssueResponse(data)


# --- EC-ACT presentation (protocols §Presentation and Update) ---------------------------------------------------

@dataclass(frozen=True)
class ActChallenge:
    spend_amount: int
    max_top_up: int
    credential_context: bytes
    request_context: bytes = b""

    def encode(self) -> bytes:
        return struct.pack(">QQ", self.spend_amount, self.max_top_up) + vec(self.credential_context) + vec(self.request_context)

    @classmethod
    def decode(cls, data: bytes) -> "ActChallenge":
        r = Reader(data)
        s, a = struct.unpack(">QQ", r.take(16))
        ctx = r.vector()
        req = r.vector()
        r.finish()
        return cls(s, a, ctx, req)


def encode_presentation(key_id: bytes, spend) -> bytes:
    return key_id + act_wire.EncodeSpend(spend)


def decode_presentation(data: bytes):
    if len(data) < 33:
        raise WireError("PresentationAndUpdate too short")
    return data[:32], act_wire.DecodeSpend(data[32:])


def encode_update(refund) -> bytes:
    return act_wire.EncodeRefund(refund)


def decode_update(data: bytes):
    return act_wire.DecodeRefund(data)


# --- the Mole HTTP authentication scheme (http-transport §2) -------------------------------------------------------

_PARAM = re.compile(r'\s*([!#$%&\'*+.^_`|~0-9A-Za-z-]+)\s*=\s*("(?:[^"\\]|\\.)*"|[!#$%&\'*+.^_`|~0-9A-Za-z-]*)\s*')


def parse_auth_params(text: str) -> dict[str, str]:
    """auth-param list (RFC 9110 §11.2). Duplicate names are an error (http-transport §2)."""
    out: dict[str, str] = {}
    pos = 0
    while pos < len(text):
        m = _PARAM.match(text, pos)
        if not m:
            raise WireError("malformed auth-param")
        name = m.group(1).lower()
        value = m.group(2)
        if value.startswith('"'):
            value = re.sub(r"\\(.)", r"\1", value[1:-1])
        if name in out:
            raise WireError(f"duplicate parameter {name}")
        out[name] = value
        pos = m.end()
        if pos < len(text):
            if text[pos] != ",":
                raise WireError("expected ,")
            pos += 1
    return out


def split_challenges(header: str) -> list[tuple[str, dict[str, str]]]:
    """Split a WWW-Authenticate field into (scheme, params) pairs. Only handles params lists (no token68)."""
    parts = re.split(r",\s*(?=[A-Za-z][A-Za-z0-9-]*\s+[A-Za-z0-9-]+\s*=)", header.strip())
    out = []
    for part in parts:
        scheme, _, rest = part.strip().partition(" ")
        try:
            out.append((scheme, parse_auth_params(rest)))
        except WireError:
            continue  # clients ignore malformed challenges
    return out


def mole(params: dict[str, bytes]) -> str:
    """Serialize a Mole credential or challenge. Values are base64url, always quoted (senders quote empty values)."""
    return "Mole " + ", ".join(f'{k}="{b64e(v)}"' for k, v in params.items())


_OP = re.compile(r"^(endorse|redeem|challenge|credential-request|presentation|recovery|response|update)-([0-9a-fA-F]{4})$")
_OP_PREFIX = re.compile(r"^(endorse|redeem|challenge|credential-request|presentation|recovery|response|update)-")


def typed_params(params: dict[str, str]) -> dict[tuple[str, int], bytes]:
    """Decode the typed payload parameters. Unknown names are ignored; a known prefix without four hex digits is
    malformed (http-transport §2). Type 0x0000 is invalid."""
    out: dict[tuple[str, int], bytes] = {}
    for name, value in params.items():
        m = _OP.match(name)
        if not m:
            if _OP_PREFIX.match(name):
                raise WireError(f"malformed parameter name {name}")
            continue
        t = int(m.group(2), 16)
        if t == 0:
            raise WireError("type 0x0000 is invalid")
        out[(m.group(1), t)] = b64d(value)
    return out


def parse_mole_authorization(header: str) -> dict[tuple[str, int], bytes]:
    scheme, _, rest = header.strip().partition(" ")
    if scheme.lower() != "mole":
        raise WireError("not a Mole credential")
    return typed_params(parse_auth_params(rest))


__all__ = [n for n in dir() if not n.startswith("_")] + ["DeserializeError"]
