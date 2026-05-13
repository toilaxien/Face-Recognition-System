# Face Recognition Attendance System

A production-ready Facial Recognition Attendance System using a custom-trained ArcFace model, MTCNN for face detection, and a modern FastAPI + WebSockets backend.

## Features
- **Real-time Detection & Recognition:** Uses WebSockets to stream frames to the backend, ensuring low-latency bounding box tracking and recognition.
- **Custom ArcFace Model Integration:** Loads a pre-trained PyTorch ArcFace model (`.pth`).
- **Check-in / Check-out Logic:** Automatic attendance logging with a configurable cooldown timer to prevent duplicate logs.
- **Dashboard:** Modern, glassmorphism UI to view today's attendance logs in real-time.
- **SQLite Database:** Stores user embeddings and attendance logs for easy setup and querying.

## System Architecture
- **Backend:** FastAPI, PyTorch, SQLAlchemy
- **Frontend:** HTML5 Canvas, Vanilla JS, CSS Glassmorphism
- **Face Detection:** MTCNN (`facenet-pytorch`)
- **Face Recognition:** ArcFace (ResNet50 backbone)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Verify Model Path:
Ensure your `best_model.pth` is located at `d:\Project_by_myself\Face_Recognition_System\arcFace_model\best_model.pth`. If not, update the `MODEL_PATH` variable in `app.py`.

## Running the Application

1. Start the FastAPI server:
```bash
python app.py
```
*(or run `uvicorn app:app --host 0.0.0.0 --port 8000`)*

2. Open your web browser and navigate to:
```
http://localhost:8000
```

## Usage
1. **Register a User:** Click the "Register New User" button. Fill in the Student/Employee ID, Name, and upload a clear picture containing only one face.
2. **Start Camera:** Click "Start Camera" to begin real-time attendance.
3. **Attendance Logic:** 
   - The first time a user is recognized, it logs a **Check-in**.
   - After a cooldown period (default: 1 minute for testing, can be adjusted in `app.py`), the next recognition logs a **Check-out**.

## Project Structure
- `app.py`: Main FastAPI application.
- `models/arcface.py`: Model definition for loading custom ArcFace weights.
- `detection/detector.py`: MTCNN implementation for detecting and cropping faces.
- `recognition/recognizer.py`: Embedding extraction and Cosine Similarity logic.
- `database/db_manager.py` & `models.py`: SQLite Database operations and ORM.
- `attendance/manager.py`: Attendance business logic.
- `ui/`: Frontend assets (HTML, CSS, JS).

## Disclaimer
This system uses a basic similarity threshold. In a real-world production environment, the threshold might need to be fine-tuned based on lighting conditions and the variance of your specific dataset.
