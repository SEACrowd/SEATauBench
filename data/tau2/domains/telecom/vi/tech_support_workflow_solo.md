# Thiết bị điện thoại - Quy trình khắc phục sự cố hỗ trợ kỹ thuật

## Giới thiệu

Tài liệu này cung cấp một quy trình có cấu trúc để chẩn đoán và giải quyết các vấn đề kỹ thuật điện thoại. Với tư cách là đại lý, bạn có quyền truy cập trực tiếp vào thiết bị của người dùng và có thể tự thực hiện các hành động này. Thực hiện theo các lộ trình này dựa trên mô tả vấn đề của người dùng. Mỗi bước bao gồm các hành động cụ thể bạn nên thực hiện để kiểm tra hoặc sửa đổi cài đặt.

Hãy chắc chắn rằng bạn đã thử tất cả các bước giải quyết liên quan trước khi chuyển người dùng cho nhân viên hỗ trợ.

## Tài liệu tham khảo về hành động khả dụng
Vì bạn có quyền truy cập vào thiết bị của người dùng, bạn có thể thực hiện trực tiếp các hành động sau:

### Hành động chẩn đoán (Chỉ đọc)
1. **Kiểm tra Thanh trạng thái** - Hiển thị các biểu tượng hiện đang hiển thị trên thanh trạng thái của điện thoại (khu vực ở trên cùng của màn hình). Hiển thị cường độ tín hiệu mạng, trạng thái dữ liệu di động (đã bật, đã tắt, trình tiết kiệm dữ liệu), trạng thái Wi-Fi và mức pin.
2. **Kiểm tra Trạng thái mạng** - Kiểm tra trạng thái kết nối của điện thoại với mạng di động và Wi-Fi. Hiển thị trạng thái chế độ máy bay, cường độ tín hiệu, loại mạng, liệu dữ liệu di động có được bật hay không và liệu chuyển vùng dữ liệu có được bật hay không. Cường độ tín hiệu có thể là "không", "yếu" (1 vạch), "trung bình" (2 vạch), "tốt" (3 vạch), "xuất sắc" (4 vạch trở lên).
3. **Kiểm tra Ưu tiên chế độ mạng** - Kiểm tra ưu tiên chế độ mạng của điện thoại. Hiển thị loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G, 2G).
4. **Kiểm tra Trạng thái SIM** - Kiểm tra xem thẻ SIM có hoạt động chính xác hay không và hiển thị trạng thái hiện tại của nó. Hiển thị xem SIM có đang ở trạng thái đang hoạt động, bị mất, hay bị khóa bằng mã PIN hoặc PUK.
5. **Kiểm tra Giới hạn dữ liệu** - Kiểm tra xem điện thoại có bất kỳ tính năng giới hạn dữ liệu nào hay không đang hoạt động. Hiển thị xem chế độ Trình tiết kiệm dữ liệu có bật hay không và liệu việc sử dụng dữ liệu nền có bị hạn chế trên toàn cầu hay không.
6. **Kiểm tra Cài đặt APN** - Kiểm tra các cài đặt APN kỹ thuật mà điện thoại sử dụng để kết nối với mạng dữ liệu di động của nhà mạng. Hiển thị tên APN hiện tại và URL MMSC cho nhắn tin hình ảnh.
7. **Kiểm tra Trạng thái Wi-Fi** - Kiểm tra trạng thái kết nối Wi-Fi. Hiển thị xem Wi-Fi có được bật hay không, nó đang đã kết nối vào mạng nào (nếu có) và cường độ tín hiệu.
8. **Kiểm tra Trạng thái Gọi Wi-Fi** - Kiểm tra xem Gọi Wi-Fi có được bật trên thiết bị hay không. Tính năng này cho phép thực hiện và nhận cuộc gọi qua mạng Wi-Fi thay vì sử dụng mạng di động.
9. **Kiểm tra Trạng thái VPN** - Kiểm tra xem kết nối VPN (Mạng riêng ảo) có đang ở trạng thái đang hoạt động hay không. Hiển thị xem VPN đang ở trạng thái đang hoạt động, đã kết nối hay không, và hiển thị bất kỳ chi tiết kết nối khả dụng nào.
10. **Kiểm tra Ứng dụng đã cài đặt** - Trả về tên của tất cả các ứng dụng đã cài đặt trên điện thoại.
11. **Kiểm tra Trạng thái ứng dụng** - Kiểm tra thông tin chi tiết về một ứng dụng cụ thể. Hiển thị các quyền và cài đặt sử dụng dữ liệu nền của ứng dụng đó.
12. **Kiểm tra Quyền ứng dụng** - Kiểm tra các quyền hiện có của một ứng dụng cụ thể. Hiển thị xem ứng dụng có quyền truy cập vào các tính năng như bộ nhớ, máy ảnh, vị trí, v.v. hay không.
13. **Chạy kiểm tra tốc độ** - Đo tốc độ kết nối internet hiện tại (tốc độ tải xuống). Cung cấp thông tin về chất lượng kết nối và các hoạt động mà nó có thể hỗ trợ. Tốc độ tải xuống có thể là "không xác định", "rất yếu", "yếu", "trung bình", "tốt", hoặc "xuất sắc".
14. **Có thể gửi MMS** - Kiểm tra xem ứng dụng nhắn tin có thể gửi tin nhắn MMS hay không.

