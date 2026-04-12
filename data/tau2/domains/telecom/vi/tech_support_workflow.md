# Điện thoại - Quy trình Khắc phục sự cố Hỗ trợ Kỹ thuật

## Giới thiệu

Tài liệu này cung cấp một quy trình có cấu trúc để chẩn đoán và giải quyết các vấn đề kỹ thuật trên điện thoại. Hãy làm theo các quy trình này dựa trên mô tả vấn đề của người dùng. Mỗi bước bao gồm hướng dẫn về hành động khắc phục sự cố cụ thể nào cần thực hiện dựa trên những gì cần kiểm tra hoặc sửa đổi.

Đảm bảo bạn đã thử tất cả các bước giải quyết liên quan trước khi chuyển người dùng đến nhân viên hỗ trợ con người.

## Tham khảo Hành động Người dùng có sẵn
Đây là các hành động mà người dùng có thể thực hiện trên thiết bị của họ.
Bạn phải hiểu rõ những điều này vì là một phần của hỗ trợ kỹ thuật, bạn sẽ phải giúp khách hàng thực hiện một loạt các hành động.

Nhân viên hỗ trợ nên hướng dẫn người dùng thực hiện các hành động cụ thể này khi cần trong quá trình khắc phục sự cố:


### Hành động Chẩn đoán (Chỉ đọc)
1. **Check Status Bar** - Hiển thị các biểu tượng hiện đang hiển thị trên thanh trạng thái của điện thoại (khu vực ở đầu màn hình). Hiển thị cường độ tín hiệu mạng, trạng thái dữ liệu di động (đã bật, đã tắt, tiết kiệm dữ liệu), trạng thái Wi-Fi và mức pin.
2. **Check Network Status** - Kiểm tra trạng thái kết nối của điện thoại với mạng di động và Wi-Fi. Hiển thị trạng thái chế độ máy bay, cường độ tín hiệu, loại mạng, liệu dữ liệu di động có được bật hay không và liệu chuyển vùng dữ liệu có được bật hay không. Cường độ tín hiệu có thể là "none", "poor" (1 vạch), "fair" (2 vạch), "good" (3 vạch), "excellent" (4+ vạch).
3. **Check Network Mode Preference** - Kiểm tra tùy chọn chế độ mạng của điện thoại. Hiển thị loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G, 2G).
4. **Check SIM Status** - Kiểm tra xem thẻ SIM có hoạt động tốt không và hiển thị trạng thái hiện tại. Hiển thị xem SIM có đang hoạt động, bị thiếu, hay bị khóa bằng mã PIN hoặc PUK.
5. **Check Data Restrictions** - Kiểm tra xem điện thoại có tính năng hạn chế dữ liệu nào đang hoạt động không. Hiển thị xem chế độ Tiết kiệm dữ liệu (Data Saver) có bật không và liệu sử dụng dữ liệu nền có bị hạn chế trên toàn cầu hay không.
6. **Check APN Settings** - Kiểm tra cài đặt APN kỹ thuật điện thoại sử dụng để kết nối với mạng dữ liệu di động của nhà mạng. Hiển thị tên APN hiện tại và URL MMSC cho tin nhắn hình ảnh.
7. **Check Wi-Fi Status** - Kiểm tra trạng thái kết nối Wi-Fi. Hiển thị xem Wi-Fi đã bật chưa, mạng nào đang kết nối (nếu có) và cường độ tín hiệu.
8. **Check Wi-Fi Calling Status** - Kiểm tra xem Wi-Fi Calling có được bật trên thiết bị không. Tính năng này cho phép thực hiện và nhận cuộc gọi qua mạng Wi-Fi thay vì sử dụng mạng di động.
9. **Check VPN Status** - Kiểm tra xem bạn có đang sử dụng kết nối VPN (Mạng riêng ảo) không. Hiển thị xem VPN đang hoạt động, có kết nối và hiển thị bất kỳ chi tiết kết nối nào.
10. **Check Installed Apps** - Trả về tên của tất cả các ứng dụng cài đặt trên điện thoại.
11. **Check App Status** - Kiểm tra thông tin chi tiết về một ứng dụng cụ thể. Hiển thị quyền và cài đặt sử dụng dữ liệu nền.
12. **Check App Permissions** - Kiểm tra quyền mà một ứng dụng cụ thể hiện có. Hiển thị liệu ứng dụng có quyền truy cập vào các tính năng như bộ nhớ, camera, vị trí, v.v.
13. **Run Speed Test** - Đo tốc độ kết nối internet hiện tại (tốc độ tải xuống). Cung cấp thông tin chất lượng kết nối và các hoạt động mà nó có thể hỗ trợ. Tốc độ tải xuống có thể là "unknown", "very poor", "poor", "fair", "good" hoặc "excellent".
14. **Can Send MMS** - Kiểm tra xem ứng dụng nhắn tin có thể gửi tin nhắn MMS không.

