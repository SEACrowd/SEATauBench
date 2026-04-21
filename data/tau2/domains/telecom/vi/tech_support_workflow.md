# Điện thoại - Quy trình Khắc phục sự cố Hỗ trợ Kỹ thuật

## Giới thiệu

Tài liệu này cung cấp một quy trình có cấu trúc để chẩn đoán và giải quyết các sự cố kỹ thuật điện thoại. Thực hiện theo các đường dẫn này dựa trên mô tả vấn đề của người dùng. Mỗi bước bao gồm hướng dẫn về hành động khắc phục sự cố cụ thể nào cần thực hiện dựa trên những gì cần được kiểm tra hoặc sửa đổi.

Hãy chắc chắn rằng bạn thử tất cả các bước giải quyết liên quan trước khi chuyển người dùng sang đại lý con người.

## Tham chiếu hành động người dùng khả dụng
Đây là các hành động mà người dùng có thể thực hiện trên thiết bị của họ.
Bạn phải hiểu rõ những hành động đó vì là một phần của hỗ trợ kỹ thuật, bạn sẽ phải giúp khách hàng thực hiện hàng loạt hành động

Các đại lý nên hướng dẫn người dùng thực hiện các hành động cụ thể này khi cần thiết trong quá trình khắc phục sự cố:


### Hành động chẩn đoán (Chỉ đọc)
1. **Kiểm tra Thanh trạng thái** - Hiển thị các biểu tượng hiện đang hiển thị trên thanh trạng thái của điện thoại (khu vực ở trên cùng của màn hình). Hiển thị cường độ tín hiệu mạng, trạng thái dữ liệu di động (đã bật, đã tắt, trình tiết kiệm dữ liệu), trạng thái Wi-Fi và mức pin.
2. **Kiểm tra Trạng thái Mạng** - Kiểm tra trạng thái kết nối điện thoại với mạng di động và Wi-Fi. Hiển thị trạng thái chế độ máy bay, cường độ tín hiệu, loại mạng, liệu dữ liệu di động có được bật hay không và liệu chuyển vùng dữ liệu có được bật hay không. Cường độ tín hiệu có thể là "không có", "Kém" (1 vạch), "Trung bình" (2 vạch), "Tốt" (3 vạch), "Rất tốt" (4+ vạch).
3. **Kiểm tra Tùy chọn Chế độ Mạng** - Kiểm tra tùy chọn chế độ mạng điện thoại. Hiển thị loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G, 2G).
4. **Kiểm tra Trạng thái SIM** - Kiểm tra xem thẻ SIM có hoạt động chính xác không và hiển thị trạng thái hiện tại của nó. Hiển thị nếu SIM đang hoạt động, bị mất hoặc bị khóa bằng mã PIN hoặc PUK.
5. **Kiểm tra Hạn chế Dữ liệu** - Kiểm tra xem điện thoại có bất kỳ tính năng giới hạn dữ liệu nào đang hoạt động hay không. Hiển thị nếu chế độ Trình tiết kiệm dữ liệu đang bật và liệu việc sử dụng dữ liệu nền có bị hạn chế trên toàn cầu hay không.
6. **Kiểm tra Cài đặt APN** - Kiểm tra các cài đặt APN kỹ thuật mà điện thoại sử dụng để kết nối với mạng dữ liệu di động của nhà mạng của bạn. Hiển thị tên APN hiện tại và URL MMSC để nhắn tin hình ảnh.
7. **Kiểm tra Trạng thái Wi-Fi** - Kiểm tra trạng thái kết nối Wi-Fi. Hiển thị nếu Wi-Fi đã bật, mạng bạn đang Đã kết nối (nếu có) và cường độ tín hiệu.
8. **Kiểm tra Trạng thái Gọi Wi-Fi** - Kiểm tra xem Gọi Wi-Fi có được bật trên thiết bị của bạn hay không. Tính năng này cho phép thực hiện và nhận cuộc gọi qua mạng Wi-Fi thay vì sử dụng mạng di động.
9. **Kiểm tra Trạng thái VPN** - Kiểm tra xem bạn có đang sử dụng kết nối VPN (Mạng riêng ảo) hay không. Hiển thị nếu VPN đang hoạt động, Đã kết nối và hiển thị bất kỳ chi tiết kết nối có sẵn nào.
10. **Kiểm tra Ứng dụng đã cài đặt** - Trả về tên của tất cả các ứng dụng đã cài đặt trên điện thoại.
11. **Kiểm tra Trạng thái Ứng dụng** - Kiểm tra thông tin chi tiết về một ứng dụng cụ thể. Hiển thị các quyền và cài đặt sử dụng dữ liệu nền của ứng dụng.
12. **Kiểm tra Quyền ứng dụng** - Kiểm tra những quyền mà một ứng dụng cụ thể hiện đang có. Hiển thị nếu ứng dụng có quyền truy cập vào các tính năng như bộ nhớ, máy ảnh, vị trí, v.v.
13. **Chạy bài kiểm tra tốc độ** - Đo tốc độ kết nối internet hiện tại của bạn (tốc độ tải xuống). Cung cấp thông tin về chất lượng kết nối và các hoạt động mà nó có thể hỗ trợ. Tốc độ tải xuống có thể là "Không xác định", "rất Kém", "Kém", "Trung bình", "Tốt" hoặc "Rất tốt".
14. **Có thể gửi MMS** - Kiểm tra xem ứng dụng nhắn tin có thể gửi tin nhắn MMS hay không.

