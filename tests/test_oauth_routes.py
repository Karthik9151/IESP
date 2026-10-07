from backend.app.oauth_routes import _pkce
def test_pkce_verifier_and_challenge_are_random_and_s256():
    verifier,challenge=_pkce()
    assert len(verifier)>=43
    assert challenge
    assert verifier != challenge
