import torch
from facenet_pytorch import MTCNN
from PIL import Image
import numpy as np
import cv2

class FaceDetector:
    def __init__(self, device='cpu'):
        self.device = device
        # Initialize MTCNN for face detection
        # keep_all=True allows detecting multiple faces in one frame
        self.mtcnn = MTCNN(
            image_size=112, 
            margin=0, 
            min_face_size=40,
            thresholds=[0.6, 0.7, 0.7], 
            factor=0.709, 
            keep_all=True, 
            device=device
        )
        
    def detect_and_crop(self, image_pil):
        """
        Detects faces in a PIL image and returns:
        - cropped_faces: List of PIL images cropped and resized to 112x112
        - boxes: List of bounding boxes [x1, y1, x2, y2]
        - probs: List of detection probabilities
        """
        # Detect faces
        boxes, probs = self.mtcnn.detect(image_pil)
        
        if boxes is None:
            return [], [], []
            
        cropped_faces = []
        valid_boxes = []
        valid_probs = []
        
        for box, prob in zip(boxes, probs):
            if prob < 0.90:  # Ignore low confidence detections
                continue
                
            # Expand box slightly (margin)
            x1, y1, x2, y2 = box
            w = x2 - x1
            h = y2 - y1
            
            # Simple margin
            margin_x = w * 0.1
            margin_y = h * 0.1
            
            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(image_pil.width, x2 + margin_x)
            y2 = min(image_pil.height, y2 + margin_y)
            
            face = image_pil.crop((x1, y1, x2, y2))
            face = face.resize((112, 112), Image.Resampling.BILINEAR)
            
            cropped_faces.append(face)
            valid_boxes.append([x1, y1, x2, y2])
            valid_probs.append(prob)
            
        return cropped_faces, valid_boxes, valid_probs
