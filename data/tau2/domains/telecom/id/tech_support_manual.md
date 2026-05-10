# Pendahuluan
Dokumen ini berfungsi sebagai panduan komprehensif bagi agen dukungan teknis. Dokumen ini memberikan prosedur terperinci dan langkah-langkah pemecahan masalah untuk membantu pengguna yang mengalami masalah umum dengan layanan seluler ponsel, konektivitas data seluler, dan Multimedia Messaging Service (MMS). Panduan ini disusun untuk membantu agen mendiagnosis dan menyelesaikan masalah secara efisien dengan menguraikan cara kerja layanan ini, masalah umum, dan alat available untuk penyelesaian.

Bagian utama yang dibahas adalah:
*   **Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda**: Membahas masalah terkait koneksi jaringan, kekuatan sinyal, dan masalah kartu SIM.
*   **Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda**: Berfokus pada masalah akses internet melalui jaringan seluler, termasuk kecepatan dan konektivitas.
*   **Memahami dan Memecahkan Masalah MMS (Pesan Gambar/Video)**: Mencakup masalah terkait pengiriman dan penerimaan pesan multimedia.

Pastikan Anda mencoba semua cara yang mungkin untuk menyelesaikan masalah user sebelum mentransfer ke agen manusia.

# Apa yang dapat dilakukan user pada perangkat mereka
Berikut adalah tindakan yang dapat dilakukan oleh user pada perangkat mereka.
Anda harus memahami tindakan tersebut dengan baik karena sebagai bagian dari dukungan teknis Anda harus membantu pelanggan melakukan serangkaian tindakan

## Tindakan Diagnostik (Hanya-baca)
1. **check_status_bar** - Menampilkan ikon apa saja yang saat ini terlihat di bilah status ponsel Anda (area di bagian atas layar).
   - Status mode pesawat ("✈️ Mode Pesawat" saat diaktifkan)
   - Kekuatan sinyal jaringan ("📵 Tidak Ada Sinyal", "📶¹ Lemah", "📶² Cukup", "📶³ Baik", "📶⁴ Sangat baik")
   - Teknologi jaringan (misalnya, "5G", "4G", dll.)
   - Status data seluler ("📱 Data Diaktifkan" atau "📵 Data Dinonaktifkan")
   - Status penghemat data ("🔽 Penghemat Data" saat diaktifkan)
   - Status Wi-Fi ("📡 Terhubung ke [SSID]" atau "📡 Diaktifkan")
   - Status VPN ("🔒 VPN Terhubung" saat terhubung)
   - Tingkat baterai ("🔋 [persentase]%")
