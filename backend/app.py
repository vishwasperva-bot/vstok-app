from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import SessionLocal, engine
from models import Base, User
from auth import hash_password, verify_password, create_access_token
from crypto import encrypt, decrypt

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VSTOK Backend",
    description="SEBI-safe technical signal backend",
    version="0.3.0"
)

# ------------------ SCHEMAS ------------------

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    telegram_chat_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    # Make alert_interval default to 0 but detect if it was provided using __fields_set__
    alert_interval: int = 0


class ProfileResponse(BaseModel):
    username: str
    telegram_chat_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    alert_interval: int = 0


# ------------------ DB DEPENDENCY ------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------ BASIC ------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "VSTOK backend running"
    }


# ------------------ AUTH ------------------

@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=data.username,
        password=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    return {"message": "User registered successfully"}


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.username)
    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ------------------ PROFILE (ENCRYPT / DECRYPT) ------------------

@app.post("/profile/update")
def update_profile(
    data: ProfileUpdateRequest,
    db: Session = Depends(get_db)
):
    # TEMP: first user (JWT auth comes next)
    user = db.query(User).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔐 Encrypt on WRITE
    if data.telegram_chat_id is not None:
        user.telegram_chat_id = encrypt(data.telegram_chat_id)

    if data.whatsapp_number is not None:
        user.whatsapp_number = encrypt(data.whatsapp_number)

    # Only update alert_interval if it was provided in the request payload
    if "alert_interval" in data.__fields_set__:
        user.alert_interval = data.alert_interval

    db.commit()
    return {"message": "Profile updated successfully"}


@app.get("/profile", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    # TEMP: first user (JWT auth comes next)
    user = db.query(User).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔓 Decrypt on READ (only if values exist). Guard against None/empty and any decrypt errors.
    telegram = None
    if user.telegram_chat_id:
        try:
            telegram = decrypt(user.telegram_chat_id)
        except Exception:
            telegram = None

    whatsapp = None
    if user.whatsapp_number:
        try:
            whatsapp = decrypt(user.whatsapp_number)
        except Exception:
            whatsapp = None

    alert = user.alert_interval if user.alert_interval is not None else 0

    return ProfileResponse(
        username=user.username,
        telegram_chat_id=telegram,
        whatsapp_number=whatsapp,
        alert_interval=alert
    )
