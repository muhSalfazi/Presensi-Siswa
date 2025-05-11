import cv2
import numpy as np
from PIL import Image
import os

def train_model(dataset_path='dataset', model_path='models/trainer.yml'):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    image_paths = [os.path.join(dataset_path, f) for f in os.listdir(dataset_path)]
    face_samples, labels = [], []
    label_map, label_counter = {}, 0

    for path in image_paths:
        name = os.path.split(path)[-1].split('.')[1]
        if name not in label_map:
            label_map[name] = label_counter
            label_counter += 1

        img = Image.open(path).convert('L')
        img_np = np.array(img, 'uint8')
        label = label_map[name]
        faces = detector.detectMultiScale(img_np)
        for (x, y, w, h) in faces:
            face = cv2.resize(img_np[y:y+h, x:x+w], (150, 150))
            face_samples.append(face)
            labels.append(label)

    recognizer.train(face_samples, np.array(labels))
    if not os.path.exists('models'):
        os.makedirs('models')
    recognizer.write(model_path)

    with open('models/labels.txt', 'w') as f:
        for name, label in label_map.items():
            f.write(f"{label}:{name}\n")

    print("[INFO] Training selesai dan model disimpan.")