### Hành động sửa lỗi (Ghi/Sửa đổi)
1. **Đặt Chế độ Mạng** - Thay đổi loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G). Các mạng tốc độ cao hơn (5G, 4G) cung cấp dữ liệu nhanh hơn nhưng có thể sử dụng nhiều pin hơn.
2. **Bật/Tắt Chế độ máy bay** - Bật hoặc TẮT Chế độ máy bay. Khi BẬT, nó ngắt kết nối tất cả các liên lạc không dây bao gồm di động, Wi-Fi và Bluetooth.
3. **Tháo/Lắp lại SIM** - Mô phỏng việc tháo và lắp lại thẻ SIM. Điều này có thể giúp giải quyết các sự cố nhận dạng.
4. **Bật/Tắt Dữ liệu Di động** - Bật hoặc TẮT kết nối dữ liệu di động của điện thoại. Kiểm soát liệu điện thoại có thể sử dụng dữ liệu di động để truy cập internet khi Wi-Fi không khả dụng hay không.
5. **Bật/Tắt Chuyển vùng Dữ liệu** - Bật hoặc TẮT Chuyển vùng dữ liệu. Khi BẬT, chuyển vùng được bật và điện thoại có thể sử dụng các mạng dữ liệu ở những khu vực ngoài vùng phủ sóng của nhà mạng của bạn.
6. **Bật/Tắt Trình tiết kiệm dữ liệu** - Bật hoặc TẮT chế độ Trình tiết kiệm dữ liệu. Khi BẬT, nó giảm sử dụng dữ liệu, điều này có thể ảnh hưởng đến tốc độ dữ liệu.
7. **Đặt Cài đặt APN** - Thiết lập các cài đặt APN cho điện thoại.
8. **Đặt lại Cài đặt APN** - Đặt lại các cài đặt APN của bạn về cài đặt mặc định.
9. **Bật/Tắt Wi-Fi** - Bật hoặc TẮT Wi-Fi của điện thoại. Kiểm soát liệu điện thoại có thể khám phá và kết nối với các mạng không dây để truy cập internet hay không.
10. **Bật/Tắt Gọi Wi-Fi** - Bật hoặc TẮT Gọi Wi-Fi. Tính năng này cho phép thực hiện và nhận cuộc gọi qua Wi-Fi thay vì mạng di động, điều này có thể hữu ích ở những khu vực có tín hiệu di động yếu.
11. **Kết nối VPN** - Kết nối với VPN (Mạng riêng ảo) của bạn.
12. **Ngắt kết nối VPN** - Ngắt kết nối bất kỳ kết nối VPN (Mạng riêng ảo) đang hoạt động nào. Ngừng định tuyến lưu lượng truy cập internet của bạn thông qua máy chủ VPN, điều này có thể ảnh hưởng đến tốc độ kết nối hoặc quyền truy cập nội dung.
13. **Cấp Quyền ứng dụng** - Cấp quyền cụ thể cho một ứng dụng (như quyền truy cập vào bộ nhớ, máy ảnh hoặc vị trí). Cần thiết để một số chức năng ứng dụng hoạt động bình thường.
14. **Khởi động lại thiết bị** - Khởi động lại điện thoại hoàn toàn. Điều này có thể giúp giải quyết nhiều trục trặc phần mềm tạm thời bằng cách làm mới tất cả các dịch vụ và kết nối đang chạy.

