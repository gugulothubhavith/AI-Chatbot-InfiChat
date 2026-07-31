from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response, UploadFile, File
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.user import User, UserSession
from app.models.admin import AdminProfile, AdminSession, AdminAuditLog, AdminRole, AdminStatus
from app.models.otp import OTP
from app.schemas.auth import OTPRequest, OTPVerify, AuthResponse, UserCreate, UserLogin, TokenRefresh
from app.services.email_service import send_otp_email
from datetime import datetime, timedelta, timezone
import secrets
import hashlib
import base64
from app.core.config import settings
from app.core.auth import create_access_token, create_refresh_token, decode_token, verify_token_type, hash_password, verify_password
from app.core.security import limiter
from app.core.cookies import set_refresh_cookie, clear_refresh_cookie
from app.services.consent_service import record_consent

router = APIRouter(prefix="/auth", tags=["Auth"])

OTP_EXPIRE_MINUTES = 5
MAX_ATTEMPTS = 3

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

@router.post("/request-otp")
@limiter.limit("5/minute")
def request_otp(request: Request, payload: OTPRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
    
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    
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
@limiter.limit("5/minute")
def verify_otp(request: Request, response: Response, payload: OTPVerify, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
    if datetime.now(timezone.utc) > otp_record.expires_at:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired")
        
    # 3. Check Attempts
    if otp_record.attempts >= MAX_ATTEMPTS:
        # Disptach Critical Brute-Force Alert before rejecting
        try:
            from app.services.email_service import send_security_alert_email
            background_tasks.add_task(
                send_security_alert_email,
                to_email=email,
                threat_type="Brute Force Authentication Blocked",
                details={
                    "ip_address": "Client Connection", # Could be parsed via Request IP if passed down
                    "user_agent": "OTP System Guard",
                    "action_blocked": f"Exceeded {MAX_ATTEMPTS} sequential OTP verification failures"
                },
                cc_email=settings.SMTP_USER
            )
        except Exception as e:
            pass
            
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Too many failed attempts. Security Alert dispatched.")
        
    # 4. Validate Hash (Using timing-attack resilient HMAC digest)
    import hmac
    calculated_hash = hash_otp(input_otp)
    if not hmac.compare_digest(calculated_hash, otp_record.otp_hash):
        otp_record.attempts += 1
        db.commit()
        # Trigger brute-force alert immediately on the final strike
        if otp_record.attempts >= MAX_ATTEMPTS:
            try:
                from app.services.email_service import send_security_alert_email
                background_tasks.add_task(
                    send_security_alert_email,
                    to_email=email,
                    threat_type="Brute Force Authentication Blocked",
                    details={
                        "ip_address": "Client Connection",
                        "user_agent": "OTP System Guard",
                        "action_blocked": f"Exceeded {MAX_ATTEMPTS} sequential OTP verification failures"
                    },
                    cc_email=settings.SMTP_USER
                )
            except Exception:
                pass
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    # 5. Check if user needs password verification
    user = db.query(User).filter(User.email == email).first()
    if user and user.hashed_password and not otp_record.password_verified:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Password verification required for this account.")

    # 5b. This endpoint doubles as a registration path, so first-time OTP
    # sign-in needs the same mandatory consent as /auth/register. Checked
    # before the OTP is consumed so a rejected signup can retry with the
    # same code instead of having to request a fresh one.
    # Only enforced when creating an account: an existing user must be able to
    # log in even with stale consent, or they could never reach the re-consent
    # and account-deletion endpoints.
    if not user and (not payload.accept_terms or not payload.accept_privacy):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONSENT_REQUIRED",
                "message": (
                    "You must accept the Terms of Service and the Privacy "
                    "Policy to create an account."
                ),
                "required_terms_version": settings.CURRENT_TERMS_VERSION,
                "required_privacy_version": settings.CURRENT_PRIVACY_VERSION,
            },
        )

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
        db.flush()  # assign user.id before the consent audit row references it
        record_consent(db, user, request=request)
    else:
        if not user.is_verified:
            user.is_verified = True
    
    db.commit()
    db.refresh(user)
    
    # 8. Generate Tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # 9. Create Session
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_otp(refresh_token), # Reuse hash_otp for simplicity
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "Unknown Client"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        is_active=True
    )
    db.add(new_session)
    
    perms = []
    admin_prof = db.query(AdminProfile).filter(AdminProfile.user_id == user.id).first()
    if admin_prof and admin_prof.status == "ACTIVE":
        if admin_prof.is_super_admin:
            perms.append("super_admin")
        if admin_prof.role:
            for p in admin_prof.role.permissions:
                perms.append(p.name)
        for p in admin_prof.custom_permissions:
            perms.append(p.name)
            
        # Log session and audit for admin
        new_sess = AdminSession(
            admin_id=admin_prof.id,
            refresh_token_hash=hash_otp(refresh_token),
            ip_address=request.client.host if request.client else "unknown",
            device_info=request.headers.get("user-agent", "Unknown Client"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            last_seen=datetime.now(timezone.utc)
        )
        new_audit = AdminAuditLog(
            admin_id=admin_prof.id,
            action="ADMIN_LOGIN",
            resource_type="AdminProfile",
            resource_id=str(admin_prof.id),
            ip_address="127.0.0.1",
            new_state={"login": "success"}
        )
        db.add(new_sess)
        db.add(new_audit)
        
    db.commit()

    set_refresh_cookie(response, refresh_token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "name": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_new_user": is_new,
        "role": user.role,
        "permissions": list(set(perms))
    }

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, response: Response, payload: UserLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Login with email and password. Generates JWT directly if correct. Sends OTP upon failure.
    """
    email = payload.email.lower()

    user = db.query(User).filter(User.email == email).first()

    # AUTO-SEED: If no users exist at all, create this user as admin on the fly
    if not user:
        from app.models.user import RoleEnum
        total_users = db.query(User).count()
        if total_users == 0:
            # No consent is recorded here on purpose. /auth/login carries no
            # consent payload, and fabricating an acceptance the operator
            # never made would be a false audit record. The bootstrap admin is
            # left with NULL consent, so require_consent blocks them on their
            # first protected request until they accept via POST
            # /legal/consent — the gate is the backstop for this path.
            user = User(
                email=email,
                username=email.split("@")[0],
                hashed_password=hash_password(payload.password),
                role=RoleEnum.admin,
                is_verified=True,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            # Create admin profile
            try:
                role = db.query(AdminRole).filter(AdminRole.name == "SuperAdmin").first()
                if not role:
                    role = AdminRole(name="SuperAdmin", hierarchy_level=1)
                    db.add(role)
                    db.commit()
                    db.refresh(role)
                profile = AdminProfile(
                    user_id=user.id, role_id=role.id,
                    is_super_admin=True, status=AdminStatus.ACTIVE,
                )
                db.add(profile)
                db.commit()
            except Exception:
                db.rollback()
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="Account has no password set. Use OTP login by requesting an OTP directly via /request-otp.")

    if verify_password(payload.password, user.hashed_password):
        # Generate Tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Create Session
        new_session = UserSession(
            user_id=user.id,
            refresh_token_hash=hash_otp(refresh_token),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "Unknown Client"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_active=True
        )
        db.add(new_session)
        
        perms = []
        admin_prof = db.query(AdminProfile).filter(AdminProfile.user_id == user.id).first()
        if admin_prof and admin_prof.status == "ACTIVE":
            if admin_prof.is_super_admin:
                perms.append("super_admin")
            if admin_prof.role:
                for p in admin_prof.role.permissions:
                    perms.append(p.name)
            for p in admin_prof.custom_permissions:
                perms.append(p.name)
                
            # Log session and audit for admin
            new_sess = AdminSession(
                admin_id=admin_prof.id,
                refresh_token_hash=hash_otp(refresh_token),
                ip_address=request.client.host if request.client else "unknown",
                device_info=request.headers.get("user-agent", "Unknown Client"),
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                last_seen=datetime.now(timezone.utc)
            )
            new_audit = AdminAuditLog(
                admin_id=admin_prof.id,
                action="ADMIN_LOGIN",
                resource_type="AdminProfile",
                resource_id=str(admin_prof.id),
                ip_address=request.client.host if request.client else "unknown",
                new_state={"login": "success"}
            )
            db.add(new_sess)
            db.add(new_audit)
        
        db.commit()

        set_refresh_cookie(response, refresh_token)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "name": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "is_new_user": False,
            "role": user.role,
            "permissions": list(set(perms))
        }

    # WRONG PASSWORD — 401, not 400: the request was well-formed, the
    # credentials were not. The message is identical to the unknown-email case
    # so this endpoint cannot be used to enumerate registered addresses.
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("10/minute")
def refresh_token_endpoint(request: Request, response: Response, payload: TokenRefresh | None = None, db: Session = Depends(get_db)):
    """
    Refresh access token using a valid refresh token.
    Implements refresh token rotation.

    The refresh token is read from the httpOnly cookie first (the secure path
    used by Frontend-New). For backward compatibility with the admin/legacy
    frontends that still send it in the body, we fall back to the JSON payload.
    """
    incoming_refresh = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not incoming_refresh and payload is not None:
        incoming_refresh = payload.refresh_token
    if not incoming_refresh:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    token_payload = decode_token(incoming_refresh)
    if not token_payload or not verify_token_type(token_payload, "refresh"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    # Verify session in DB
    rf_hash = hash_otp(incoming_refresh)
    session = db.query(UserSession).filter(
        UserSession.refresh_token_hash == rf_hash,
        UserSession.is_active == True
    ).first()

    if not session:
        # POTENTIAL REUSE ATTACK! In 10/10 security, we might want to invalidate ALL sessions for this user.
        # For now, just block the refresh.
        raise HTTPException(status_code=401, detail="Refresh token reused or session revoked")
        
    # expires_at is stored naive on SQLite and aware on Postgres; normalise
    # before comparing so this rejects rather than raising a TypeError (which
    # would surface as a 500 and effectively block all refreshes on SQLite).
    session_expires = session.expires_at
    if session_expires is not None and session_expires.tzinfo is None:
        session_expires = session_expires.replace(tzinfo=timezone.utc)
    if session_expires is not None and session_expires < datetime.now(timezone.utc):
        session.is_active = False
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
        
    # Rotate tokens
    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    # Update session (Rotation)
    session.refresh_token_hash = hash_otp(new_refresh_token)
    session.last_activity = datetime.now(timezone.utc)
    
    # Also update AdminSession if applicable
    admin_sess = db.query(AdminSession).filter(
        AdminSession.refresh_token_hash == rf_hash,
        AdminSession.is_active == True
    ).first()
    if admin_sess:
        admin_sess.refresh_token_hash = hash_otp(new_refresh_token)
        admin_sess.last_seen = datetime.now(timezone.utc)
        
    db.commit()
    
    # Get permissions
    perms = []
    admin_prof = db.query(AdminProfile).filter(AdminProfile.user_id == user.id).first()
    if admin_prof and admin_prof.status == "ACTIVE":
        if admin_prof.is_super_admin: perms.append("super_admin")
        if admin_prof.role: perms.extend([p.name for p in admin_prof.role.permissions])
        perms.extend([p.name for p in admin_prof.custom_permissions])
        
    set_refresh_cookie(response, new_refresh_token)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "name": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_new_user": False,
        "role": user.role,
        "permissions": list(set(perms))
    }

@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Log out and deactivate all active sessions for the current user.
    For 10/10 security, we invalidate all devices.
    """
    db.query(UserSession).filter(UserSession.user_id == current_user.id).update({"is_active": False})
    
    # Also invalidate admin sessions
    admin_prof = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    if admin_prof:
        db.query(AdminSession).filter(AdminSession.admin_id == admin_prof.id).update({"is_active": False})
        
    db.commit()
    clear_refresh_cookie(response)
    return {"message": "Logged out successfully from all devices"}

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
        # User signed up via OTP/Google — they are setting a password for the first time.
        # We cannot verify an old password that doesn't exist, so just allow it.
        # No old_password check needed.
        pass
    elif not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    current_user.hashed_password = hash_password(new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/register", response_model=AuthResponse)
@limiter.limit("3/minute")
def register(request: Request, response: Response, payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.

    Both consent flags are mandatory: signup is refused outright without
    them, rather than inferring agreement from the act of registering.
    Passive acceptance is not valid consent under GDPR Art. 7 / India DPDP.
    """
    # Consent gate first — reject before creating anything.
    if not payload.accept_terms or not payload.accept_privacy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONSENT_REQUIRED",
                "message": (
                    "You must accept the Terms of Service and the Privacy "
                    "Policy to create an account."
                ),
                "required_terms_version": settings.CURRENT_TERMS_VERSION,
                "required_privacy_version": settings.CURRENT_PRIVACY_VERSION,
                "accept_terms": payload.accept_terms,
                "accept_privacy": payload.accept_privacy,
            },
        )

    email = payload.email.lower()

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user — first ever user gets auto-promoted to admin
    from app.models.user import RoleEnum
    user_count = db.query(User).count()
    new_role = RoleEnum.admin if user_count == 0 else RoleEnum.user

    new_user = User(
        email=email,
        username=email.split("@")[0],
        hashed_password=hash_password(payload.password),
        is_verified=True,
        role=new_role,
    )
    db.add(new_user)
    db.flush()  # assign new_user.id so the consent audit row can reference it

    # Record consent in the same transaction as the user row: an account must
    # never exist without its consent record.
    record_consent(db, new_user, request=request)

    db.commit()
    db.refresh(new_user)

    # If this is the first user (admin), also create admin profile
    if new_role == RoleEnum.admin:
        try:
            from app.models.admin import AdminProfile, AdminRole, AdminStatus
            role = db.query(AdminRole).filter(AdminRole.name == "SuperAdmin").first()
            if not role:
                role = AdminRole(name="SuperAdmin", hierarchy_level=1)
                db.add(role)
                db.commit()
                db.refresh(role)
            profile = AdminProfile(
                user_id=new_user.id,
                role_id=role.id,
                is_super_admin=True,
                status=AdminStatus.ACTIVE,
            )
            db.add(profile)
            db.commit()
        except Exception as e:
            db.rollback()
            # Non-fatal — auth still works
    
    # Generate Tokens (matching login flow)
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": str(new_user.id)}
    )
    
    # Create session (matching login flow)
    new_session = UserSession(
        user_id=new_user.id,
        refresh_token_hash=hash_otp(refresh_token),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "Unknown Client"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        is_active=True
    )
    db.add(new_session)
    db.commit()

    set_refresh_cookie(response, refresh_token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(new_user.id),
        "name": new_user.username,
        "email": new_user.email,
        "avatar_url": new_user.avatar_url,
        "is_new_user": True,
        "role": new_user.role
    }


@router.get("/me", response_model=AuthResponse)
def read_users_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get current logged in user details.
    """
    
    perms = []
    admin_prof = db.query(AdminProfile).filter(AdminProfile.user_id == current_user.id).first()
    from app.models.admin import AdminStatus
    import datetime
    
    if admin_prof:
        # Enforce expiration logic on the base auth fetch
        if admin_prof.access_expires_at and admin_prof.access_expires_at < datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
            admin_prof.status = AdminStatus.EXPIRED
            db.commit()

        if admin_prof.status == AdminStatus.ACTIVE:
            if admin_prof.is_super_admin:
                perms.append("super_admin")
            if admin_prof.role:
                for p in admin_prof.role.permissions:
                    perms.append(p.name)
            for p in admin_prof.custom_permissions:
                perms.append(p.name)

    return {
        "access_token": "",  # Token not re-issued on /me; client should use the existing token
        "token_type": "bearer",
        "user_id": str(current_user.id),
        "name": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "is_new_user": False,
        "role": current_user.role,
        "permissions": list(set(perms))
    }


@router.post("/google", response_model=AuthResponse)
def google_login(request: Request, response: Response, payload: dict, db: Session = Depends(get_db)):
    """
    Login with Google credential. Generates JWT directly and sets up AdminSession if applicable.

    First-time sign-in through Google is a *registration*, so it carries the
    same mandatory consent gate as ``POST /auth/register``: the client must
    send ``accept_terms`` and ``accept_privacy``. Returning users are let
    through here and picked up by the request-time gate if their accepted
    version has gone stale, so a policy change cannot lock them out of
    logging in to withdraw or export their data.

    ``request`` is required to capture the consent IP and user agent for the
    audit record.
    """
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    from app.core.config import settings
    import httpx

    credential = payload.get("credential")
    if not credential:
        raise HTTPException(status_code=400, detail="Missing credential")

    try:
        client_id = settings.GOOGLE_CLIENT_ID
        
        if credential.startswith("ya29."):
            # Handle Access Token
            with httpx.Client() as client:
                # 1. Verify token audience
                token_info_resp = client.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={credential}")
                if token_info_resp.status_code != 200:
                    raise ValueError("Invalid Google access token")
                token_info = token_info_resp.json()
                
                azp = token_info.get("azp")
                aud = token_info.get("aud")
                if client_id not in (azp, aud):
                    if aud or azp:
                        raise ValueError(f"Token was not issued to this client (expected {client_id})")
                
                # 2. Get user info
                user_info_resp = client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo", 
                    headers={"Authorization": f"Bearer {credential}"}
                )
                if user_info_resp.status_code != 200:
                    raise ValueError("Failed to fetch Google user info")
                idinfo = user_info_resp.json()
        else:
            # Handle ID Token
            idinfo = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id, clock_skew_in_seconds=10)
            
        email = idinfo['email'].lower()
        
        # Robustly extract name
        given_name = idinfo.get("given_name", "").strip()
        family_name = idinfo.get("family_name", "").strip()
        full_name = idinfo.get("name", "").strip()
        
        if not full_name:
            if given_name or family_name:
                full_name = f"{given_name} {family_name}".strip()
            else:
                full_name = email.split("@")[0]

    except Exception as e:
        import sys
        print(f"Google Token Verification Error: {e}")
        sys.stdout.flush()
        raise HTTPException(status_code=400, detail=f"Validate Error: {str(e)}")

    # 1. Get or Create User
    user = db.query(User).filter(User.email == email).first()
    is_new = False

    if not user:
        # New account via Google == registration, so consent is mandatory.
        # Checked only on this branch: an existing user must still be able to
        # log in when the policy version changes, otherwise a stale user could
        # never reach the re-consent or account-deletion endpoints.
        if not payload.get("accept_terms") or not payload.get("accept_privacy"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CONSENT_REQUIRED",
                    "message": (
                        "You must accept the Terms of Service and the Privacy "
                        "Policy to create an account."
                    ),
                    "required_terms_version": settings.CURRENT_TERMS_VERSION,
                    "required_privacy_version": settings.CURRENT_PRIVACY_VERSION,
                },
            )

        is_new = True
        user = User(
            email=email,
            username=full_name,
            is_verified=True,
            role="user"
        )
        if "picture" in idinfo:
            user.avatar_url = idinfo["picture"]
        db.add(user)
        db.flush()  # assign user.id before the consent audit row references it
        record_consent(db, user, request=request)
        db.commit()
        db.refresh(user)
    else:
        updated = False
        if not user.is_verified:
            user.is_verified = True
            updated = True
            
        # Ensure existing users get their Gmail profile photo updated
        if "picture" in idinfo and user.avatar_url != idinfo["picture"]:
            user.avatar_url = idinfo["picture"]
            updated = True
            
        # Update username if they were stuck with the old email prefix or we found a better name
        if full_name and user.username != full_name:
            user.username = full_name
            updated = True
            
        if updated:
            db.commit()
            db.refresh(user)

    # 2. Generate Tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # 3. Create Session
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_otp(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        is_active=True
    )
    db.add(new_session)

    perms = []
    admin_prof = db.query(AdminProfile).filter(AdminProfile.user_id == user.id).first()
    if admin_prof and admin_prof.status == "ACTIVE":
        if admin_prof.is_super_admin:
            perms.append("super_admin")
        if admin_prof.role:
            for p in admin_prof.role.permissions:
                perms.append(p.name)
        for p in admin_prof.custom_permissions:
            perms.append(p.name)

        # Log session and audit for admin
        new_sess = AdminSession(
            admin_id=admin_prof.id,
            refresh_token_hash=hash_otp(refresh_token),
            ip_address="127.0.0.1",
            device_info="Google Auth Client",
            is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            last_seen=datetime.now(timezone.utc)
        )
        new_audit = AdminAuditLog(
            admin_id=admin_prof.id,
            action="ADMIN_LOGIN_GOOGLE",
            resource_type="AdminProfile",
            resource_id=str(admin_prof.id),
            ip_address="127.0.0.1",
            new_state={"login": "success_google"}
        )
        db.add(new_sess)
        db.add(new_audit)

    db.commit()

    set_refresh_cookie(response, refresh_token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "name": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_new_user": is_new,
        "role": user.role,
        "permissions": list(set(perms))
    }

