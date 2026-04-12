# Giới thiệu
Tài liệu này đóng vai trò là hướng dẫn toàn diện cho nhân viên hỗ trợ kỹ thuật. Nó cung cấp các quy trình chi tiết và các bước khắc phục sự cố để hỗ trợ người dùng gặp phải các vấn đề thường gặp với dịch vụ di động, kết nối dữ liệu di động và Dịch vụ Nhắn tin Đa phương tiện (MMS) trên điện thoại. Hướng dẫn này được cấu trúc để giúp nhân viên chẩn đoán và giải quyết vấn đề hiệu quả bằng cách phác thảo cách các dịch vụ này hoạt động, các vấn đề thường gặp và các công cụ có sẵn để giải quyết.

Các phần chính được bao gồm là:
*   **Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn**: Giải quyết các vấn đề liên quan đến kết nối mạng, cường độ tín hiệu và các vấn đề về thẻ SIM.
*   **Hiểu và Khắc phục sự cố Dữ liệu di động trên Điện thoại của bạn**: Tập trung vào các vấn đề truy cập internet qua mạng di động, bao gồm tốc độ và khả năng kết nối.
*   **Hiểu và Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Video)**: Đề cập đến các vấn đề liên quan đến gửi và nhận tin nhắn đa phương tiện.

Hãy đảm bảo bạn đã thử tất cả các cách có thể để giải quyết vấn đề của người dùng trước khi chuyển cho nhân viên hỗ trợ con người.

# Những gì người dùng có thể làm trên thiết bị của họ
Đây là các hành động mà người dùng có thể thực hiện trên thiết bị của họ.
Bạn phải hiểu rõ những điều này vì với tư cách là nhân viên hỗ trợ kỹ thuật, bạn sẽ phải giúp khách hàng thực hiện một loạt các hành động.

## Hành động Chẩn đoán (Chỉ đọc)
1. **check_status_bar** - Hiển thị các biểu tượng hiện đang hiển thị trên thanh trạng thái của điện thoại (khu vực ở đầu màn hình).
   - Trạng thái chế độ máy bay ("✈️ Airplane Mode" khi được bật)
   - Cường độ tín hiệu mạng ("📵 No Signal", "📶¹ Poor", "📶² Fair", "📶³ Good", "📶⁴ Excellent")
   - Công nghệ mạng (ví dụ: "5G", "4G", v.v.)
   - Trạng thái dữ liệu di động ("📱 Data Enabled" hoặc "📵 Data Disabled")
   - Trạng thái tiết kiệm dữ liệu ("🔽 Data Saver" khi được bật)
   - Trạng thái Wi-Fi ("📡 Connected to [SSID]" hoặc "📡 Enabled")
   - Trạng thái VPN ("🔒 VPN Connected" khi được kết nối)
   - Mức pin ("🔋 [percentage]%")