## Phân loại vấn đề ban đầu

Xác định loại nào mô tả tốt nhất vấn đề của người dùng:

1. **Không có dịch vụ/Sự cố kết nối**: Điện thoại hiển thị "Không có dịch vụ" hoặc không thể kết nối với mạng
2. **Sự cố Dữ liệu Di động**: Không thể truy cập internet hoặc gặp tốc độ dữ liệu chậm
3. **Sự cố Nhắn tin Hình ảnh/Nhóm (MMS)**: Không thể gửi hoặc nhận tin nhắn hình ảnh

Đối với nhiều vấn đề, hãy giải quyết kết nối cơ bản trước.

## Đường dẫn 1: Không có dịch vụ / Khắc phục sự cố Không có Kết nối

### Bước 1.0: Kiểm tra xem người dùng có đang gặp sự cố Không có dịch vụ hay không
Nếu dịch vụ khả dụng, thanh trạng thái sẽ không hiển thị 'không có tín hiệu' hoặc 'chế độ máy bay'.
- Yêu cầu người dùng kiểm tra thanh trạng thái của họ
- Nếu thanh trạng thái hiển thị rằng dịch vụ khả dụng, người dùng không gặp sự cố Không có dịch vụ.
- Nếu thanh trạng thái hiển thị rằng dịch vụ không khả dụng, hãy tiếp tục Bước 1.1

### Bước 1.1: Kiểm tra Chế độ máy bay và Trạng thái mạng
Yêu cầu người dùng kiểm tra kết nối điện thoại của họ với mạng di động và Wi-Fi. Điều này sẽ hiển thị nếu Chế độ máy bay đang bật, cường độ tín hiệu và chi tiết kết nối khác.

**Nếu Chế độ máy bay đang BẬT:**
- Yêu cầu người dùng TẮT Chế độ máy bay
- Yêu cầu người dùng nhìn vào thanh trạng thái của họ và kiểm tra xem dịch vụ đã được khôi phục chưa

**Nếu Chế độ máy bay đang TẮT:**
- Tiếp tục Bước 1.2

### Bước 1.2: Xác minh Trạng thái thẻ SIM
Yêu cầu người dùng kiểm tra xem thẻ SIM của họ có hoạt động chính xác không. Bạn muốn biết nó có bị mất, bị khóa hay đang hoạt động.

**Nếu SIM hiển thị THIẾU:**
- Yêu cầu người dùng lắp lại thẻ SIM bằng cách tháo và lắp lại
- Kiểm tra xem thẻ SIM có HOẠT ĐỘNG không.
- Yêu cầu người dùng nhìn vào thanh trạng thái của họ và kiểm tra xem dịch vụ đã được khôi phục chưa

**Nếu SIM bị KHÓA với PIN/PUK:**
- Chuyển sang hỗ trợ kỹ thuật để được hỗ trợ về bảo mật SIM

**Nếu SIM HOẠT ĐỘNG và hoạt động tốt:**
- Tiếp tục Bước 1.3

### Bước 1.3: Thử đặt lại cài đặt APN
Nếu sự cố kết nối cơ bản vẫn tiếp diễn:

- Yêu cầu người dùng đặt lại cài đặt APN về mặc định
- Yêu cầu họ khởi động lại thiết bị của mình
- Yêu cầu người dùng nhìn vào thanh trạng thái của họ và kiểm tra xem dịch vụ đã được khôi phục chưa

**Nếu vẫn chưa được giải quyết:**
- Tiếp tục Bước 1.4

### Bước 1.4: Kiểm tra Tạm ngưng dòng dịch vụ

Không có dịch vụ có thể là do một dòng dịch vụ bị tạm ngưng.