2. **check_network_status** - Memeriksa status koneksi ponsel Anda ke jaringan seluler dan Wi-Fi. Menampilkan status mode pesawat, kekuatan sinyal, jenis jaringan, apakah data seluler diaktifkan, dan apakah roaming data diaktifkan. Kekuatan sinyal bisa berupa "tidak ada", "lemah" (1 batang), "cukup" (2 batang), "baik" (3 batang), "sangat baik" (4+ batang).
3. **check_network_mode_preference** - Memeriksa preferensi mode jaringan ponsel Anda. Menampilkan jenis jaringan seluler yang lebih disukai oleh ponsel Anda untuk disambungkan (misalnya, 5G, 4G, 3G, 2G).
4. **check_sim_status** - Memeriksa apakah kartu SIM Anda berfungsi dengan benar dan menampilkan statusnya saat ini. Menampilkan apakah SIM sedang aktif, hilang, atau terkunci dengan kode PIN atau PUK.
5. **check_data_restriction_status** - Memeriksa apakah ponsel Anda memiliki fitur pembatas data aktif. Menampilkan apakah mode Penghemat Data aktif dan apakah penggunaan data latar belakang dibatasi secara global.
6. **check_apn_settings** - Memeriksa pengaturan APN teknis yang digunakan ponsel Anda untuk terhubung ke jaringan data seluler operator Anda. Menampilkan nama APN saat ini dan URL MMSC untuk pengiriman pesan gambar.
7. **check_wifi_status** - Memeriksa status koneksi Wi-Fi Anda. Menampilkan apakah Wi-Fi diaktifkan, jaringan mana yang sedang terhubung (jika ada), dan kekuatan sinyalnya.
8. **check_wifi_calling_status** - Memeriksa apakah Panggilan Wi-Fi diaktifkan di perangkat Anda. Fitur ini memungkinkan Anda untuk melakukan dan menerima panggilan melalui jaringan Wi-Fi, bukan menggunakan jaringan seluler.
9. **check_vpn_status** - Memeriksa apakah Anda menggunakan koneksi VPN (Virtual Private Network). Menampilkan apakah VPN sedang aktif, terhubung, dan menampilkan detail koneksi available.
10. **check_installed_apps** - Mengembalikan nama semua aplikasi yang terinstal di ponsel.
11. **check_app_status** - Memeriksa informasi terperinci tentang aplikasi tertentu. Menampilkan izin dan pengaturan penggunaan data latar belakangnya.
12. **check_app_permissions** - Memeriksa izin apa saja yang saat ini dimiliki aplikasi tertentu. Menampilkan apakah aplikasi memiliki akses ke fitur seperti penyimpanan, kamera, lokasi, dll.
13. **run_speed_test** - Mengukur kecepatan koneksi internet Anda saat ini (kecepatan unduh). Memberikan informasi tentang kualitas koneksi dan aktivitas apa saja yang dapat didukungnya. Kecepatan unduh bisa berupa "tidak diketahui", "sangat lemah", "lemah", "cukup", "baik", atau "sangat baik".
14. **can_send_mms** - Memeriksa apakah aplikasi perpesanan dapat mengirim pesan MMS.

## Tindakan Perbaikan (Tulis/Modifikasi)
1. **set_network_mode_preference** - Mengubah jenis jaringan seluler yang lebih disukai oleh ponsel Anda untuk disambungkan (misalnya, 5G, 4G, 3G). Jaringan berkecepatan tinggi (5G, 4G) memberikan data lebih cepat tetapi mungkin lebih menguras baterai.
2. **toggle_airplane_mode** - Mengaktifkan atau menonaktifkan Mode Pesawat. Saat AKTIF, fitur ini memutuskan semua komunikasi nirkabel termasuk seluler, Wi-Fi, dan Bluetooth.
3. **reseat_sim_card** - Mensimulasikan pelepasan dan pemasangan kembali kartu SIM Anda. Ini dapat membantu mengatasi masalah pengenalan.
4. **toggle_data** - Mengaktifkan atau menonaktifkan koneksi data seluler ponsel Anda. Mengontrol apakah ponsel Anda dapat menggunakan data seluler untuk akses internet saat Wi-Fi tidak tersedia.
5. **toggle_roaming** - Mengaktifkan atau menonaktifkan Roaming Data. Saat AKTIF, roaming diaktifkan dan ponsel Anda dapat menggunakan jaringan data di area di luar cakupan operator Anda.
6. **toggle_data_saver_mode** - Mengaktifkan atau menonaktifkan mode Penghemat Data. Saat AKTIF, fitur ini mengurangi penggunaan data, yang mungkin memengaruhi kecepatan data.
7. **set_apn_settings** - Mengatur pengaturan APN untuk ponsel.
8. **reset_apn_settings** - Mengatur ulang pengaturan APN Anda ke pengaturan default.
9. **toggle_wifi** - Mengaktifkan atau menonaktifkan radio Wi-Fi ponsel Anda. Mengontrol apakah ponsel Anda dapat menemukan dan terhubung ke jaringan nirkabel untuk akses internet.
10. **toggle_wifi_calling** - Mengaktifkan atau menonaktifkan Panggilan Wi-Fi. Fitur ini memungkinkan Anda untuk melakukan dan menerima panggilan melalui Wi-Fi, bukan menggunakan jaringan seluler, yang dapat membantu di area dengan sinyal seluler yang lemah.
11. **connect_vpn** - Terhubung ke VPN (Virtual Private Network) Anda.
12. **disconnect_vpn** - Memutuskan koneksi VPN (Virtual Private Network) aktif apa pun. Menghentikan perutean lalu lintas internet Anda melalui server VPN, yang mungkin memengaruhi kecepatan koneksi atau akses ke konten.
13. **grant_app_permission** - Memberikan izin tertentu ke aplikasi (seperti akses ke penyimpanan, kamera, atau lokasi). Diperlukan agar beberapa fungsi aplikasi berfungsi dengan baik.
14. **reboot_device** - Memulai ulang ponsel Anda sepenuhnya. Ini dapat membantu mengatasi banyak gangguan perangkat lunak sementara dengan menyegarkan semua layanan dan koneksi yang berjalan.

# Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda
Bagian ini merinci bagi agen bagaimana ponsel milik user terhubung ke jaringan seluler (sering disebut sebagai "layanan") dan memberikan prosedur untuk memecahkan masalah umum. Layanan seluler yang baik diperlukan untuk panggilan, teks, dan data seluler.

## Masalah Layanan Umum dan Penyebabnya
Jika user mengalami masalah layanan, berikut adalah beberapa penyebab umum:

*   **Mode Pesawat AKTIF**: Ini menonaktifkan semua radio nirkabel, termasuk seluler.
*   **Masalah Kartu SIM**:
    *   Tidak dimasukkan atau dipasang dengan tidak benar.
    *   Terkunci karena entri PIN/PUK yang salah.
*   **Pengaturan Jaringan Tidak Tepat**: Pengaturan APN mungkin salah sehingga mengakibatkan hilangnya layanan.
*   **Masalah Operator**: Saluran Anda mungkin tidak aktif karena masalah penagihan.


## Mendiagnosis Masalah Layanan
`check_status_bar()` dapat digunakan untuk memeriksa apakah user menghadapi masalah layanan.
Jika ada layanan seluler, bilah status akan menampilkan indikator kekuatan sinyal.

## Memecahkan Masalah Layanan
### Mode Pesawat
Mode Pesawat adalah fitur yang menonaktifkan semua radio nirkabel, termasuk seluler. Jika diaktifkan, ini akan mencegah koneksi seluler apa pun.
Anda dapat memeriksa apakah Mode Pesawat AKTIF dengan menggunakan `check_status_bar()` atau `check_network_status()`.
Jika AKTIF, pandu user untuk menggunakan `toggle_airplane_mode()` untuk menonaktifkannya.

### Masalah Kartu SIM
Kartu SIM adalah kartu fisik yang berisi informasi user dan memungkinkan ponsel untuk terhubung ke jaringan seluler.
Masalah dengan kartu SIM dapat menyebabkan hilangnya layanan sepenuhnya.
Masalah yang paling umum adalah kartu SIM tidak terpasang dengan benar atau user telah memasukkan kode PIN atau PUK yang salah.
Gunakan `check_sim_status()` untuk memeriksa status kartu SIM.
Jika menampilkan "Hilang", pandu user untuk menggunakan `reseat_sim_card()` untuk memastikan kartu SIM dimasukkan dengan benar.
Jika menampilkan "Terkunci" (karena entri PIN atau PUK yang salah), **lakukan eskalasi ke dukungan teknis untuk bantuan mengenai keamanan SIM**.
Jika menampilkan "Aktif", SIM itu sendiri kemungkinan besar baik-baik saja.

