# Pendahuluan
Dokumen ini berfungsi sebagai panduan komprehensif bagi agen dukungan teknis. Dokumen ini menyediakan prosedur terperinci dan langkah pemecahan masalah untuk membantu pengguna yang mengalami masalah umum dengan layanan seluler ponsel mereka, konektivitas data seluler, dan Multimedia Messaging Service (MMS). Manual ini disusun untuk membantu agen mendiagnosis dan menyelesaikan masalah secara efisien dengan menguraikan cara kerja layanan ini, masalah umum, dan alat yang tersedia untuk penyelesaiannya.

Bagian utama yang dibahas adalah:
* **Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda**: Membahas masalah terkait koneksi jaringan, kekuatan sinyal, dan masalah kartu SIM.
* **Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda**: Berfokus pada masalah akses internet melalui jaringan seluler, termasuk kecepatan dan konektivitas.
* **Memahami dan Memecahkan Masalah MMS (Pesan Gambar/Video)**: Membahas masalah pengiriman dan penerimaan pesan multimedia.

Pastikan Anda mencoba semua cara yang mungkin untuk menyelesaikan masalah user sebelum meneruskan ke agen manusia.

# Apa yang dapat dilakukan user pada perangkat mereka
Berikut adalah tindakan yang dapat dilakukan user pada perangkat mereka.
Anda harus memahaminya dengan baik karena sebagai bagian dari dukungan teknis Anda akan membantu pelanggan melakukan serangkaian tindakan

## Tindakan Diagnostik (Hanya baca)
1. **check_status_bar** - Menampilkan ikon apa saja yang saat ini terlihat di status bar ponsel Anda (area di bagian atas layar).
   - Status mode pesawat ("✈️ Airplane Mode" saat diaktifkan)
   - Kekuatan sinyal jaringan ("📵 No Signal", "📶¹ Poor", "📶² Fair", "📶³ Good", "📶⁴ Excellent")
   - Teknologi jaringan (misalnya, "5G", "4G", dll.)
   - Status data seluler ("📱 Data Enabled" atau "📵 Data Disabled")
   - Status penghemat data ("🔽 Data Saver" saat diaktifkan)
   - Status Wi-Fi ("📡 Connected to [SSID]" atau "📡 Enabled")
   - Status VPN ("🔒 VPN Connected" saat tersambung)
   - Level baterai ("🔋 [persentase]%")
2. **check_network_status** - Memeriksa status koneksi ponsel Anda ke jaringan seluler dan Wi-Fi. Menampilkan status mode pesawat, kekuatan sinyal, jenis jaringan, apakah data seluler diaktifkan, dan apakah roaming data diaktifkan. Kekuatan sinyal dapat berupa "none", "poor" (1 bar), "fair" (2 bars), "good" (3 bars), "excellent" (4+ bars).
3. **check_network_mode_preference** - Memeriksa preferensi mode jaringan ponsel Anda. Menampilkan jenis jaringan seluler yang lebih disukai ponsel untuk tersambung (misalnya, 5G, 4G, 3G, 2G).
4. **check_sim_status** - Memeriksa apakah kartu SIM Anda berfungsi dengan benar dan menampilkan statusnya saat ini. Menampilkan apakah SIM aktif, hilang, atau terkunci dengan kode PIN atau PUK.
5. **check_data_restriction_status** - Memeriksa apakah ponsel Anda memiliki fitur pembatas data yang aktif. Menampilkan apakah mode Data Saver aktif dan apakah penggunaan data latar belakang dibatasi secara global.
6. **check_apn_settings** - Memeriksa pengaturan APN teknis yang digunakan ponsel Anda untuk terhubung ke jaringan data seluler operator Anda. Menampilkan nama APN saat ini dan URL MMSC untuk pesan gambar.
7. **check_wifi_status** - Memeriksa status koneksi Wi-Fi Anda. Menampilkan apakah Wi-Fi diaktifkan, jaringan mana yang Anda sambungkan (jika ada), dan kekuatan sinyal.
8. **check_wifi_calling_status** - Memeriksa apakah Wi-Fi Calling diaktifkan di perangkat Anda. Fitur ini memungkinkan Anda melakukan dan menerima panggilan melalui jaringan Wi-Fi alih-alih menggunakan jaringan seluler.
9. **check_vpn_status** - Memeriksa apakah Anda menggunakan koneksi VPN (Virtual Private Network). Menampilkan apakah VPN aktif, tersambung, dan menampilkan detail koneksi yang tersedia.
10. **check_installed_apps** - Mengembalikan nama semua aplikasi yang terpasang di ponsel.
11. **check_app_status** - Memeriksa informasi terperinci tentang aplikasi tertentu. Menampilkan izin dan pengaturan penggunaan data latar belakangnya.
12. **check_app_permissions** - Memeriksa izin apa saja yang saat ini dimiliki aplikasi tertentu. Menampilkan apakah aplikasi memiliki akses ke fitur seperti penyimpanan, kamera, lokasi, dll.
13. **run_speed_test** - Mengukur kecepatan koneksi internet Anda saat ini (kecepatan unduh). Memberikan informasi tentang kualitas koneksi dan aktivitas apa saja yang dapat didukungnya. Kecepatan unduh dapat berupa "unknown", "very poor", "poor", "fair", "good", atau "excellent".
14. **can_send_mms** - Memeriksa apakah aplikasi pesan dapat mengirim pesan MMS.

