Face Recognition System – Employee Attendance
Project Description

This project implements a comprehensive face recognition system for employee attendance management. The system allows:

Employee Management: Add, edit employee information and update face images.
Automatic Recognition: Automatically analyzes images, extracts embeddings, and identifies employees.
Automated Attendance: Logs employee check-in/check-out times based on face recognition.
High Performance: Uses state-of-the-art deep learning models such as ArcFace + ResNet50, MobileFaceNet, EfficientFace, and SphereFace.
Extensible: Can integrate with live cameras, uploaded images, or REST APIs.
Features
Add/edit employee profile and face images.
Face detection and alignment for improved recognition accuracy.
Embedding extraction and classification using multiple models.
Multi-GPU support for faster training.
Early stopping and checkpointing during training.
Validation on benchmark datasets (LFW, CFP-FP, AgeDB).
Dataset
Training: CASIA-WebFace (~500k images, ~10k identities)
Testing/Verification: LFW (Labeled Faces in the Wild), CFP-FP, AgeDB
Notes: For best performance on Vietnamese faces, additional fine-tuning with local images is recommended.
Models

The project implements four strong face recognition models:

ArcFace + ResNet50 – High accuracy, industry-standard.
MobileFaceNet – Lightweight, suitable for real-time applications.
EfficientFace – Balanced between speed and performance.
SphereFace – Benchmark model for academic comparison.
Project Structure
FaceRecognitionSystem/
│
├── data/                   # Dataset folder (CASIA-WebFace/train, LFW/test)
│
├── models/                 # Model definitions (ResNet50, ArcFace, etc.)
│
├── checkpoints/            # Saved model checkpoints
│
├── train.py                # Training script
├── test.py                 # Testing / evaluation script
├── utils.py                # Utility functions (accuracy, transforms, loaders)
├── requirements.txt        # Python dependencies
└── README.md               # Project description

Installation
Clone the repository:
git clone https://github.com/yourusername/FaceRecognitionSystem.git
cd FaceRecognitionSystem
Install dependencies:
pip install -r requirements.txt
Prepare datasets:
Place CASIA-WebFace images in data/train/
Place LFW images in data/test/
Training
Training script: train.py
Supports multi-GPU via torch.nn.DataParallel.
Data augmentation applied: Resize, RandomHorizontalFlip, Normalize.
Optimizer: Adam with learning rate scheduler StepLR.
Early stopping monitors validation loss to save best checkpoint.
python train.py --batch_size 64 --epochs 30 --lr 0.0001
Testing / Evaluation
Evaluate the trained model on LFW or custom test dataset.
Outputs accuracy, loss, and saves predictions if required.
python test.py --model checkpoints/best_arcface_resnet50.pth
Notes
Training with CASIA-WebFace may take a long time due to large dataset size. Consider using multi-GPU and larger batch sizes if VRAM allows.
For deployment in Vietnam, additional fine-tuning with local employee images improves recognition accuracy.
References
ArcFace: https://arxiv.org/abs/1801.07698
CASIA-WebFace: http://www.cbsr.ia.ac.cn/english/CASIA-WebFace-Database.html
Face Recognition Benchmarks: LFW, CFP-FP, AgeDB
