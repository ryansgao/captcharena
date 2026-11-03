import pytest

from pactlab import wire


def test_auth_params_and_typed_names():
    p = wire.parse_mole_authorization('Mole redeem-0002="AAEC", credential-request-0001=AwQ, realm="x"')
    assert p == {("redeem", 2): b"\x00\x01\x02", ("credential-request", 1): b"\x03\x04"}
    assert wire.parse_mole_authorization('Mole REDEEM-000A=""') == {("redeem", 10): b""}
    for bad in ['Mole redeem-0002="AA", redeem-0002="AA"',  # duplicate
                'Mole redeem-02="AA"',                       # known prefix, not 4 hex digits
                'Mole redeem-0000="AA"',                     # type zero
                'Mole redeem-0002="AA=="',                   # padded
                'Mole redeem-0002="AB"',                     # noncanonical (trailing bits)
                'Basic abc']:
        with pytest.raises(wire.WireError):
            wire.parse_mole_authorization(bad)


def test_split_challenges():
    h = 'Mole redeem-0002="AAAA", Mole challenge-0001="BBBB", PrivateToken challenge="x", token-key="y"'
    got = wire.split_challenges(h)
    assert [s for s, _ in got] == ["Mole", "Mole", "PrivateToken"]


def test_act_challenge_roundtrip():
    c = wire.ActChallenge(3, 1, b"ctx", b"req")
    assert wire.ActChallenge.decode(c.encode()) == c
    with pytest.raises(Exception):
        wire.ActChallenge.decode(c.encode() + b"\x00")


def test_grant_messages_reject_bad_lengths():
    sid = bytes(32)
    assert wire.decode_grant_commitments(wire.encode_grant_commitments(sid, [bytes(66)] * 2)) == (sid, [bytes(66)] * 2)
    with pytest.raises(wire.WireError):
        wire.decode_grant_commitments(sid + wire.vec(bytes(65)))
    with pytest.raises(wire.WireError):
        wire.decode_grant_request(b"\x00")
