# Giới thiệu
Tài liệu này đóng vai trò là hướng dẫn toàn diện cho các đại lý hỗ trợ kỹ thuật. Nó cung cấp các quy trình chi tiết và các bước khắc phục sự cố để hỗ trợ người dùng gặp các vấn đề thường gặp với dịch vụ di động, kết nối dữ liệu di động và Dịch vụ Nhắn tin Đa phương tiện (MMS) trên điện thoại của họ. Hướng dẫn này được cấu trúc để giúp các đại lý chẩn đoán và giải quyết vấn đề hiệu quả bằng cách phác thảo cách các dịch vụ này hoạt động, các vấn đề phổ biến và các công cụ sẵn có để giải quyết.

Các phần chính được đề cập là:
*   **Hiểu và khắc phục sự cố dịch vụ di động trên điện thoại của bạn**: Giải quyết các vấn đề liên quan đến kết nối mạng, cường độ tín hiệu và các vấn đề về thẻ SIM.
*   **Hiểu và khắc phục sự cố dữ liệu di động trên điện thoại của bạn**: Tập trung vào các vấn đề truy cập internet qua mạng di động, bao gồm tốc độ và khả năng kết nối.
*   **Hiểu và khắc phục sự cố MMS (Nhắn tin Hình ảnh/Video)**: Đề cập đến các vấn đề liên quan đến việc gửi và nhận tin nhắn đa phương tiện.

Hãy chắc chắn rằng bạn đã thử mọi cách có thể để giải quyết vấn đề của người dùng trước khi chuyển cho nhân viên hỗ trợ.

# Những gì người dùng có thể làm trên thiết bị của họ
Dưới đây là các hành động mà người dùng có thể thực hiện trên thiết bị của họ.
Bạn phải hiểu rõ những hành động này vì là một phần của hỗ trợ kỹ thuật, bạn sẽ phải giúp khách hàng thực hiện một loạt hành động.

## Hành động chẩn đoán (Chỉ đọc)
1. **check_status_bar** - Hiển thị các biểu tượng hiện đang hiển thị trên thanh trạng thái của điện thoại (khu vực ở trên cùng của màn hình).
   - Trạng thái chế độ máy bay ("✈️ Chế độ máy bay" khi được bật)
   - Cường độ tín hiệu mạng ("📵 Không có tín hiệu", "📶¹ Yếu", "📶² Trung bình", "📶³ Tốt", "📶⁴ Xuất sắc")
   - Công nghệ mạng (ví dụ: "5G", "4G", v.v.)
   - Trạng thái dữ liệu di động ("📱 Dữ liệu đã bật" hoặc "📵 Dữ liệu đã tắt")
   - Trạng thái trình tiết kiệm dữ liệu ("🔽 Trình tiết kiệm dữ liệu" khi được bật)
   - Trạng thái Wi-Fi ("📡 Đã kết nối tới [SSID]" hoặc "📡 Đã bật")
   - Trạng thái VPN ("🔒 VPN đã kết nối" khi đã kết nối)
   - Mức pin ("🔋 [tỷ lệ phần trăm]%")