2. **check_network_status** - Kiểm tra trạng thái kết nối của điện thoại với mạng di động và Wi-Fi. Hiển thị trạng thái chế độ máy bay, cường độ tín hiệu, loại mạng, liệu dữ liệu di động có được bật hay không và liệu chuyển vùng dữ liệu có được bật hay không. Cường độ tín hiệu có thể là "none", "poor" (1 vạch), "fair" (2 vạch), "good" (3 vạch), "excellent" (4+ vạch).
3. **check_network_mode_preference** - Kiểm tra tùy chọn chế độ mạng của điện thoại. Hiển thị loại mạng di động mà điện thoại của bạn ưu tiên kết nối (ví dụ: 5G, 4G, 3G, 2G).
4. **check_sim_status** - Kiểm tra xem thẻ SIM hoạt động bình thường không và hiển thị trạng thái hiện tại. Hiển thị liệu thẻ SIM đang hoạt động, bị thiếu, hay bị khóa bằng mã PIN hoặc PUK.
5. **check_data_restriction_status** - Kiểm tra xem điện thoại của bạn có tính năng hạn chế dữ liệu nào đang hoạt động hay không. Hiển thị xem chế độ Tiết kiệm dữ liệu (Data Saver) có bật không và liệu việc sử dụng dữ liệu nền có bị hạn chế trên toàn cầu hay không.
6. **check_apn_settings** - Kiểm tra cài đặt APN kỹ thuật mà điện thoại của bạn sử dụng để kết nối với mạng dữ liệu di động của nhà mạng. Hiển thị tên APN hiện tại và URL MMSC cho tin nhắn hình ảnh.
7. **check_wifi_status** - Kiểm tra trạng thái kết nối Wi-Fi. Hiển thị xem Wi-Fi đã bật chưa, mạng nào đang kết nối (nếu có) và cường độ tín hiệu.
8. **check_wifi_calling_status** - Kiểm tra xem tính năng Wi-Fi Calling có được bật trên thiết bị hay không. Tính năng này cho phép bạn thực hiện và nhận cuộc gọi qua mạng Wi-Fi thay vì sử dụng mạng di động.
9. **check_vpn_status** - Kiểm tra xem bạn có đang sử dụng kết nối VPN (Mạng riêng ảo) hay không. Hiển thị xem VPN đang hoạt động, đã kết nối và hiển thị bất kỳ chi tiết kết nối nào có sẵn.
10. **check_installed_apps** - Trả về tên của tất cả các ứng dụng đã cài đặt trên điện thoại.
11. **check_app_status** - Kiểm tra thông tin chi tiết về một ứng dụng cụ thể. Hiển thị các quyền và cài đặt sử dụng dữ liệu nền của ứng dụng.
12. **check_app_permissions** - Kiểm tra các quyền mà một ứng dụng cụ thể hiện có. Hiển thị liệu ứng dụng có quyền truy cập vào các tính năng như bộ nhớ, camera, vị trí, v.v.
13. **run_speed_test** - Đo tốc độ kết nối internet hiện tại của bạn (tốc độ tải xuống). Cung cấp thông tin về chất lượng kết nối và các hoạt động mà nó có thể hỗ trợ. Tốc độ tải xuống có thể là "unknown", "very poor", "poor", "fair", "good", hoặc "excellent".
14. **can_send_mms** - Kiểm tra xem ứng dụng nhắn tin có thể gửi tin nhắn MMS không.

## Hành động Khắc phục (Ghi/Sửa đổi)
1. **set_network_mode_preference** - Thay đổi loại mạng di động mà điện thoại của bạn ưu tiên kết nối (ví dụ: 5G, 4G, 3G). Các mạng tốc độ cao (5G, 4G) cung cấp dữ liệu nhanh hơn nhưng có thể tiêu tốn nhiều pin hơn.
2. **toggle_airplane_mode** - Bật hoặc tắt Chế độ máy bay. Khi BẬT, nó ngắt kết nối tất cả các liên lạc không dây bao gồm di động, Wi-Fi và Bluetooth.
3. **reseat_sim_card** - Mô phỏng việc tháo và lắp lại thẻ SIM. Điều này có thể giúp giải quyết các vấn đề nhận dạng.
4. **toggle_data** - Bật hoặc tắt kết nối dữ liệu di động của điện thoại. Kiểm soát liệu điện thoại của bạn có thể sử dụng dữ liệu di động để truy cập internet khi Wi-Fi không khả dụng hay không.
5. **toggle_roaming** - Bật hoặc tắt Chuyển vùng dữ liệu. Khi BẬT, chuyển vùng được kích hoạt và điện thoại của bạn có thể sử dụng các mạng dữ liệu ở những khu vực ngoài vùng phủ sóng của nhà mạng bạn.
6. **toggle_data_saver_mode** - Bật hoặc tắt chế độ Tiết kiệm dữ liệu. Khi BẬT, nó làm giảm mức sử dụng dữ liệu, điều này có thể ảnh hưởng đến tốc độ dữ liệu.
7. **set_apn_settings** - Thiết lập các cài đặt APN cho điện thoại.
8. **reset_apn_settings** - Đưa cài đặt APN của bạn về cài đặt mặc định.
9. **toggle_wifi** - Bật hoặc tắt Wi-Fi của điện thoại. Kiểm soát liệu điện thoại của bạn có thể khám phá và kết nối với các mạng không dây để truy cập internet hay không.
10. **toggle_wifi_calling** - Bật hoặc tắt Wi-Fi Calling. Tính năng này cho phép bạn thực hiện và nhận cuộc gọi qua Wi-Fi thay vì mạng di động, điều này có thể hữu ích ở những khu vực có tín hiệu di động yếu.
11. **connect_vpn** - Kết nối với VPN (Mạng riêng ảo) của bạn.
12. **disconnect_vpn** - Ngắt kết nối bất kỳ kết nối VPN (Mạng riêng ảo) đang hoạt động nào. Ngừng định tuyến lưu lượng truy cập internet của bạn qua máy chủ VPN, điều này có thể ảnh hưởng đến tốc độ kết nối hoặc quyền truy cập nội dung.
13. **grant_app_permission** - Cấp một quyền cụ thể cho một ứng dụng (như quyền truy cập bộ nhớ, camera hoặc vị trí). Được yêu cầu để một số chức năng ứng dụng hoạt động bình thường.
14. **reboot_device** - Khởi động lại điện thoại của bạn hoàn toàn. Điều này có thể giúp giải quyết nhiều lỗi phần mềm tạm thời bằng cách làm mới tất cả các dịch vụ và kết nối đang chạy.

# Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn
Phần này chi tiết cho nhân viên cách điện thoại của người dùng kết nối với mạng di động (thường được gọi là "dịch vụ") và cung cấp các quy trình để khắc phục các sự cố thường gặp. Dịch vụ di động tốt là yêu cầu bắt buộc đối với cuộc gọi, văn bản và dữ liệu di động.

## Sự cố Dịch vụ Thường gặp và Nguyên nhân
Nếu người dùng đang gặp vấn đề về dịch vụ, đây là một số nguyên nhân phổ biến:

*   **Chế độ Máy bay đang BẬT**: Điều này vô hiệu hóa tất cả các thiết bị thu phát sóng không dây, bao gồm cả di động.
*   **Vấn đề về Thẻ SIM**:
    *   Chưa lắp hoặc lắp không đúng cách.
    *   Bị khóa do nhập sai mã PIN/PUK.
*   **Cài đặt mạng không chính xác**: Cài đặt APN có thể không chính xác dẫn đến mất dịch vụ.
*   **Vấn đề từ Nhà mạng**: Số thuê bao của bạn có thể không hoạt động do vấn đề thanh toán.


## Chẩn đoán Sự cố Dịch vụ
`check_status_bar()` có thể được sử dụng để kiểm tra xem người dùng có đang gặp sự cố dịch vụ hay không.
Nếu có dịch vụ di động, thanh trạng thái sẽ hiển thị chỉ báo cường độ tín hiệu.

## Khắc phục sự cố Dịch vụ
### Chế độ Máy bay
Chế độ Máy bay là một tính năng vô hiệu hóa tất cả các thiết bị thu phát sóng không dây, bao gồm cả di động. Nếu nó được bật, nó sẽ chặn bất kỳ kết nối di động nào.
Bạn có thể kiểm tra xem Chế độ Máy bay có đang BẬT không bằng cách sử dụng `check_status_bar()` hoặc `check_network_status()`.
Nếu nó ĐANG BẬT, hãy hướng dẫn người dùng sử dụng `toggle_airplane_mode()` để TẮT nó.

### Vấn đề về Thẻ SIM
Thẻ SIM là thẻ vật lý chứa thông tin của người dùng và cho phép điện thoại kết nối với mạng di động.
Các vấn đề với thẻ SIM có thể dẫn đến việc mất dịch vụ hoàn toàn.
Vấn đề phổ biến nhất là thẻ SIM không được đặt đúng cách hoặc người dùng đã nhập sai mã PIN hoặc PUK.
Sử dụng `check_sim_status()` để kiểm tra trạng thái của thẻ SIM.
Nếu nó hiển thị "Missing", hãy hướng dẫn người dùng sử dụng `reseat_sim_card()` để đảm bảo thẻ SIM được lắp chính xác.
Nếu nó hiển thị "Locked" (do nhập sai mã PIN hoặc PUK), **hãy chuyển cho hỗ trợ kỹ thuật để được trợ giúp về bảo mật SIM**.
Nếu nó hiển thị "Active", thẻ SIM có khả năng hoạt động tốt.

### Cài đặt APN không chính xác
Cài đặt Tên Điểm truy cập (APN) rất quan trọng đối với kết nối mạng.
Nếu `check_apn_settings()` hiển thị "Incorrect", hãy hướng dẫn người dùng sử dụng `reset_apn_settings()` để đặt lại cài đặt APN.
Sau khi đặt lại cài đặt APN, người dùng phải được hướng dẫn sử dụng `reboot_device()` để các thay đổi có hiệu lực.

