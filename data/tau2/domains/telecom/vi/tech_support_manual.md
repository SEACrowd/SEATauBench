# Giới thiệu
Tài liệu này đóng vai trò là hướng dẫn toàn diện cho các đại lý hỗ trợ kỹ thuật. Nó cung cấp các quy trình chi tiết và các bước khắc phục sự cố để hỗ trợ người dùng gặp các vấn đề thường gặp với dịch vụ di động, kết nối dữ liệu di động và Dịch vụ Nhắn tin Đa phương tiện (MMS) trên điện thoại của họ. Hướng dẫn được cấu trúc để giúp các đại lý chẩn đoán và giải quyết vấn đề hiệu quả bằng cách phác thảo cách các dịch vụ này hoạt động, các vấn đề thường gặp và các công cụ available để giải quyết.

Các phần chính được đề cập là:
*   **Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn**: Giải quyết các vấn đề liên quan đến kết nối mạng, cường độ tín hiệu và các vấn đề về thẻ SIM.
*   **Hiểu và Khắc phục sự cố Dữ liệu Di động trên Điện thoại của bạn**: Tập trung vào các vấn đề truy cập internet qua mạng di động, bao gồm tốc độ và kết nối.
*   **Hiểu và Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Video)**: Đề cập đến các vấn đề liên quan đến việc gửi và nhận tin nhắn đa phương tiện.

Đảm bảo bạn thử tất cả các cách có thể để giải quyết vấn đề của user trước khi chuyển cho nhân viên con người.

# Những gì user có thể làm trên thiết bị của họ
Đây là các hành động mà user có thể thực hiện trên thiết bị của họ.
Bạn phải hiểu rõ những điều này vì là một phần của hỗ trợ kỹ thuật, bạn sẽ phải giúp khách hàng thực hiện một loạt các hành động.

## Hành động Chẩn đoán (Chỉ đọc)
1. **check_status_bar** - Hiển thị các biểu tượng hiện đang hiển thị trên thanh trạng thái điện thoại của bạn (khu vực ở trên cùng của màn hình).
   - Trạng thái chế độ máy bay ("✈️ Airplane Mode" khi được bật)
   - Cường độ tín hiệu mạng ("📵 No Signal", "📶¹ Poor", "📶² Fair", "📶³ Good", "📶⁴ Excellent")
   - Công nghệ mạng (ví dụ: "5G", "4G", v.v.)
   - Trạng thái dữ liệu di động ("📱 Data Enabled" hoặc "📵 Data Disabled")
   - Trạng thái trình tiết kiệm dữ liệu ("🔽 Data Saver" khi được bật)
   - Trạng thái Wi-Fi ("📡 Connected to [SSID]" hoặc "📡 Enabled")
   - Trạng thái VPN ("🔒 VPN Connected" khi đã kết nối)
   - Mức pin ("🔋 [percentage]%")