2. **check_network_status** - Kiểm tra trạng thái kết nối của điện thoại với mạng di động và Wi-Fi. Hiển thị trạng thái chế độ máy bay, cường độ tín hiệu, loại mạng, liệu dữ liệu di động có được bật hay không và liệu chuyển vùng dữ liệu có được bật hay không. Cường độ tín hiệu có thể là "không", "yếu" (1 vạch), "trung bình" (2 vạch), "tốt" (3 vạch), "xuất sắc" (4 vạch trở lên).
3. **check_network_mode_preference** - Kiểm tra ưu tiên chế độ mạng của điện thoại. Hiển thị loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G, 2G).
4. **check_sim_status** - Kiểm tra xem thẻ SIM có hoạt động chính xác hay không và hiển thị trạng thái hiện tại của nó. Hiển thị xem SIM có đang ở trạng thái đang hoạt động, bị mất, hay bị khóa bằng mã PIN hoặc PUK.
5. **check_data_restriction_status** - Kiểm tra xem điện thoại có bất kỳ tính năng giới hạn dữ liệu nào hay không đang hoạt động. Hiển thị xem chế độ Trình tiết kiệm dữ liệu có bật hay không và liệu việc sử dụng dữ liệu nền có bị hạn chế trên toàn cầu hay không.
6. **check_apn_settings** - Kiểm tra các cài đặt APN kỹ thuật mà điện thoại sử dụng để kết nối với mạng dữ liệu di động của nhà mạng. Hiển thị tên APN hiện tại và URL MMSC cho nhắn tin hình ảnh.
7. **check_wifi_status** - Kiểm tra trạng thái kết nối Wi-Fi. Hiển thị xem Wi-Fi có được bật hay không, bạn đang đã kết nối vào mạng nào (nếu có) và cường độ tín hiệu.
8. **check_wifi_calling_status** - Kiểm tra xem Gọi Wi-Fi có được bật trên thiết bị hay không. Tính năng này cho phép bạn thực hiện và nhận cuộc gọi qua mạng Wi-Fi thay vì sử dụng mạng di động.
9. **check_vpn_status** - Kiểm tra xem bạn có đang sử dụng kết nối VPN (Mạng riêng ảo) hay không. Hiển thị xem VPN đang ở trạng thái đang hoạt động, đã kết nối hay không, và hiển thị bất kỳ chi tiết kết nối khả dụng nào.
10. **check_installed_apps** - Trả về tên của tất cả các ứng dụng đã cài đặt trên điện thoại.
11. **check_app_status** - Kiểm tra thông tin chi tiết về một ứng dụng cụ thể. Hiển thị các quyền và cài đặt sử dụng dữ liệu nền của ứng dụng đó.
12. **check_app_permissions** - Kiểm tra các quyền hiện có của một ứng dụng cụ thể. Hiển thị xem ứng dụng có quyền truy cập vào các tính năng như bộ nhớ, máy ảnh, vị trí, v.v. hay không.
13. **run_speed_test** - Đo tốc độ kết nối internet hiện tại của bạn (tốc độ tải xuống). Cung cấp thông tin về chất lượng kết nối và các hoạt động mà nó có thể hỗ trợ. Tốc độ tải xuống có thể là "không xác định", "rất yếu", "yếu", "trung bình", "tốt", hoặc "xuất sắc".
14. **can_send_mms** - Kiểm tra xem ứng dụng nhắn tin có thể gửi tin nhắn MMS hay không.

