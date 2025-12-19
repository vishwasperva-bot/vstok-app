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
    alert_interval: Optional[int] = None


class ProfileResponse(BaseModel):
    username: str
    telegram_chat_id: Optional[str]
    whatsapp_number: Optional[str]
    alert_interval: int


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

    if data.alert_interval is not None:
        user.alert_interval = data.alert_interval

    db.commit()
    return {"message": "Profile updated successfully"}


@app.get("/profile", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    # TEMP: first user (JWT auth comes next)
    user = db.query(User).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔓 Decrypt on READ
    return ProfileResponse(
        username=user.username,
        telegram_chat_id=decrypt(user.telegram_chat_id),
        whatsapp_number=decrypt(user.whatsapp_number),
        alert_interval=user.alert_interval
    )
