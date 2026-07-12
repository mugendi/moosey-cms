"""
Deterministic, reversible, file-safe token generator.

Not a "hash" in the cryptographic sense (hashes are one-way) — this is
deterministic symmetric encryption. Same (key, input) -> same output,
every time, and it can be decrypted back with the same key.

Output alphabet is filesystem/URL safe: A-Z a-z 0-9 - _
"""

import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key():
    return 'sksh'


def _derive_key(key: bytes) -> bytes:
    """Stretch an arbitrary-length key into a 32-byte AES-256 key."""
    return hashlib.sha256(key).digest()


def _derive_nonce(key: bytes, plaintext: bytes) -> bytes:
    """
    Deterministic 12-byte nonce derived from HMAC(key, plaintext).
    This is what makes encryption repeatable for the same input,
    while still being unpredictable to anyone without the key.
    """
    return hmac.new(key, plaintext, hashlib.sha256).digest()[:12]


def encode(value: str, key: str) -> str:
    """
    Deterministically encrypt `value` with `key` and return a
    file-safe token (base64 urlsafe, no padding).
    """
    key_bytes = key.encode("utf-8")
    aes_key = _derive_key(key_bytes)
    plaintext = value.encode("utf-8")

    nonce = _derive_nonce(aes_key, plaintext)
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, associated_data=None)

    # nonce doesn't need to be stored separately since it's re-derivable
    # from the key + plaintext, but we still need it to decrypt without
    # re-deriving, so we prepend it for simplicity/robustness.
    token_bytes = nonce + ciphertext
    return base64.urlsafe_b64encode(token_bytes).decode("ascii").rstrip("=")


def decode(token: str, key: str) -> str:
    """
    Reverse `encode`: recover the original string using the same key.
    Raises ValueError if the key is wrong or token was tampered with.
    """
    key_bytes = key.encode("utf-8")
    aes_key = _derive_key(key_bytes)

    padded = token + "=" * (-len(token) % 4)
    token_bytes = base64.urlsafe_b64decode(padded.encode("ascii"))

    nonce, ciphertext = token_bytes[:12], token_bytes[12:]
    try:
        plaintext = AESGCM(aes_key).decrypt(nonce, ciphertext, associated_data=None)
    except Exception as e:
        raise ValueError("Invalid token or wrong key") from e

    return plaintext.decode("utf-8")


if __name__ == "__main__":
    key = "super-secret-key"

    for value in ["hello world", "user:12345", "hello world"]:
        token = encode(value, key)
        recovered = decode(token, key)
        print(f"{value!r:20} -> {token!r:40} -> {recovered!r}")

    # wrong key demo
    try:
        decode(encode("hello world", key), "wrong-key")
    except ValueError as e:
        print("wrong key correctly rejected:", e)