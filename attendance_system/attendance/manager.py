from datetime import datetime
from utils.logger import logger

class AttendanceManager:
    def __init__(self, db_manager, cooldown_seconds=5):
        self.db = db_manager
        self.cooldown_seconds = cooldown_seconds
        
    def process_recognition(self, user_id, user_name, similarity_score, threshold=0.5, captured_image_path=None):
        """
        Process a recognized face and handle check-in/out logic.
        Logic:
        - First scan of the day -> Check-in
        - Next scan (same person, past cooldown) -> toggles: Check-in becomes Check-out, Check-out becomes Check-in
        - Within cooldown -> ignored (prevents accidental double scans)
        """
        if similarity_score < threshold:
            return {"status": "Unknown", "message": "Similarity too low"}
            
        last_log = self.db.get_last_attendance_today(user_id)
        now = datetime.now()
        
        if not last_log:
            # First time seeing today -> Check-in
            log_id = self.db.log_attendance(user_id, "Check-in", similarity_score, captured_image_path)
            logger.info(f"User {user_name} (ID: {user_id}) Checked-in. Score: {similarity_score:.2f}")
            return {"status": "Check-in", "name": user_name, "message": "Check-in successful", "log_id": log_id}
            
        # Already logged today, check time difference (in seconds)
        time_diff = (now - last_log["timestamp"]).total_seconds()
        
        if time_diff < self.cooldown_seconds:
            # Within cooldown, ignore to prevent spam
            remaining = int(self.cooldown_seconds - time_diff)
            return {"status": "Cooldown", "name": user_name, "message": f"Please wait {remaining}s"}
            
        # Passed cooldown -> Toggle status
        if last_log["status"] == "Check-in":
            # Was checked in -> now check out
            log_id = self.db.log_attendance(user_id, "Check-out", similarity_score, captured_image_path)
            logger.info(f"User {user_name} (ID: {user_id}) Checked-out. Score: {similarity_score:.2f}")
            return {"status": "Check-out", "name": user_name, "message": "Check-out successful", "log_id": log_id}
        else:
            # Was checked out -> now check in again
            log_id = self.db.log_attendance(user_id, "Check-in", similarity_score, captured_image_path)
            logger.info(f"User {user_name} (ID: {user_id}) Checked-in again. Score: {similarity_score:.2f}")
            return {"status": "Check-in", "name": user_name, "message": "Check-in successful", "log_id": log_id}
