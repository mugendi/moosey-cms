"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

"""
URL-safe encode/decode using PyNaCl (libsodium bindings).
Install: uv pip install pynacl
"""

import base64
from nacl.secret import SecretBox
from nacl.utils import random


def generate_key() -> str:
    """
    Generate a new 32-byte secret key and return it as a base64 text string.

    The returned string is safe to store in config files, environment
    variables, or any text-based medium.  Pass it to
    :func:`urlsafe_encrypt` / :func:`urlsafe_decrypt` via :func:`decode_key`.
    """
    raw = random(SecretBox.KEY_SIZE)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _pad_b64(token: str) -> bytes:
    """Decode a URL-safe base64 string, re-adding padding if needed."""
    padding = 4 - len(token) % 4
    if padding != 4:
        token += "=" * padding
    return base64.urlsafe_b64decode(token.encode("ascii"))


def decode_key(key: str) -> bytes:
    """
    Decode a base64 text key (from :func:`generate_key`) back to raw bytes
    suitable for :class:`nacl.secret.SecretBox`.
    """
    return _pad_b64(key)


def urlsafe_encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt plaintext and return URL-safe base64 string.

    Args:
        plaintext: String to encrypt
        key: Base64 text key from :func:`generate_key`

    Returns:
        URL-safe base64 encoded ciphertext (nonce + encrypted)
    """
    box = SecretBox(decode_key(key))

    # Encrypt (generates nonce automatically)
    encrypted = box.encrypt(plaintext.encode("utf-8"))

    # encrypted format: nonce (24 bytes) + ciphertext

    # Encode to URL-safe base64
    return base64.urlsafe_b64encode(encrypted).rstrip(b"=").decode("ascii")


def urlsafe_decrypt(token: str, key: str) -> str | None:
    """
    Decrypt URL-safe base64 token back to plaintext.

    Args:
        token: URL-safe base64 encoded ciphertext
        key: Base64 text key from :func:`generate_key`

    Returns:
        Decrypted string or None if invalid
    """
    box = SecretBox(decode_key(key))

    try:
        encrypted = _pad_b64(token)
        decrypted = box.decrypt(encrypted)
        return decrypted.decode("utf-8")
    except Exception:
        return None


def urlsafe_encrypt_detached(plaintext: str, key: str) -> tuple[str, str]:
    """
    Encrypt and return nonce and ciphertext separately as URL-safe strings.
    Useful when you need to store nonce separately.
    """
    box = SecretBox(decode_key(key))
    nonce = random(SecretBox.NONCE_SIZE)
    ciphertext = box.encrypt(plaintext.encode("utf-8"), nonce)
    
    # ciphertext includes nonce prefix, so we split it
    actual_nonce = ciphertext[:SecretBox.NONCE_SIZE]
    actual_ciphertext = ciphertext[SecretBox.NONCE_SIZE:]
    
    nonce_b64 = base64.urlsafe_b64encode(actual_nonce).rstrip(b"=").decode("ascii")
    cipher_b64 = base64.urlsafe_b64encode(actual_ciphertext).rstrip(b"=").decode("ascii")
    
    return nonce_b64, cipher_b64


def urlsafe_decrypt_detached(nonce_b64: str, cipher_b64: str, key: str) -> str | None:
    """
    Decrypt using separate nonce and ciphertext.
    """
    box = SecretBox(decode_key(key))

    try:
        nonce = _pad_b64(nonce_b64)
        ciphertext = _pad_b64(cipher_b64)
        
        # Reconstruct full message: nonce + ciphertext
        full = nonce + ciphertext
        decrypted = box.decrypt(full)
        
        return decrypted.decode("utf-8")
    except Exception:
        return None


# Example usage
if __name__ == "__main__":
    # Generate key once, store securely
    key = generate_key()
    
    message = "Hello, Secret World!"
    
    # Encrypt
    token = urlsafe_encrypt(message, key)
    print(f"Token: {token}")
    
    # Decrypt
    decrypted = urlsafe_decrypt(token, key)
    print(f"Decrypted: {decrypted}")
    
    # Detached mode
    nonce, cipher = urlsafe_encrypt_detached(message, key)
    print(f"\nNonce: {nonce}")
    print(f"Cipher: {cipher}")
    
    decrypted2 = urlsafe_decrypt_detached(nonce, cipher, key)
    print(f"Decrypted: {decrypted2}")