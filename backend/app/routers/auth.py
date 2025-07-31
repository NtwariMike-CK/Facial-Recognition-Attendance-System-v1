# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models import Admin, Employee
from app.schemas import AdminRegister, AdminLogin, EmployeeLogin, Token
from app.utils.auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/admin/register", response_model=Token)
async def admin_register(admin_data: AdminRegister, db: Session = Depends(get_db)):
    """Register a new admin."""
    
    # Check if admin with this email already exists
    existing_admin = db.query(Admin).filter(Admin.email == admin_data.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this email already exists"
        )
    
    # Create new admin
    hashed_password = get_password_hash(admin_data.password)
    new_admin = Admin(
        name=admin_data.name,
        email=admin_data.email,
        role=admin_data.role,
        password_hash=hashed_password,
        company=admin_data.company
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": new_admin.id,
            "user_type": "admin",
            "company": new_admin.company
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "admin",
        "user_id": new_admin.id,
        "company": new_admin.company
    }

@router.post("/admin/login", response_model=Token)
async def admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    """Admin login."""
    
    # Find admin by email
    admin = db.query(Admin).filter(Admin.email == login_data.email).first()
    if not admin or not verify_password(login_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": admin.id,
            "user_type": "admin",
            "company": admin.company
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "admin",
        "user_id": admin.id,
        "company": admin.company
    }

@router.post("/employee/login", response_model=Token)
async def employee_login(login_data: EmployeeLogin, db: Session = Depends(get_db)):
    """Employee login."""
    
    # Find employee by id, email, and company
    employee = db.query(Employee).filter(
        Employee.id == login_data.id,
        Employee.email == login_data.email,
        Employee.company == login_data.company
    ).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid employee credentials"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": employee.id,
            "user_type": "employee",
            "company": employee.company
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "employee",
        "user_id": employee.id,
        "company": employee.company
    }