### Đình chỉ Số thuê bao (Line Suspension)
Nếu số thuê bao bị đình chỉ, người dùng sẽ không có dịch vụ di động.
Điều tra xem số thuê bao có bị đình chỉ hay không. Tham khảo chính sách đại lý chung để biết nguyên tắc xử lý đình chỉ số thuê bao.
*   Nếu số thuê bao bị đình chỉ và đại lý có thể bỏ đình chỉ (theo chính sách chung), hãy xác minh xem dịch vụ đã được khôi phục chưa.
*   Nếu không thể bỏ đình chỉ (ví dụ: do ngày kết thúc hợp đồng như đã đề cập trong chính sách chung, hoặc các lý do khác mà đại lý không thể giải quyết), **hãy chuyển cho hỗ trợ kỹ thuật**.


# Hiểu và Khắc phục sự cố Dữ liệu di động trên Điện thoại của bạn
Phần này giải thích cho nhân viên cách điện thoại của người dùng sử dụng dữ liệu di động để truy cập internet khi không có Wi-Fi và chi tiết cách khắc phục sự cố cho các vấn đề kết nối và tốc độ phổ biến.

## Dữ liệu di động là gì?
Dữ liệu di động cho phép điện thoại kết nối với internet bằng mạng di động của nhà mạng. Điều này cho phép duyệt web, sử dụng ứng dụng, truyền phát video và gửi/nhận email khi không kết nối với Wi-Fi. Thanh trạng thái thường hiển thị các biểu tượng như "5G", "LTE", "4G", "3G", "H+" hoặc "E" để chỉ kết nối dữ liệu di động đang hoạt động và loại của nó.

## Điều kiện tiên quyết cho Dữ liệu di động
Để dữ liệu di động hoạt động, người dùng trước tiên phải có **dịch vụ di động**. Tham khảo hướng dẫn "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" nếu người dùng không có dịch vụ.

## Sự cố Dữ liệu di động Thường gặp và Nguyên nhân
Ngay cả khi có dịch vụ di động, các vấn đề về dữ liệu di động vẫn có thể xảy ra. Các nguyên nhân phổ biến bao gồm:

*   **Chế độ Máy bay đang BẬT**: Vô hiệu hóa tất cả các kết nối không dây, bao gồm cả dữ liệu di động.
*   **Dữ liệu di động ĐANG TẮT**: Công tắc chính cho dữ liệu di động có thể đã bị vô hiệu hóa trong cài đặt của điện thoại.
*   **Vấn đề chuyển vùng (Khi Người dùng ở Nước ngoài)**:
    *   Chuyển vùng dữ liệu đã TẮT trên điện thoại.
    *   Số thuê bao không bật chuyển vùng.
*   **Đã đạt giới hạn gói dữ liệu**: Người dùng có thể đã sử dụng hết hạn mức dữ liệu hàng tháng của họ và nhà mạng đã làm chậm hoặc cắt dữ liệu.
*   **Chế độ Tiết kiệm dữ liệu ĐANG BẬT**: Tính năng này hạn chế việc sử dụng dữ liệu nền và có thể làm cho một số ứng dụng hoặc dịch vụ có vẻ chậm hoặc không phản hồi để tiết kiệm dữ liệu.
*   **Vấn đề VPN**: Kết nối VPN đang hoạt động có thể chậm hoặc được cấu hình sai, ảnh hưởng đến tốc độ hoặc kết nối dữ liệu.
*   **Tùy chọn mạng xấu**: Điện thoại được đặt thành công nghệ mạng cũ hơn như 2G/3G.

## Chẩn đoán Sự cố Dữ liệu di động
`run_speed_test()` có thể được sử dụng để kiểm tra các vấn đề tiềm ẩn với dữ liệu di động.
Khi dữ liệu di động không khả dụng, một bài kiểm tra tốc độ sẽ trả về 'no connection'.
Nếu dữ liệu khả dụng, bài kiểm tra tốc độ cũng sẽ trả về tốc độ dữ liệu.
Bất kỳ tốc độ nào dưới 'Excellent' đều được coi là chậm.

## Khắc phục sự cố Dữ liệu di động
### Chế độ Máy bay
Tham khảo phần "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" để biết hướng dẫn về cách kiểm tra và tắt Chế độ Máy bay.