### Pengaturan APN yang Salah
Pengaturan Nama Titik Akses (APN) sangat penting untuk konektivitas jaringan.
Jika `check_apn_settings()` menampilkan "Salah", pandu user untuk menggunakan `reset_apn_settings()` untuk mengatur ulang pengaturan APN.
Setelah mengatur ulang pengaturan APN, user harus diinstruksikan untuk menggunakan `reboot_device()` agar perubahan diterapkan.

### Penangguhan Saluran
Jika saluran ditangguhkan, user tidak akan memiliki layanan seluler.
Selidiki apakah saluran tersebut ditangguhkan. Lihat kebijakan agen umum untuk pedoman penanganan penangguhan saluran.
*   Jika saluran ditangguhkan dan agen dapat mencabut penangguhan (sesuai kebijakan umum), verifikasi apakah layanan telah dipulihkan.
*   Jika penangguhan tidak dapat dicabut oleh agen (misalnya, karena tanggal berakhir kontrak seperti yang disebutkan dalam kebijakan umum, atau alasan lainnya yang tidak dapat diselesaikan oleh agen), **lakukan eskalasi ke dukungan teknis**.


# Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda
Bagian ini menjelaskan bagi agen bagaimana ponsel milik user menggunakan data seluler untuk akses internet saat Wi-Fi tidak tersedia, dan merinci pemecahan masalah untuk masalah konektivitas dan kecepatan umum.

## Apa itu Data Seluler?
Data seluler memungkinkan ponsel untuk terhubung ke internet menggunakan jaringan seluler operator. Ini memungkinkan penjelajahan situs web, penggunaan aplikasi, streaming video, dan pengiriman/penerimaan email saat tidak terhubung ke Wi-Fi. Bilah status biasanya menampilkan ikon seperti "5G", "LTE", "4G", "3G", "H+", atau "E" untuk menunjukkan koneksi data seluler aktif dan jenisnya.

## Prasyarat untuk Data Seluler
Agar data seluler berfungsi, user harus memiliki **layanan seluler** terlebih dahulu. Lihat panduan "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" jika user tidak memiliki layanan.

## Masalah dan Penyebab Data Seluler Umum
Bahkan dengan layanan seluler, masalah data seluler mungkin terjadi. Alasan umum meliputi:

*   **Mode Pesawat AKTIF**: Menonaktifkan semua koneksi nirkabel, termasuk data seluler.
*   **Data Seluler Dinonaktifkan**: Sakelar utama untuk data seluler mungkin dinonaktifkan di pengaturan ponsel.
*   **Masalah Roaming (Saat Pengguna di Luar Negeri)**:
    *   Roaming Data dinonaktifkan pada ponsel.
    *   Saluran tidak diaktifkan untuk roaming.
*   **Batas Paket Data Tercapai**: user mungkin telah menghabiskan jatah data bulanan mereka, dan operator telah memperlambat atau memutus data.
*   **Mode Penghemat Data AKTIF**: Fitur ini membatasi penggunaan data latar belakang dan dapat membuat beberapa aplikasi atau layanan terasa lambat atau tidak responsif demi menghemat data.
*   **Masalah VPN**: Koneksi VPN aktif mungkin lambat atau salah dikonfigurasi, memengaruhi kecepatan data atau konektivitas.
*   **Preferensi Jaringan Buruk**: ponsel diatur ke teknologi jaringan lama seperti 2G/3G.

## Mendiagnosis Masalah Data Seluler
`run_speed_test()` dapat digunakan untuk memeriksa potensi masalah dengan data seluler.
Saat data seluler tidak tersedia, tes kecepatan akan mengembalikan 'tidak ada koneksi'.
Jika data available, tes kecepatan juga akan mengembalikan kecepatan data.
Kecepatan apa pun di bawah 'Sangat baik' dianggap lambat.

## Memecahkan Masalah Data Seluler
### Mode Pesawat
Lihat bagian "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" untuk instruksi tentang cara memeriksa dan menonaktifkan Mode Pesawat.

