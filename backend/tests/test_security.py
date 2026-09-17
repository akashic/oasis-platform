"""
Tests for FINDING-005's Argon2id password hashing (app/security.py).
"""

from app.security import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_then_verify_succeeds(self):
        """test_REQ_SEC_FINDING_005_hash_verify_round_trip"""
        password = "correct-horse-battery-staple"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        """test_REQ_SEC_FINDING_005_wrong_password_rejected"""
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("wrong-password", hashed) is False

    def test_verify_never_raises_on_malformed_hash(self):
        """test_REQ_SEC_FINDING_005_malformed_hash_returns_false"""
        assert verify_password("anything", "not-an-argon2-hash") is False

    def test_verify_empty_hash_returns_false(self):
        assert verify_password("anything", "") is False

    def test_hash_is_argon2_format(self):
        hashed = hash_password("some-password")
        assert hashed.startswith("$argon2id$")