### Đã tắt Dữ liệu di động
Công tắc dữ liệu di động cho phép điện thoại kết nối với internet bằng mạng di động của nhà mạng.
Nếu `check_network_status()` hiển thị dữ liệu di động đã tắt, hãy hướng dẫn người dùng sử dụng `toggle_data()` để bật dữ liệu di động.

### Giải quyết các vấn đề Chuyển vùng dữ liệu (Data Roaming)
Chuyển vùng dữ liệu cho phép người dùng sử dụng kết nối dữ liệu của điện thoại ở các khu vực ngoài mạng nội bộ của họ (ví dụ: khi đi du lịch nước ngoài).
Nếu người dùng đang ở ngoài khu vực phủ sóng chính của nhà mạng (chuyển vùng) và dữ liệu di động không hoạt động, hãy hướng dẫn họ sử dụng `toggle_roaming()` để đảm bảo Chuyển vùng dữ liệu đang BẬT.
Bạn nên kiểm tra xem số thuê bao liên kết với số điện thoại mà người dùng cung cấp có được bật chuyển vùng hay không. Nếu không, người dùng sẽ không thể sử dụng kết nối dữ liệu của điện thoại ở những khu vực ngoài mạng nội bộ của họ.
Tham khảo chính sách chung để biết nguyên tắc bật chuyển vùng.

### Chế độ Tiết kiệm dữ liệu
Chế độ Tiết kiệm dữ liệu là một tính năng hạn chế việc sử dụng dữ liệu nền và có thể ảnh hưởng đến tốc độ dữ liệu.
Nếu `check_data_restriction_status()` hiển thị "Data Saver mode is ON", hãy hướng dẫn người dùng sử dụng `toggle_data_saver_mode()` để TẮT nó.

### Sự cố kết nối VPN
VPN (Mạng riêng ảo) là một tính năng mã hóa lưu lượng truy cập internet và có thể giúp cải thiện tốc độ và tính bảo mật của dữ liệu.
Tuy nhiên, trong một số trường hợp, VPN có thể làm tốc độ giảm đáng kể.
Nếu `check_vpn_status()` hiển thị "VPN is ON and connected" và mức hiệu suất là "Poor", hãy hướng dẫn người dùng sử dụng `disconnect_vpn()` để ngắt kết nối VPN.

### Đã đạt giới hạn gói dữ liệu
Mỗi gói cước chỉ định giới hạn sử dụng dữ liệu tối đa mỗi tháng.
Nếu mức sử dụng dữ liệu của người dùng cho một số thuê bao liên kết với số điện thoại mà người dùng cung cấp vượt quá giới hạn dữ liệu của gói, kết nối dữ liệu sẽ bị gián đoạn.
Người dùng có 2 tùy chọn:
- Đổi sang gói cước có nhiều dữ liệu hơn.
- Thêm dữ liệu cho số thuê bao bằng cách "nạp thêm" dữ liệu với giá mỗi GB được chỉ định bởi gói cước.
Tham khảo chính sách chung để biết nguyên tắc về các tùy chọn đó.

### Tối ưu hóa Tùy chọn Chế độ Mạng
Tùy chọn chế độ mạng là các cài đặt xác định loại mạng di động mà điện thoại sẽ kết nối.
Sử dụng các chế độ cũ hơn như 2G/3G có thể hạn chế đáng kể tốc độ.
Nếu `check_network_mode_preference()` hiển thị "2G" hoặc "3G", hãy hướng dẫn người dùng sử dụng `set_network_mode_preference(mode: str)` với chế độ `"4g_5g_preferred"` để cho phép điện thoại kết nối với 5G.

# Hiểu và Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Video)
Phần này giải thích cho nhân viên cách khắc phục sự cố Dịch vụ Nhắn tin Đa phương tiện (MMS), cho phép người dùng gửi và nhận tin nhắn chứa hình ảnh, video hoặc âm thanh.

## MMS là gì?
MMS là một phần mở rộng của SMS (nhắn tin văn bản) cho phép nội dung đa phương tiện. Khi người dùng gửi ảnh cho bạn bè qua ứng dụng nhắn tin của họ, họ thường sử dụng MMS.

## Điều kiện tiên quyết cho MMS
Để MMS hoạt động, người dùng phải có dịch vụ di động và dữ liệu di động (bất kỳ tốc độ nào).
Tham khảo các phần "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" và "Hiểu và Khắc phục sự cố Dữ liệu di động trên Điện thoại của bạn" để biết thêm thông tin.

