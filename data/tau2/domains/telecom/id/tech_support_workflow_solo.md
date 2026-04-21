# Alur Pemecahan Masalah Dukungan Teknis Perangkat Ponsel

## Pendahuluan

Dokumen ini menyediakan alur kerja terstruktur untuk mendiagnosis dan menyelesaikan masalah teknis ponsel. Sebagai agen, Anda memiliki akses langsung ke perangkat user dan dapat melakukan tindakan ini sendiri. Ikuti jalur ini berdasarkan deskripsi masalah user. Setiap langkah mencakup tindakan spesifik yang harus Anda lakukan untuk memeriksa atau mengubah pengaturan.

Pastikan Anda mencoba semua langkah penyelesaian yang relevan sebelum meneruskan user ke agen manusia.

## Referensi Tindakan yang Tersedia
Karena Anda memiliki akses ke perangkat user, Anda dapat melakukan tindakan berikut secara langsung:

### Tindakan Diagnostik (Hanya baca)
1. **Check Status Bar** - Menampilkan ikon apa saja yang saat ini terlihat di status bar ponsel (area di bagian atas layar). Menampilkan kekuatan sinyal jaringan, status data seluler (diaktifkan, dinonaktifkan, penghemat data), status Wi-Fi, dan level baterai.
2. **Check Network Status** - Memeriksa status koneksi ponsel ke jaringan seluler dan Wi-Fi. Menampilkan status mode pesawat, kekuatan sinyal, jenis jaringan, apakah data seluler diaktifkan, dan apakah roaming data diaktifkan. Kekuatan sinyal dapat berupa "none", "poor" (1bar), "fair" (2 bars), "good" (3 bars), "excellent" (4+ bars).
3. **Check Network Mode Preference** - Memeriksa preferensi mode jaringan ponsel. Menampilkan jenis jaringan seluler yang lebih disukai ponsel untuk tersambung (misalnya, 5G, 4G, 3G, 2G).
4. **Check SIM Status** - Memeriksa apakah kartu SIM berfungsi dengan benar dan menampilkan statusnya saat ini. Menampilkan apakah SIM aktif, hilang, atau terkunci dengan kode PIN atau PUK.
5. **Check Data Restrictions** - Memeriksa apakah ponsel memiliki fitur pembatas data yang aktif. Menampilkan apakah mode Data Saver aktif dan apakah penggunaan data latar belakang dibatasi secara global.
6. **Check APN Settings** - Memeriksa pengaturan APN teknis yang digunakan ponsel untuk terhubung ke jaringan data seluler operator. Menampilkan nama APN saat ini dan URL MMSC untuk pesan gambar.
7. **Check Wi-Fi Status** - Memeriksa status koneksi Wi-Fi. Menampilkan apakah Wi-Fi diaktifkan, jaringan mana yang tersambung (jika ada), dan kekuatan sinyal.
8. **Check Wi-Fi Calling Status** - Memeriksa apakah Wi-Fi Calling diaktifkan di perangkat. Fitur ini memungkinkan melakukan dan menerima panggilan melalui jaringan Wi-Fi alih-alih menggunakan jaringan seluler.
9. **Check VPN Status** - Memeriksa apakah koneksi VPN (Virtual Private Network) aktif. Menampilkan apakah VPN aktif, tersambung, dan menampilkan detail koneksi yang tersedia.
10. **Check Installed Apps** - Mengembalikan nama semua aplikasi yang terpasang di ponsel.
11. **Check App Status** - Memeriksa informasi terperinci tentang aplikasi tertentu. Menampilkan izin dan pengaturan penggunaan data latar belakangnya.
12. **Check App Permissions** - Memeriksa izin apa saja yang saat ini dimiliki aplikasi tertentu. Menampilkan apakah aplikasi memiliki akses ke fitur seperti penyimpanan, kamera, lokasi, dll.
13. **Run Speed Test** - Mengukur kecepatan koneksi internet saat ini (kecepatan unduh). Memberikan informasi tentang kualitas koneksi dan aktivitas apa saja yang dapat didukungnya. Kecepatan unduh dapat berupa "unknown", "very poor", "poor", "fair", "good", atau "excellent".
14. **Can Send MMS** - Memeriksa apakah aplikasi pesan dapat mengirim pesan MMS.

