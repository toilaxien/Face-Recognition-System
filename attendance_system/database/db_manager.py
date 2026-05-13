from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, AttendanceLog
import json
import numpy as np
from datetime import datetime, date

class DatabaseManager:
    def __init__(self, db_url="sqlite:///attendance.db"):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def add_user(self, student_id, name, embedding_array, image_path=None):
        session = self.Session()
        try:
            # Check if user exists
            user = session.query(User).filter_by(student_id=student_id).first()
            if user:
                # Update embedding and name
                user.name = name
                user.embedding = json.dumps(embedding_array.tolist())
                if image_path: user.image_path = image_path
            else:
                user = User(
                    student_id=student_id,
                    name=name,
                    image_path=image_path,
                    embedding=json.dumps(embedding_array.tolist())
                )
                session.add(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding user: {e}")
            return False
        finally:
            session.close()

    def get_all_users(self):
        session = self.Session()
        try:
            users = session.query(User).all()
            user_data = []
            for u in users:
                user_data.append({
                    "id": u.id,
                    "student_id": u.student_id,
                    "name": u.name,
                    "image_path": u.image_path,
                    "embedding": np.array(json.loads(u.embedding))
                })
            return user_data
        finally:
            session.close()
            
    def get_last_attendance_today(self, user_id):
        session = self.Session()
        try:
            today = date.today()
            # Get latest log for today
            log = session.query(AttendanceLog)\
                .filter(AttendanceLog.user_id == user_id)\
                .filter(AttendanceLog.timestamp >= datetime.combine(today, datetime.min.time()))\
                .order_by(AttendanceLog.timestamp.desc())\
                .first()
            
            if log:
                return {
                    "status": log.status,
                    "timestamp": log.timestamp
                }
            return None
        finally:
            session.close()

    def log_attendance(self, user_id, status, similarity_score, captured_image_path=None):
        session = self.Session()
        try:
            log = AttendanceLog(
                user_id=user_id,
                status=status,
                similarity_score=similarity_score,
                captured_image_path=captured_image_path
            )
            session.add(log)
            session.commit()
            return log.id
        except Exception as e:
            session.rollback()
            print(f"Error logging attendance: {e}")
            return None
        finally:
            session.close()
            
    def get_today_logs(self):
        session = self.Session()
        try:
            today = date.today()
            logs = session.query(AttendanceLog, User)\
                .join(User)\
                .filter(AttendanceLog.timestamp >= datetime.combine(today, datetime.min.time()))\
                .order_by(AttendanceLog.timestamp.desc())\
                .limit(50)\
                .all()
                
            result = []
            for log, user in logs:
                result.append({
                    "user_id": user.id,
                    "name": user.name,
                    "student_id": user.student_id,
                    "status": log.status,
                    "time": log.timestamp.strftime("%H:%M:%S"),
                    "score": round(log.similarity_score, 2),
                    "captured_image_path": log.captured_image_path,
                    "registered_image_path": user.image_path
                })
            return result
        finally:
            session.close()

    def delete_user(self, user_id):
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                # Delete all attendance logs for this user first (FK constraint)
                session.query(AttendanceLog).filter_by(user_id=user_id).delete()
                session.delete(user)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error deleting user: {e}")
            return False
        finally:
            session.close()
            
    def get_all_logs_full(self):
        session = self.Session()
        try:
            logs = session.query(AttendanceLog, User)\
                .join(User)\
                .order_by(AttendanceLog.timestamp.desc())\
                .all()
                
            result = []
            for log, user in logs:
                result.append({
                    "id": log.id,
                    "name": user.name,
                    "student_id": user.student_id,
                    "status": log.status,
                    "date": log.timestamp.strftime("%Y-%m-%d"),
                    "time": log.timestamp.strftime("%H:%M:%S"),
                    "score": round(log.similarity_score, 2),
                    "captured_image_path": log.captured_image_path,
                    "registered_image_path": user.image_path
                })
            return result
        finally:
            session.close()

    def get_user_logs(self, user_id):
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user: return None
            
            logs = session.query(AttendanceLog)\
                .filter(AttendanceLog.user_id == user_id)\
                .order_by(AttendanceLog.timestamp.desc())\
                .all()
                
            checkins = sum(1 for log in logs if log.status == "Check-in")
            checkouts = sum(1 for log in logs if log.status == "Check-out")
            
            return {
                "user": {
                    "id": user.id,
                    "student_id": user.student_id,
                    "name": user.name,
                    "image_path": user.image_path
                },
                "stats": {
                    "total_logs": len(logs),
                    "checkins": checkins,
                    "checkouts": checkouts,
                    "current_status": logs[0].status if logs else "None"
                },
                "logs": [{
                    "id": log.id,
                    "status": log.status,
                    "date": log.timestamp.strftime("%Y-%m-%d"),
                    "time": log.timestamp.strftime("%H:%M:%S"),
                    "score": round(log.similarity_score, 2),
                    "captured_image_path": log.captured_image_path
                } for log in logs]
            }
        finally:
            session.close()

