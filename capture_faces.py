import cv2
import os

def capture_faces(nama, save_dir='dataset'):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    count = 0

    print("[INFO] Mulai pengambilan wajah. Tekan ESC untuk keluar.")

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            count += 1
            cv2.imwrite(f"{save_dir}/User.{nama}.{count}.jpg", gray[y:y+h, x:x+w])
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow('Capture Faces', frame)
        if cv2.waitKey(1) == 27 or count >= 50:
            break

    cam.release()
    cv2.destroyAllWindows()
    print("[INFO] Pengambilan wajah selesai.")
