import base64
import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    def __init__(self, key_b64: str | None = None):
        raw = key_b64 or settings.encryption_key
        if raw:
            self.key = base64.b64decode(raw)
            if len(self.key) != 32:
                raise ValueError(f"Encryption key must be 32 bytes, got {len(self.key)}")
        else:
            self.key = AESGCM.generate_key(bit_length=256)
            logger.warning(
                "No AGENTFORGE_ENCRYPTION_KEY set. Generated ephemeral key. "
                "Keys encrypted with this key will be unrecoverable after restart."
            )

    def encrypt(self, plaintext: str) -> str:
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def decrypt(self, token: str) -> str:
        data = base64.b64decode(token)
        nonce, ciphertext = data[:12], data[12:]
        aesgcm = AESGCM(self.key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode()

    def mask_key(self, raw_key: str) -> str:
        visible = 4
        if len(raw_key) <= visible:
            return "****"
        prefix = raw_key[:raw_key.find("-") + 1] if "-" in raw_key else ""
        suffix = raw_key[-visible:]
        return f"{prefix}****{suffix}"

    @property
    def is_ephemeral(self) -> bool:
        return not (settings.encryption_key)