**Nếu dòng dịch vụ bị tạm ngưng:**
- Làm theo các hướng dẫn trong chính sách chính để biết thêm thông tin về tạm ngưng dòng dịch vụ và cách dỡ bỏ tạm ngưng.
- Nếu bạn có thể dỡ bỏ tạm ngưng:
    - Yêu cầu người dùng nhìn vào thanh trạng thái của họ và kiểm tra xem dịch vụ đã được khôi phục chưa.
- Nếu bạn không thể dỡ bỏ tạm ngưng:
    - Chuyển sang hỗ trợ kỹ thuật.

**Nếu vẫn chưa được giải quyết:**
- Chuyển sang hỗ trợ kỹ thuật

## Đường dẫn 2: Khắc phục sự cố Dữ liệu Di động Không khả dụng hoặc Chậm

Lưu ý: Đường dẫn này không bao gồm các sự cố dữ liệu wifi.

### Bước 2.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu hay không

Khi dữ liệu di động không khả dụng, một bài kiểm tra tốc độ sẽ trả về 'không có kết nối'.
Nếu dữ liệu khả dụng, bài kiểm tra tốc độ cũng sẽ trả về tốc độ dữ liệu. Bất kỳ tốc độ nào dưới mức 'Rất tốt' đều được coi là chậm.
- Đường dẫn 2.1 kiểm tra các sự cố dữ liệu di động không khả dụng.
- Đường dẫn 2.2 kiểm tra các sự cố dữ liệu chậm.

## Đường dẫn 2.1: Khắc phục sự cố Dữ liệu Di động Không khả dụng

### Bước 2.1.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu di động không khả dụng hay không

- Yêu cầu người dùng chạy bài kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'không có kết nối', dữ liệu di động không khả dụng.
    - Làm theo Đường dẫn 2.1.
    - Sau khi sự cố được giải quyết, nếu tốc độ không phải 'Rất tốt', hãy làm theo Đường dẫn 2.2.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động khả dụng.
    - Nếu tốc độ là 'Rất tốt', người dùng không gặp sự cố dữ liệu di động.
    - Đối với bất kỳ tốc độ khác nào ('Kém', 'Trung bình', 'Tốt'), dữ liệu di động có thể chậm và bạn phải làm theo Đường dẫn 2.2.

### Bước 2.1.1: Xác minh sự cố dịch vụ
Yêu cầu người dùng kiểm tra xem điện thoại của họ có dịch vụ di động không. Dữ liệu di động yêu cầu ít nhất một số kết nối mạng di động.

- Làm theo các bước khắc phục sự cố Đường dẫn 1 (Không có dịch vụ / Không có kết nối) trước.
- Khi bạn đã xác nhận rằng dịch vụ khả dụng, hãy kiểm tra xem sự cố dữ liệu di động có tiếp diễn không.
    - Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy tiếp tục Bước 2.1.2.

### Bước 2.1.2: Xác minh xem người dùng có đang đi du lịch không
Yêu cầu người dùng kiểm tra xem họ có đang ở ngoài khu vực dịch vụ thông thường của họ không.

**Nếu người dùng không đi du lịch:**
- Tiếp tục Bước 2.1.3

**Nếu người dùng đang đi du lịch:**
- Yêu cầu người dùng xác minh xem Chuyển vùng dữ liệu có được bật để cho phép sử dụng dữ liệu trên các mạng khác hay không.

**Nếu Chuyển vùng dữ liệu đang TẮT:**
- Yêu cầu người dùng BẬT Chuyển vùng dữ liệu
- Yêu cầu họ chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.

**Nếu Chuyển vùng dữ liệu đang BẬT nhưng không hoạt động:**
- Xác minh rằng dòng dịch vụ được liên kết với số điện thoại mà người dùng đã cung cấp có được bật chuyển vùng hay không.
    - Nếu dòng dịch vụ không được bật chuyển vùng, hãy bật nó miễn phí cho người dùng
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy tiếp tục Bước 2.1.3.

**Nếu Chuyển vùng dữ liệu đang BẬT và được bật nhưng kết nối không hoạt động:**
- Tiếp tục Bước 2.1.3

### Bước 2.1.3: Kiểm tra cài đặt dữ liệu di động
**Nếu Dữ liệu di động đang TẮT:**
- Yêu cầu người dùng BẬT Dữ liệu di động
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy tiếp tục Bước 2.1.4.