### Hành động Khắc phục (Ghi/Sửa đổi)
1. **Set Network Mode** - Thay đổi loại mạng di động điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G). Mạng tốc độ cao (5G, 4G) cung cấp dữ liệu nhanh hơn nhưng có thể tốn pin hơn.
2. **Toggle Airplane Mode** - Bật hoặc tắt Chế độ máy bay. Khi BẬT, ngắt kết nối tất cả liên lạc không dây bao gồm di động, Wi-Fi và Bluetooth.
3. **Reseat SIM Card** - Mô phỏng việc tháo và lắp lại thẻ SIM. Điều này có thể giải quyết vấn đề nhận dạng.
4. **Toggle Mobile Data** - Bật hoặc tắt kết nối dữ liệu di động. Kiểm soát liệu điện thoại có thể sử dụng dữ liệu di động để truy cập internet khi Wi-Fi không khả dụng hay không.
5. **Toggle Data Roaming** - Bật hoặc tắt Chuyển vùng dữ liệu. Khi BẬT, chuyển vùng được kích hoạt và điện thoại có thể sử dụng các mạng dữ liệu bên ngoài vùng phủ sóng của nhà mạng.
6. **Toggle Data Saver** - Bật hoặc tắt chế độ Tiết kiệm dữ liệu. Khi BẬT, nó làm giảm mức sử dụng dữ liệu, có thể ảnh hưởng đến tốc độ dữ liệu.
7. **Set APN Settings** - Thiết lập các cài đặt APN cho điện thoại.
8. **Reset APN Settings** - Đặt lại các cài đặt APN về cài đặt mặc định.
9. **Toggle Wi-Fi** - Bật hoặc tắt Wi-Fi. Kiểm soát liệu điện thoại có thể khám phá và kết nối với các mạng không dây để truy cập internet hay không.
10. **Toggle Wi-Fi Calling** - Bật hoặc tắt Wi-Fi Calling. Tính năng này cho phép thực hiện và nhận cuộc gọi qua Wi-Fi thay vì mạng di động, có thể hữu ích ở những khu vực tín hiệu di động yếu.
11. **Connect VPN** - Kết nối với VPN (Mạng riêng ảo).
12. **Disconnect VPN** - Ngắt kết nối bất kỳ kết nối VPN đang hoạt động nào. Dừng định tuyến lưu lượng internet qua máy chủ VPN, có thể ảnh hưởng đến tốc độ kết nối hoặc truy cập nội dung.
13. **Grant App Permission** - Cấp một quyền cụ thể cho ứng dụng (như quyền truy cập bộ nhớ, camera hoặc vị trí). Được yêu cầu để các chức năng ứng dụng hoạt động chính xác.
14. **Reboot Device** - Khởi động lại hoàn toàn điện thoại. Điều này có thể giải quyết các lỗi phần mềm tạm thời bằng cách làm mới tất cả dịch vụ và kết nối.

## Phân loại Vấn đề Ban đầu

Xác định hạng mục nào mô tả đúng nhất vấn đề của người dùng:

