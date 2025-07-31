from sqlalchemy import inspect, select
from sqlalchemy.orm import Session
from database import engine, Base
from models import Admin, Employee, AttendanceRecord # Make sure all models are imported

# def drop_attendance_record_table():
#     inspector = inspect(engine)
#     table_name = "attendance_records"

#     if table_name in inspector.get_table_names():
#         print(f"⚠️ Dropping table '{table_name}'...")
#         AttendanceRecord.__table__.drop(engine)
#         print(f"✅ Table '{table_name}' has been dropped successfully.")
#     else:
#         print(f"❌ Table '{table_name}' does not exist.")

# if __name__ == "__main__":
#     drop_attendance_record_table()


# def show_all_attendance_records():
#     inspector = inspect(engine)
#     table_name = "attendance_records"

#     if table_name not in inspector.get_table_names():
#         print(f"❌ Table '{table_name}' does not exist in the database.")
#         return

#     with Session(engine) as session:
#         records = session.query(AttendanceRecord).all()
        
#         if records:
#             print(f"✅ Found {len(records)} attendance record(s):\n")
#             for record in records:
#                 print(f"ID: {record.id}")
#                 print(f"Employee ID: {record.employee_id}")
#                 print(f"arrival_time: {record.arrival_time}")
#                 print(f"departure_time: {record.departure_time}")
#                 print(f"hours_worked: {record.hours_worked}")
#                 print(f"status: {record.status}")
#                 print(f"camera_used: {record.camera_used}")
#                 print(f"date: {record.date}")
#                 print(f"company: {record.company}")
#                 print("-" * 30)
#         else:
#             print("❌ No attendance records found.")


def delete_all_attendance_records():
    inspector = inspect(engine)
    table_name = "attendance_records"

    if table_name not in inspector.get_table_names():
        print(f"❌ Table '{table_name}' does not exist in the database.")
        return

    with Session(engine) as session:
        try:
            deleted = session.query(AttendanceRecord).delete()
            session.commit()
            print(f"✅ Deleted {deleted} attendance record(s).")
        except Exception as e:
            session.rollback()
            print(f"❌ Error deleting attendance records: {e}")

if __name__ == "__main__":
    delete_all_attendance_records()



# from sqlalchemy import inspect
# from database import engine, Base




# # 👇 This is critical
# from models import Admin, Employee # Attendance  # Make sure all models are imported

# def list_employee_columns(id: int = 1):
#     inspector = inspect(engine)
#     table_name = "employees"

#     if table_name not in inspector.get_table_names():
#         print(f"❌ Table '{table_name}' does not exist in the database.")
#         return

#     columns = inspector.get_columns(table_name)
#     print(f"✅ Columns in the '{table_name}' table:")
#     for column in columns:
#         print(f" - {column['name']} ({column['type']})")

# if __name__ == "__main__":
#     list_employee_columns()

