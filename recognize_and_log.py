import cv2
from database.db_config import get_connection
from datetime import datetime, time

JAM_MULAI = time(7, 0)
JAM_TELAT = time(8, 0)
JAM_KELUAR = time(16, 0)


def load_label_map(path='models/labels.txt'):
    label_map = {}
    with open(path, 'r') as f:
        for line in f:
            label, name = line.strip().split(':')
            label_map[int(label)] = name
    return label_map


def recognize_and_log(model_path='models/trainer.yml'):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    label_map = load_label_map()

    conn = get_connection()
    cursor = conn.cursor()

    cam = cv2.VideoCapture(0)
    print("[INFO] Mulai presensi. Tekan ESC untuk keluar.")

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.2, 5)
        now = datetime.now().time()

        for (x, y, w, h) in faces:
            face_img = cv2.resize(gray[y:y+h, x:x+w], (150, 150))
            label, confidence = recognizer.predict(face_img)
            kode_nama = label_map.get(label, "Unknown")

            if confidence < 70 and kode_nama != "Unknown":
                cursor.execute(
                    "SELECT id, nama, kelas FROM siswa WHERE kode_nama = %s", (kode_nama,))
                result = cursor.fetchone()
                if result:
                    id_siswa, nama, kelas = result
                    cursor.execute(
                        "SELECT id, jam_masuk, jam_keluar, status FROM presensi WHERE id_siswa = %s AND tanggal = CURDATE()", (id_siswa,))
                    presensi = cursor.fetchone()

                    status_presensi = "On Time"
                    status_msg = ""

                    if not presensi:
                        if now < JAM_MULAI:
                            status_msg = "Belum waktu presensi"
                        elif now > JAM_TELAT:
                            status_presensi = "Terlambat"
                            status_msg = "Terlambat"
                        else:
                            status_msg = "Presensi masuk tercatat"
                        cursor.execute(
                            "INSERT INTO presensi (id_siswa, tanggal, jam_masuk, status) VALUES (%s, CURDATE(), NOW(), %s)", (id_siswa, status_presensi))
                        conn.commit()
                    elif presensi[1] and not presensi[2]:
                        if presensi[3] == 'Terlambat':
                            cursor.execute(
                                "SELECT * FROM alasan_telat WHERE id_siswa = %s AND tanggal = CURDATE()", (id_siswa,))
                            alasan = cursor.fetchone()
                            if not alasan:
                                print(
                                    f"⚠️ {nama} terlambat dan belum mengisi alasan.")
                                alasan_input = input(
                                    f"Masukkan alasan keterlambatan untuk {nama}: ")
                                cursor.execute(
                                    "INSERT INTO alasan_telat (id_siswa, tanggal, alasan) VALUES (%s, CURDATE(), %s)", (id_siswa, alasan_input))
                                conn.commit()
                                status_msg = "Alasan disimpan. Silakan scan ulang untuk presensi keluar."
                            else:
                                status_msg = "Presensi keluar tercatat"
                                cursor.execute(
                                    "UPDATE presensi SET jam_keluar = NOW() WHERE id = %s", (presensi[0],))
                                conn.commit()
                        else:
                            if now < JAM_KELUAR:
                                status_msg = "Belum bisa presensi keluar"
                            else:
                                status_msg = "Presensi keluar tercatat"
                                cursor.execute(
                                    "UPDATE presensi SET jam_keluar = NOW() WHERE id = %s", (presensi[0],))
                                conn.commit()
                    else:
                        status_msg = "Sudah presensi hari ini"

                    baris1 = f"{nama} | {kelas}"
                    baris2 = status_msg

                    box_x = x
                    box_y = y - 55 if y - 55 > 0 else y + h + 10
                    cv2.rectangle(frame, (box_x, box_y),
                                  (box_x + 300, box_y + 50), (0, 0, 0), -1)

                    cv2.putText(frame, baris1, (box_x + 10, box_y + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    cv2.putText(frame, baris2, (box_x + 10, box_y + 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 1)
                else:
                    cv2.putText(frame, "Nama tidak terdaftar", (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Unknown", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Presensi", frame)
        if cv2.waitKey(1) == 27:
            break

    cam.release()
    conn.close()
    cv2.destroyAllWindows()
    print("[INFO] Presensi selesai.")