## Tindakan Perbaikan (Tulis/Ubah)
1. **set_network_mode_preference** - Mengubah jenis jaringan seluler yang lebih disukai ponsel Anda untuk tersambung (misalnya, 5G, 4G, 3G). Jaringan berkecepatan lebih tinggi (5G, 4G) memberikan data lebih cepat tetapi mungkin menggunakan lebih banyak baterai.
2. **toggle_airplane_mode** - Menghidupkan atau mematikan Mode Pesawat. Saat dihidupkan, ini memutus semua komunikasi nirkabel termasuk seluler, Wi-Fi, dan Bluetooth.
3. **reseat_sim_card** - Mensimulasikan melepas dan memasang kembali kartu SIM Anda. Ini dapat membantu menyelesaikan masalah pengenalan.
4. **toggle_data** - Menghidupkan atau mematikan koneksi data seluler ponsel Anda. Mengontrol apakah ponsel dapat menggunakan data seluler untuk akses internet saat Wi-Fi tidak tersedia.
5. **toggle_roaming** - Menghidupkan atau mematikan Roaming Data. Saat dihidupkan, roaming diaktifkan dan ponsel Anda dapat menggunakan jaringan data di area di luar cakupan operator Anda.
6. **toggle_data_saver_mode** - Menghidupkan atau mematikan mode Data Saver. Saat dihidupkan, ini mengurangi penggunaan data, yang dapat memengaruhi kecepatan data.
7. **set_apn_settings** - Menetapkan pengaturan APN untuk ponsel.
8. **reset_apn_settings** - Mengembalikan pengaturan APN ke pengaturan default.
9. **toggle_wifi** - Menghidupkan atau mematikan radio Wi-Fi ponsel Anda. Mengontrol apakah ponsel Anda dapat menemukan dan tersambung ke jaringan nirkabel untuk akses internet.
10. **toggle_wifi_calling** - Menghidupkan atau mematikan Wi-Fi Calling. Fitur ini memungkinkan Anda melakukan dan menerima panggilan melalui Wi-Fi alih-alih jaringan seluler, yang dapat membantu di area dengan sinyal seluler lemah.
11. **connect_vpn** - Menyambungkan ke VPN (Virtual Private Network) Anda.
12. **disconnect_vpn** - Memutus koneksi VPN (Virtual Private Network) yang aktif. Menghentikan perutean lalu lintas internet Anda melalui server VPN, yang mungkin memengaruhi kecepatan koneksi atau akses ke konten.
13. **grant_app_permission** - Memberikan izin tertentu ke aplikasi (seperti akses ke penyimpanan, kamera, atau lokasi). Diperlukan agar beberapa fungsi aplikasi dapat bekerja dengan benar.
14. **reboot_device** - Memulai ulang ponsel Anda sepenuhnya. Ini dapat membantu menyelesaikan banyak gangguan perangkat lunak sementara dengan menyegarkan semua layanan dan koneksi yang berjalan.

# Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda
Bagian ini menjelaskan kepada agen bagaimana ponsel user terhubung ke jaringan seluler (sering disebut sebagai "service") dan memberikan prosedur untuk memecahkan masalah umum. Layanan seluler yang baik diperlukan untuk panggilan, pesan teks, dan data seluler.

## Masalah Layanan Umum dan Penyebabnya
Jika user mengalami masalah layanan, berikut beberapa penyebab umum:

* **Mode Pesawat AKTIF**: Ini menonaktifkan semua radio nirkabel, termasuk seluler.
* **Masalah Kartu SIM**:
    * Tidak terpasang atau tidak terpasang dengan benar.
    * Terkunci karena entri PIN/PUK yang salah.
