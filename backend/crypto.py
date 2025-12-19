from cryptography.fernet import Fernet
import os

KEY_FILE = "backend/secret.key"

# Create key once
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as f:
    _key = f.read()

cipher = Fernet(_key)


def encrypt(text: str | None) -> str | None:
    if text is None:
        return None
    return cipher.encrypt(text.encode()).decode()


def decrypt(token: str | None) -> str | None:
    if token is None:
        return None
    return cipher.decrypt(token.encode()).decode()