2. **check_network_status** - Kiểm tra trạng thái kết nối của điện thoại của bạn với mạng di động và Wi-Fi. Hiển thị trạng thái chế độ máy bay, cường độ tín hiệu, loại mạng, liệu dữ liệu di động có được bật hay không và liệu chuyển vùng dữ liệu có được bật hay không. Cường độ tín hiệu có thể là "không có", "yếu" (1 vạch), "trung bình" (2 vạch), "tốt" (3 vạch), "xuất sắc" (4+ vạch).
3. **check_network_mode_preference** - Kiểm tra tùy chọn chế độ mạng của điện thoại của bạn. Hiển thị loại mạng di động mà điện thoại của bạn ưu tiên kết nối (ví dụ: 5G, 4G, 3G, 2G).
4. **check_sim_status** - Kiểm tra xem thẻ SIM của bạn có hoạt động chính xác không và hiển thị trạng thái hiện tại của nó. Hiển thị xem SIM có phải là đang hoạt động, bị mất hay bị khóa bằng mã PIN hoặc PUK không.
5. **check_data_restriction_status** - Kiểm tra xem điện thoại của bạn có bất kỳ tính năng giới hạn dữ liệu nào không đang hoạt động. Hiển thị xem chế độ Trình tiết kiệm dữ liệu có bật hay không và liệu mức sử dụng dữ liệu nền có bị hạn chế trên toàn cầu hay không.
6. **check_apn_settings** - Kiểm tra các cài đặt APN kỹ thuật mà điện thoại của bạn sử dụng để kết nối với mạng dữ liệu di động của nhà mạng của bạn. Hiển thị tên APN hiện tại và URL MMSC để nhắn tin hình ảnh.
7. **check_wifi_status** - Kiểm tra trạng thái kết nối Wi-Fi của bạn. Hiển thị xem Wi-Fi có được bật không, bạn đang đã kết nối với mạng nào (nếu có) và cường độ tín hiệu.
8. **check_wifi_calling_status** - Kiểm tra xem Wi-Fi Calling có được bật trên thiết bị của bạn hay không. Tính năng này cho phép bạn thực hiện và nhận cuộc gọi qua mạng Wi-Fi thay vì sử dụng mạng di động.
9. **check_vpn_status** - Kiểm tra xem bạn có đang sử dụng kết nối VPN (Mạng riêng ảo) không. Hiển thị xem VPN đang đang hoạt động, đã kết nối và hiển thị bất kỳ chi tiết kết nối available nào.
10. **check_installed_apps** - Trả về tên của tất cả các ứng dụng đã cài đặt trên điện thoại.
11. **check_app_status** - Kiểm tra thông tin chi tiết về một ứng dụng cụ thể. Hiển thị quyền và cài đặt mức sử dụng dữ liệu nền của nó.
12. **check_app_permissions** - Kiểm tra xem một ứng dụng cụ thể hiện có những quyền gì. Hiển thị xem ứng dụng có quyền truy cập vào các tính năng như bộ nhớ, máy ảnh, vị trí, v.v. không.
13. **run_speed_test** - Đo tốc độ kết nối internet hiện tại của bạn (tốc độ tải xuống). Cung cấp thông tin về chất lượng kết nối và những hoạt động nào nó có thể hỗ trợ. Tốc độ tải xuống có thể là "không xác định", "rất yếu", "yếu", "trung bình", "tốt" hoặc "xuất sắc".
14. **can_send_mms** - Kiểm tra xem ứng dụng nhắn tin có thể gửi tin nhắn MMS không.

## Hành động Khắc phục (Ghi/Sửa đổi)
1. **set_network_mode_preference** - Thay đổi loại mạng di động mà điện thoại của bạn ưu tiên kết nối (ví dụ: 5G, 4G, 3G). Các mạng tốc độ cao hơn (5G, 4G) cung cấp dữ liệu nhanh hơn nhưng có thể tốn nhiều pin hơn.
2. **toggle_airplane_mode** - Bật hoặc Tắt Chế độ Máy bay. Khi BẬT, nó ngắt kết nối tất cả liên lạc không dây bao gồm di động, Wi-Fi và Bluetooth.
3. **reseat_sim_card** - Mô phỏng việc tháo và lắp lại thẻ SIM của bạn. Điều này có thể giúp giải quyết các vấn đề nhận dạng.
4. **toggle_data** - Bật hoặc Tắt kết nối dữ liệu di động của điện thoại của bạn. Kiểm soát liệu điện thoại của bạn có thể sử dụng dữ liệu di động để truy cập internet khi Wi-Fi không khả dụng hay không.
5. **toggle_roaming** - Bật hoặc Tắt Chuyển vùng Dữ liệu. Khi BẬT, chuyển vùng được kích hoạt và điện thoại của bạn có thể sử dụng các mạng dữ liệu ở các khu vực bên ngoài vùng phủ sóng của nhà mạng của bạn.
6. **toggle_data_saver_mode** - Bật hoặc Tắt chế độ Trình tiết kiệm dữ liệu. Khi BẬT, nó giảm mức sử dụng dữ liệu, điều này có thể ảnh hưởng đến tốc độ dữ liệu.
7. **set_apn_settings** - Đặt cài đặt APN cho điện thoại.
8. **reset_apn_settings** - Đặt lại cài đặt APN của bạn về cài đặt mặc định.
9. **toggle_wifi** - Bật hoặc Tắt đài Wi-Fi của điện thoại của bạn. Kiểm soát liệu điện thoại của bạn có thể khám phá và kết nối với các mạng không dây để truy cập internet hay không.
10. **toggle_wifi_calling** - Bật hoặc Tắt Wi-Fi Calling. Tính năng này cho phép bạn thực hiện và nhận cuộc gọi qua Wi-Fi thay vì mạng di động, điều này có thể giúp ích ở những khu vực có tín hiệu di động yếu.
11. **connect_vpn** - Kết nối với VPN (Mạng riêng ảo) của bạn.
12. **disconnect_vpn** - Ngắt kết nối bất kỳ kết nối VPN (Mạng riêng ảo) đang hoạt động nào. Ngừng định tuyến lưu lượng truy cập internet của bạn qua máy chủ VPN, điều này có thể ảnh hưởng đến tốc độ kết nối hoặc quyền truy cập vào nội dung.
13. **grant_app_permission** - Cấp một quyền cụ thể cho một ứng dụng (như quyền truy cập vào bộ nhớ, máy ảnh hoặc vị trí). Cần thiết để một số chức năng của ứng dụng hoạt động chính xác.
14. **reboot_device** - Khởi động lại hoàn toàn điện thoại của bạn. Điều này có thể giúp giải quyết nhiều trục trặc phần mềm tạm thời bằng cách làm mới tất cả các dịch vụ và kết nối đang chạy.

# Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn
Phần này trình bày chi tiết cho các đại lý cách điện thoại của user kết nối với mạng di động (thường được gọi là "dịch vụ") và cung cấp các quy trình để khắc phục các sự cố thường gặp. Dịch vụ di động tốt là cần thiết cho các cuộc gọi, văn bản và dữ liệu di động.

## Các Sự cố Dịch vụ Phổ biến và Nguyên nhân của chúng
Nếu user đang gặp vấn đề về dịch vụ, đây là một số nguyên nhân phổ biến:

*   **Chế độ Máy bay đang BẬT**: Điều này vô hiệu hóa tất cả các đài không dây, bao gồm cả di động.
*   **Vấn đề về Thẻ SIM**:
    *   Không được lắp hoặc lắp không đúng cách.
    *   Bị khóa do nhập sai mã PIN/PUK.
*   **Cài đặt Mạng không chính xác**: Cài đặt APN có thể không chính xác dẫn đến mất dịch vụ.
*   **Vấn đề từ Nhà mạng**: Dòng dịch vụ của bạn có thể không hoạt động do vấn đề thanh toán.


## Chẩn đoán Sự cố Dịch vụ
`check_status_bar()` có thể được sử dụng để kiểm tra xem user có đang gặp sự cố về dịch vụ hay không.
Nếu có dịch vụ di động, thanh trạng thái sẽ trả về chỉ báo cường độ tín hiệu.

## Khắc phục sự cố Dịch vụ
### Chế độ Máy bay
Chế độ Máy bay là tính năng vô hiệu hóa tất cả các đài không dây, bao gồm cả di động. Nếu nó được kích hoạt, nó sẽ ngăn chặn bất kỳ kết nối di động nào.
Bạn có thể kiểm tra xem Chế độ Máy bay có đang BẬT hay không bằng cách sử dụng `check_status_bar()` hoặc `check_network_status()`.
Nếu nó đang BẬT, hãy hướng dẫn user sử dụng `toggle_airplane_mode()` để Tắt nó.

### Sự cố Thẻ SIM
Thẻ SIM là thẻ vật lý chứa thông tin của user và cho phép điện thoại kết nối với mạng di động.
Các vấn đề với thẻ SIM có thể dẫn đến mất hoàn toàn dịch vụ.
Vấn đề phổ biến nhất là thẻ SIM không được lắp đúng cách hoặc user đã nhập sai mã PIN hoặc PUK.
Sử dụng `check_sim_status()` để kiểm tra trạng thái của thẻ SIM.
Nếu nó hiển thị "Missing", hãy hướng dẫn user sử dụng `reseat_sim_card()` để đảm bảo thẻ SIM được lắp đúng cách.
Nếu nó hiển thị "Locked" (do nhập sai mã PIN hoặc PUK), **leo thang cho hỗ trợ kỹ thuật để được hỗ trợ về bảo mật SIM**.
Nếu nó hiển thị "Đang hoạt động", bản thân thẻ SIM có khả năng là ổn.

### Cài đặt APN không chính xác
Cài đặt Tên Điểm Truy cập (APN) rất quan trọng đối với kết nối mạng.
Nếu `check_apn_settings()` hiển thị "Incorrect", hãy hướng dẫn user sử dụng `reset_apn_settings()` để đặt lại cài đặt APN.
Sau khi đặt lại cài đặt APN, user phải được hướng dẫn sử dụng `reboot_device()` để các thay đổi có hiệu lực.