* **Pengaturan Jaringan Salah**: Pengaturan APN mungkin salah sehingga mengakibatkan hilangnya layanan.
* **Masalah Operator**: Saluran Anda mungkin tidak aktif karena masalah penagihan.

## Mendiagnosis Masalah Layanan
`check_status_bar()` dapat digunakan untuk memeriksa apakah user menghadapi masalah layanan.
Jika ada layanan seluler, status bar akan menampilkan indikator kekuatan sinyal.

## Pemecahan Masalah Layanan
### Mode Pesawat
Mode Pesawat adalah fitur yang menonaktifkan semua radio nirkabel, termasuk seluler. Jika diaktifkan, ini akan mencegah koneksi seluler apa pun.
Anda dapat memeriksa apakah Mode Pesawat AKTIF dengan menggunakan `check_status_bar()` atau `check_network_status()`.
Jika AKTIF, pandu user untuk menggunakan `toggle_airplane_mode()` untuk mematikannya.

### Masalah Kartu SIM
Kartu SIM adalah kartu fisik yang berisi informasi user dan memungkinkan ponsel terhubung ke jaringan seluler.
Masalah dengan kartu SIM dapat menyebabkan hilangnya layanan sepenuhnya.
Masalah yang paling umum adalah kartu SIM tidak terpasang dengan benar atau user telah memasukkan kode PIN atau PUK yang salah.
Gunakan `check_sim_status()` untuk memeriksa status kartu SIM.
Jika menampilkan "Missing", pandu user untuk menggunakan `reseat_sim_card()` agar kartu SIM terpasang dengan benar.
Jika menampilkan "Locked" (karena entri PIN atau PUK yang salah), **eskalasi ke dukungan teknis untuk bantuan keamanan SIM**.
Jika menampilkan "Active", kemungkinan SIM-nya baik-baik saja.

### Pengaturan APN Salah
Pengaturan Access Point Name (APN) sangat penting untuk konektivitas jaringan.
Jika `check_apn_settings()` menampilkan "Incorrect", pandu user untuk menggunakan `reset_apn_settings()` untuk mengatur ulang pengaturan APN.
Setelah mengatur ulang pengaturan APN, user harus diarahkan untuk menggunakan `reboot_device()` agar perubahan diterapkan.

### Penangguhan Saluran
Jika saluran ditangguhkan, user tidak akan memiliki layanan seluler.
Selidiki apakah saluran ditangguhkan. Lihat kebijakan agen umum untuk panduan menangani penangguhan saluran.
* Jika saluran ditangguhkan dan agen dapat mencabut penangguhan (sesuai kebijakan umum), verifikasi apakah layanan telah pulih.
* Jika penangguhan tidak dapat dicabut oleh agen (misalnya, karena tanggal akhir kontrak seperti yang disebutkan dalam kebijakan umum, atau alasan lain yang tidak dapat diselesaikan oleh agen), **eskalasi ke dukungan teknis**.

# Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda
Bagian ini menjelaskan kepada agen bagaimana ponsel user menggunakan data seluler untuk akses internet saat Wi-Fi tidak tersedia, dan merinci pemecahan masalah untuk masalah konektivitas dan kecepatan umum.

## Apa itu Data Seluler?
Data seluler memungkinkan ponsel terhubung ke internet menggunakan jaringan seluler operator. Ini memungkinkan penjelajahan situs web, penggunaan aplikasi, streaming video, serta mengirim/menerima email saat tidak tersambung ke Wi-Fi. Status bar biasanya menampilkan ikon seperti "5G", "LTE", "4G", "3G", "H+", atau "E" untuk menunjukkan koneksi data seluler aktif dan jenisnya.

## Prasyarat untuk Data Seluler
Agar data seluler berfungsi, user harus terlebih dahulu memiliki **layanan seluler**. Lihat panduan "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" jika user tidak memiliki layanan.

## Masalah dan Penyebab Umum Data Seluler
Bahkan dengan layanan seluler, masalah data seluler dapat terjadi. Alasan umum meliputi:

* **Mode Pesawat AKTIF**: Menonaktifkan semua koneksi nirkabel, termasuk data seluler.
* **Data Seluler Dimatikan**: Sakelar utama untuk data seluler mungkin dinonaktifkan di pengaturan ponsel.
* **Masalah Roaming (Saat Pengguna di Luar Negeri)**:
    * Roaming Data dimatikan di ponsel.
    * Saluran tidak memiliki roaming aktif.