### Data Seluler Dinonaktifkan
Sakelar data seluler memungkinkan ponsel untuk terhubung ke internet menggunakan jaringan seluler operator.
Jika `check_network_status()` menampilkan data seluler dinonaktifkan, pandu user untuk menggunakan `toggle_data()` untuk mengaktifkan data seluler.

### Mengatasi Masalah Roaming Data
Roaming data memungkinkan user untuk menggunakan koneksi data ponsel mereka di area di luar jaringan asal mereka (misalnya saat bepergian ke luar negeri).
Jika user berada di luar area cakupan utama operator mereka (roaming) dan data seluler tidak berfungsi, pandu mereka untuk menggunakan `toggle_roaming()` untuk memastikan Roaming Data AKTIF.
Anda harus memeriksa apakah saluran yang terkait dengan nomor ponsel yang diberikan oleh user diaktifkan untuk roaming. Jika tidak, user tidak akan dapat menggunakan koneksi data ponsel mereka di area di luar jaringan asal mereka.
Lihat kebijakan umum untuk pedoman tentang mengaktifkan roaming.

### Mode Penghemat Data
Mode Penghemat Data adalah fitur yang membatasi penggunaan data latar belakang dan dapat memengaruhi kecepatan data.
Jika `check_data_restriction_status()` menampilkan "Mode Penghemat Data AKTIF", pandu user untuk menggunakan `toggle_data_saver_mode()` untuk menonaktifkannya.

### Masalah Koneksi VPN
VPN (Virtual Private Network) adalah fitur yang mengenkripsi lalu lintas internet dan dapat membantu meningkatkan kecepatan dan keamanan data.
Namun dalam beberapa kasus, VPN dapat menyebabkan kecepatan turun secara signifikan.
Jika `check_vpn_status()` menampilkan "VPN AKTIF dan terhubung" dan tingkat kinerjanya "Lemah", pandu user untuk menggunakan `disconnect_vpn()` untuk memutuskan koneksi VPN.

### Batas Paket Data Tercapai
Setiap paket menentukan penggunaan data maksimum per bulan.
Jika penggunaan data user untuk saluran yang terkait dengan nomor ponsel yang diberikan oleh user melebihi batas data paket, konektivitas data akan hilang.
user memiliki 2 opsi:
- Mengubah ke paket dengan lebih banyak data.
- Menambahkan lebih banyak data ke saluran dengan "mengisi ulang" data dengan harga per GB yang ditentukan oleh paket.
Lihat kebijakan umum untuk pedoman mengenai opsi tersebut.

### Mengoptimalkan Preferensi Mode Jaringan
Preferensi mode jaringan adalah pengaturan yang menentukan jenis jaringan seluler yang akan disambungkan oleh ponsel.
Menggunakan mode lama seperti 2G/3G dapat membatasi kecepatan secara signifikan.
Jika `check_network_mode_preference()` menampilkan "2G" atau "3G", pandu user untuk menggunakan `set_network_mode_preference(mode: str)` dengan mode `"4G/5G lebih disukai"` untuk memungkinkan ponsel terhubung ke 5G.

# Memahami dan Memecahkan Masalah MMS (Pesan Gambar/Video)
Bagian ini menjelaskan bagi agen cara memecahkan masalah Multimedia Messaging Service (MMS), yang memungkinkan pengguna untuk mengirim dan menerima pesan yang berisi gambar, video, atau audio.

## Apa itu MMS?
MMS adalah perluasan dari SMS (pesan teks) yang memungkinkan konten multimedia. Saat user mengirim foto ke teman melalui aplikasi perpesanan mereka, mereka biasanya menggunakan MMS.

## Prasyarat untuk MMS
Agar MMS berfungsi, user harus memiliki layanan seluler dan data seluler (kecepatan apa pun).
Lihat bagian "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" dan "Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda" untuk informasi lebih lanjut.