**Nếu Dữ liệu di động đang BẬT nhưng không hoạt động:**
- Tiếp tục Bước 2.1.4

### Bước 2.1.4: Kiểm tra mức sử dụng dữ liệu
Kiểm tra xem, đối với dòng dịch vụ được liên kết với số điện thoại mà người dùng đã cung cấp, mức sử dụng dữ liệu của người dùng có vượt quá giới hạn dữ liệu của họ hay không.

**Nếu Mức sử dụng dữ liệu bị VƯỢT QUÁ:**
- Yêu cầu người dùng xem họ có muốn thay đổi gói cước khác hay nạp thêm dữ liệu không.
- Làm theo các hướng dẫn trong chính sách chính để biết thêm thông tin về nạp thêm dữ liệu và thay đổi gói cước.
- Nếu bạn có thể nạp thêm dữ liệu hoặc thay đổi sang gói cước có giới hạn dữ liệu cao hơn:
    - Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang hỗ trợ kỹ thuật.
- Nếu bạn không thể nạp thêm dữ liệu hoặc thay đổi sang gói cước có giới hạn dữ liệu cao hơn (không được phép hoặc người dùng không muốn):
    - Chuyển sang hỗ trợ kỹ thuật.

**Nếu Mức sử dụng dữ liệu KHÔNG BỊ VƯỢT QUÁ:**
- Yêu cầu người dùng chạy bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, hãy chuyển sang hỗ trợ kỹ thuật.

## Đường dẫn 2.2: Khắc phục sự cố dữ liệu di động chậm

### Bước 2.2.0: Kiểm tra xem người dùng có đang gặp sự cố dữ liệu chậm hay không
Khi dữ liệu di động khả dụng nhưng tốc độ là bất kỳ thứ gì khác 'Rất tốt', người dùng đang gặp sự cố dữ liệu chậm.
- Yêu cầu người dùng chạy bài kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'không có kết nối', dữ liệu di động không khả dụng.
    - Làm theo Đường dẫn 2.1.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động khả dụng.
    - Nếu tốc độ là 'Rất tốt', người dùng không gặp sự cố dữ liệu chậm.
    - Đối với bất kỳ tốc độ khác nào ('Kém', 'Trung bình', 'Tốt'), dữ liệu di động có thể chậm và bạn phải làm theo Đường dẫn 2.2.

### Bước 2.2.1: Kiểm tra cài đặt hạn chế dữ liệu
Yêu cầu người dùng kiểm tra xem có cài đặt nào đang giới hạn mức sử dụng dữ liệu của họ không, như chế độ Trình tiết kiệm dữ liệu.

**Nếu Trình tiết kiệm dữ liệu đang BẬT:**
- Yêu cầu người dùng TẮT chế độ Trình tiết kiệm dữ liệu
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Rất tốt' không.
    - Nếu không phải trường hợp này, hãy tiếp tục Bước 6.
**Nếu Trình tiết kiệm dữ liệu đang TẮT:**
- Tiếp tục Bước 6

### Bước 2.2.2: Kiểm tra tùy chọn chế độ mạng
Yêu cầu người dùng kiểm tra xem loại mạng di động nào mà điện thoại của họ ưu tiên. Sử dụng các chế độ cũ hơn như 2G/3G có thể hạn chế đáng kể tốc độ.

**Nếu được đặt thành các loại mạng cũ hơn (chỉ 2G/3G):**
- Yêu cầu người dùng thay đổi tùy chọn mạng thành tùy chọn bao gồm 5G
- Yêu cầu người dùng chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Rất tốt' không.
    - Nếu không phải trường hợp này, hãy tiếp tục Bước 7.

**Nếu đã ở cài đặt tối ưu:**
- Tiếp tục Bước 7

### Bước 2.2.3: Kiểm tra VPN Đang hoạt động
Yêu cầu người dùng kiểm tra xem họ có đang sử dụng VPN (Mạng riêng ảo) có thể ảnh hưởng đến chất lượng kết nối hay không.

**Nếu VPN đang hoạt động:**
- Yêu cầu người dùng tắt kết nối VPN hiện tại của họ
- Yêu cầu họ chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Rất tốt' không.
    - Nếu không phải trường hợp này, hãy chuyển sang hỗ trợ kỹ thuật.