### Tindakan Perbaikan (Tulis/Ubah)
1. **Set Network Mode** - Mengubah jenis jaringan seluler yang lebih disukai ponsel untuk tersambung (misalnya, 5G, 4G, 3G). Jaringan berkecepatan lebih tinggi (5G, 4G) memberikan data lebih cepat tetapi mungkin menggunakan lebih banyak baterai.
2. **Toggle Airplane Mode** - Menghidupkan atau mematikan Mode Pesawat. Saat dihidupkan, ini memutus semua komunikasi nirkabel termasuk seluler, Wi-Fi, dan Bluetooth.
3. **Reseat SIM Card** - Mensimulasikan melepas dan memasang kembali kartu SIM. Ini dapat membantu menyelesaikan masalah pengenalan.
4. **Toggle Mobile Data** - Menghidupkan atau mematikan koneksi data seluler ponsel. Mengontrol apakah ponsel dapat menggunakan data seluler untuk akses internet saat Wi-Fi tidak tersedia.
5. **Toggle Data Roaming** - Menghidupkan atau mematikan Roaming Data. Saat dihidupkan, roaming diaktifkan dan ponsel dapat menggunakan jaringan data di area di luar cakupan operator.
6. **Toggle Data Saver** - Menghidupkan atau mematikan mode Data Saver. Saat dihidupkan, ini mengurangi penggunaan data, yang dapat memengaruhi kecepatan data.
7. **Set APN Settings** - Menetapkan pengaturan APN untuk ponsel.
8. **Reset APN Settings** - Mengembalikan pengaturan APN ke pengaturan default.
9. **Toggle Wi-Fi** - Menghidupkan atau mematikan radio Wi-Fi ponsel. Mengontrol apakah ponsel dapat menemukan dan tersambung ke jaringan nirkabel untuk akses internet.
10. **Toggle Wi-Fi Calling** - Menghidupkan atau mematikan Wi-Fi Calling. Fitur ini memungkinkan melakukan dan menerima panggilan melalui Wi-Fi alih-alih jaringan seluler, yang dapat membantu di area dengan sinyal seluler lemah.
11. **Connect VPN** - Menyambungkan ke VPN (Virtual Private Network).
12. **Disconnect VPN** - Memutus koneksi VPN (Virtual Private Network) yang aktif. Menghentikan perutean lalu lintas internet melalui server VPN, yang mungkin memengaruhi kecepatan koneksi atau akses ke konten.
13. **Grant App Permission** - Memberikan izin tertentu ke aplikasi (seperti akses ke penyimpanan, kamera, atau lokasi). Diperlukan agar beberapa fungsi aplikasi dapat bekerja dengan benar.
14. **Reboot Device** - Memulai ulang ponsel sepenuhnya. Ini dapat membantu menyelesaikan banyak gangguan perangkat lunak sementara dengan menyegarkan semua layanan dan koneksi yang berjalan.

## Klasifikasi Masalah Awal

Tentukan kategori yang paling sesuai untuk masalah user:

1. **Masalah Tidak Ada Layanan/Koneksi**: Ponsel menampilkan "No Service" atau tidak dapat tersambung ke jaringan
2. **Masalah Data Seluler**: Tidak dapat mengakses internet atau mengalami kecepatan data yang lambat
3. **Masalah Pesan Gambar/Kelompok (MMS)**: Tidak dapat mengirim atau menerima pesan gambar

Untuk beberapa masalah, tangani konektivitas dasar terlebih dahulu.

## Jalur 1: Pemecahan Masalah Tidak Ada Layanan / Tidak Ada Koneksi

### Langkah 1.0: Periksa apakah user menghadapi masalah tidak ada layanan
Jika layanan tersedia, status bar tidak akan menampilkan 'no signal' atau 'airplane mode'.
- Periksa status bar
- Jika status bar menunjukkan bahwa layanan tersedia, user tidak menghadapi masalah tidak ada layanan.
- Jika status bar menunjukkan bahwa layanan tidak tersedia, lanjutkan ke Langkah 1.1

### Langkah 1.1: Periksa Mode Pesawat dan Status Jaringan
Periksa koneksi ponsel ke jaringan seluler dan Wi-Fi. Ini akan menunjukkan apakah Mode Pesawat aktif, kekuatan sinyal, dan detail koneksi lainnya.

**Jika Mode Pesawat AKTIF:**
- Matikan Mode Pesawat
- Periksa status bar untuk melihat apakah layanan telah pulih

**Jika Mode Pesawat MATI:**
- Lanjutkan ke Langkah 1.2