## Sự cố MMS Thường gặp và Nguyên nhân
*   **Không có dịch vụ di động hoặc Dữ liệu di động TẮT/Không hoạt động**: Các lý do phổ biến nhất. MMS dựa vào các điều này.
*   **Cài đặt APN không chính xác**: Cụ thể là thiếu hoặc URL MMSC không chính xác.
*   **Đang kết nối với mạng 2G**: Mạng 2G thường không phù hợp cho MMS.
*   **Cấu hình Wi-Fi Calling**: Trong một số trường hợp, cách Wi-Fi Calling được cấu hình có thể ảnh hưởng đến MMS, đặc biệt nếu nhà mạng của bạn không hỗ trợ MMS qua Wi-Fi.
*   **Quyền ứng dụng**: Ứng dụng nhắn tin cần quyền truy cập bộ nhớ (cho các tệp phương tiện) và thường là các chức năng SMS.

## Chẩn đoán Sự cố MMS
Công cụ `can_send_mms()` trên điện thoại của người dùng có thể được sử dụng để kiểm tra xem người dùng có đang gặp sự cố MMS hay không.

## Khắc phục sự cố MMS
### Đảm bảo Kết nối Cơ bản cho MMS
Nhắn tin MMS thành công dựa trên dịch vụ cơ bản và kết nối dữ liệu. Phần này bao gồm việc xác minh các điều kiện tiên quyết này.
Trước tiên, hãy đảm bảo người dùng có thể thực hiện cuộc gọi và dữ liệu di động của họ đang hoạt động cho các ứng dụng khác (ví dụ: duyệt web). Tham khảo các phần "Hiểu và Khắc phục sự cố Dịch vụ Di động trên Điện thoại của bạn" và "Hiểu và Khắc phục sự cố Dữ liệu di động trên Điện thoại của bạn" nếu cần.

### Công nghệ mạng không phù hợp cho MMS
MMS có các yêu cầu mạng cụ thể; các công nghệ cũ hơn như 2G không đủ. Phần này giải thích cách kiểm tra loại mạng và thay đổi nếu cần.
MMS yêu cầu kết nối mạng ít nhất 3G; mạng 2G thường không phù hợp.
Nếu `check_network_status()` hiển thị "2G", hãy hướng dẫn người dùng sử dụng `set_network_mode_preference(mode: str)` để chuyển sang chế độ mạng bao gồm 3G, 4G hoặc 5G (ví dụ: `"4g_5g_preferred"` hoặc `"4g_only"`).

### Xác minh APN (URL MMSC) cho MMS
MMSC là Trung tâm Dịch vụ Nhắn tin Đa phương tiện. Đó là máy chủ xử lý các tin nhắn MMS. Nếu không có URL MMSC chính xác, người dùng sẽ không thể gửi hoặc nhận tin nhắn MMS.
Chúng được chỉ định như một phần của cài đặt APN. URL MMSC không chính xác là một nguyên nhân rất phổ biến gây ra sự cố MMS.
Nếu `check_apn_settings()` hiển thị URL MMSC chưa được đặt, hãy hướng dẫn người dùng sử dụng `reset_apn_settings()` để đặt lại các cài đặt APN.
Sau khi đặt lại cài đặt APN, người dùng phải được hướng dẫn sử dụng `reboot_device()` để các thay đổi có hiệu lực.

### Điều tra Nhiễu Wi-Fi Calling với MMS
Cài đặt Wi-Fi Calling đôi khi có thể xung đột với chức năng MMS.
Nếu `check_wifi_calling_status()` hiển thị "Wi-Fi Calling is ON", hãy hướng dẫn người dùng sử dụng `toggle_wifi_calling()` để TẮT nó.

### Ứng dụng Messaging thiếu các Quyền cần thiết
Ứng dụng nhắn tin cần các quyền cụ thể để xử lý các tệp phương tiện và gửi tin nhắn.
Nếu `check_app_permissions(app_name="messaging")` hiển thị các quyền "storage" và "sms" không được cấp, hãy hướng dẫn người dùng sử dụng `grant_app_permission(app_name="messaging", permission="storage")` và `grant_app_permission(app_name="messaging", permission="sms")` để cấp các quyền cần thiết.