@router.get("/sessions")
def get_user_sessions(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all active sessions for the current user."""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).order_by(UserSession.last_activity.desc()).all()
    
    current_ua = request.headers.get("user-agent", "")
    current_ip = request.client.host if request.client else ""
    
    return {
        "sessions": [
            {
                "id": str(s.id),
                "ip_address": s.ip_address,
                "device_info": s.user_agent or "Unknown Client",
                "last_seen": s.last_activity.isoformat() if s.last_activity else s.created_at.isoformat(),
                "created_at": s.created_at.isoformat(),
                "is_current": s.user_agent == current_ua and s.ip_address == current_ip
            }
            for s in sessions
        ]
    }

@router.delete("/sessions/{session_id}")
def revoke_user_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Revoke a specific session."""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.is_active = False
    db.commit()
    return {"message": "Session revoked"}

@router.post("/me/avatar")
async def upload_avatar(avatar: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Upload user avatar (saved as base64 data URI)."""
    if not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    # Read file and convert to base64
    contents = await avatar.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be less than 5MB")
        
    b64 = base64.b64encode(contents).decode('utf-8')
    data_uri = f"data:{avatar.content_type};base64,{b64}"
    
    current_user.avatar_url = data_uri
    db.commit()
    return {"message": "Avatar updated", "avatar_url": data_uri}

@router.delete("/me")
def delete_account(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Permanently delete user account."""
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="Admin accounts must be deleted via admin panel")
        
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