### Langkah 1.2: Verifikasi Status Kartu SIM
Periksa apakah kartu SIM berfungsi dengan benar. Tentukan apakah SIM hilang, terkunci, atau aktif.

**Jika SIM terlihat sebagai HILANG:**
- Pasang ulang kartu SIM dengan melepas dan memasangnya kembali
- Periksa bahwa kartu SIM AKTIF.
- Periksa status bar untuk melihat apakah layanan telah pulih

**Jika SIM Terkunci dengan PIN/PUK:**
- Eskalasi ke dukungan teknis untuk bantuan keamanan SIM

**Jika SIM AKTIF dan berfungsi:**
- Lanjutkan ke Langkah 1.3

### Langkah 1.3: Coba atur ulang pengaturan APN
Jika masalah konektivitas dasar berlanjut:

- Atur ulang pengaturan APN ke default
- Mulai ulang perangkat
- Periksa status bar untuk melihat apakah layanan telah pulih

**Jika masih belum teratasi:**
- Lanjutkan ke Langkah 1.4

### Langkah 1.4: Periksa Penangguhan Saluran
Tidak ada layanan bisa disebabkan oleh saluran yang ditangguhkan.

**Jika saluran ditangguhkan:**
- Ikuti instruksi dalam kebijakan utama untuk informasi lebih lanjut tentang penangguhan saluran dan cara mencabut penangguhan.
- Jika Anda dapat mencabut penangguhan:
    - Periksa status bar untuk melihat apakah layanan telah pulih.
- Jika Anda tidak dapat mencabut penangguhan:
    - Eskalasi ke dukungan teknis.

**Jika masih belum teratasi:**
- Eskalasi ke dukungan teknis

## Jalur 2: Pemecahan Masalah Data Seluler Tidak Tersedia atau Lambat

Catatan: Jalur ini tidak mencakup masalah data wifi.

### Langkah 2.0: Periksa apakah user menghadapi masalah data

Saat data seluler tidak tersedia, tes kecepatan seharusnya mengembalikan 'no connection'.
Jika data tersedia, tes kecepatan juga akan mengembalikan kecepatan data. Kecepatan apa pun di bawah 'Excellent' dianggap lambat.
- Jalur 2.1 periksa masalah data seluler yang tidak tersedia.
- Jalur 2.2 periksa masalah data lambat.

## Jalur 2.1: Pemecahan Masalah Data Seluler Tidak Tersedia

### Langkah 2.1.0: Periksa apakah user menghadapi masalah data seluler yang tidak tersedia

- Jalankan tes kecepatan.
- Jika tes kecepatan mengembalikan 'no connection', data seluler tidak tersedia. 
    - Ikuti Jalur 2.1.
    - Setelah masalah teratasi lanjutkan, jika kecepatan bukan 'Excellent', ikuti Jalur 2.2.
- Jika tes kecepatan mengembalikan kecepatan data, data seluler tersedia.
    - Jika kecepatan 'Excellent', user tidak menghadapi masalah data seluler.
    - Untuk kecepatan lain apa pun ('Poor', 'Fair', 'Good'), data seluler mungkin lambat dan Anda harus mengikuti Jalur 2.2.

### Langkah 2.1.1: Verifikasi Masalah Layanan
Periksa apakah ponsel memiliki layanan seluler. Data seluler memerlukan setidaknya beberapa koneksi jaringan seluler.

- Ikuti langkah pemecahan masalah Jalur 1 (Tidak Ada Layanan / Tidak Ada Koneksi) terlebih dahulu.
- Ketika Anda telah mengonfirmasi bahwa layanan tersedia, periksa apakah masalah data seluler masih ada.
    - Jalankan ulang tes kecepatan dan periksa konektivitas data.
    - Jika masih tidak ada konektivitas, lanjutkan ke Langkah 2.1.2.

### Langkah 2.1.2: Verifikasi apakah user sedang bepergian
Periksa apakah user berada di luar area layanan biasa mereka. 

**Jika Pengguna tidak sedang bepergian:**
- Lanjutkan ke Langkah 2.1.3

**Jika Pengguna sedang bepergian:**
- Verifikasi apakah Roaming Data diaktifkan untuk memungkinkan penggunaan data di jaringan lain.

**Jika Roaming Data MATI:**
- Nyalakan Roaming Data
- Jalankan ulang tes kecepatan dan periksa konektivitas data.