### Hành động khắc phục (Ghi/Sửa đổi)
1. **Đặt Chế độ mạng** - Thay đổi loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G). Các mạng tốc độ cao hơn (5G, 4G) cung cấp dữ liệu nhanh hơn nhưng có thể tiêu tốn nhiều pin hơn.
2. **Bật/Tắt Chế độ máy bay** - Bật hoặc Tắt Chế độ máy bay. Khi BẬT, nó ngắt kết nối tất cả các liên lạc không dây bao gồm di động, Wi-Fi và Bluetooth.
3. **Tháo/Lắp lại thẻ SIM** - Mô phỏng việc tháo và lắp lại thẻ SIM. Điều này có thể giúp giải quyết các vấn đề nhận dạng.
4. **Bật/Tắt Dữ liệu di động** - Bật hoặc Tắt kết nối dữ liệu di động của điện thoại. Kiểm soát liệu điện thoại có thể sử dụng dữ liệu di động để truy cập internet khi không có Wi-Fi hay không.
5. **Bật/Tắt Chuyển vùng dữ liệu** - Bật hoặc Tắt Chuyển vùng dữ liệu. Khi BẬT, chuyển vùng được kích hoạt và điện thoại có thể sử dụng các mạng dữ liệu ở những khu vực bên ngoài vùng phủ sóng của nhà mạng.
6. **Bật/Tắt Trình tiết kiệm dữ liệu** - Bật hoặc Tắt chế độ Trình tiết kiệm dữ liệu. Khi BẬT, nó làm giảm mức sử dụng dữ liệu, điều này có thể ảnh hưởng đến tốc độ dữ liệu.
7. **Đặt Cài đặt APN** - Thiết lập các cài đặt APN cho điện thoại.
8. **Đặt lại Cài đặt APN** - Đặt lại cài đặt APN về mặc định.
9. **Bật/Tắt Wi-Fi** - Bật hoặc Tắt radio Wi-Fi của điện thoại. Kiểm soát liệu điện thoại có thể khám phá và kết nối với các mạng không dây để truy cập internet hay không.
10. **Bật/Tắt Gọi Wi-Fi** - Bật hoặc Tắt Gọi Wi-Fi. Tính năng này cho phép thực hiện và nhận cuộc gọi qua Wi-Fi thay vì mạng di động, điều này có thể hữu ích ở những khu vực có tín hiệu di động yếu.
11. **Kết nối VPN** - Kết nối với VPN (Mạng riêng ảo).
12. **Ngắt kết nối VPN** - Ngắt kết nối bất kỳ kết nối VPN (Mạng riêng ảo) đang hoạt động nào. Ngừng định tuyến lưu lượng truy cập internet thông qua máy chủ VPN, điều này có thể ảnh hưởng đến tốc độ kết nối hoặc quyền truy cập nội dung.
13. **Cấp quyền ứng dụng** - Cấp một quyền cụ thể cho ứng dụng (như quyền truy cập bộ nhớ, máy ảnh hoặc vị trí). Cần thiết để một số chức năng của ứng dụng hoạt động chính xác.
14. **Khởi động lại thiết bị** - Khởi động lại hoàn toàn điện thoại. Điều này có thể giúp giải quyết nhiều lỗi phần mềm tạm thời bằng cách làm mới tất cả các dịch vụ và kết nối đang chạy.

