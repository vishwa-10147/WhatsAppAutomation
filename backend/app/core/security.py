import base64
import hashlib
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    return f"wa_{secrets.token_urlsafe(32)}"


class CredentialEncryption:
    def __init__(self, key: Optional[str] = None):
        if key is None:
            key = settings.encryption_key
        self._fernet = self._create_fernet(key)

    def _create_fernet(self, key: str) -> Fernet:
        key_bytes = base64.urlsafe_b64decode(key)
        if len(key_bytes) != 32:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"whatsapp-automation-salt",
                iterations=100_000,
            )
            key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(key_bytes)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            raise ValueError("Failed to decrypt credential")


credential_encryption = CredentialEncryption()