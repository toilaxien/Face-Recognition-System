import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
import numpy as np
import os
from utils.logger import logger

class ArcMarginProduct(nn.Module):
    """
    Implementation of ArcFace: Additive Angular Margin Loss
    """
    def __init__(self, in_features, out_features, s=30.0, m=0.50, easy_margin=False):
        super(ArcMarginProduct, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.s = s
        self.m = m
        self.easy_margin = easy_margin
        
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        nn.init.xavier_uniform_(self.weight)
    
    def forward(self, input, label):
        cosine = F.linear(F.normalize(input), F.normalize(self.weight))
        sine = torch.sqrt(1.0 - torch.pow(cosine, 2))
        phi = cosine * np.cos(self.m) - sine * np.sin(self.m)
        
        if self.easy_margin:
            phi = torch.where(cosine > 0, phi, cosine)
        else:
            phi = torch.where(cosine > np.cos(np.pi - self.m), phi, cosine - np.sin(np.pi - self.m) * self.m)
        
        one_hot = torch.zeros(cosine.size(), device=input.device)
        one_hot.scatter_(1, label.view(-1, 1).long(), 1)
        
        output = (one_hot * phi) + ((1.0 - one_hot) * cosine)
        output *= self.s
        
        return output

class ArcFaceModel(nn.Module):
    def __init__(self, backbone='resnet50', embedding_size=512, num_classes=10575, pretrained=False):
        super(ArcFaceModel, self).__init__()
        
        # 1. Backbone
        if backbone == 'resnet50':
            self.backbone = models.resnet50(pretrained=pretrained)
            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        elif backbone == 'resnet101':
            self.backbone = models.resnet101(pretrained=pretrained)
            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")
        
        # 2. Embedding Head
        self.embedding = nn.Sequential(
            nn.BatchNorm1d(in_features),
            nn.Dropout(0.4),
            nn.Linear(in_features, embedding_size),
            nn.BatchNorm1d(embedding_size),
        )
        
        # 3. ArcFace Head
        # Default params as used in the notebook
        self.arcface = ArcMarginProduct(
            in_features=embedding_size,
            out_features=num_classes,
            s=30.0,  
            m=0.40   
        )
    
    def forward(self, x, labels=None):
        features = self.backbone(x)
        embeddings = self.embedding(features)
        
        if labels is not None:
            output = self.arcface(embeddings, labels)
            return output, embeddings
        
        return embeddings

def load_model(model_path, device='cpu'):
    """
    Loads the trained ArcFace model.
    Handles DataParallel prefixes if the model was trained on multiple GPUs.
    """
    logger.info(f"Loading ArcFace model from {model_path} on {device}...")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # Initialize model with the same architecture
    model = ArcFaceModel(backbone='resnet50', embedding_size=512, num_classes=10572, pretrained=False)
    
    # Load state dict
    checkpoint = torch.load(model_path, map_location=device)
    
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint
        
    # Remove 'module.' prefix if saved with DataParallel
    new_state_dict = {}
    for k, v in state_dict.items():
        name = k[7:] if k.startswith('module.') else k
        new_state_dict[name] = v
        
    # Load the state dict
    model.load_state_dict(new_state_dict, strict=True)
    model.to(device)
    model.eval()
    logger.info("ArcFace model loaded successfully.")
    return model