* **Batas Paket Data Tercapai**: user mungkin telah menghabiskan jatah data bulanan mereka, dan operator memperlambat atau memutus data.
* **Mode Data Saver AKTIF**: Fitur ini membatasi penggunaan data latar belakang dan dapat membuat beberapa aplikasi atau layanan tampak lambat atau tidak responsif untuk menghemat data.
* **Masalah VPN**: Koneksi VPN yang aktif mungkin lambat atau salah konfigurasi, memengaruhi kecepatan atau konektivitas data.
* **Preferensi Jaringan Buruk**: Ponsel diatur ke teknologi jaringan yang lebih lama seperti 2G/3G.

## Mendiagnosis Masalah Data Seluler
`run_speed_test()` dapat digunakan untuk memeriksa potensi masalah dengan data seluler.
Saat data seluler tidak tersedia, tes kecepatan seharusnya mengembalikan 'no connection'.
Jika data tersedia, tes kecepatan juga akan mengembalikan kecepatan data.
Kecepatan apa pun di bawah 'Excellent' dianggap lambat.

## Pemecahan Masalah Data Seluler
### Mode Pesawat
Lihat bagian "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" untuk instruksi tentang cara memeriksa dan mematikan Mode Pesawat.

### Data Seluler Dinonaktifkan
Sakelar data seluler memungkinkan ponsel terhubung ke internet menggunakan jaringan seluler operator.
Jika `check_network_status()` menunjukkan data seluler dinonaktifkan, pandu user untuk menggunakan `toggle_data()` untuk menghidupkan data seluler.

### Mengatasi Masalah Roaming Data
Roaming data memungkinkan user menggunakan koneksi data ponsel mereka di area di luar jaringan rumah mereka (misalnya saat bepergian ke luar negeri).
Jika user berada di luar area cakupan utama operator mereka (roaming) dan data seluler tidak berfungsi, pandu mereka untuk menggunakan `toggle_roaming()` untuk memastikan Roaming Data AKTIF.
Anda harus memeriksa bahwa saluran yang terkait dengan nomor telepon yang diberikan user memiliki roaming aktif. Jika tidak, user tidak akan dapat menggunakan koneksi data ponsel mereka di area di luar jaringan rumah mereka.
Lihat kebijakan umum untuk panduan mengaktifkan roaming.

### Mode Data Saver
Mode Data Saver adalah fitur yang membatasi penggunaan data latar belakang dan dapat memengaruhi kecepatan data.
Jika `check_data_restriction_status()` menampilkan "Data Saver mode is ON", pandu user untuk menggunakan `toggle_data_saver_mode()` untuk mematikannya.

### Masalah Koneksi VPN
VPN (Virtual Private Network) adalah fitur yang mengenkripsi lalu lintas internet dan dapat membantu meningkatkan kecepatan dan keamanan data.
Namun dalam beberapa kasus, VPN dapat menyebabkan kecepatan turun secara signifikan.
Jika `check_vpn_status()` menampilkan "VPN is ON and connected" dan tingkat performa adalah "Poor", pandu user untuk menggunakan `disconnect_vpn()` untuk memutus VPN.

### Batas Paket Data Tercapai
Setiap paket menentukan penggunaan data maksimum per bulan.
Jika penggunaan data user untuk saluran yang terkait dengan nomor telepon yang diberikan user melebihi batas data paket, konektivitas data akan hilang.
user memiliki 2 opsi:
- Beralih ke paket dengan data lebih banyak.
- Menambahkan lebih banyak data ke saluran dengan "mengisi ulang" data dengan harga per GB yang ditentukan oleh paket.
Lihat kebijakan umum untuk panduan tentang opsi-opsi tersebut.

### Mengoptimalkan Preferensi Mode Jaringan
Preferensi mode jaringan adalah pengaturan yang menentukan jenis jaringan seluler yang akan disambungkan oleh ponsel.
Menggunakan mode yang lebih lama seperti 2G/3G dapat sangat membatasi kecepatan.
Jika `check_network_mode_preference()` menampilkan "2G" atau "3G", pandu user untuk menggunakan `set_network_mode_preference(mode: str)` dengan mode `"4g_5g_preferred"` agar ponsel dapat tersambung ke 5G.

# Memahami dan Memecahkan Masalah MMS (Pesan Gambar/Video)
Bagian ini menjelaskan kepada agen cara memecahkan masalah Multimedia Messaging Service (MMS), yang memungkinkan pengguna mengirim dan menerima pesan berisi gambar, video, atau audio.