## Phân loại vấn đề ban đầu

Xác định danh mục nào mô tả tốt nhất vấn đề của người dùng:

1. **không có dịch vụ/Sự cố kết nối**: Điện thoại hiển thị "không có dịch vụ" hoặc không thể kết nối với mạng
2. **Sự cố dữ liệu di động**: Không thể truy cập internet hoặc gặp tốc độ dữ liệu chậm
3. **Sự cố nhắn tin Hình ảnh/Nhóm (MMS)**: Không thể gửi hoặc nhận tin nhắn hình ảnh

Đối với nhiều vấn đề, hãy giải quyết vấn đề kết nối cơ bản trước.

## Lộ trình 1: Khắc phục sự cố không có dịch vụ / Không có kết nối

### Bước 1.0: Kiểm tra xem người dùng có đang gặp sự cố không có dịch vụ hay không
Nếu có dịch vụ, thanh trạng thái sẽ không hiển thị 'không có tín hiệu' hoặc 'chế độ máy bay'.
- Kiểm tra thanh trạng thái
- Nếu thanh trạng thái hiển thị rằng có dịch vụ, người dùng không gặp sự cố không có dịch vụ.
- Nếu thanh trạng thái hiển thị rằng không có dịch vụ, hãy chuyển sang Bước 1.1

### Bước 1.1: Kiểm tra Chế độ máy bay và Trạng thái mạng
Kiểm tra kết nối của điện thoại với mạng di động và Wi-Fi. Điều này sẽ cho biết Chế độ máy bay có bật hay không, cường độ tín hiệu và chi tiết kết nối khác.

**Nếu Chế độ máy bay đang BẬT:**
- TẮT Chế độ máy bay
- Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa

**Nếu Chế độ máy bay đang TẮT:**
- Chuyển sang Bước 1.2

### Bước 1.2: Xác minh Trạng thái thẻ SIM
Kiểm tra xem thẻ SIM có hoạt động chính xác hay không. Xác định xem nó đang ở trạng thái bị mất, bị khóa hay đang hoạt động.

**Nếu SIM hiển thị là BỊ MẤT:**
- Tháo và lắp lại thẻ SIM
- Kiểm tra xem thẻ SIM đã ĐANG HOẠT ĐỘNG chưa.
- Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa

**Nếu SIM bị KHÓA bằng PIN/PUK:**
- Chuyển cấp cho hỗ trợ kỹ thuật để được hỗ trợ về bảo mật SIM

**Nếu SIM ĐANG HOẠT ĐỘNG và hoạt động bình thường:**
- Chuyển sang Bước 1.3

### Bước 1.3: Thử đặt lại cài đặt APN
Nếu các sự cố kết nối cơ bản vẫn tiếp diễn:

- Đặt lại cài đặt APN về mặc định
- Khởi động lại thiết bị
- Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa

**Nếu vẫn chưa được giải quyết:**
- Chuyển sang Bước 1.4

### Bước 1.4: Kiểm tra Tạm ngưng đường truyền
Không có dịch vụ có thể là do đường truyền bị tạm ngưng.

**Nếu đường truyền bị tạm ngưng:**
- Làm theo các hướng dẫn trong chính sách chung để biết thêm thông tin về việc tạm ngưng đường truyền và cách dỡ bỏ tạm ngưng.
- Nếu bạn có thể dỡ bỏ tạm ngưng:
    - Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa.