### Tạm dừng Dòng dịch vụ
Nếu dòng dịch vụ bị tạm dừng, user sẽ không có dịch vụ di động.
Điều tra xem dòng dịch vụ có bị tạm dừng hay không. Tham khảo chính sách đại lý chung để biết hướng dẫn về cách xử lý việc tạm dừng dòng dịch vụ.
*   Nếu dòng dịch vụ bị tạm dừng và đại lý có thể dỡ bỏ việc tạm dừng (theo chính sách chung), hãy xác minh xem dịch vụ có được khôi phục không.
*   Nếu việc tạm dừng không thể được dỡ bỏ bởi đại lý (ví dụ: do ngày kết thúc hợp đồng như đã đề cập trong chính sách chung, hoặc các lý do khác không thể giải quyết được bởi đại lý), **leo thang cho hỗ trợ kỹ thuật**.


# Hiểu và Khắc phục sự cố Dữ liệu Di động trên Điện thoại của bạn
Phần này giải thích cho các đại lý cách điện thoại của user sử dụng dữ liệu di động để truy cập internet khi không có Wi-Fi, và trình bày chi tiết cách khắc phục các vấn đề phổ biến về kết nối và tốc độ.

## Dữ liệu Di động là gì?
Dữ liệu di động cho phép điện thoại kết nối với internet bằng mạng di động của nhà mạng. Điều này cho phép duyệt web, sử dụng ứng dụng, truyền phát video và gửi/nhận email khi không đã kết nối với Wi-Fi. Thanh trạng thái thường hiển thị các biểu tượng như "5G", "LTE", "4G", "3G", "H+" hoặc "E" để biểu thị kết nối dữ liệu di động đang hoạt động và loại của nó.

## Điều kiện tiên quyết cho Dữ liệu Di động
Để dữ liệu di động hoạt động, user trước tiên phải có **dịch vụ di động**. Tham khảo hướng dẫn "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" nếu user không có dịch vụ.

## Các Sự cố Dữ liệu Di động Phổ biến và Nguyên nhân
Ngay cả với dịch vụ di động, các vấn đề về dữ liệu di động vẫn có thể xảy ra. Các lý do phổ biến bao gồm:

*   **Chế độ Máy bay đang BẬT**: Vô hiệu hóa tất cả các kết nối không dây, bao gồm cả dữ liệu di động.
*   **Dữ liệu Di động bị Tắt**: Công tắc chính cho dữ liệu di động có thể bị vô hiệu hóa trong cài đặt của điện thoại.
*   **Vấn đề Chuyển vùng (Khi người dùng ở nước ngoài)**:
    *   Chuyển vùng Dữ liệu bị Tắt trên điện thoại.
    *   Dòng dịch vụ không được kích hoạt chuyển vùng.
*   **Đã đạt giới hạn Gói Dữ liệu**: user có thể đã sử dụng hết hạn mức dữ liệu hàng tháng của họ, và nhà mạng đã làm chậm hoặc cắt dữ liệu.
*   **Chế độ Trình tiết kiệm Dữ liệu đang BẬT**: Tính năng này hạn chế mức sử dụng dữ liệu nền và có thể làm cho một số ứng dụng hoặc dịch vụ có vẻ chậm hoặc không phản hồi để tiết kiệm dữ liệu.
*   **Vấn đề VPN**: Kết nối VPN đang hoạt động có thể chậm hoặc được cấu hình sai, ảnh hưởng đến tốc độ dữ liệu hoặc kết nối.
*   **Tùy chọn Mạng không tốt**: điện thoại được đặt thành công nghệ mạng cũ hơn như 2G/3G.

## Chẩn đoán Sự cố Dữ liệu Di động
`run_speed_test()` có thể được sử dụng để kiểm tra các sự cố tiềm ẩn với dữ liệu di động.
Khi dữ liệu di động không khả dụng, một bài kiểm tra tốc độ sẽ trả về 'no connection'.
Nếu dữ liệu đang available, một bài kiểm tra tốc độ cũng sẽ trả về tốc độ dữ liệu.
Bất kỳ tốc độ nào dưới 'Excellent' đều được coi là chậm.

## Khắc phục sự cố Dữ liệu Di động
### Chế độ Máy bay
Tham khảo phần "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" để biết hướng dẫn về cách kiểm tra và tắt Chế độ Máy bay.

