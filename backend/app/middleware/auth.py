# middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Union

from app.database import get_db
from app.models import Admin, Employee
from app.utils.auth import verify_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Union[Admin, Employee]:
    """Get current authenticated user (admin or employee)."""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        user_id: int = payload.get("user_id")
        user_type: str = payload.get("user_type")
        company: str = payload.get("company")
        
        if user_id is None or user_type is None or company is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    if user_type == "admin":
        user = db.query(Admin).filter(
            Admin.id == user_id,
            Admin.company == company
        ).first()
    elif user_type == "employee":
        user = db.query(Employee).filter(
            Employee.id == user_id,
            Employee.company == company
        ).first()
    else:
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_admin(
    current_user: Union[Admin, Employee] = Depends(get_current_user)
) -> Admin:
    """Ensure current user is an admin."""
    if not isinstance(current_user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user

async def get_current_employee(
    current_user: Union[Admin, Employee] = Depends(get_current_user)
) -> Employee:
    """Ensure current user is an employee."""
    if not isinstance(current_user, Employee):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Employee access required."
        )
    return current_user