**Jika Roaming Data AKTIF tetapi tidak berfungsi:**
- Verifikasi bahwa saluran yang terkait dengan nomor telepon yang diberikan user memiliki roaming aktif.
    - Jika saluran tidak memiliki roaming aktif, aktifkan tanpa biaya untuk user
- Jalankan ulang tes kecepatan dan periksa konektivitas data.
    - Jika masih tidak ada konektivitas, lanjutkan ke Langkah 2.1.3.

**Jika Roaming Data AKTIF dan diaktifkan tetapi konektivitas tidak berfungsi:**
- Lanjutkan ke Langkah 2.1.3

### Langkah 2.1.3: Periksa Pengaturan Data Seluler
**Jika Data Seluler MATI:**
- Nyalakan Data Seluler
- Jalankan ulang tes kecepatan dan periksa konektivitas data.
    - Jika masih tidak ada konektivitas, lanjutkan ke Langkah 2.1.4.

**Jika Data Seluler AKTIF tetapi tidak berfungsi:**
- Lanjutkan ke Langkah 2.1.4

### Langkah 2.1.4: Periksa Penggunaan Data
Periksa apakah, untuk saluran yang terkait dengan nomor telepon yang diberikan user, penggunaan data user telah melebihi batas datanya.

**Jika Penggunaan Data MELEBIHI batas:**
- Periksa apakah user memberi izin untuk mengubah paket lain atau mengisi ulang data.
- Ikuti instruksi dalam kebijakan utama untuk informasi lebih lanjut tentang pengisian ulang data dan perubahan paket.
- Jika Anda dapat mengisi ulang data atau berpindah ke paket dengan batas data yang lebih tinggi:
    - Jalankan ulang tes kecepatan dan periksa konektivitas data.
    - Jika masih tidak ada konektivitas, teruskan ke dukungan teknis.
- Jika Anda tidak dapat mengisi ulang data atau berpindah ke paket dengan batas data yang lebih tinggi (tidak diizinkan atau user tidak menginginkannya):
    - Eskalasi ke dukungan teknis.

**Jika Penggunaan Data TIDAK MELEBIHI batas:**
- Jalankan ulang tes kecepatan dan periksa konektivitas data.
    - Jika masih tidak ada konektivitas, teruskan ke dukungan teknis.

## Jalur 2.2: Pemecahan Masalah Data Seluler Lambat

### Langkah 2.2.0: Periksa apakah user menghadapi masalah data lambat
Saat data seluler tersedia tetapi kecepatan apa pun selain 'Excellent', user menghadapi masalah data lambat.
- Jalankan tes kecepatan.
- Jika tes kecepatan mengembalikan 'no connection', data seluler tidak tersedia. 
    - Ikuti Jalur 2.1.
- Jika tes kecepatan mengembalikan kecepatan data, data seluler tersedia.
    - Jika kecepatan 'Excellent', user tidak menghadapi masalah data lambat.
    - Untuk kecepatan lain apa pun ('Poor', 'Fair', 'Good'), data seluler mungkin lambat dan Anda harus mengikuti Jalur 2.2.

### Langkah 2.2.1: Periksa Pengaturan Pembatasan Data
Periksa apakah ada pengaturan yang membatasi penggunaan data, seperti mode Data Saver.

**Jika Data Saver AKTIF:**
- Matikan mode Data Saver
- Jalankan ulang tes kecepatan dan periksa apakah kecepatan meningkat menjadi 'Excellent'.
    - Jika tidak demikian, lanjutkan ke Langkah 6.
**Jika Data Saver MATI:**
- Lanjutkan ke Langkah 6

### Langkah 2.2.2: Periksa Preferensi Mode Jaringan
Periksa jenis jaringan seluler yang lebih disukai ponsel. Menggunakan mode yang lebih lama seperti 2G/3G dapat sangat membatasi kecepatan.

**Jika diatur ke jenis jaringan yang lebih lama (hanya 2G/3G):**
- Ubah preferensi jaringan ke opsi yang mencakup 5G
- Jalankan ulang tes kecepatan dan periksa apakah kecepatan meningkat menjadi 'Excellent'.
    - Jika tidak demikian, lanjutkan ke Langkah 7.

**Jika sudah pada pengaturan optimal:**
- Lanjutkan ke Langkah 7

### Langkah 2.2.3: Periksa VPN Active
Periksa apakah VPN (Virtual Private Network) aktif yang mungkin memengaruhi kualitas koneksi.