### Dữ liệu Di động bị Tắt
Công tắc dữ liệu di động cho phép điện thoại kết nối với internet bằng mạng di động của nhà mạng.
Nếu `check_network_status()` hiển thị dữ liệu di động bị tắt, hãy hướng dẫn user sử dụng `toggle_data()` để Bật dữ liệu di động.

### Giải quyết các vấn đề Chuyển vùng Dữ liệu
Chuyển vùng dữ liệu cho phép user sử dụng kết nối dữ liệu của điện thoại của họ ở các khu vực bên ngoài mạng gia đình của họ (ví dụ: khi đi du lịch nước ngoài).
Nếu user ở bên ngoài vùng phủ sóng chính của nhà mạng của họ (chuyển vùng) và dữ liệu di động không hoạt động, hãy hướng dẫn họ sử dụng `toggle_roaming()` để đảm bảo Chuyển vùng Dữ liệu được BẬT.
Bạn nên kiểm tra xem dòng dịch vụ liên quan đến số điện thoại mà user cung cấp có được kích hoạt chuyển vùng hay không. Nếu không, user sẽ không thể sử dụng kết nối dữ liệu của điện thoại của họ ở các khu vực bên ngoài mạng gia đình của họ.
Tham khảo chính sách chung để biết hướng dẫn về việc kích hoạt chuyển vùng.

### Chế độ Trình tiết kiệm Dữ liệu
Chế độ Trình tiết kiệm dữ liệu là một tính năng hạn chế mức sử dụng dữ liệu nền và có thể ảnh hưởng đến tốc độ dữ liệu.
Nếu `check_data_restriction_status()` hiển thị "Data Saver mode is ON", hãy hướng dẫn user sử dụng `toggle_data_saver_mode()` để Tắt nó.

### Sự cố Kết nối VPN
VPN (Mạng riêng ảo) là một tính năng mã hóa lưu lượng truy cập internet và có thể giúp cải thiện tốc độ và bảo mật dữ liệu.
Tuy nhiên, trong một số trường hợp, VPN có thể làm tốc độ giảm đáng kể.
Nếu `check_vpn_status()` hiển thị "VPN is ON and đã kết nối" và mức hiệu suất là "Poor", hãy hướng dẫn user sử dụng `disconnect_vpn()` để ngắt kết nối VPN.

### Đã đạt giới hạn Gói Dữ liệu
Mỗi gói cước chỉ định mức sử dụng dữ liệu tối đa mỗi tháng.
Nếu mức sử dụng dữ liệu của user cho một dòng dịch vụ liên quan đến số điện thoại mà user cung cấp vượt quá giới hạn dữ liệu của gói cước, kết nối dữ liệu sẽ bị mất.
user có 2 tùy chọn:
- Thay đổi sang gói cước có nhiều dữ liệu hơn.
- Thêm nhiều dữ liệu hơn vào dòng dịch vụ bằng cách "nạp thêm" dữ liệu với giá mỗi GB do gói cước chỉ định.
Tham khảo chính sách chung để biết hướng dẫn về các tùy chọn đó.

### Tối ưu hóa Tùy chọn Chế độ Mạng
Tùy chọn chế độ mạng là các cài đặt xác định loại mạng di động mà điện thoại sẽ kết nối.
Sử dụng các chế độ cũ hơn như 2G/3G có thể làm giảm đáng kể tốc độ.
Nếu `check_network_mode_preference()` hiển thị "2G" hoặc "3G", hãy hướng dẫn user sử dụng `set_network_mode_preference(mode: str)` với chế độ `"ưu tiên 4g_5g"` để cho phép điện thoại kết nối với 5G.

# Hiểu và Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Video)
Phần này giải thích cho các đại lý cách khắc phục sự cố Dịch vụ Nhắn tin Đa phương tiện (MMS), cho phép người dùng gửi và nhận tin nhắn chứa hình ảnh, video hoặc âm thanh.

## MMS là gì?
MMS là phần mở rộng của SMS (nhắn tin văn bản) cho phép nội dung đa phương tiện. Khi user gửi ảnh cho bạn bè qua ứng dụng nhắn tin của họ, họ thường sử dụng MMS.