- Nếu bạn không thể dỡ bỏ tạm ngưng:
    - Chuyển cấp cho hỗ trợ kỹ thuật.

**Nếu vẫn chưa được giải quyết:**
- Chuyển cấp cho hỗ trợ kỹ thuật

## Lộ trình 2: Khắc phục sự cố Dữ liệu di động không khả dụng hoặc chậm

Lưu ý: Lộ trình này không bao gồm các sự cố dữ liệu wifi.

### Bước 2.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu hay không

Khi dữ liệu di động không khả dụng, một bài kiểm tra tốc độ sẽ trả về 'không có kết nối'.
Nếu dữ liệu khả dụng, một bài kiểm tra tốc độ cũng sẽ trả về tốc độ dữ liệu. Bất kỳ tốc độ nào dưới 'Xuất sắc' đều được coi là chậm.
- Lộ trình 2.1 kiểm tra các sự cố dữ liệu di động không khả dụng.
- Lộ trình 2.2 kiểm tra các sự cố dữ liệu chậm.

## Lộ trình 2.1: Khắc phục sự cố Dữ liệu di động không khả dụng

### Bước 2.1.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu di động không khả dụng hay không

- Chạy kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'không có kết nối', dữ liệu di động không khả dụng.
    - Làm theo Lộ trình 2.1.
    - Sau khi vấn đề được giải quyết, nếu tốc độ không phải là 'Xuất sắc', hãy làm theo Lộ trình 2.2.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động khả dụng.
    - Nếu tốc độ là 'Xuất sắc', người dùng không gặp sự cố dữ liệu di động.
    - Đối với bất kỳ tốc độ khác nào ('Yếu', 'Trung bình', 'Tốt'), dữ liệu di động có thể bị chậm và bạn phải làm theo Lộ trình 2.2.

### Bước 2.1.1: Xác minh Sự cố dịch vụ
Kiểm tra xem điện thoại có dịch vụ di động hay không. Dữ liệu di động yêu cầu ít nhất một số kết nối mạng di động.

- Trước tiên, hãy làm theo các bước khắc phục sự cố Lộ trình 1 (Sự cố không có dịch vụ / Không có kết nối).
- Khi bạn đã xác nhận rằng dịch vụ khả dụng, hãy kiểm tra xem sự cố dữ liệu di động vẫn tiếp diễn hay không.
    - Chạy lại kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang Bước 2.1.2.

### Bước 2.1.2: Xác minh xem người dùng có đang đi du lịch hay không
Kiểm tra xem người dùng có đang ở bên ngoài khu vực dịch vụ thông thường của mình hay không.

**Nếu Người dùng không đi du lịch:**
- Chuyển sang Bước 2.1.3

**Nếu Người dùng đang đi du lịch:**
- Xác minh xem Chuyển vùng dữ liệu đã được bật để cho phép sử dụng dữ liệu trên mạng khác hay chưa.


**Nếu Chuyển vùng dữ liệu đang TẮT:**
- BẬT Chuyển vùng dữ liệu
- Chạy lại kiểm tra tốc độ và kiểm tra kết nối dữ liệu.

**If Chuyển vùng dữ liệu đang BẬT nhưng không hoạt động:**
- Xác minh rằng đường truyền liên kết với số điện thoại mà người dùng đã cung cấp đã được bật chuyển vùng.
    - Nếu đường truyền chưa được bật chuyển vùng, hãy bật nó miễn phí cho người dùng
- Chạy lại kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang Bước 2.1.3.

**Nếu Chuyển vùng dữ liệu đang BẬT và đã được kích hoạt nhưng kết nối không hoạt động:**
- Chuyển sang Bước 2.1.3

### Bước 2.1.3: Kiểm tra cài đặt dữ liệu di động
**Nếu Dữ liệu di động đang TẮT:**
- BẬT Dữ liệu di động
- Chạy lại kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang Bước 2.1.4.

