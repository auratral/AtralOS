from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.core import StaffAccount
from app.schemas.auth import TokenResponse, UserMeResponse
from app.security.auth import verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    result = await db.execute(select(StaffAccount).where(StaffAccount.email == form_data.username.lower()))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account is inactive",
        )
        
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "department_id": user.department_id,
        "name": user.name
    }

@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: StaffAccount = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "department_id": current_user.department_id,
        "status": current_user.status
    }