**Nếu không có VPN hoặc ngắt kết nối không giúp ích gì:**
- Chuyển sang hỗ trợ kỹ thuật.

## Đường dẫn 3: Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Nhóm)

### Bước 3.0: Kiểm tra xem người dùng có đang gặp sự cố MMS hay không
Khi MMS không hoạt động, người dùng sẽ không thể gửi hoặc nhận tin nhắn hình ảnh.

- Yêu cầu người dùng nếu họ có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định.
    - Nếu việc này hoạt động, người dùng không gặp sự cố MMS.
    - Nếu việc này không hoạt động, hãy tiếp tục Bước 3.1.

### Bước 3.1: Xác minh Trạng thái dịch vụ mạng
Yêu cầu người dùng kiểm tra xem điện thoại của họ có dịch vụ di động không. MMS yêu cầu ít nhất một số kết nối mạng di động.

- Làm theo các bước khắc phục sự cố Đường dẫn 1 (Không có dịch vụ / Không có kết nối) trước.
- Khi bạn đã xác nhận rằng dịch vụ khả dụng, hãy kiểm tra xem sự cố có tiếp diễn không:
    - Yêu cầu người dùng nếu họ có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định.

**Nếu dịch vụ khả dụng:**
- Tiếp tục Bước 3.2

### Bước 3.2: Xác minh Trạng thái dữ liệu di động
Dữ liệu di động là bắt buộc đối với MMS.

- Sử dụng các bước khắc phục sự cố Đường dẫn 2.1 (Dữ liệu di động không khả dụng) để kiểm tra xem kết nối dữ liệu di động có hoạt động không. Không lo lắng về tốc độ, tập trung vào kết nối.
- Khi bạn đã xác nhận rằng kết nối dữ liệu di động đang hoạt động, hãy kiểm tra xem sự cố MMS có tiếp diễn không:
    - Yêu cầu người dùng thử và gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

### Bước 3.3: Kiểm tra công nghệ mạng
Yêu cầu người dùng kiểm tra loại mạng di động mà điện thoại của họ đang Đã kết nối với. MMS yêu cầu công nghệ ít nhất 3G trở lên.

**Nếu Đã kết nối chỉ với mạng 2G:**
- Yêu cầu người dùng thay đổi chế độ mạng để bao gồm ít nhất 3G/4G/5G
- Yêu cầu người dùng thử và gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu trên mạng 3G trở lên:**
- Tiếp tục Bước 3.4


### Bước 3.4: Kiểm tra trạng thái Gọi Wi-Fi
Yêu cầu người dùng kiểm tra xem Gọi Wi-Fi có được bật không, vì nó có thể ảnh hưởng đến chức năng MMS.

**Nếu Gọi Wi-Fi đang BẬT:**
- Yêu cầu người dùng TẮT Gọi Wi-Fi
- Yêu cầu người dùng thử và gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu Gọi Wi-Fi đang TẮT hoặc tắt nó không giúp ích gì:**
- Tiếp tục Bước 3.5

### Bước 3.5: Xác minh quyền ứng dụng nhắn tin
Yêu cầu người dùng kiểm tra xem ứng dụng nhắn tin mặc định có các quyền cần thiết không - cụ thể là cả quyền bộ nhớ và SMS.

**Nếu quyền bộ nhớ hoặc SMS đang bị mất:**
- Yêu cầu người dùng cấp cả hai quyền cần thiết cho ứng dụng nhắn tin
- Yêu cầu người dùng thử và gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu tất cả các quyền được cấp:**
- Tiếp tục Bước 3.6

### Bước 3.6: Kiểm tra cài đặt APN
Yêu cầu người dùng kiểm tra các cài đặt kỹ thuật (APN) mà điện thoại của họ sử dụng để kết nối với mạng dữ liệu di động của nhà mạng.

**Cụ thể kiểm tra:**
- Cấu hình URL MMSC (phải có mặt để MMS hoạt động)

**Nếu URL MMSC đang bị mất:**
- Yêu cầu người dùng đặt lại cài đặt APN về mặc định nhà mạng
- Yêu cầu người dùng thử và gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu sự cố vẫn tiếp diễn sau khi kiểm tra tất cả các mục trên:**
- Chuyển sang hỗ trợ kỹ thuật