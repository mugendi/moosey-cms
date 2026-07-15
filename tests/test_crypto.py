from moosey_cms.lib.crypto import (
    generate_key,
    encode,
    decode,
)


class TestGenerateKey:
    def test_returns_text_string(self):
        key = generate_key()
        assert isinstance(key, str)

    def test_is_nonempty(self):
        key = generate_key()
        assert len(key) > 0


class TestRoundtrip:
    def test_encrypt_decrypt_roundtrip(self):
        key = generate_key()
        msg = "Hello, Moosey!"
        token = encode(msg, key)
        assert decode(token, key) == msg

    def test_wrong_key_raises(self):
        key = generate_key()
        other = generate_key()
        token = encode("secret", key)
        try:
            decode(token, other)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_invalid_token_raises(self):
        key = generate_key()
        try:
            decode("not-a-valid-token", key)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_deterministic(self):
        key = generate_key()
        msg = "deterministic test"
        assert encode(msg, key) == encode(msg, key)
