# database_client.py
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseClient:
    """Enhanced client with login flow and company data fetching"""
    
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.token = None
        self.user_info = None
        
    def _make_request(self, method: str, endpoint: str, token: str = None, **kwargs) -> Dict:
        """Make HTTP request to API"""
        url = self.config.get_api_url(endpoint)
        
        # Use stored token if no token provided
        if not token and self.token:
            token = self.token
            
        # Add authorization header if token provided
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_data = response.json()
                    message = error_data.get("detail", f"HTTP {response.status_code}")
                except:
                    message = f"HTTP {response.status_code}"
                
                return {"success": False, "message": message}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Cannot connect to server. Check your internet connection and API URL."}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Request timed out"}
        except Exception as e:
            return {"success": False, "message": f"Request failed: {str(e)}"}
    
    def login_and_load_company_data(self, email: str, password: str) -> Dict:
        """Complete login flow: authenticate, get profile, load company data"""
        logger.info(f"Starting login process for {email}")
        
        # Step 1: Login
        login_result = self.login(email, password)
        if not login_result["success"]:
            return login_result
            
        # Step 2: Get user profile
        profile_result = self.get_user_profile()
        if not profile_result["success"]:
            logger.warning("Failed to get user profile, continuing anyway")
            
        # Step 3: Load company data
        company_data_result = self.load_company_data()
        
        return {
            "success": True,
            "login_data": login_result,
            "profile_data": profile_result.get("data") if profile_result["success"] else None,
            "company_data": company_data_result
        }
    
    def login(self, email: str, password: str) -> Dict:
        """Login admin and get access token"""
        data = {
            "email": email,
            "password": password
        }
        
        result = self._make_request("POST", "auth/admin/login", json=data)
        
        if result["success"]:
            token_data = result["data"]
            # Store token and user info for subsequent requests
            self.token = token_data["access_token"]
            self.user_info = {
                "user_id": token_data["user_id"],
                "company": token_data["company"],
                "user_type": token_data.get("user_type", "admin")
            }
            
            logger.info(f"Login successful for company: {self.user_info['company']}")
            
            return {
                "success": True,
                "token": self.token,
                "company": self.user_info["company"],
                "user_id": self.user_info["user_id"],
                "user_type": self.user_info["user_type"]
            }
        else:
            logger.error(f"Login failed: {result['message']}")
            return result
    
    def get_user_profile(self) -> Dict:
        """Get current user profile"""
        if not self.token:
            return {"success": False, "message": "Not authenticated"}
            
        result = self._make_request("GET", "admin/profile")
        
        if result["success"]:
            logger.info("User profile retrieved successfully")
            return result
        else:
            logger.error(f"Failed to get user profile: {result['message']}")
            return result
    
    def load_company_data(self) -> Dict:
        """Load all company-specific data in parallel-like fashion"""
        if not self.token:
            return {"success": False, "message": "Not authenticated"}
            
        logger.info(f"Loading company data for: {self.user_info.get('company', 'Unknown')}")
        
        # Fetch all company data
        company_data = {
            "employees": None,
            "employee_images": None,
            "camera_settings": None,
            "today_attendance": None,
            "camera_status": None
        }
        
        errors = []
        
        # Get employees
        employees_result = self.get_employees()
        if employees_result:
            company_data["employees"] = employees_result
            logger.info(f"Loaded {len(employees_result)} employees")
        else:
            errors.append("Failed to load employees")
        
        # Get employee images
        images_result = self.get_employee_images()
        if images_result:
            company_data["employee_images"] = images_result
            logger.info(f"Loaded images for {len(images_result)} employees")
        else:
            errors.append("Failed to load employee images")
        
        # Get camera settings
        camera_settings_result = self.get_camera_settings()
        if camera_settings_result:
            company_data["camera_settings"] = camera_settings_result
            logger.info("Camera settings loaded")
        else:
            errors.append("Failed to load camera settings")
        
        # Get today's attendance
        attendance_result = self.get_today_attendance()
        if attendance_result:
            company_data["today_attendance"] = attendance_result
            logger.info("Today's attendance loaded")
        else:
            errors.append("Failed to load today's attendance")
        
        # Get camera status (optional)
        try:
            status_result = self._make_request("GET", "admin/camera-settings/status")
            if status_result["success"]:
                company_data["camera_status"] = status_result["data"]
                logger.info("Camera status loaded")
        except Exception as e:
            logger.warning(f"Could not load camera status: {e}")
        
        return {
            "success": True,
            "data": company_data,
            "errors": errors,
            "company": self.user_info.get("company"),
            "loaded_at": datetime.now().isoformat()
        }
    
    def get_employees(self) -> Optional[List[Dict]]:
        """Get all employees for the company"""
        result = self._make_request("GET", "admin/employees")
        
        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Failed to get employees: {result['message']}")
            return None
    
    def get_employee_images(self) -> Optional[List[Dict]]:
        """Get all employee images with base64 data"""
        result = self._make_request("GET", "admin/employees/images/all")
        
        if result["success"]:
            return result["data"]["employees"]
        else:
            logger.error(f"Failed to get employee images: {result['message']}")
            return None
    
    def get_camera_settings(self) -> Optional[Dict]:
        """Get camera settings for the company"""
        result = self._make_request("GET", "admin/camera-settings")
        
        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Failed to get camera settings: {result['message']}")
            return None
    
    def get_today_attendance(self) -> Optional[Dict]:
        """Get today's attendance records"""
        result = self._make_request("GET", "admin/attendance/today")
        
        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Failed to get today's attendance: {result['message']}")
            return None
    
    def create_attendance_record(self, attendance_data: Dict) -> bool:
        """Create attendance record"""
        result = self._make_request("POST", "admin/attendance", json=attendance_data)
        
        if result["success"]:
            logger.info(f"Attendance record created: {result['data']}")
            return True
        else:
            logger.error(f"Failed to create attendance record: {result['message']}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.token is not None
    
    def get_current_company(self) -> Optional[str]:
        """Get current company name"""
        return self.user_info.get("company") if self.user_info else None
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self.user_info.get("user_id") if self.user_info else None
    
    def logout(self):
        """Clear authentication data"""
        self.token = None
        self.user_info = None
        logger.info("Logged out")