## Hành động khắc phục (Ghi/Sửa đổi)
1. **set_network_mode_preference** - Thay đổi loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G). Các mạng tốc độ cao hơn (5G, 4G) cung cấp dữ liệu nhanh hơn nhưng có thể tiêu tốn nhiều pin hơn.
2. **toggle_airplane_mode** - Bật hoặc Tắt Chế độ Máy bay. Khi BẬT, nó ngắt kết nối tất cả các liên lạc không dây bao gồm di động, Wi-Fi và Bluetooth.
3. **reseat_sim_card** - Mô phỏng việc tháo và lắp lại thẻ SIM. Điều này có thể giúp giải quyết các vấn đề nhận dạng.
4. **toggle_data** - Bật hoặc Tắt kết nối dữ liệu di động của điện thoại. Kiểm soát liệu điện thoại có thể sử dụng dữ liệu di động để truy cập internet khi không có Wi-Fi hay không.
5. **toggle_roaming** - Bật hoặc Tắt Chuyển vùng dữ liệu. Khi BẬT, chuyển vùng được kích hoạt và điện thoại của bạn có thể sử dụng các mạng dữ liệu ở những khu vực bên ngoài vùng phủ sóng của nhà mạng.
6. **toggle_data_saver_mode** - Bật hoặc Tắt chế độ Trình tiết kiệm dữ liệu. Khi BẬT, nó làm giảm mức sử dụng dữ liệu, điều này có thể ảnh hưởng đến tốc độ dữ liệu.
7. **set_apn_settings** - Thiết lập các cài đặt APN cho điện thoại.
8. **reset_apn_settings** - Đặt lại cài đặt APN của bạn về cài đặt mặc định.
9. **toggle_wifi** - Bật hoặc Tắt radio Wi-Fi của điện thoại. Kiểm soát liệu điện thoại có thể khám phá và kết nối với các mạng không dây để truy cập internet hay không.
10. **toggle_wifi_calling** - Bật hoặc Tắt Gọi Wi-Fi. Tính năng này cho phép bạn thực hiện và nhận cuộc gọi qua Wi-Fi thay vì mạng di động, điều này có thể hữu ích ở những khu vực có tín hiệu di động yếu.
11. **connect_vpn** - Kết nối với VPN (Mạng riêng ảo) của bạn.
12. **disconnect_vpn** - Ngắt kết nối bất kỳ kết nối VPN (Mạng riêng ảo) đang hoạt động nào. Ngừng định tuyến lưu lượng truy cập internet của bạn thông qua máy chủ VPN, điều này có thể ảnh hưởng đến tốc độ kết nối hoặc quyền truy cập nội dung.
13. **grant_app_permission** - Cấp một quyền cụ thể cho ứng dụng (như quyền truy cập bộ nhớ, máy ảnh hoặc vị trí). Cần thiết để một số chức năng của ứng dụng hoạt động chính xác.
14. **reboot_device** - Khởi động lại hoàn toàn điện thoại. Điều này có thể giúp giải quyết nhiều lỗi phần mềm tạm thời bằng cách làm mới tất cả các dịch vụ và kết nối đang chạy.

# Hiểu và khắc phục sự cố dịch vụ di động trên điện thoại của bạn
Phần này chi tiết cho các đại lý biết cách điện thoại của người dùng kết nối với mạng di động (thường được gọi là "dịch vụ") và cung cấp các quy trình để khắc phục các sự cố thường gặp. Dịch vụ di động tốt là yêu cầu bắt buộc cho cuộc gọi, tin nhắn văn bản và dữ liệu di động.

## Các sự cố dịch vụ thường gặp và nguyên nhân
Nếu người dùng gặp vấn đề về dịch vụ, đây là một số nguyên nhân phổ biến:

*   **Chế độ máy bay đang BẬT**: Điều này vô hiệu hóa tất cả các radio không dây, bao gồm cả di động.
*   **Vấn đề về thẻ SIM**:
    *   Không được lắp hoặc lắp không đúng cách.
    *   Bị khóa do nhập sai mã PIN/PUK.
*   **Cài đặt mạng không chính xác**: Cài đặt APN có thể không chính xác dẫn đến mất dịch vụ.
*   **Vấn đề từ nhà mạng**: Đường truyền của bạn có thể không hoạt động do các vấn đề thanh toán.


## Chẩn đoán sự cố dịch vụ
`check_status_bar()` có thể được sử dụng để kiểm tra xem người dùng có đang gặp sự cố dịch vụ hay không.
Nếu có dịch vụ di động, thanh trạng thái sẽ trả về chỉ báo cường độ tín hiệu.

## Khắc phục sự cố dịch vụ
### Chế độ máy bay
Chế độ máy bay là một tính năng vô hiệu hóa tất cả các radio không dây, bao gồm cả di động. Nếu nó được bật, nó sẽ ngăn chặn bất kỳ kết nối di động nào.
Bạn có thể kiểm tra xem Chế độ máy bay có đang BẬT bằng cách sử dụng `check_status_bar()` hoặc `check_network_status()`.
Nếu nó đang BẬT, hãy hướng dẫn người dùng sử dụng `toggle_airplane_mode()` để TẮT nó.