1. **Vấn đề Không có Dịch vụ/Kết nối**: Điện thoại hiển thị "Không có dịch vụ" hoặc không thể kết nối mạng
2. **Vấn đề Dữ liệu di động**: Không thể truy cập internet hoặc tốc độ dữ liệu chậm
3. **Các vấn đề Nhắn tin Hình ảnh/Nhóm (MMS)**: Không thể gửi hoặc nhận tin nhắn hình ảnh

Đối với nhiều vấn đề, hãy giải quyết kết nối cơ bản trước.

## Quy trình 1: Khắc phục sự cố Không có Dịch vụ / Không có Kết nối

### Bước 1.0: Kiểm tra xem người dùng có đang gặp sự cố không có dịch vụ hay không
Nếu dịch vụ khả dụng, thanh trạng thái sẽ không hiển thị 'không có tín hiệu' hoặc 'chế độ máy bay'.
- Yêu cầu người dùng kiểm tra thanh trạng thái của họ
- Nếu thanh trạng thái hiển thị dịch vụ khả dụng, người dùng không gặp sự cố không có dịch vụ.
- Nếu thanh trạng thái hiển thị dịch vụ không khả dụng, hãy chuyển sang Bước 1.1

### Bước 1.1: Kiểm tra Chế độ máy bay và Trạng thái mạng
Yêu cầu người dùng kiểm tra kết nối điện thoại với mạng di động và Wi-Fi. Điều này sẽ cho thấy Chế độ máy bay có bật không, cường độ tín hiệu và các chi tiết kết nối khác.

**Nếu Chế độ máy bay đang BẬT:**
- Yêu cầu người dùng TẮT Chế độ máy bay
- Yêu cầu người dùng nhìn vào thanh trạng thái và kiểm tra xem dịch vụ đã được khôi phục chưa

**Nếu Chế độ máy bay đang TẮT:**
- Chuyển sang Bước 1.2

### Bước 1.2: Xác minh Trạng thái Thẻ SIM
Yêu cầu người dùng kiểm tra xem thẻ SIM có hoạt động tốt không. Bạn cần biết liệu nó có bị thiếu, bị khóa hay đang hoạt động hay không.

**Nếu SIM hiển thị là BỊ THIẾU (MISSING):**
- Yêu cầu người dùng lắp lại thẻ SIM bằng cách tháo ra và lắp lại
- Kiểm tra xem thẻ SIM có đang HOẠT ĐỘNG không.
- Yêu cầu người dùng nhìn vào thanh trạng thái và kiểm tra xem dịch vụ đã được khôi phục chưa

**Nếu SIM BỊ KHÓA bằng PIN/PUK:**
- Chuyển cho hỗ trợ kỹ thuật để được trợ giúp về bảo mật SIM

**Nếu SIM đang HOẠT ĐỘNG và hoạt động tốt:**
- Chuyển sang Bước 1.3

### Bước 1.3: Cố gắng đặt lại cài đặt APN
Nếu sự cố kết nối cơ bản vẫn tiếp diễn:

- Yêu cầu người dùng đặt lại cài đặt APN về mặc định
- Yêu cầu họ khởi động lại thiết bị
- Yêu cầu người dùng nhìn vào thanh trạng thái và kiểm tra xem dịch vụ đã được khôi phục chưa

**Nếu vẫn không giải quyết được:**
- Chuyển sang Bước 1.4

### Bước 1.4: Kiểm tra Đình chỉ Số thuê bao (Line Suspension)

Không có dịch vụ có thể là do số thuê bao bị đình chỉ.

**Nếu số thuê bao bị đình chỉ:**
- Làm theo hướng dẫn trong chính sách chung để biết thêm thông tin về đình chỉ số thuê bao và cách bỏ đình chỉ.
- Nếu bạn có thể bỏ đình chỉ:
    - Yêu cầu người dùng nhìn vào thanh trạng thái và kiểm tra xem dịch vụ đã được khôi phục chưa.