**Nếu Dữ liệu di động đang BẬT nhưng không hoạt động:**
- Chuyển sang Bước 2.1.4

### Bước 2.1.4: Kiểm tra Mức sử dụng dữ liệu
Kiểm tra xem, đối với đường truyền liên kết với số điện thoại mà người dùng đã cung cấp, mức sử dụng dữ liệu của người dùng có vượt quá giới hạn dữ liệu của họ hay không.

**Nếu Mức sử dụng dữ liệu ĐÃ VƯỢT QUÁ:**
- Kiểm tra xem người dùng có cho phép thay đổi gói cước khác hay nạp thêm dữ liệu hay không.
- Làm theo các hướng dẫn trong chính sách chung để biết thêm thông tin về nạp thêm dữ liệu và thay đổi gói cước.
- Nếu bạn có thể nạp thêm dữ liệu hoặc thay đổi sang gói cước có giới hạn dữ liệu cao hơn:
    - Chạy lại kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang hỗ trợ kỹ thuật.
- Nếu bạn không thể nạp thêm dữ liệu hoặc thay đổi sang gói cước có giới hạn dữ liệu cao hơn (không được phép hoặc người dùng không muốn):
    - Chuyển cấp cho hỗ trợ kỹ thuật.

**Nếu Mức sử dụng dữ liệu CHƯA VƯỢT QUÁ:**
- Chạy lại kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang hỗ trợ kỹ thuật.

## Lộ trình 2.2: Khắc phục sự cố Dữ liệu di động chậm

### Bước 2.2.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu chậm hay không
Khi dữ liệu di động khả dụng nhưng tốc độ khác hơn 'Xuất sắc', người dùng đang gặp sự cố dữ liệu chậm.
- Chạy kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'không có kết nối', dữ liệu di động không khả dụng.
    - Làm theo Lộ trình 2.1.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động khả dụng.
    - Nếu tốc độ là 'Xuất sắc', người dùng không gặp sự cố dữ liệu chậm.
    - Đối với bất kỳ tốc độ khác nào ('Yếu', 'Trung bình', 'Tốt'), dữ liệu di động có thể bị chậm và bạn phải làm theo Lộ trình 2.2.

### Bước 2.2.1: Kiểm tra Cài đặt hạn chế dữ liệu
Kiểm tra xem có bất kỳ cài đặt nào đang giới hạn mức sử dụng dữ liệu của họ hay không, chẳng hạn như chế độ Trình tiết kiệm dữ liệu.

**Nếu Trình tiết kiệm dữ liệu đang BẬT:**
- TẮT chế độ Trình tiết kiệm dữ liệu
- Chạy lại kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Xuất sắc' hay không.
    - Nếu không phải trường hợp này, hãy chuyển sang Bước 6.
**Nếu Trình tiết kiệm dữ liệu đang TẮT:**
- Chuyển sang Bước 6

### Bước 2.2.2: Kiểm tra Ưu tiên chế độ mạng
Kiểm tra loại mạng di động mà điện thoại của họ ưu tiên. Sử dụng các chế độ cũ hơn như 2G/3G có thể làm hạn chế đáng kể tốc độ.

**Nếu được đặt thành các loại mạng cũ hơn (chỉ 2G/3G):**
- Thay đổi ưu tiên mạng thành một tùy chọn bao gồm 5G
- Chạy lại kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Xuất sắc' hay không.
    - Nếu không phải trường hợp này, hãy chuyển sang Bước 7.

**Nếu đã ở cài đặt tối ưu:**
- Chuyển sang Bước 7

### Bước 2.2.3: Kiểm tra VPN Đang hoạt động
Kiểm tra xem VPN (Mạng riêng ảo) có đang ở trạng thái đang hoạt động hay không, điều này có thể ảnh hưởng đến chất lượng kết nối.

**Nếu VPN đang ở trạng thái đang hoạt động:**
- Tắt kết nối VPN hiện tại
- Chạy lại kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Xuất sắc' hay không.
    - Nếu không phải trường hợp này, hãy chuyển cấp cho hỗ trợ kỹ thuật.