### Vấn đề về thẻ SIM
Thẻ SIM là thẻ vật lý chứa thông tin của người dùng và cho phép điện thoại kết nối với mạng di động.
Các vấn đề với thẻ SIM có thể dẫn đến mất hoàn toàn dịch vụ.
Sự cố phổ biến nhất là thẻ SIM không được lắp đúng cách hoặc người dùng đã nhập sai mã PIN hoặc PUK.
Sử dụng `check_sim_status()` để kiểm tra trạng thái của thẻ SIM.
Nếu nó hiển thị "Bị mất", hãy hướng dẫn người dùng sử dụng `reseat_sim_card()` để đảm bảo thẻ SIM đã được lắp đúng cách.
Nếu nó hiển thị "Đã khóa" (do nhập sai mã PIN hoặc PUK), **hãy chuyển cấp cho hỗ trợ kỹ thuật để được hỗ trợ về bảo mật SIM**.
Nếu nó hiển thị "Đang hoạt động", bản thân thẻ SIM có khả năng là vẫn ổn.

### Cài đặt APN không chính xác
Cài đặt Tên điểm truy cập (APN) rất quan trọng đối với kết nối mạng.
Nếu `check_apn_settings()` hiển thị "Không chính xác", hãy hướng dẫn người dùng sử dụng `reset_apn_settings()` để đặt lại cài đặt APN.
Sau khi đặt lại cài đặt APN, người dùng phải được hướng dẫn sử dụng `reboot_device()` để các thay đổi có hiệu lực.

### Tạm ngưng đường truyền
Nếu đường truyền bị tạm ngưng, người dùng sẽ không có dịch vụ di động.
Điều tra xem đường truyền có bị tạm ngưng hay không. Tham khảo chính sách chung của đại lý để biết hướng dẫn về việc xử lý tạm ngưng đường truyền.
*   Nếu đường truyền bị tạm ngưng và đại lý có thể dỡ bỏ tạm ngưng (theo chính sách chung), hãy xác minh xem dịch vụ đã được khôi phục chưa.
*   Nếu việc tạm ngưng không thể được dỡ bỏ bởi đại lý (ví dụ: do ngày kết thúc hợp đồng như đã đề cập trong chính sách chung, hoặc vì các lý do khác mà đại lý không thể giải quyết), **hãy chuyển cấp cho hỗ trợ kỹ thuật**.


# Hiểu và khắc phục sự cố dữ liệu di động trên điện thoại của bạn
Phần này giải thích cho các đại lý cách điện thoại của người dùng sử dụng dữ liệu di động để truy cập internet khi không có Wi-Fi và chi tiết việc khắc phục sự cố cho các vấn đề thường gặp về kết nối và tốc độ.

## Dữ liệu di động là gì?
Dữ liệu di động cho phép điện thoại kết nối với internet bằng mạng di động của nhà mạng. Điều này cho phép duyệt web, sử dụng ứng dụng, truyền phát video và gửi/nhận email khi không đã kết nối vào Wi-Fi. Thanh trạng thái thường hiển thị các biểu tượng như "5G", "LTE", "4G", "3G", "H+" hoặc "E" để cho biết kết nối dữ liệu di động đang hoạt động và loại kết nối đó.

## Điều kiện tiên quyết cho dữ liệu di động
Để dữ liệu di động hoạt động, trước tiên người dùng phải có **dịch vụ di động**. Tham khảo hướng dẫn "Hiểu và khắc phục sự cố dịch vụ di động trên điện thoại của bạn" nếu người dùng không có dịch vụ.

## Các vấn đề thường gặp và nguyên nhân gây ra sự cố dữ liệu di động
Ngay cả khi có dịch vụ di động, các vấn đề về dữ liệu di động vẫn có thể xảy ra. Các nguyên nhân phổ biến bao gồm:

