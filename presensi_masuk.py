import cv2
from database.db_config import get_connection
from datetime import datetime, time

JAM_MULAI = time(7, 0)
JAM_TELAT = time(8, 0)

def load_label_map(path='models/labels.txt'):
    label_map = {}
    with open(path, 'r') as f:
        for line in f:
            label, name = line.strip().split(':')
            label_map[int(label)] = name
    return label_map

def presensi_masuk(model_path='models/trainer.yml'):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    label_map = load_label_map()

    conn = get_connection()
    cursor = conn.cursor()
    cam = cv2.VideoCapture(0)
    print("[INFO] Mulai presensi MASUK. Tekan ESC untuk keluar.")
    now = datetime.now().time()

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            face_img = cv2.resize(gray[y:y+h, x:x+w], (150, 150))
            label, confidence = recognizer.predict(face_img)
            kode_nama = label_map.get(label, "Unknown")

            if confidence < 70 and kode_nama != "Unknown":
                cursor.execute("SELECT id, nama, kelas FROM siswa WHERE kode_nama = %s", (kode_nama,))
                result = cursor.fetchone()
                if result:
                    id_siswa, nama, kelas = result
                    cursor.execute("SELECT * FROM presensi WHERE id_siswa = %s AND tanggal = CURDATE()", (id_siswa,))
                    presensi = cursor.fetchone()

                    if not presensi:
                        if now > JAM_TELAT:
                            status = "Terlambat"
                            print(f"⚠️ {nama} dinyatakan TERLAMBAT.")
                            alasan_input = input(f"Masukkan alasan keterlambatan untuk {nama}: ")
                            cursor.execute("INSERT INTO alasan_telat (id_siswa, tanggal, alasan) VALUES (%s, CURDATE(), %s)", (id_siswa, alasan_input))
                        else:
                            status = "On Time"

                        cursor.execute("INSERT INTO presensi (id_siswa, tanggal, jam_masuk, status) VALUES (%s, CURDATE(), NOW(), %s)", (id_siswa, status))
                        conn.commit()
                        status_msg = f"Presensi masuk dicatat: {status}"
                    else:
                        status_msg = "Sudah presensi masuk"

                    label_text = f"{nama} | {kelas}"
                    info_text = status_msg

                    box_x, box_y = x, y - 55 if y - 55 > 0 else y + h + 10
                    cv2.rectangle(frame, (box_x, box_y), (box_x + 300, box_y + 50), (0, 0, 0), -1)
                    cv2.putText(frame, label_text, (box_x + 10, box_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
                    cv2.putText(frame, info_text, (box_x + 10, box_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,255,200), 1)
            else:
                cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

        cv2.imshow("Presensi Masuk", frame)
        if cv2.waitKey(1) == 27:
            break

    cam.release()
    conn.close()
    cv2.destroyAllWindows()
    print("[INFO] Presensi masuk selesai.")
