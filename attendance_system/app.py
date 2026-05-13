import os
import io
import base64
import json
import torch
import asyncio
import uuid
from PIL import Image
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from utils.logger import logger
from models.arcface import load_model
from detection.detector import FaceDetector
from recognition.recognizer import FaceRecognizer
from database.db_manager import DatabaseManager
from attendance.manager import AttendanceManager

# Constants
MODEL_PATH = r"d:\Project_by_myself\Face_Recognition_System\arcFace_model\best_model.pth"
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Initialize App
app = FastAPI(title="Face Recognition Attendance System")

# Ensure UI and Data dirs exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(UI_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "registered"), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "captured"), exist_ok=True)

app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# Global instances
db = DatabaseManager()
attendance_mgr = AttendanceManager(db, cooldown_seconds=30)  # 30 sec cooldown - person reads info then walks away
detector = FaceDetector(device=DEVICE)

# Load ArcFace Model
try:
    arcface_model = load_model(MODEL_PATH, device=DEVICE)
    recognizer = FaceRecognizer(arcface_model, device=DEVICE)
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    recognizer = None

# Cache users in memory for fast matching
users_cache = []
embeddings_cache = []
user_ids_cache = []

def refresh_cache():
    global users_cache, embeddings_cache, user_ids_cache
    users = db.get_all_users()
    users_cache = users
    if users:
        import numpy as np
        embeddings_cache = np.array([u["embedding"] for u in users])
        user_ids_cache = [u["id"] for u in users]
        # Store user dicts for quick lookup
        users_cache = users
    else:
        embeddings_cache = []
        user_ids_cache = []
    logger.info(f"Refreshed cache. Total users: {len(users)}")

refresh_cache()

@app.get("/")
async def get_index():
    with open(os.path.join(UI_DIR, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/api/register")
async def register_user(
    student_id: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...)
):
    if not recognizer:
        raise HTTPException(status_code=500, detail="Model not loaded")
        
    # Read image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert('RGB')
    
    # Detect face
    cropped_faces, boxes, probs = detector.detect_and_crop(image)
    
    if len(cropped_faces) == 0:
        raise HTTPException(status_code=400, detail="No face detected in the image")
    if len(cropped_faces) > 1:
        raise HTTPException(status_code=400, detail="Multiple faces detected. Please use an image with only one face.")
        
    # Extract embedding
    face_img = cropped_faces[0]
    embedding = recognizer.get_embedding(face_img)
    
    # Save registered image
    img_filename = f"{student_id}_{uuid.uuid4().hex[:8]}.jpg"
    img_path = os.path.join(DATA_DIR, "registered", img_filename)
    face_img.save(img_path)
    relative_img_path = f"/data/registered/{img_filename}"
    
    # Save to DB
    success = db.add_user(student_id, name, embedding, image_path=relative_img_path)
    
    if success:
        refresh_cache()
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save user to database")

@app.get("/api/stats")
async def get_stats():
    logs = db.get_today_logs()
    return {
        "total_users": len(users_cache),
        "today_logs": logs
    }

@app.get("/api/users")
async def get_users():
    # Return user list without embeddings to save bandwidth
    return [{"id": u["id"], "student_id": u["student_id"], "name": u["name"]} for u in users_cache]

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    success = db.delete_user(user_id)
    if success:
        refresh_cache()
        return {"message": "User deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found or delete failed")

@app.get("/api/logs/all")
async def get_all_logs():
    return db.get_all_logs_full()

@app.get("/api/users/{user_id}/logs")
async def get_user_logs_api(user_id: int):
    data = db.get_user_logs(user_id)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return data

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if not recognizer:
        await websocket.send_json({"error": "Model not loaded on server"})
        await websocket.close()
        return
        
    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_text()
            
            # Format: "data:image/jpeg;base64,....."
            if not data.startswith("data:image/jpeg;base64,"):
                continue
                
            base64_data = data.split(",")[1]
            image_data = base64.b64decode(base64_data)
            image_pil = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            # 1. Detect faces
            cropped_faces, boxes, probs = detector.detect_and_crop(image_pil)
            
            results = []
            
            # 2. Recognize and process attendance
            for i, face_img in enumerate(cropped_faces):
                # Get embedding from ArcFace
                emb = recognizer.get_embedding(face_img)
                
                # Match against registered users
                # Higher threshold = stricter matching (fewer false positives)
                matched_id, score = recognizer.match(emb, embeddings_cache, user_ids_cache, threshold=0.6)
                
                logger.info(f"Face {i}: best_score={score:.4f}, matched_id={matched_id}, threshold=0.6")
                
                if matched_id:
                    # Find user
                    user = next(u for u in users_cache if u["id"] == matched_id)
                    
                    # Pre-generate image path in case it's a successful log
                    cap_filename = f"log_{uuid.uuid4().hex}.jpg"
                    cap_path = os.path.join(DATA_DIR, "captured", cap_filename)
                    relative_cap_path = f"/data/captured/{cap_filename}"
                    
                    # Process attendance
                    att_result = attendance_mgr.process_recognition(matched_id, user["name"], score, captured_image_path=relative_cap_path)
                    
                    if att_result["status"] in ["Check-in", "Check-out"]:
                        # Save the image since it's a valid log
                        face_img.save(cap_path)
                    
                    results.append({
                        "box": boxes[i],
                        "name": user["name"],
                        "student_id": user["student_id"],
                        "score": round(score, 2),
                        "status": att_result["status"],
                        "message": att_result["message"],
                        "registered_image": user.get("image_path", ""),
                        "captured_image": relative_cap_path if att_result["status"] in ["Check-in", "Check-out"] else ""
                    })
                else:
                    results.append({
                        "box": boxes[i],
                        "name": "Unknown",
                        "student_id": "",
                        "score": round(score, 2) if score else 0.0,
                        "status": "Unknown",
                        "message": "Not recognized"
                    })
                    
            # Send back results
            await websocket.send_json({"results": results})
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
