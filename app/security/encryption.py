import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

class PiiEncryptionService:
    def __init__(self):
        # 1. New KMS-style base64 key
        try:
            key_bytes = base64.b64decode(settings.ENCRYPTION_KEY)
            self.aesgcm = AESGCM(key_bytes)
        except Exception as e:
            # Fallback/default key if base64 decoding fails
            fallback_key = hashlib.sha256(settings.KMS_PASSPHRASE.encode("utf-8")).digest()
            self.aesgcm = AESGCM(fallback_key)

        # 2. Legacy JS key derivation (SHA-256 hash of passphrase)
        legacy_key_bytes = hashlib.sha256(settings.SYS_CRYPTO_PASSPHRASE.encode("utf-8")).digest()
        self.legacy_aesgcm = AESGCM(legacy_key_bytes)

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return ""
        nonce = os.urandom(12)
        cipher_bytes = self.aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
        combined = nonce + cipher_bytes
        return base64.b64encode(combined).decode("utf-8")

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return ""
        try:
            combined = base64.b64decode(encrypted_text.encode("utf-8"))
            if len(combined) < 12:
                return encrypted_text
            nonce = combined[:12]
            ciphertext = combined[12:]
            decrypted_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode("utf-8")
        except Exception:
            # If decryption fails, try the legacy decryptor (useful during migration and compatibility)
            return self.decrypt_legacy(encrypted_text)

    def decrypt_legacy(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return ""
        try:
            combined = base64.b64decode(encrypted_text.encode("utf-8"))
            if len(combined) < 12:
                return encrypted_text
            nonce = combined[:12]
            ciphertext = combined[12:]
            decrypted_bytes = self.legacy_aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode("utf-8")
        except Exception:
            # Return original value if both decryptions fail (helps with unencrypted values)
            return encrypted_text

pii_service = PiiEncryptionService()
