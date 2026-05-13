import torch
from torchvision import transforms
import numpy as np

class FaceRecognizer:
    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.to(device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((112, 112)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        
    def get_embedding(self, face_pil):
        """
        Extracts embedding from a cropped PIL image.
        """
        tensor = self.transform(face_pil).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model(tensor)
            # Normalize embedding for Cosine Similarity
            embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
        return embedding.cpu().numpy()[0]
        
    def compute_similarity(self, emb1, emb2):
        """
        Computes cosine similarity between two embeddings.
        """
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
    def match(self, target_embedding, db_embeddings, db_user_ids, threshold=0.5):
        """
        Finds the best match in the database.
        db_embeddings is a numpy array of shape (N, embedding_size)
        db_user_ids is a list of length N
        """
        if len(db_embeddings) == 0:
            return None, 0.0
            
        # target_embedding shape: (embedding_size,)
        # Compute similarities with all DB embeddings
        similarities = np.dot(db_embeddings, target_embedding) / (
            np.linalg.norm(db_embeddings, axis=1) * np.linalg.norm(target_embedding)
        )
        
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            return db_user_ids[best_idx], float(best_score)
        
        return None, float(best_score)
