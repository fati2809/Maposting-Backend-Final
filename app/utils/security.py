# renstricciones para las claves

from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password(password: str):

    # mínimo 8 caracteres
    if len(password) < 8:
        raise ValueError("La contraseña debe tener mínimo 8 caracteres")

    # máximo permitido por bcrypt
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede tener más de 72 caracteres")

    # al menos un número
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe contener al menos un número")

    # al menos un caracter especial
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("La contraseña debe contener al menos un caracter especial")

    return True


# ============================
# 🔐 HASH PASSWORD
# ============================
def hash_password(password: str):

    # ⚠️ Validar antes de hashear
    validate_password(password)

    return pwd_context.hash(password)


# ============================
# ✅ VERIFY PASSWORD
# ============================
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)