*   **Chế độ máy bay đang BẬT**: Vô hiệu hóa tất cả các kết nối không dây, bao gồm cả dữ liệu di động.
*   **Dữ liệu di động đã TẮT**: Công tắc chính cho dữ liệu di động có thể đã bị tắt trong cài đặt của điện thoại.
*   **Sự cố chuyển vùng (Khi người dùng ở nước ngoài)**:
    *   Chuyển vùng dữ liệu đã TẮT trên điện thoại.
    *   Đường truyền chưa được bật chuyển vùng.
    *   Nếu `check_network_status()` hiển thị Chuyển vùng dữ liệu đang TẮT trong khi người dùng ở nước ngoài, hãy yêu cầu người dùng BẬT Chuyển vùng dữ liệu trước khi chuyển sang bất kỳ chẩn đoán khác nào.
*   **Đã đạt giới hạn gói dữ liệu**: Người dùng có thể đã sử dụng hết hạn mức dữ liệu hàng tháng của họ và nhà mạng đã làm chậm hoặc cắt dữ liệu.
*   **Chế độ Trình tiết kiệm dữ liệu đang BẬT**: Tính năng này hạn chế mức sử dụng dữ liệu nền và có thể làm cho một số ứng dụng hoặc dịch vụ có vẻ chậm hoặc không phản hồi để tiết kiệm dữ liệu.
*   **Sự cố VPN**: Kết nối VPN đang hoạt động có thể bị chậm hoặc cấu hình sai, ảnh hưởng đến tốc độ dữ liệu hoặc khả năng kết nối.
*   **Ưu tiên mạng xấu**: điện thoại được đặt thành công nghệ mạng cũ hơn như 2G/3G.

## Chẩn đoán sự cố dữ liệu di động
`run_speed_test()` có thể được sử dụng để kiểm tra các sự cố tiềm ẩn với dữ liệu di động.
Khi dữ liệu di động không khả dụng, một bài kiểm tra tốc độ sẽ trả về 'không có kết nối'.
Nếu dữ liệu khả dụng, một bài kiểm tra tốc độ cũng sẽ trả về tốc độ dữ liệu.
Bất kỳ tốc độ nào dưới 'Xuất sắc' đều được coi là chậm.

## Khắc phục sự cố dữ liệu di động
### Chế độ máy bay
Tham khảo phần "Hiểu và khắc phục sự cố dịch vụ di động trên điện thoại của bạn" để biết hướng dẫn về cách kiểm tra và tắt Chế độ máy bay.

### Dữ liệu di động đã tắt
Công tắc dữ liệu di động cho phép điện thoại kết nối với internet bằng mạng di động của nhà mạng.
Nếu `check_network_status()` hiển thị dữ liệu di động đã tắt, hãy hướng dẫn người dùng sử dụng `toggle_data()` để bật dữ liệu di động.

### Giải quyết các vấn đề chuyển vùng dữ liệu
Chuyển vùng dữ liệu cho phép người dùng sử dụng kết nối dữ liệu của điện thoại ở những khu vực bên ngoài mạng gia đình của họ (ví dụ: khi đi du lịch nước ngoài).
Nếu người dùng ở bên ngoài vùng phủ sóng chính của nhà mạng (chuyển vùng) và dữ liệu di động không hoạt động, hãy hướng dẫn họ sử dụng `toggle_roaming()` để đảm bảo Chuyển vùng dữ liệu đang BẬT.
Trước tiên, bạn phải xác định chính xác đường truyền khớp với số điện thoại mà người dùng đã cung cấp. Nếu khách hàng có nhiều đường truyền, đừng đoán hoặc sử dụng đường truyền đầu tiên; hãy kiểm tra chi tiết đường truyền và chọn đường truyền có số điện thoại khớp với số của người dùng.
Sau đó, xác minh xem đường truyền này đã được bật chuyển vùng hay chưa. Nếu chưa, người dùng sẽ không thể sử dụng kết nối dữ liệu của điện thoại ở những khu vực bên ngoài mạng gia đình của họ.
Tham khảo chính sách chung để biết hướng dẫn về việc bật chuyển vùng.