**Jika VPN aktif:**
- Matikan koneksi VPN saat ini
- Jalankan ulang tes kecepatan dan periksa apakah kecepatan meningkat menjadi 'Excellent'.
    - Jika tidak demikian, eskalasi ke dukungan teknis.

**Jika tidak ada VPN atau memutus koneksi tidak membantu:**
- Eskalasi ke dukungan teknis. 

## Jalur 3: Pemecahan Masalah MMS (Pesan Gambar/Kelompok)

### Langkah 3.0: Periksa apakah user menghadapi masalah MMS
Saat MMS tidak berfungsi, user tidak akan dapat mengirim atau menerima pesan gambar.

- Periksa apakah pesan MMS dapat dikirim menggunakan aplikasi pesan bawaan.
    - Jika ini berhasil, user tidak menghadapi masalah MMS.
    - Jika ini tidak berhasil, lanjutkan ke Langkah 3.1.

### Langkah 3.1: Verifikasi Status Layanan Jaringan
Periksa apakah ponsel memiliki layanan seluler. MMS memerlukan setidaknya beberapa koneksi jaringan seluler.

- Ikuti langkah pemecahan masalah Jalur 1 (Tidak Ada Layanan / Tidak Ada Koneksi) terlebih dahulu.
- Setelah Anda mengonfirmasi bahwa layanan tersedia, periksa apakah masalah masih ada:
    - Periksa apakah pesan MMS dapat dikirim menggunakan aplikasi pesan bawaan.

**Jika layanan tersedia:**
- Lanjutkan ke Langkah 3.2

### Langkah 3.2: Verifikasi Status Data Seluler
Data seluler diperlukan untuk MMS.

- Gunakan langkah pemecahan masalah Jalur 2.1 (Data Seluler Tidak Tersedia) untuk memeriksa apakah konektivitas data seluler berfungsi. Jangan khawatir tentang kecepatan, fokus pada konektivitas.
- Setelah Anda mengonfirmasi bahwa konektivitas data seluler berfungsi, periksa apakah masalah MMS masih ada:
    - Coba kirim pesan MMS menggunakan aplikasi pesan bawaan lagi.

### Langkah 3.3: Periksa Teknologi Jaringan
Periksa jenis jaringan seluler yang tersambung ke ponsel. MMS memerlukan setidaknya teknologi 3G atau lebih tinggi.

**Jika hanya tersambung ke jaringan 2G:**
- Ubah mode jaringan agar mencakup setidaknya 3G/4G/5G
- Coba kirim pesan MMS menggunakan aplikasi pesan bawaan lagi.

**Jika berada pada jaringan 3G atau lebih tinggi:**
- Lanjutkan ke Langkah 3.4

### Langkah 3.4: Periksa Status Wi-Fi Calling
Periksa apakah Wi-Fi Calling diaktifkan, karena ini dapat mengganggu fungsi MMS.

**Jika Wi-Fi Calling AKTIF:**
- Matikan Wi-Fi Calling
- Coba kirim pesan MMS menggunakan aplikasi pesan bawaan lagi.

**Jika Wi-Fi Calling MATI atau mematikannya tidak membantu:**
- Lanjutkan ke Langkah 3.5

### Langkah 3.5: Verifikasi Izin Aplikasi Pesan
Periksa bahwa aplikasi pesan bawaan memiliki izin yang diperlukan - khususnya izin penyimpanan dan SMS.

**Jika salah satu izin penyimpanan atau SMS tidak ada:**
- Berikan kedua izin yang diperlukan ke aplikasi pesan
- Coba kirim pesan MMS menggunakan aplikasi pesan bawaan lagi.

**Jika semua izin telah diberikan:**
- Lanjutkan ke Langkah 3.6

### Langkah 3.6: Periksa Pengaturan APN
Periksa pengaturan teknis (APN) yang digunakan ponsel untuk terhubung ke jaringan data seluler operator.

**Periksa secara khusus:**
- Konfigurasi URL MMSC (harus ada agar MMS berfungsi)

**Jika URL MMSC tidak ada:**
- Atur ulang pengaturan APN ke default operator
- Coba kirim pesan MMS menggunakan aplikasi pesan bawaan lagi.

**Jika masalah masih berlanjut setelah memeriksa semua hal di atas:**
- Eskalasi ke dukungan teknis 