## Masalah dan Penyebab MMS Umum
*   **Tidak Ada Layanan Seluler atau Data Seluler Dinonaktifkan/Tidak Berfungsi**: Alasan paling umum. MMS mengandalkan hal-hal ini.
*   **Pengaturan APN Salah**: Secara khusus, hilang atau URL MMSC salah.
*   **Terhubung ke Jaringan 2G**: Jaringan 2G umumnya tidak cocok untuk MMS.
*   **Konfigurasi Panggilan Wi-Fi**: Dalam beberapa kasus, cara Panggilan Wi-Fi dikonfigurasi dapat memengaruhi MMS, terutama jika operator Anda tidak mendukung MMS melalui Wi-Fi.
*   **Izin Aplikasi**: Aplikasi perpesanan memerlukan izin untuk mengakses penyimpanan (untuk file media) dan biasanya fungsionalitas SMS.

## Mendiagnosis Masalah MMS
Alat `can_send_mms()` pada ponsel milik user dapat digunakan untuk memeriksa apakah user menghadapi masalah MMS.

## Memecahkan Masalah MMS
### Memastikan Konektivitas Dasar untuk MMS
Pesan MMS yang sukses mengandalkan layanan mendasar dan konektivitas data. Bagian ini mencakup verifikasi prasyarat tersebut.
Pertama, pastikan user dapat melakukan panggilan dan data seluler mereka berfungsi untuk aplikasi lainnya (misalnya, menjelajahi web). Lihat bagian "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" dan "Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda" jika diperlukan.

### Teknologi Jaringan yang Tidak Cocok untuk MMS
MMS memiliki persyaratan jaringan khusus; teknologi lama seperti 2G tidak memadai. Bagian ini menjelaskan cara memeriksa jenis jaringan dan mengubahnya jika perlu.
MMS memerlukan setidaknya koneksi jaringan 3G; jaringan 2G umumnya tidak cocok.
Jika `check_network_status()` menampilkan "2G", pandu user untuk menggunakan `set_network_mode_preference(mode: str)` untuk beralih ke mode jaringan yang menyertakan 3G, 4G, atau 5G (misalnya, `"4G/5G lebih disukai"` atau `"hanya 4G"`).

### Memverifikasi APN (URL MMSC) untuk MMS
MMSC adalah Pusat Layanan Pesan Multimedia. Ini adalah server yang menangani pesan MMS. Tanpa URL MMSC yang benar, user tidak akan dapat mengirim atau menerima pesan MMS.
Hal tersebut ditentukan sebagai bagian dari pengaturan APN. URL MMSC yang salah adalah penyebab umum masalah MMS.
Jika `check_apn_settings()` menampilkan URL MMSC tidak diatur, pandu user untuk menggunakan `reset_apn_settings()` untuk mengatur ulang pengaturan APN.
Setelah mengatur ulang pengaturan APN, user harus diinstruksikan untuk menggunakan `reboot_device()` agar perubahan diterapkan.

### Menyelidiki Gangguan Panggilan Wi-Fi dengan MMS
Pengaturan Panggilan Wi-Fi terkadang dapat bertentangan dengan fungsionalitas MMS.
Jika `check_wifi_calling_status()` menampilkan "Panggilan Wi-Fi AKTIF", pandu user untuk menggunakan `toggle_wifi_calling()` untuk menonaktifkannya.

### Aplikasi Perpesanan Kurang Izin yang Diperlukan
Aplikasi perpesanan memerlukan izin khusus untuk menangani media dan mengirim pesan.
Jika `check_app_permissions(app_name="messaging")` menampilkan izin "penyimpanan" dan "sms" tidak terdaftar sebagai diberikan, pandu user untuk menggunakan `grant_app_permission(app_name="messaging", permission="storage")` dan `grant_app_permission(app_name="messaging", permission="sms")` untuk memberikan izin yang diperlukan.