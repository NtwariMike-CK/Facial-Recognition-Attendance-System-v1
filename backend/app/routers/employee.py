# routers/employee.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List
from datetime import datetime, date, time

from app.database import get_db
from app.models import Employee, AttendanceRecord, Ticket, Admin
from app.schemas import (
    EmployeeDashboard, TicketCreate, TicketResponse,
    AttendanceRecord as AttendanceRecordSchema
)
from app.middleware.auth import get_current_employee

router = APIRouter()

@router.get("/dashboard", response_model=EmployeeDashboard)
async def get_employee_dashboard(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get employee dashboard with attendance summary."""
    
    employee_id = current_employee.id
    
    # Get attendance statistics
    attendance_stats = db.query(
        AttendanceRecord.status,
        func.count(AttendanceRecord.id).label('count')
    ).filter(
        AttendanceRecord.employee_id == employee_id
    ).group_by(AttendanceRecord.status).all()
    
    # Initialize counters
    total_present = 0
    total_late = 0
    total_absent = 0
    
    for status, count in attendance_stats:
        if status == "present":
            total_present = count
        elif status == "late":
            total_late = count
        elif status == "absent":
            total_absent = count
    
    # Calculate average arrival and departure times
    avg_times = db.query(
        func.avg(func.extract('hour', AttendanceRecord.arrival_time)).label('avg_arrival_hour'),
        func.avg(func.extract('minute', AttendanceRecord.arrival_time)).label('avg_arrival_minute'),
        func.avg(func.extract('hour', AttendanceRecord.departure_time)).label('avg_departure_hour'),
        func.avg(func.extract('minute', AttendanceRecord.departure_time)).label('avg_departure_minute')
    ).filter(
        and_(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.departure_time.isnot(None)
        )
    ).first()
    
    # Format average times
    average_arrival_time = None
    average_departure_time = None
    
    if avg_times.avg_arrival_hour is not None:
        avg_arrival_hour = int(avg_times.avg_arrival_hour)
        avg_arrival_minute = int(avg_times.avg_arrival_minute or 0)
        average_arrival_time = f"{avg_arrival_hour:02d}:{avg_arrival_minute:02d}"
    
    if avg_times.avg_departure_hour is not None:
        avg_departure_hour = int(avg_times.avg_departure_hour)
        avg_departure_minute = int(avg_times.avg_departure_minute or 0)
        average_departure_time = f"{avg_departure_hour:02d}:{avg_departure_minute:02d}"
    
    # Get recent attendance records (last 10)
    recent_attendance = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == employee_id
    ).order_by(AttendanceRecord.date.desc()).limit(10).all()
    
    return EmployeeDashboard(
        total_present=total_present,
        total_late=total_late,
        total_absent=total_absent,
        average_arrival_time=average_arrival_time,
        average_departure_time=average_departure_time,
        recent_attendance=recent_attendance
    )

@router.get("/attendance", response_model=List[AttendanceRecordSchema])
async def get_employee_attendance(
    date_from: str = None,
    date_to: str = None,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get employee's attendance records with optional date filters."""
    
    query = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == current_employee.id
    )
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(func.date(AttendanceRecord.date) >= from_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(func.date(AttendanceRecord.date) <= to_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    attendance_records = query.order_by(AttendanceRecord.date.desc()).all()
    
    return attendance_records

@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Create a new support ticket."""
    
    # Get the admin for this employee's company
    admin = db.query(Admin).filter(
        Admin.company == current_employee.company
    ).first()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No admin found for your company"
        )
    
    # Create new ticket
    new_ticket = Ticket(
        admin_id=admin.id,
        employee_id=current_employee.id,
        message=ticket_data.message,
        status="pending"
    )
    
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    return new_ticket

@router.get("/tickets", response_model=List[TicketResponse])
async def get_employee_tickets(
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get all tickets submitted by the employee."""
    
    tickets = db.query(Ticket).filter(
        Ticket.employee_id == current_employee.id
    ).order_by(Ticket.created_at.desc()).all()
    
    return tickets

@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Get a specific ticket by ID."""
    
    ticket = db.query(Ticket).filter(
        and_(
            Ticket.id == ticket_id,
            Ticket.employee_id == current_employee.id
        )
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return ticket

@router.get("/profile")
async def get_employee_profile(
    current_employee: Employee = Depends(get_current_employee)
):
    """Get employee profile information."""
    
    return {
        "id": current_employee.id,
        "name": current_employee.name,
        "email": current_employee.email,
        "role": current_employee.role,
        "department": current_employee.department,
        "company": current_employee.company,
        "created_at": current_employee.created_at
    }