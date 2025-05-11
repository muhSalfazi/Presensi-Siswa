import cv2
from database.db_config import get_connection
from datetime import datetime, time

JAM_KELUAR = time(16, 0)

def load_label_map(path='models/labels.txt'):
    label_map = {}
    with open(path, 'r') as f:
        for line in f:
            label, name = line.strip().split(':')
            label_map[int(label)] = name
    return label_map

def presensi_keluar(model_path='models/trainer.yml'):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    label_map = load_label_map()

    conn = get_connection()
    cursor = conn.cursor()
    cam = cv2.VideoCapture(0)
    print("[INFO] Mulai presensi KELUAR. Tekan ESC untuk keluar.")
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
                    cursor.execute("SELECT id, jam_keluar, status FROM presensi WHERE id_siswa = %s AND tanggal = CURDATE()", (id_siswa,))
                    presensi = cursor.fetchone()

                    if presensi:
                        if presensi[1] is not None:
                            status_msg = "Sudah presensi keluar"
                        elif now < JAM_KELUAR:
                            status_msg = "Belum waktunya keluar"
                        else:
                            if presensi[2] == "Terlambat":
                                cursor.execute("SELECT * FROM alasan_telat WHERE id_siswa = %s AND tanggal = CURDATE()", (id_siswa,))
                                alasan = cursor.fetchone()
                                if not alasan:
                                    print(f"⚠️ {nama} belum isi alasan keterlambatan.")
                                    alasan_input = input(f"Masukkan alasan untuk {nama}: ")
                                    cursor.execute("INSERT INTO alasan_telat (id_siswa, tanggal, alasan) VALUES (%s, CURDATE(), %s)", (id_siswa, alasan_input))
                                    conn.commit()
                            cursor.execute("UPDATE presensi SET jam_keluar = NOW() WHERE id = %s", (presensi[0],))
                            conn.commit()
                            status_msg = "Presensi keluar tercatat"
                    else:
                        status_msg = "Belum presensi masuk"

                    label_text = f"{nama} | {kelas}"
                    info_text = status_msg

                    box_x, box_y = x, y - 55 if y - 55 > 0 else y + h + 10
                    cv2.rectangle(frame, (box_x, box_y), (box_x + 300, box_y + 50), (0, 0, 0), -1)
                    cv2.putText(frame, label_text, (box_x + 10, box_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
                    cv2.putText(frame, info_text, (box_x + 10, box_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,255,200), 1)
            else:
                cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

        cv2.imshow("Presensi Keluar", frame)
        if cv2.waitKey(1) == 27:
            break

    cam.release()
    conn.close()
    cv2.destroyAllWindows()
    print("[INFO] Presensi keluar selesai.")