- Nếu bạn không thể bỏ đình chỉ:
    - Chuyển cho hỗ trợ kỹ thuật.

**Nếu vẫn không giải quyết được:**
- Chuyển cho hỗ trợ kỹ thuật

## Quy trình 2: Khắc phục sự cố Dữ liệu di động không khả dụng hoặc Chậm

Lưu ý: Quy trình này không đề cập đến các vấn đề dữ liệu wifi.

### Bước 2.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu không

Khi dữ liệu di động không khả dụng, bài kiểm tra tốc độ sẽ trả về 'no connection'.
Nếu dữ liệu khả dụng, bài kiểm tra tốc độ cũng sẽ trả về tốc độ dữ liệu. Bất kỳ tốc độ nào dưới 'Excellent' đều được coi là chậm.
- Quy trình 2.1 kiểm tra các vấn đề dữ liệu di động không khả dụng.
- Quy trình 2.2 kiểm tra các vấn đề dữ liệu chậm.

## Quy trình 2.1: Khắc phục sự cố Dữ liệu di động không khả dụng

### Bước 2.1.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu di động không khả dụng hay không

- Yêu cầu người dùng chạy bài kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'no connection', dữ liệu di động không khả dụng.
    - Làm theo Quy trình 2.1.
    - Sau khi sự cố được giải quyết, nếu tốc độ không phải là 'Excellent', hãy làm theo Quy trình 2.2.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động khả dụng.
    - Nếu tốc độ là 'Excellent', người dùng không gặp vấn đề dữ liệu di động.
    - Đối với bất kỳ tốc độ nào khác ('Poor', 'Fair', 'Good'), dữ liệu di động có thể chậm và bạn phải làm theo Quy trình 2.2.

### Bước 2.1.1: Xác minh Sự cố Dịch vụ
Yêu cầu người dùng kiểm tra xem điện thoại của họ có dịch vụ di động không. Dữ liệu di động yêu cầu ít nhất một số kết nối mạng di động.

- Thực hiện các bước khắc phục sự cố Quy trình 1 (Không có Dịch vụ / Không có Kết nối) trước.
- Khi bạn đã xác nhận dịch vụ khả dụng, hãy kiểm tra xem sự cố dữ liệu di động có tiếp diễn không.
    - Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang Bước 2.1.2.

### Bước 2.1.2: Xác minh xem người dùng có đang đi du lịch không
Hỏi người dùng xem họ có đang ở ngoài khu vực dịch vụ thông thường của họ không.

**Nếu Người dùng không đi du lịch:**
- Chuyển sang Bước 2.1.3

**Nếu Người dùng đang đi du lịch:**
- Yêu cầu người dùng xác minh xem Chuyển vùng dữ liệu có được bật để cho phép sử dụng dữ liệu trên các mạng khác không.

**Nếu Chuyển vùng dữ liệu đang TẮT:**
- Yêu cầu người dùng BẬT Chuyển vùng dữ liệu
- Yêu cầu họ chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.

**Nếu Chuyển vùng dữ liệu đang BẬT nhưng không hoạt động:**
- Xác minh xem số thuê bao liên kết với số điện thoại người dùng cung cấp có được bật chuyển vùng không.
    - Nếu số thuê bao không được bật chuyển vùng, hãy bật miễn phí cho người dùng
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang Bước 2.1.3.

**Nếu Chuyển vùng dữ liệu đang BẬT và được kích hoạt nhưng kết nối không hoạt động:**
- Chuyển sang Bước 2.1.3

### Bước 2.1.3: Kiểm tra Cài đặt Dữ liệu di động
**Nếu Dữ liệu di động đang TẮT:**
- Yêu cầu người dùng BẬT Dữ liệu di động
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang Bước 2.1.4.

**Nếu Dữ liệu di động đang BẬT nhưng không hoạt động:**
- Chuyển sang Bước 2.1.4

