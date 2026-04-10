import os

with open("app/api/auth.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

clean_lines = lines[:417]

get_me = """
@router.get("/me", response_model=AuthResponse)
def read_users_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    \"\"\"
    Get current logged in user details.
    \"\"\"
    
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
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "is_new_user": False,
        "role": current_user.role,
        "permissions": list(set(perms))
    }
"""

google_login = """
@router.post("/google", response_model=AuthResponse)
def google_login(payload: dict, db: Session = Depends(get_db)):
    \"\"\"
    Login with Google credential. Generates JWT directly and sets up AdminSession if applicable.
    \"\"\"
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    from app.core.config import settings

    credential = payload.get("credential")
    if not credential:
        raise HTTPException(status_code=400, detail="Missing credential")

    try:
        client_id = settings.GOOGLE_CLIENT_ID
        idinfo = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
        email = idinfo['email'].lower()
    except Exception as e:
        print(f"Google Token Verification Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid Google token")

    # 1. Get or Create User
    user = db.query(User).filter(User.email == email).first()
    is_new = False
    
    if not user:
        is_new = True
        user = User(
            email=email,
            username=email.split("@")[0],
            is_verified=True,
            role="user"
        )
        if "picture" in idinfo:
            user.avatar_url = idinfo["picture"]
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.is_verified:
            user.is_verified = True
            db.commit()

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

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_new_user": is_new,
        "role": user.role,
        "permissions": list(set(perms))
    }
"""

with open("app/api/auth.py", "w", encoding="utf-8") as f:
    f.writelines(clean_lines)
    f.write(get_me)
    f.write("\n")
    f.write(google_login)
    f.write("\n")
