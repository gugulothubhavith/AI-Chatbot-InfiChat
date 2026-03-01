from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.core.auth import create_access_token, hash_password, verify_password
from app.models.user import User
from app.models.otp import OTP
from app.schemas.auth import OTPRequest, OTPVerify, AuthResponse, UserCreate, UserLogin
from app.services.email_service import send_otp_email
from datetime import datetime, timedelta
import secrets
import hashlib
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

OTP_EXPIRE_MINUTES = 5
MAX_ATTEMPTS = 3

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

@router.post("/request-otp")
def request_otp(payload: OTPRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Generate and send OTP for password-less login/signup.
    Blocks if user has a password set.
    """
    email = payload.email.lower()
    
    # Check if user exists and has a password
    user = db.query(User).filter(User.email == email).first()
    if user and user.hashed_password:
        raise HTTPException(
            status_code=400, 
            detail="Account has a password. Please sign in with your password."
        )
    
    # 1. Generate 6-digit OTP
    otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_hash = hash_otp(otp_code)
    
    # 2. Store in DB
    db.query(OTP).filter(OTP.email == email).delete()
    
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    
    new_otp = OTP(
        email=email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        password_verified=False
    )
    db.add(new_otp)
    db.commit()
    
    # 4. Send Email (Background task)
    background_tasks.add_task(send_otp_email, email, otp_code)
    
    return {"message": "OTP sent to email"}

@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    """
    Verify OTP and return JWT.
    Enforces password verification if user has a password set.
    """
    email = payload.email.lower()
    input_otp = payload.otp
    
    # 1. Fetch OTP record
    otp_record = db.query(OTP).filter(OTP.email == email).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP or expired")
        
    # 2. Check Expiry
    if datetime.utcnow() > otp_record.expires_at:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired")
        
    # 3. Check Attempts
    if otp_record.attempts >= MAX_ATTEMPTS:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Too many failed attempts. Request a new OTP.")
        
    # 4. Validate Hash
    calculated_hash = hash_otp(input_otp)
    if calculated_hash != otp_record.otp_hash:
        otp_record.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    # 5. Check if user needs password verification
    user = db.query(User).filter(User.email == email).first()
    if user and user.hashed_password and not otp_record.password_verified:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Password verification required for this account.")

    # 6. Success - Delete OTP
    db.delete(otp_record)
    
    # 7. Get or Create User
    is_new = False
    if not user:
        is_new = True
        user = User(
            email=email,
            username=email.split("@")[0],
            is_verified=True
        )
        db.add(user)
    else:
        if not user.is_verified:
            user.is_verified = True
    
    db.commit()
    db.refresh(user)
    
    # 8. Generate Token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": str(user.id),
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_new_user": is_new
    }

@router.post("/login")
def login(payload: UserLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Login with email and password. Sends OTP upon success.
    """
    email = payload.email.lower()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
        
    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="Account has no password set. Use OTP login.")
        
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
        
    # Correct password - now send OTP
    otp_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_hash = hash_otp(otp_code)
    
    db.query(OTP).filter(OTP.email == email).delete()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    
    new_otp = OTP(
        email=email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        password_verified=True
    )
    db.add(new_otp)
    db.commit()
    
    background_tasks.add_task(send_otp_email, email, otp_code)
    
    return {"message": "OTP sent for verification", "otp_required": True}

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}

@router.patch("/password")
def update_password(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user password.
    """
    old_password = payload.get("old_password")
    new_password = payload.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Old and new passwords required")
        
    if not current_user.hashed_password:
        # User might have signed up via OTP/Google and doesn't have a password yet.
        pass
    elif not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    current_user.hashed_password = hash_password(new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/register", response_model=AuthResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.
    """
    email = payload.email.lower()
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Create new user
    new_user = User(
        email=email,
        username=email, # Use email as username
        hashed_password=hash_password(payload.password),
        is_verified=True, 
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate Token
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": str(new_user.id),
        "email": new_user.email,
        "avatar_url": new_user.avatar_url,
        "is_new_user": True
    }

@router.get("/me", response_model=AuthResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged in user details.
    """
    return {
        "access_token": "valid_session", # Placeholder or could omit if schema allows
        "token_type": "bearer",
        "user_id": str(current_user.id),
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "is_new_user": False
    }