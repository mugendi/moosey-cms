from moosey_cms.crypto import (
    generate_key,
    decode_key,
    urlsafe_encrypt,
    urlsafe_decrypt,
    urlsafe_encrypt_detached,
    urlsafe_decrypt_detached,
)


class TestGenerateKey:
    def test_returns_text_string(self):
        key = generate_key()
        assert isinstance(key, str)

    def test_is_base64_decodable(self):
        key = generate_key()
        decoded = decode_key(key)
        assert len(decoded) == 32


class TestRoundtrip:
    def test_encrypt_decrypt_roundtrip(self):
        key = generate_key()
        msg = "Hello, Moosey!"
        token = urlsafe_encrypt(msg, key)
        assert urlsafe_decrypt(token, key) == msg

    def test_wrong_key_returns_none(self):
        key = generate_key()
        other = generate_key()
        token = urlsafe_encrypt("secret", key)
        assert urlsafe_decrypt(token, other) is None

    def test_invalid_token_returns_none(self):
        key = generate_key()
        assert urlsafe_decrypt("not-a-valid-token", key) is None


class TestDetachedRoundtrip:
    def test_detached_roundtrip(self):
        key = generate_key()
        msg = "Detached message"
        nonce, cipher = urlsafe_encrypt_detached(msg, key)
        assert urlsafe_decrypt_detached(nonce, cipher, key) == msg

    def test_detached_wrong_key_returns_none(self):
        key = generate_key()
        other = generate_key()
        nonce, cipher = urlsafe_encrypt_detached("secret", key)
        assert urlsafe_decrypt_detached(nonce, cipher, other) is None
