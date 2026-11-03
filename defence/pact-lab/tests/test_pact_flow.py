"""C1 PACT-lab: Anchor -> Endorsement -> Moderator -> Credential -> metered requests, over real HTTP routing."""
import time

import pytest
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from pactlab import wire
from pactlab.anchor import Anchor, bearer_accounts
from pactlab.client import MoleClient, MoleError, Wallet
from pactlab.moderator import Moderator, moderator_app

EPOCH = b"2026-11"
BASE = "http://testserver/site"


def build(initial_balance=20, retention=300):
    app = FastAPI()
    a = Anchor("accounts", "http://testserver/a/mole/grant", EPOCH, bearer_accounts({"tok-alice": "alice", "tok-bob": "bob"}, 3), budget_per_subject=3)
    b = Anchor("other", "http://testserver/b/mole/grant", EPOCH, bearer_accounts({"tok-carol": "carol"}))
    c = Anchor("not-trusted", "http://testserver/c/mole/grant", EPOCH, bearer_accounts({"tok-mallory": "mallory"}))
    m = Moderator("testserver", BASE + "/mole/issue", {EPOCH: [a.key_bytes, b.key_bytes]},
                  initial_balance=initial_balance, result_retention=retention, judge=lambda info: info["path"].startswith("/trap"))

    async def protected(request, info):
        return PlainTextResponse(f"hello {info['path']}")

    for anchor, p in ((a, "/a"), (b, "/b"), (c, "/c")):
        app.include_router(anchor.router(p))
    app.include_router(moderator_app(m, protected, "/site"))
    return TestClient(app), a, b, c, m


def kid(m):
    return wire.b64e(m.key_id)


def test_end_to_end_metered_access():
    http, a, b, c, m = build()
    alice = MoleClient(Wallet(), http)
    assert alice.get_endorsements("http://testserver/a/.well-known/mole-anchor", 2, "Bearer tok-alice") == 2
    r = alice.fetch(BASE + "/page", BASE)
    assert r.status_code == 200 and r.text == "hello /page"
    assert alice.wallet.balance(kid(m)) == 19
    for _ in range(5):
        assert alice.fetch(BASE + "/page", BASE).status_code == 200
    assert alice.wallet.balance(kid(m)) == 14
    assert len(alice.wallet.endorsements) == 1  # one redeemed, one left
    assert m.stats["issued"] == 1 and m.stats["accepted"] == 6


def test_abuse_ends_the_chain_and_costs_an_endorsement():
    http, a, b, c, m = build()
    alice = MoleClient(Wallet(), http)
    alice.get_endorsements("http://testserver/a/.well-known/mole-anchor", 2, "Bearer tok-alice")
    assert alice.fetch(BASE + "/page", BASE).status_code == 200
    r = alice.fetch(BASE + "/trap/x", BASE)
    assert r.status_code == 200  # the operation ran, but ...
    assert r.headers["mole-credential"] == 'update-0001=""'  # ... NoUpdate: the chain and its balance are gone
    assert kid(m) not in alice.wallet.credentials
    assert alice.fetch(BASE + "/page", BASE).status_code == 200  # second Endorsement redeemed
    alice.fetch(BASE + "/trap/y", BASE)
    with pytest.raises(MoleError, match="no Endorsement"):
        alice.fetch(BASE + "/page", BASE)
    assert m.stats["revoked"] == 2


def test_balance_runs_out_then_redeem_again():
    http, a, b, c, m = build(initial_balance=2)
    alice = MoleClient(Wallet(), http)
    alice.get_endorsements("http://testserver/a/.well-known/mole-anchor", 2, "Bearer tok-alice")
    for _ in range(4):
        assert alice.fetch(BASE + "/p", BASE).status_code == 200
    assert m.stats["issued"] == 2 and len(alice.wallet.endorsements) == 0


def test_duplicate_presentation_returns_recorded_result_409_and_recovery():
    http, a, b, c, m = build()
    alice = MoleClient(Wallet(), http)
    alice.get_endorsements("http://testserver/a/.well-known/mole-anchor", 1, "Bearer tok-alice")
    alice.fetch(BASE + "/p", BASE)
    # Build a presentation, send it, and "lose" the response.
    headers = alice._presentation_headers(BASE)
    lost = http.get(BASE + "/p", headers=headers)
    assert lost.status_code == 200
    dup = http.get(BASE + "/p", headers=headers)
    assert dup.status_code == 409 and dup.headers["mole-credential"] == lost.headers["mole-credential"]
    rec = http.post(BASE + "/mole/issue", headers={"Authorization": wire.mole({"recovery-0001": alice.recovery_handle()})})
    assert rec.status_code == 200 and rec.headers["mole-credential"] == lost.headers["mole-credential"]
    alice._process_update(rec)
    assert alice.wallet.balance(kid(m)) == 18
    bogus = http.post(BASE + "/mole/issue", headers={"Authorization": wire.mole({"recovery-0001": bytes(96)})})
    assert bogus.status_code == 404 and "mole-credential" not in bogus.headers


