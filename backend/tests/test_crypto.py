"""
Tests for FINDING-006's envelope encryption of Redis-stored credentials
(app/crypto.py).
"""

from app.crypto import decrypt_secret, encrypt_secret


class TestEncryptDecryptRoundTrip:
    def test_round_trip(self):
        """test_REQ_SEC_FINDING_006_encrypt_decrypt_round_trip"""
        plaintext = "sk-super-secret-api-key-1234567890"
        token = encrypt_secret(plaintext)
        assert token != plaintext
        assert decrypt_secret(token) == plaintext

    def test_empty_string_passes_through(self):
        assert encrypt_secret("") == ""
        assert decrypt_secret("") == ""

    def test_ciphertext_does_not_contain_plaintext(self):
        """test_REQ_SEC_FINDING_006_ciphertext_not_plaintext"""
        plaintext = "AKIAABCDEFGHIJKLMNOP"
        token = encrypt_secret(plaintext)
        assert plaintext not in token

    def test_two_encryptions_differ(self):
        """Fernet includes a random IV/timestamp — repeated encryption of
        the same value must not produce identical ciphertext."""
        plaintext = "twilio-auth-token-abc123"
        assert encrypt_secret(plaintext) != encrypt_secret(plaintext)


class TestLegacyPlaintextFallback:
    def test_decrypt_of_legacy_plaintext_returns_unchanged(self):
        """FINDING-006: values written before this fix are plaintext, not
        Fernet tokens. Decryption must fall back to returning them as-is
        rather than raising or discarding the credential.

        test_REQ_SEC_FINDING_006_legacy_plaintext_fallback
        """
        legacy_value = "sk-legacy-plaintext-key"
        assert decrypt_secret(legacy_value) == legacy_value

    def test_decrypt_of_garbage_returns_unchanged(self):
        assert decrypt_secret("not-a-fernet-token") == "not-a-fernet-token"
