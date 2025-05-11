from capture_faces import capture_faces
from helpers.face_trainer import train_model
from recognize_and_log import recognize_and_log
from database.db_config import get_connection

def tampilkan_siswa():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama, kode_nama FROM siswa")
    siswa_list = cursor.fetchall()
    cursor.close()
    conn.close()

    print("Daftar Siswa:")
    for s in siswa_list:
        print(f"{s[0]}. {s[1]} (kode: {s[2]})")

    return {str(s[0]): s[2] for s in siswa_list}
def menu():
    while True:
        print("""
======= MENU PRESENSI WAJAH BERBASIS NAMA =======
1. Ambil Wajah Baru (dari DB)
2. Training Wajah
3. Presensi Masuk
4. Presensi Keluar
5. Daftarkan Siswa Baru
0. Keluar
""")
        pilihan = input("Pilih [0-5]: ")

        if pilihan == '1':
            siswa_map = tampilkan_siswa()
            id_pilih = input("Masukkan ID siswa yang dipilih: ")
            if id_pilih in siswa_map:
                capture_faces(siswa_map[id_pilih])
            else:
                print("❌ ID tidak ditemukan.")
        elif pilihan == '2':
            train_model()
        elif pilihan == '3':
            from presensi_masuk import presensi_masuk
            presensi_masuk()
        elif pilihan == '4':
            from presensi_keluar import presensi_keluar
            presensi_keluar()
        elif pilihan == '5':
            import register_siswa
            register_siswa.register_siswa()
        elif pilihan == '0':
            print("Keluar.")
            break
        else:
            print("Pilihan tidak valid.")


if __name__ == '__main__':
    menu()
