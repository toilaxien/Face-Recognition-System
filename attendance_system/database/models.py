from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    image_path = Column(String(255), nullable=True) # Path to registered face image
    embedding = Column(String, nullable=False) # Store JSON string of the float array
    created_at = Column(DateTime, default=datetime.now)
    
    logs = relationship("AttendanceLog", back_populates="user")

class AttendanceLog(Base):
    __tablename__ = 'attendance_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    status = Column(String(20), nullable=False) # 'Check-in' or 'Check-out'
    similarity_score = Column(Float, nullable=False)
    captured_image_path = Column(String(255), nullable=True) # Path to face image captured during log
    
    user = relationship("User", back_populates="logs")
