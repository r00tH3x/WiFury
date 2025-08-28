# 🤖WiFury – “The Finisher”

> *“The Finisher”* – Battle Tested  

---

##  Deskripsi Singkat

**WiFury** adalah tool berbasis Python yang dirancang untuk memudahkan proses pemindaian, penangkapan handshake, dan cracking jaringan Wi‑Fi dengan proteksi WPA/WPA2. Tools ini dibangun memakai library **Rich** untuk tampilan antarmuka yang menarik dan interaktif.

---

##  Fitur Utama

1. **Banner Keren**  
   Tampilan banner ASCII dengan frame panel warna-warni menggunakan `rich` untuk kesan “gaya dan garang” di setiap run.

2. **Deteksi Dependensi Otomatis**  
   Mengecek tool eksternal yang dibutuhkan: `airmon-ng`, `airodump‑ng`, `hashcat`, `cap2hccapx` — dan memberhentikan eksekusi bila ada yang belum terpasang.

3. **Mode Monitor Otomatis**  
   Mengaktifkan dan menonaktifkan mode monitor (misal: `wlan0mon`) menggunakan `airmon‑ng`, serta me-restart NetworkManager ketika selesai.

4. **Smart Scan**  
   Pindai jaringan WPA/WPA2 dalam durasi tertentu (default: 30 detik), parsing hasil CSV, dan menampilkan daftar SSID, BSSID, channel, serta sinyal dalam bentuk tabel interaktif.

5. **Wordlist Cerdas Otomatis**  
   Membangkitkan wordlist dengan:

   - Variasi dari ESSID (huruf besar, kecil, capital)
   - Pola belajar (`patterns`)
   - Tahun (2000–tahun sekarang +1)
   - Tambahan digit dan simbol  

   Diproses dengan progress bar, dan hasil tersimpan dalam file teks.

6. **Menangkap Handshake WPA**  
   - Jalankan de-auth flooding ke target BSSID.
   - Jalur `airodump‑ng` untuk passive sniff.
   - Tunggu hingga handshake ditemukan (dengan progress bar).
   - Validasi hasil.

7. **Hybrid Crack (Wordlist + Mask Brute-Force)**  
   - Konversi file `.cap` ke `.hccapx`.
   - Crack dengan `hashcat` mode wordlist terlebih dahulu.
   - Bila gagal, lanjut ke serangan mask:
     - Mode interaktif: pengguna pilih panjang & karakter (lower/upper/digit/simbol).
     - Mode otomatis: default mask angka 8–10 digit.
   - Jika berhasil, simpan password, catat pola belajar, dan tampilkan hasilnya.

8. **Armageddon Mode**  
   Satu tombol serang semua target yang terdeteksi, otomatis loop melalui semua network:
   - Tangkap handshake
   - Crack secara otomatis (tanpa intervensi)
   - Buat laporan akhir dalam tabel (ESSID, BSSID, status, password).

9. **Penyimpanan Otomatis & Belajar Pola**  
   - Hasil crack disimpan ke `cracked.txt`.
   - Pola password yang berhasil disimpan dalam `wifury_learned.json` untuk meningkatkan wordlist ke depan.

10. **Tabel Interaktif & Progress Bar Dengan `rich`**  
    Semua output — mulai dari banner, tabel jaringan, progress bar, hingga panel laporan — dibuat menarik dan jelas.

---

##  Instalasi & Persyaratan

###  Prasyarat Sistem

- **Python 3.x**
- Dijalankan dengan **hak akses root** (gunakan `sudo`)
- Tool eksternal:
  - `airmon-ng`
  - `airodump-ng`
  - `hashcat`
  - `cap2hccapx`

  Pastikan sudah terpasang (umumnya paket `aircrack-ng` dan `hashcat`).

###  Instalasi Tool Ini

1. Install Terlebih Dahulu:
   ```bash
   sudo apt update
   sudo apt install aircrack-ng hashcat
   sudo apt install hashcat-utils
   ```

2. Clone repository:
   ```bash
   git clone https://github.com/r00tH3x/WiFury.git
   cd WiFury
   ```

3. Install dependensi Python:
   ```bash
   pip install -r requirements.txt
   ```

4. Jalankan tool:
   ```bash
   sudo python3 wifury.py
   ```

---

##  Cara Menggunakan WiFury

1. Jalankan dengan `sudo python3 wifury.py`.
2. **Display Banner** lalu cek dependensi.
3. **Pilih interface** untuk di-monitorkan (default: `wlan0`).
4. Menu utama muncul:
   ```
   1. Smart Scan
   2. Hybrid Crack (Single Target)
   3. Armageddon Mode (Attack All)
   4. Exit
   ```
5. **Smart Scan**: temukan jaringan WPA/WPA2.
6. **Hybrid Crack**:
   - Pilih target dari list.
   - Tangkap handshake dan lanjut ke cracking interaktif.
7. **Armageddon Mode**:
   - Jalankan serangan otomatis ke semua target tanpa intervensi.
   - Tampilkan laporan akhir.
8. Tekan **Exit** → mode monitor otomatis dimatikan → selesai.

---

##  Struktur File yang Dihasilkan

- `wifury_config.json`: konfigurasi (interface default)
- `wifury_learned.json`: pola password hasil crack sebelumnya
- `cracked.txt`: catatan ESSID, BSSID, dan password yang berhasil ditemukan
- `wifury_session_[timestamp]/`: folder hasil kerja—menyimpan:
  - File scan (`.csv`)
  - Wordlist (`ai_wordlist_ESSID.txt`)
  - Capture handshake (`handshake_[...].cap`)
  - File untuk cracking (`*.hccapx`)

---

##  Contoh Alur Penggunaan

```
sudo python3 wifury.py
└──> Banner & cek dependensi → pilih interface → monitor mode aktif
    └──> Menu pilih “Smart Scan” → muncul tabel jaringan
        └──> Pilih jaringan XYZ → start “Hybrid Crack”
            ├──–> Tangkap handshake
            ├──–> Crack cocok dari wordlist
            └──–> (jika gagal) minta input mask dan brute-force lagi
                ├──–> Kalau ketemu: simpan → update pola → tampil
                └──> Kalau tetap gagal: tampil gagal
    └──> Bila pilih “Armageddon Mode” → menyerang semua target sekali jalan
    └──> Exit → mode monitor dimatikan → bye :v
```

---

##  Catatan Penting

- Tool hanya untuk **tujuan pengujian dan edukasi**, tidak digunakan untuk hal ilegal.
- Selalu gunakan jaringan di mana kamu memiliki izin eksplisit.
- Penggunaan tanpa izin adalah tindak kejahatan dan bertentangan hukum.