## Apa itu MMS?
MMS adalah perluasan dari SMS (pesan teks) yang memungkinkan konten multimedia. Ketika seorang user mengirim foto ke teman melalui aplikasi pesan mereka, biasanya mereka menggunakan MMS.

## Prasyarat untuk MMS
Agar MMS berfungsi, user harus memiliki layanan seluler dan data seluler (kecepatan apa pun).
Lihat bagian "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" dan "Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda" untuk informasi lebih lanjut.

## Masalah dan Penyebab Umum MMS
* **Tidak Ada Layanan Seluler atau Data Seluler Mati/Tidak Berfungsi**: Alasan paling umum. MMS bergantung pada hal ini.
* **Pengaturan APN Salah**: Khususnya, URL MMSC yang hilang atau salah.
* **Tersambung ke Jaringan 2G**: Jaringan 2G umumnya tidak cocok untuk MMS.
* **Konfigurasi Wi-Fi Calling**: Dalam beberapa kasus, cara Wi-Fi Calling dikonfigurasi dapat memengaruhi MMS, terutama jika operator Anda tidak mendukung MMS melalui Wi-Fi.
* **Izin Aplikasi**: Aplikasi pesan memerlukan izin untuk mengakses penyimpanan (untuk file media) dan biasanya fungsi SMS.

## Mendiagnosis Masalah MMS
Alat `can_send_mms()` pada ponsel user dapat digunakan untuk memeriksa apakah user menghadapi masalah MMS.

## Pemecahan Masalah MMS
### Memastikan Konektivitas Dasar untuk MMS
Pengiriman MMS yang berhasil bergantung pada layanan dasar dan konektivitas data. Bagian ini mencakup verifikasi prasyarat tersebut.
Pertama, pastikan user dapat melakukan panggilan dan data selulernya berfungsi untuk aplikasi lain (misalnya, menjelajah web). Lihat bagian "Memahami dan Memecahkan Masalah Layanan Seluler Ponsel Anda" dan "Memahami dan Memecahkan Masalah Data Seluler Ponsel Anda" jika diperlukan.

### Teknologi Jaringan yang Tidak Cocok untuk MMS
MMS memiliki persyaratan jaringan tertentu; teknologi yang lebih lama seperti 2G tidak memadai. Bagian ini menjelaskan cara memeriksa jenis jaringan dan mengubahnya jika perlu.
MMS memerlukan setidaknya koneksi jaringan 3G; jaringan 2G umumnya tidak cocok.
Jika `check_network_status()` menampilkan "2G", pandu user untuk menggunakan `set_network_mode_preference(mode: str)` untuk beralih ke mode jaringan yang mencakup 3G, 4G, atau 5G (misalnya, `"4g_5g_preferred"` atau `"4g_only"`).

### Memverifikasi APN (MMSC URL) untuk MMS
MMSC adalah Multimedia Messaging Service Center. Ini adalah server yang menangani pesan MMS. Tanpa URL MMSC yang benar, user tidak akan dapat mengirim atau menerima pesan MMS.
Itu ditentukan sebagai bagian dari pengaturan APN. URL MMSC yang salah merupakan penyebab umum masalah MMS.
Jika `check_apn_settings()` menunjukkan URL MMSC tidak diatur, pandu user untuk menggunakan `reset_apn_settings()` untuk mengatur ulang pengaturan APN.
Setelah mengatur ulang pengaturan APN, user harus diarahkan untuk menggunakan `reboot_device()` agar perubahan diterapkan.

### Menyelidiki Gangguan Wi-Fi Calling dengan MMS
Pengaturan Wi-Fi Calling kadang-kadang dapat bertentangan dengan fungsi MMS.
Jika `check_wifi_calling_status()` menampilkan "Wi-Fi Calling is ON", pandu user untuk menggunakan `toggle_wifi_calling()` untuk mematikannya.

### Aplikasi Pesan Tidak Memiliki Izin yang Diperlukan
Aplikasi pesan memerlukan izin tertentu untuk menangani media dan mengirim pesan.
Jika `check_app_permissions(app_name="messaging")` menampilkan izin "storage" dan "sms" tidak tercantum sebagai diberikan, pandu user untuk menggunakan `grant_app_permission(app_name="messaging", permission="storage")` dan `grant_app_permission(app_name="messaging", permission="sms")` untuk memberikan izin yang diperlukan.