from database.db_config import get_connection

def register_siswa():
    conn = get_connection()
    cursor = conn.cursor()

    nama = input("Masukkan Nama: ")
    kelas = input("Masukkan Kelas: ")
    kode_nama = nama.lower().replace(" ", "_")

    try:
        cursor.execute("INSERT INTO siswa (nama, kelas, kode_nama) VALUES (%s, %s, %s)", (nama, kelas, kode_nama))
        conn.commit()
        print("✅ Siswa berhasil didaftarkan.")
    except Exception as e:
        print("❌ Gagal:", e)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    register_siswa()