def test_copied_credential_is_accepted_once():
    """Agent lane: the user hands the wallet to an agent. Copies share the nullifier, so only one copy works."""
    http, a, b, c, m = build()
    alice = MoleClient(Wallet(), http)
    alice.get_endorsements("http://testserver/a/.well-known/mole-anchor", 1, "Bearer tok-alice")
    alice.fetch(BASE + "/p", BASE)
    agent = MoleClient(Wallet.from_json(alice.wallet.to_json()), http)
    agent.challenges = dict(alice.challenges)
    assert agent.fetch(BASE + "/agent-task", BASE).status_code == 200
    assert agent.wallet.balance(kid(m)) == 18
    r = http.get(BASE + "/p", headers=alice._presentation_headers(BASE))  # the user's stale copy
    assert r.status_code == 401 and "already spent" in r.text


def test_endorsement_cannot_be_redeemed_twice():
    http, a, b, c, m = build()
    alice = MoleClient(Wallet(), http)
    alice.get_endorsements("http://testserver/a/.well-known/mole-anchor", 1, "Bearer tok-alice")
    copy = MoleClient(Wallet.from_json(alice.wallet.to_json()), http)
    assert alice.fetch(BASE + "/p", BASE).status_code == 200
    with pytest.raises(MoleError, match="already redeemed"):
        copy.fetch(BASE + "/p", BASE)


def test_anchor_outside_the_accepted_set_is_refused():
    http, a, b, c, m = build()
    mallory = MoleClient(Wallet(), http)
    mallory.get_endorsements("http://testserver/c/.well-known/mole-anchor", 1, "Bearer tok-mallory")
    with pytest.raises(MoleError, match="no Endorsement from an Anchor"):
        mallory.fetch(BASE + "/p", BASE)
    # a forged redemption claiming the set is rejected by the Moderator itself
    carol = MoleClient(Wallet(), http)
    carol.get_endorsements("http://testserver/b/.well-known/mole-anchor", 1, "Bearer tok-carol")
    assert carol.fetch(BASE + "/p", BASE).status_code == 200  # second Anchor in the set works (issuer hiding)


def test_anchor_policy_budget_and_session_rules():
    http, a, b, c, m = build()
    hdr = {"Content-Type": "application/mole-endorsement-request; type=0002"}
    r = http.post("http://testserver/a/mole/grant", content=wire.encode_grant_request(1), headers=hdr)
    assert r.status_code == 401 and r.headers["www-authenticate"] == 'Mole endorse-0002=""'
    assert http.post("http://testserver/a/mole/grant", content=wire.encode_grant_request(1), headers={"Content-Type": "text/plain"}).status_code == 415
    bob = MoleClient(Wallet(), http)
    assert bob.get_endorsements("http://testserver/a/.well-known/mole-anchor", 10, "Bearer tok-bob") == 3  # capped by policy
    with pytest.raises(MoleError, match="403"):
        bob.get_endorsements("http://testserver/a/.well-known/mole-anchor", 1, "Bearer tok-bob")
    # a GrantChallenges for a session that was already claimed is rejected
    r1 = http.post("http://testserver/b/mole/grant", content=wire.encode_grant_request(1), headers={**hdr, "Authorization": "Bearer tok-carol"})
    sid, commits = wire.decode_grant_commitments(r1.content)
    body = wire.encode_grant_challenges(sid, [bytes(31) + b"\x01"])
    assert http.post("http://testserver/b/mole/grant", content=body, headers=hdr).status_code == 200
    assert http.post("http://testserver/b/mole/grant", content=body, headers=hdr).status_code == 400


def test_no_or_greased_presentation_gets_both_challenges():
    http, a, b, c, m = build()
    r = http.get(BASE + "/p")
    assert r.status_code == 401
    ch = wire.split_challenges(r.headers["www-authenticate"])
    assert {tuple(wire.typed_params(p))[0] for _, p in ch} == {("redeem", 2), ("challenge", 1)}
    greased = http.get(BASE + "/p", headers={"Authorization": wire.mole({"presentation-1a1a": b"\x00" * 40})})
    assert greased.status_code == 401  # unknown type treated as absent


def test_presentation_size_and_time():
    http, a, b, c, m = build()
    alice = MoleClient(Wallet(), http)
    alice.get_endorsements("http://testserver/a/.well-known/mole-anchor", 1, "Bearer tok-alice")
    alice.fetch(BASE + "/p", BASE)
    t = time.perf_counter()
    h = alice._presentation_headers(BASE)
    prove = time.perf_counter() - t
    t = time.perf_counter()
    r = http.get(BASE + "/p", headers=h)
    alice._process_update(r)
    verify = time.perf_counter() - t
    print(f"\nPresentation header {len(h['Authorization'])} bytes; client prove {prove*1000:.0f} ms; server verify+refund+client finalize {verify*1000:.0f} ms")
    assert len(h["Authorization"]) < 8192