### Chế độ Trình tiết kiệm dữ liệu
Chế độ trình tiết kiệm dữ liệu là một tính năng hạn chế mức sử dụng dữ liệu nền và có thể ảnh hưởng đến tốc độ dữ liệu.
Nếu `check_data_restriction_status()` hiển thị "Chế độ trình tiết kiệm dữ liệu đang BẬT", hãy hướng dẫn người dùng sử dụng `toggle_data_saver_mode()` để TẮT nó.

### Sự cố kết nối VPN
VPN (Mạng riêng ảo) là một tính năng mã hóa lưu lượng truy cập internet và có thể giúp cải thiện tốc độ dữ liệu và bảo mật.
Tuy nhiên, trong một số trường hợp, VPN có thể làm tốc độ giảm đáng kể.
Nếu `check_vpn_status()` hiển thị "VPN đang BẬT và đã kết nối" và mức hiệu suất là "Yếu", hãy hướng dẫn người dùng sử dụng `disconnect_vpn()` để ngắt kết nối VPN.

### Đã đạt giới hạn gói dữ liệu
Mỗi gói cước chỉ định mức sử dụng dữ liệu tối đa mỗi tháng.
Nếu mức sử dụng dữ liệu của người dùng cho một đường truyền liên kết với số điện thoại mà người dùng đã cung cấp vượt quá giới hạn dữ liệu của gói cước, kết nối dữ liệu sẽ bị mất.
Người dùng có 2 tùy chọn:
- Thay đổi sang gói cước có nhiều dữ liệu hơn.
- Thêm nhiều dữ liệu hơn vào đường truyền bằng cách "nạp thêm" dữ liệu với giá mỗi GB được chỉ định bởi gói cước.
Tham khảo chính sách chung để biết hướng dẫn về các tùy chọn đó.

### Tối ưu hóa ưu tiên chế độ mạng
Ưu tiên chế độ mạng là các cài đặt xác định loại mạng di động mà điện thoại sẽ kết nối.
Sử dụng các chế độ cũ hơn như 2G/3G có thể làm hạn chế đáng kể tốc độ.
Nếu `check_network_mode_preference()` hiển thị "2G" hoặc "3G", hãy hướng dẫn người dùng sử dụng `set_network_mode_preference(mode: str)` với chế độ `"4g_5g_preferred"` để cho phép điện thoại kết nối với 5G.

# Hiểu và khắc phục sự cố MMS (Nhắn tin Hình ảnh/Video)
Phần này giải thích cho các đại lý cách khắc phục sự cố Dịch vụ Nhắn tin Đa phương tiện (MMS), cho phép người dùng gửi và nhận tin nhắn chứa hình ảnh, video hoặc âm thanh.

## MMS là gì?
MMS là một phần mở rộng của SMS (nhắn tin văn bản) cho phép nội dung đa phương tiện. Khi người dùng gửi ảnh cho bạn bè qua ứng dụng nhắn tin của họ, họ thường đang sử dụng MMS.

## Điều kiện tiên quyết cho MMS
Để MMS hoạt động, người dùng phải có dịch vụ di động và dữ liệu di động (bất kỳ tốc độ nào).
Tham khảo các phần "Hiểu và khắc phục sự cố dịch vụ di động trên điện thoại của bạn" và "Hiểu và khắc phục sự cố dữ liệu di động trên điện thoại của bạn" để biết thêm thông tin.

