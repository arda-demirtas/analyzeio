import random
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, VerificationCode
from backend.schemas import UserCreate, UserLogin, UserChangePassword, UserResponse, Token, ProfilePictureUpdate, VerificationConfirm, CodeConfirm
from backend.auth import get_password_hash, verify_password, create_access_token, get_current_user
from backend.email_helper import send_verification_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register/request", status_code=status.HTTP_200_OK)
def register_request(user_data: UserCreate, db: Session = Depends(get_db)):
    """Validates registration details and sends a 6-digit email verification code."""
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Generate 6-digit code
    code = f"{random.randint(100000, 999999)}"
    
    # Store verification code
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    
    # Delete any existing verification codes for this email and purpose to prevent clutter
    db.query(VerificationCode).filter(
        VerificationCode.email == user_data.email, 
        VerificationCode.purpose == "register"
    ).delete()
    
    payload = {
        "username": user_data.username,
        "password": user_data.password
    }
    
    verification_entry = VerificationCode(
        email=user_data.email,
        code=code,
        purpose="register",
        data=json.dumps(payload),
        expires_at=expires_at
    )
    db.add(verification_entry)
    db.commit()
    
    # Send verification email
    sent = send_verification_email(user_data.email, code, "register")
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again."
        )
        
    return {"message": "Verification code sent to your email"}

@router.post("/register/confirm", response_model=Token)
def register_confirm(confirm_data: VerificationConfirm, db: Session = Depends(get_db)):
    """Verifies the registration code and creates the user account, returning a login token."""
    now = datetime.datetime.utcnow()
    # Find verification entry
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == confirm_data.email,
        VerificationCode.code == confirm_data.code,
        VerificationCode.purpose == "register",
        VerificationCode.expires_at > now
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
        
    # Extract payload
    try:
        payload = json.loads(verification.data)
        username = payload["username"]
        password = payload["password"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Corrupted verification data"
        )
        
    # Double check username/email uniqueness in case someone else registered in the meantime
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    existing_email = db.query(User).filter(User.email == confirm_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create user
    hashed_pwd = get_password_hash(password)
    new_user = User(
        username=username,
        email=confirm_data.email,
        hashed_password=hashed_pwd
    )
    db.add(new_user)
    
    # Delete the verification entry
    db.delete(verification)
    db.commit()
    
    # Authenticate and return JWT access token
    access_token = create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticates user credentials and returns a JWT access token."""
    # Find user by username
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create and return access token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/change-password/request", status_code=status.HTTP_200_OK)
def change_password_request(data: UserChangePassword, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verifies old password and sends a verification code to user's email for password change."""
    # Verify current password
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
        
    # Generate 6-digit code
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    
    # Delete previous change_password entries for this email
    db.query(VerificationCode).filter(
        VerificationCode.email == current_user.email,
        VerificationCode.purpose == "change_password"
    ).delete()
    
    payload = {
        "new_password": data.new_password
    }
    
    verification_entry = VerificationCode(
        email=current_user.email,
        code=code,
        purpose="change_password",
        data=json.dumps(payload),
        expires_at=expires_at
    )
    db.add(verification_entry)
    db.commit()
    
    # Send verification email
    sent = send_verification_email(current_user.email, code, "change_password")
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
        
    return {"message": "Verification code sent to your email"}

@router.post("/change-password/confirm", status_code=status.HTTP_200_OK)
def change_password_confirm(confirm_data: CodeConfirm, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verifies code and performs the password update."""
    now = datetime.datetime.utcnow()
    # Find verification entry
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == current_user.email,
        VerificationCode.code == confirm_data.code,
        VerificationCode.purpose == "change_password",
        VerificationCode.expires_at > now
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
        
    # Extract payload
    try:
        payload = json.loads(verification.data)
        new_password = payload["new_password"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Corrupted verification data"
        )
        
    # Update user password
    current_user.hashed_password = get_password_hash(new_password)
    
    # Delete the verification entry
    db.delete(verification)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.delete("/delete-account", status_code=status.HTTP_200_OK)
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Permanently deletes the current user's profile and watchlist items (closes account)."""
    db.delete(current_user)
    db.commit()
    return {"message": "Account successfully closed and all user data deleted"}

@router.put("/profile-picture", response_model=UserResponse)
def update_profile_picture(data: ProfilePictureUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Updates the profile picture of the currently logged-in user."""
    current_user.profile_picture = data.profile_picture
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently logged-in user profile details (including avatar)."""
    return current_user

@router.post("/premium/toggle", response_model=UserResponse)
def toggle_premium(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggles the premium membership status of the currently authenticated user."""
    current_user.is_premium = not current_user.is_premium
    db.commit()
    db.refresh(current_user)
    return current_user