### Bước 2.1.4: Kiểm tra Mức sử dụng dữ liệu
Kiểm tra xem, đối với số thuê bao liên kết với số điện thoại người dùng cung cấp, mức sử dụng dữ liệu của người dùng đã vượt quá giới hạn dữ liệu chưa.

**Nếu Mức sử dụng dữ liệu ĐÃ VƯỢT QUÁ:**
- Hỏi người dùng xem họ có muốn thay đổi gói cước khác hoặc nạp thêm dữ liệu không.
- Làm theo hướng dẫn trong chính sách chung để biết thêm thông tin về nạp thêm dữ liệu và thay đổi gói cước.
- Nếu bạn có thể nạp thêm dữ liệu hoặc thay đổi gói cước với giới hạn dữ liệu cao hơn:
    - Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển cho hỗ trợ kỹ thuật.
- Nếu bạn không thể nạp thêm dữ liệu hoặc thay đổi gói cước (không được phép hoặc người dùng không muốn):
    - Chuyển cho hỗ trợ kỹ thuật.

**Nếu Mức sử dụng dữ liệu CHƯA VƯỢT QUÁ:**
- Yêu cầu người dùng chạy bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển cho hỗ trợ kỹ thuật.

## Quy trình 2.2: Khắc phục sự cố Dữ liệu di động Chậm

### Bước 2.2.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu chậm không
Khi dữ liệu di động khả dụng nhưng tốc độ khác với 'Excellent', người dùng đang gặp sự cố dữ liệu chậm.
- Yêu cầu người dùng chạy bài kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'no connection', dữ liệu di động không khả dụng.
    - Làm theo Quy trình 2.1.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động khả dụng.
    - Nếu tốc độ là 'Excellent', người dùng không gặp vấn đề dữ liệu chậm.
    - Đối với bất kỳ tốc độ nào khác ('Poor', 'Fair', 'Good'), dữ liệu di động có thể chậm và bạn phải làm theo Quy trình 2.2.

### Bước 2.2.1: Kiểm tra Cài đặt Hạn chế dữ liệu
Yêu cầu người dùng kiểm tra xem có cài đặt nào hạn chế mức sử dụng dữ liệu của họ không, như chế độ Tiết kiệm dữ liệu.

**Nếu Tiết kiệm dữ liệu đang BẬT:**
- Yêu cầu người dùng TẮT chế độ Tiết kiệm dữ liệu
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên mức 'Excellent' không.
    - Nếu không, hãy chuyển sang Bước 6.
**Nếu Tiết kiệm dữ liệu đang TẮT:**
- Chuyển sang Bước 6

### Bước 2.2.2: Kiểm tra Tùy chọn Chế độ mạng
Yêu cầu người dùng kiểm tra xem điện thoại của họ ưu tiên loại mạng di động nào. Sử dụng các chế độ cũ như 2G/3G có thể hạn chế đáng kể tốc độ.

**Nếu được đặt thành các loại mạng cũ hơn (chỉ 2G/3G):**
- Yêu cầu người dùng thay đổi tùy chọn mạng thành tùy chọn bao gồm 5G
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên mức 'Excellent' không.
    - Nếu không, hãy chuyển sang Bước 7.

**Nếu đã ở cài đặt tối ưu:**
- Chuyển sang Bước 7

### Bước 2.2.3: Kiểm tra VPN Active
Yêu cầu người dùng kiểm tra xem họ có đang sử dụng VPN (Mạng riêng ảo) có thể ảnh hưởng đến chất lượng kết nối không.

**Nếu VPN đang hoạt động:**
- Yêu cầu người dùng TẮT kết nối VPN hiện tại
- Yêu cầu họ chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên mức 'Excellent' không.
    - Nếu không, hãy chuyển cho hỗ trợ kỹ thuật.

**Nếu không có VPN hoặc ngắt kết nối không giúp ích:**
- Chuyển cho hỗ trợ kỹ thuật.

## Quy trình 3: Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Nhóm)