## Các vấn đề thường gặp và nguyên nhân gây ra sự cố MMS
*   **Không có dịch vụ di động hoặc Dữ liệu di động đã tắt/không hoạt động**: Các lý do phổ biến nhất. MMS phụ thuộc vào những thứ này.
*   **Cài đặt APN không chính xác**: Cụ thể là một bị mất hoặc URL MMSC không chính xác.
*   **Đang kết nối với mạng 2G**: Mạng 2G thường không phù hợp cho MMS.
*   **Cấu hình gọi Wi-Fi**: Trong một số trường hợp, cách cấu hình Gọi Wi-Fi có thể ảnh hưởng đến MMS, đặc biệt nếu nhà mạng của bạn không hỗ trợ MMS qua Wi-Fi.
*   **Quyền ứng dụng**: Ứng dụng nhắn tin cần quyền truy cập vào bộ nhớ (cho các tệp đa phương tiện) và thường là các chức năng SMS.

## Chẩn đoán sự cố MMS
Công cụ `can_send_mms()` trên điện thoại của người dùng có thể được sử dụng để kiểm tra xem người dùng có đang gặp sự cố MMS hay không.

## Khắc phục sự cố MMS
### Đảm bảo kết nối cơ bản cho MMS
Nhắn tin MMS thành công dựa trên dịch vụ cơ bản và kết nối dữ liệu. Phần này bao gồm việc xác minh các điều kiện tiên quyết này.
Trước tiên, hãy đảm bảo người dùng có thể thực hiện cuộc gọi và dữ liệu di động của họ đang hoạt động cho các ứng dụng khác (ví dụ: duyệt web). Tham khảo các phần "Hiểu và khắc phục sự cố dịch vụ di động trên điện thoại của bạn" và "Hiểu và khắc phục sự cố dữ liệu di động trên điện thoại của bạn" nếu cần.

### Công nghệ mạng không phù hợp cho MMS
MMS có các yêu cầu mạng cụ thể; các công nghệ cũ hơn như 2G là không đủ. Phần này giải thích cách kiểm tra loại mạng và thay đổi nếu cần.
MMS yêu cầu ít nhất một kết nối mạng 3G; mạng 2G thường không phù hợp.
Nếu `check_network_status()` hiển thị "2G", hãy hướng dẫn người dùng sử dụng `set_network_mode_preference(mode: str)` để chuyển sang chế độ mạng bao gồm 3G, 4G hoặc 5G (ví dụ: `"4g_5g_preferred"` hoặc `"4g_only"`).

### Xác minh APN (URL MMSC) cho MMS
MMSC là Trung tâm Dịch vụ Nhắn tin Đa phương tiện. Đây là máy chủ xử lý các tin nhắn MMS. Không có URL MMSC chính xác, người dùng sẽ không thể gửi hoặc nhận tin nhắn MMS.
Những cài đặt đó được chỉ định là một phần của cài đặt APN. URL MMSC không chính xác là nguyên nhân rất phổ biến gây ra các sự cố MMS.
Nếu `check_apn_settings()` hiển thị URL MMSC chưa được đặt, hãy hướng dẫn người dùng sử dụng `reset_apn_settings()` để đặt lại cài đặt APN.
Sau khi đặt lại cài đặt APN, người dùng phải được hướng dẫn sử dụng `reboot_device()` để các thay đổi có hiệu lực.

### Điều tra nhiễu Gọi Wi-Fi với MMS
Cài đặt Gọi Wi-Fi đôi khi có thể xung đột với chức năng MMS.
Nếu `check_wifi_calling_status()` hiển thị "Gọi Wi-Fi đang BẬT", hãy hướng dẫn người dùng sử dụng `toggle_wifi_calling()` để TẮT nó.

### Ứng dụng nhắn tin thiếu các quyền cần thiết
Ứng dụng nhắn tin cần các quyền cụ thể để xử lý phương tiện và gửi tin nhắn.
Nếu `check_app_permissions(app_name="messaging")` hiển thị quyền "bộ nhớ" và "sms" không được liệt kê là đã cấp, hãy hướng dẫn người dùng sử dụng `grant_app_permission(app_name="messaging", permission="storage")` và `grant_app_permission(app_name="messaging", permission="sms")` để cấp các quyền cần thiết.