## Điều kiện tiên quyết cho MMS
Để MMS hoạt động, user phải có dịch vụ di động và dữ liệu di động (bất kỳ tốc độ nào).
Tham khảo các phần "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" và "Hiểu và Khắc phục sự cố Dữ liệu Di động trên Điện thoại của bạn" để biết thêm thông tin.

## Các Sự cố MMS Phổ biến và Nguyên nhân
*   **Không có Dịch vụ Di động hoặc Dữ liệu Di động Tắt/Không hoạt động**: Các lý do phổ biến nhất. MMS dựa vào những điều này.
*   **Cài đặt APN không chính xác**: Cụ thể là bị mất hoặc URL MMSC không chính xác.
*   **Kết nối với Mạng 2G**: Mạng 2G thường không phù hợp với MMS.
*   **Cấu hình Wi-Fi Calling**: Trong một số trường hợp, cách Wi-Fi Calling được cấu hình có thể ảnh hưởng đến MMS, đặc biệt nếu nhà mạng của bạn không hỗ trợ MMS qua Wi-Fi.
*   **Quyền Ứng dụng**: Ứng dụng nhắn tin cần quyền truy cập vào bộ nhớ (cho các tệp phương tiện) và thường là các chức năng SMS.

## Chẩn đoán Sự cố MMS
Công cụ `can_send_mms()` trên điện thoại của user có thể được sử dụng để kiểm tra xem user có đang gặp sự cố MMS hay không.

## Khắc phục sự cố MMS
### Đảm bảo Kết nối Cơ bản cho MMS
Nhắn tin MMS thành công dựa vào dịch vụ và kết nối dữ liệu cơ bản. Phần này bao gồm việc xác minh các điều kiện tiên quyết này.
Trước tiên, hãy đảm bảo user có thể thực hiện cuộc gọi và dữ liệu di động của họ đang hoạt động cho các ứng dụng khác (ví dụ: duyệt web). Tham khảo các phần "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" và "Hiểu và Khắc phục sự cố Dữ liệu Di động trên Điện thoại của bạn" nếu cần.

### Công nghệ mạng không phù hợp cho MMS
MMS có các yêu cầu mạng cụ thể; các công nghệ cũ hơn như 2G là không đủ. Phần này giải thích cách kiểm tra loại mạng và thay đổi nó nếu cần thiết.
MMS yêu cầu kết nối mạng ít nhất là 3G; mạng 2G thường không phù hợp.
Nếu `check_network_status()` hiển thị "2G", hãy hướng dẫn user sử dụng `set_network_mode_preference(mode: str)` để chuyển sang chế độ mạng bao gồm 3G, 4G hoặc 5G (ví dụ: `"ưu tiên 4g_5g"` hoặc `"chỉ 4g"`).

### Xác minh APN (URL MMSC) cho MMS
MMSC là Trung tâm Dịch vụ Nhắn tin Đa phương tiện. Đây là máy chủ xử lý tin nhắn MMS. Nếu không có URL MMSC chính xác, user sẽ không thể gửi hoặc nhận tin nhắn MMS.
Chúng được chỉ định như một phần của cài đặt APN. URL MMSC không chính xác là nguyên nhân rất phổ biến gây ra các sự cố MMS.
Nếu `check_apn_settings()` hiển thị URL MMSC chưa được đặt, hãy hướng dẫn user sử dụng `reset_apn_settings()` để đặt lại cài đặt APN.
Sau khi đặt lại cài đặt APN, user phải được hướng dẫn sử dụng `reboot_device()` để các thay đổi có hiệu lực.

### Điều tra sự can thiệp của Wi-Fi Calling với MMS
Cài đặt Wi-Fi Calling đôi khi có thể xung đột với chức năng MMS.
Nếu `check_wifi_calling_status()` hiển thị "Wi-Fi Calling is ON", hãy hướng dẫn user sử dụng `toggle_wifi_calling()` để Tắt nó.

### Ứng dụng nhắn tin thiếu các quyền cần thiết
Ứng dụng nhắn tin cần các quyền cụ thể để xử lý phương tiện và gửi tin nhắn.
Nếu `check_app_permissions(app_name="messaging")` hiển thị quyền "storage" và "sms" không được liệt kê là đã cấp, hãy hướng dẫn user sử dụng `grant_app_permission(app_name="messaging", permission="storage")` và `grant_app_permission(app_name="messaging", permission="sms")` để cấp các quyền cần thiết.