### Bước 3.0: Kiểm tra xem người dùng có đang gặp sự cố MMS không
Khi MMS không hoạt động, người dùng sẽ không thể gửi hoặc nhận tin nhắn hình ảnh.

- Yêu cầu người dùng nếu họ có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định.
    - Nếu điều này hoạt động, người dùng không gặp sự cố MMS.
    - Nếu không, hãy chuyển sang Bước 3.1.

### Bước 3.1: Xác minh Trạng thái Dịch vụ mạng
Yêu cầu người dùng kiểm tra xem điện thoại của họ có dịch vụ di động không. MMS yêu cầu ít nhất một số kết nối mạng di động.

- Thực hiện các bước khắc phục sự cố Quy trình 1 (Không có Dịch vụ / Không có Kết nối) trước.
- Khi bạn đã xác nhận dịch vụ khả dụng, hãy kiểm tra xem sự cố có tiếp diễn không:
    - Yêu cầu người dùng nếu họ có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định.

**Nếu dịch vụ khả dụng:**
- Chuyển sang Bước 3.2

### Bước 3.2: Xác minh Trạng thái Dữ liệu di động
Dữ liệu di động được yêu cầu cho MMS.

- Sử dụng các bước khắc phục sự cố Quy trình 2.1 (Dữ liệu di động không khả dụng) để kiểm tra xem kết nối dữ liệu di động có hoạt động không. Không cần quan tâm đến tốc độ, hãy tập trung vào khả năng kết nối.
- Khi bạn đã xác nhận kết nối dữ liệu di động hoạt động, hãy kiểm tra xem sự cố MMS có tiếp diễn không:
    - Yêu cầu người dùng thử gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

### Bước 3.3: Kiểm tra Công nghệ mạng
Yêu cầu người dùng kiểm tra loại mạng di động điện thoại của họ đang kết nối. MMS yêu cầu ít nhất công nghệ 3G trở lên.

**Nếu chỉ kết nối với mạng 2G:**
- Yêu cầu người dùng thay đổi chế độ mạng để bao gồm ít nhất 3G/4G/5G
- Yêu cầu người dùng thử gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu trên mạng 3G trở lên:**
- Chuyển sang Bước 3.4


### Bước 3.4: Kiểm tra Trạng thái Wi-Fi Calling
Yêu cầu người dùng kiểm tra xem Wi-Fi Calling có được bật không, vì nó có thể cản trở chức năng MMS.

**Nếu Wi-Fi Calling đang BẬT:**
- Yêu cầu người dùng TẮT Wi-Fi Calling
- Yêu cầu người dùng thử gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu Wi-Fi Calling đang TẮT hoặc tắt nó đi không giúp ích gì:**
- Chuyển sang Bước 3.5

### Bước 3.5: Xác minh Quyền Ứng dụng Nhắn tin
Yêu cầu người dùng kiểm tra xem ứng dụng nhắn tin mặc định có các quyền cần thiết không - cụ thể là cả quyền bộ nhớ và SMS.

**Nếu thiếu quyền bộ nhớ hoặc SMS:**
- Yêu cầu người dùng cấp cả hai quyền cần thiết cho ứng dụng nhắn tin
- Yêu cầu người dùng thử gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu tất cả các quyền đã được cấp:**
- Chuyển sang Bước 3.6

### Bước 3.6: Kiểm tra cài đặt APN
Yêu cầu người dùng kiểm tra các cài đặt kỹ thuật (APN) điện thoại của họ sử dụng để kết nối với mạng dữ liệu di động của nhà mạng.

**Đặc biệt kiểm tra:**
- Cấu hình URL MMSC (phải có mặt để MMS hoạt động)

**Nếu thiếu URL MMSC:**
- Yêu cầu người dùng đặt lại cài đặt APN về mặc định của nhà mạng
- Yêu cầu người dùng thử gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu sự cố vẫn tồn tại sau khi kiểm tra tất cả các điều trên:**
- Chuyển cho hỗ trợ kỹ thuật