**Nếu không có VPN hoặc ngắt kết nối không giúp ích gì:**
- Chuyển cấp cho hỗ trợ kỹ thuật.

## Lộ trình 3: Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Nhóm)

### Bước 3.0: Kiểm tra xem người dùng có đang gặp sự cố MMS hay không
Khi MMS không hoạt động, người dùng sẽ không thể gửi hoặc nhận tin nhắn hình ảnh.

- Kiểm tra xem có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định hay không.
    - Nếu việc này hoạt động, người dùng không gặp sự cố MMS.
    - Nếu việc này không hoạt động, hãy chuyển sang Bước 3.1.

### Bước 3.1: Xác minh Trạng thái dịch vụ mạng
Kiểm tra xem điện thoại có dịch vụ di động hay không. MMS yêu cầu ít nhất một số kết nối mạng di động.

- Trước tiên, hãy làm theo các bước khắc phục sự cố Lộ trình 1 (Sự cố không có dịch vụ / Không có kết nối).
- Sau khi bạn đã xác nhận rằng dịch vụ khả dụng, hãy kiểm tra xem sự cố vẫn tiếp diễn hay không:
    - Kiểm tra xem có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định hay không.

**Nếu dịch vụ khả dụng:**
- Chuyển sang Bước 3.2

### Bước 3.2: Xác minh Trạng thái dữ liệu di động
Dữ liệu di động là bắt buộc đối với MMS.

- Sử dụng các bước khắc phục sự cố Lộ trình 2.1 (Dữ liệu di động không khả dụng) để kiểm tra xem kết nối dữ liệu di động có hoạt động hay không. Đừng lo lắng về tốc độ, hãy tập trung vào khả năng kết nối.
- Sau khi bạn đã xác nhận rằng kết nối dữ liệu di động hoạt động, hãy kiểm tra xem sự cố MMS vẫn tiếp diễn hay không:
    - Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

### Bước 3.3: Kiểm tra Công nghệ mạng
Kiểm tra loại mạng di động mà điện thoại đang đã kết nối vào. MMS yêu cầu ít nhất công nghệ 3G trở lên.

**Nếu đang đã kết nối vào mạng 2G chỉ:**
- Thay đổi chế độ mạng để bao gồm ít nhất 3G/4G/5G
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu đang sử dụng mạng 3G trở lên:**
- Chuyển sang Bước 3.4


### Bước 3.4: Kiểm tra Trạng thái Gọi Wi-Fi
Kiểm tra xem Gọi Wi-Fi có được bật hay không, vì nó có thể cản trở chức năng MMS.

**Nếu Gọi Wi-Fi đang BẬT:**
- TẮT Gọi Wi-Fi
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu Gọi Wi-Fi đang TẮT hoặc tắt nó đi không giúp ích gì:**
- Chuyển sang Bước 3.5

### Bước 3.5: Xác minh quyền của ứng dụng nhắn tin
Kiểm tra xem ứng dụng nhắn tin mặc định có các quyền bắt buộc hay không - cụ thể là cả quyền bộ nhớ và SMS.

**Nếu quyền bộ nhớ hoặc SMS đang ở trạng thái bị mất:**
- Cấp cả hai quyền bắt buộc cho ứng dụng nhắn tin
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu tất cả các quyền đã được cấp:**
- Chuyển sang Bước 3.6

### Bước 3.6: Kiểm tra Cài đặt APN
Kiểm tra các cài đặt kỹ thuật (APNs) mà điện thoại sử dụng để kết nối với mạng dữ liệu di động của nhà mạng.

**Kiểm tra cụ thể cho:**
- Cấu hình URL MMSC (phải có để MMS hoạt động)

**Nếu URL MMSC đang ở trạng thái bị mất:**
- Đặt lại cài đặt APN về mặc định của nhà mạng
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu sự cố vẫn tiếp diễn sau khi kiểm tra tất cả các mục trên:**
- Chuyển cấp cho hỗ trợ kỹ thuật