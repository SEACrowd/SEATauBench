# Điện thoại - Quy trình Khắc phục sự cố Hỗ trợ Kỹ thuật
## Giới thiệu

Tài liệu này cung cấp một quy trình có cấu trúc để chẩn đoán và giải quyết các vấn đề kỹ thuật của điện thoại. Với tư cách là đại lý, bạn có quyền truy cập trực tiếp vào thiết bị của user và có thể tự mình thực hiện các hành động này. Thực hiện theo các đường dẫn này dựa trên mô tả vấn đề của user. Mỗi bước bao gồm các hành động cụ thể bạn nên thực hiện để kiểm tra hoặc sửa đổi cài đặt.

Đảm bảo bạn thử tất cả các bước giải quyết có liên quan trước khi chuyển user cho một đại lý con người.
## Tài liệu tham khảo Hành động có sẵn
Vì bạn có quyền truy cập vào thiết bị của user, bạn có thể thực hiện trực tiếp các hành động sau:
### Hành động Chẩn đoán (Chỉ đọc)
1. **Kiểm tra Thanh Trạng thái** - Hiển thị các biểu tượng hiện đang hiển thị trên thanh trạng thái của điện thoại (khu vực ở trên cùng của màn hình). Hiển thị cường độ tín hiệu mạng, trạng thái dữ liệu di động (đã bật, đã tắt, trình tiết kiệm dữ liệu), trạng thái Wi-Fi và mức pin.
2. **Kiểm tra Trạng thái Mạng** - Kiểm tra trạng thái kết nối của điện thoại với mạng di động và Wi-Fi. Hiển thị trạng thái chế độ máy bay, cường độ tín hiệu, loại mạng, liệu dữ liệu di động có được bật hay không và liệu chuyển vùng dữ liệu có được bật hay không. Cường độ tín hiệu có thể là "không có", "yếu" (1 vạch), "trung bình" (2 vạch), "tốt" (3 vạch), "xuất sắc" (4+ vạch).
3. **Kiểm tra Tùy chọn Chế độ Mạng** - Kiểm tra tùy chọn chế độ mạng của điện thoại. Hiển thị loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G, 2G).
4. **Kiểm tra Trạng thái SIM** - Kiểm tra xem thẻ SIM có hoạt động chính xác không và hiển thị trạng thái hiện tại của nó. Hiển thị xem SIM có phải là đang hoạt động, bị mất hay bị khóa bằng mã PIN hoặc PUK không.
5. **Kiểm tra Hạn chế Dữ liệu** - Kiểm tra xem điện thoại có bất kỳ tính năng giới hạn dữ liệu nào không đang hoạt động. Hiển thị xem chế độ Trình tiết kiệm dữ liệu có bật hay không và liệu mức sử dụng dữ liệu nền có bị hạn chế trên toàn cầu hay không.
6. **Kiểm tra Cài đặt APN** - Kiểm tra các cài đặt APN kỹ thuật mà điện thoại sử dụng để kết nối với mạng dữ liệu di động của nhà mạng. Hiển thị tên APN hiện tại và URL MMSC để nhắn tin hình ảnh.
7. **Kiểm tra Trạng thái Wi-Fi** - Kiểm tra trạng thái kết nối Wi-Fi. Hiển thị xem Wi-Fi có được bật không, nó đang đã kết nối với mạng nào (nếu có) và cường độ tín hiệu.
8. **Kiểm tra Trạng thái Wi-Fi Calling** - Kiểm tra xem Wi-Fi Calling có được bật trên thiết bị hay không. Tính năng này cho phép thực hiện và nhận cuộc gọi qua mạng Wi-Fi thay vì sử dụng mạng di động.
9. **Kiểm tra Trạng thái VPN** - Kiểm tra xem kết nối VPN (Mạng riêng ảo) đang đang hoạt động. Hiển thị xem VPN đang đang hoạt động, đã kết nối và hiển thị bất kỳ chi tiết kết nối available nào.
10. **Kiểm tra Ứng dụng đã cài đặt** - Trả về tên của tất cả các ứng dụng đã cài đặt trên điện thoại.
11. **Kiểm tra Trạng thái Ứng dụng** - Kiểm tra thông tin chi tiết về một ứng dụng cụ thể. Hiển thị quyền và cài đặt mức sử dụng dữ liệu nền của nó.
12. **Kiểm tra Quyền Ứng dụng** - Kiểm tra xem một ứng dụng cụ thể hiện có những quyền gì. Hiển thị xem ứng dụng có quyền truy cập vào các tính năng như bộ nhớ, máy ảnh, vị trí, v.v. không.
13. **Chạy Bài kiểm tra Tốc độ** - Đo tốc độ kết nối internet hiện tại (tốc độ tải xuống). Cung cấp thông tin về chất lượng kết nối và những hoạt động nào nó có thể hỗ trợ. Tốc độ tải xuống có thể là "không xác định", "rất yếu", "yếu", "trung bình", "tốt" hoặc "xuất sắc".
14. **Có thể gửi MMS** - Kiểm tra xem ứng dụng nhắn tin có thể gửi tin nhắn MMS không.
### Hành động Khắc phục (Ghi/Sửa đổi)
1. **Đặt Chế độ Mạng** - Thay đổi loại mạng di động mà điện thoại ưu tiên kết nối (ví dụ: 5G, 4G, 3G). Các mạng tốc độ cao hơn (5G, 4G) cung cấp dữ liệu nhanh hơn nhưng có thể tốn nhiều pin hơn.
2. **Bật/Tắt Chế độ Máy bay** - Bật hoặc Tắt Chế độ Máy bay. Khi BẬT, nó ngắt kết nối tất cả liên lạc không dây bao gồm di động, Wi-Fi và Bluetooth.
3. **Lắp lại thẻ SIM** - Mô phỏng việc tháo và lắp lại thẻ SIM. Điều này có thể giúp giải quyết các vấn đề nhận dạng.
4. **Bật/Tắt Dữ liệu Di động** - Bật hoặc Tắt kết nối dữ liệu di động của điện thoại. Kiểm soát liệu điện thoại có thể sử dụng dữ liệu di động để truy cập internet khi Wi-Fi không khả dụng hay không.
5. **Bật/Tắt Chuyển vùng Dữ liệu** - Bật hoặc Tắt Chuyển vùng Dữ liệu. Khi BẬT, chuyển vùng được kích hoạt và điện thoại có thể sử dụng các mạng dữ liệu ở các khu vực bên ngoài vùng phủ sóng của nhà mạng.
6. **Bật/Tắt Trình tiết kiệm Dữ liệu** - Bật hoặc Tắt chế độ Trình tiết kiệm dữ liệu. Khi BẬT, nó giảm mức sử dụng dữ liệu, điều này có thể ảnh hưởng đến tốc độ dữ liệu.
7. **Đặt Cài đặt APN** - Đặt cài đặt APN cho điện thoại.
8. **Đặt lại Cài đặt APN** - Đặt lại cài đặt APN về cài đặt mặc định.
9. **Bật/Tắt Wi-Fi** - Bật hoặc Tắt đài Wi-Fi của điện thoại. Kiểm soát liệu điện thoại có thể khám phá và kết nối với các mạng không dây để truy cập internet hay không.
10. **Bật/Tắt Wi-Fi Calling** - Bật hoặc Tắt Wi-Fi Calling. Tính năng này cho phép thực hiện và nhận cuộc gọi qua Wi-Fi thay vì mạng di động, điều này có thể giúp ở những khu vực có tín hiệu di động yếu.
11. **Kết nối VPN** - Kết nối với VPN (Mạng riêng ảo).
12. **Ngắt kết nối VPN** - Ngắt kết nối bất kỳ kết nối VPN (Mạng riêng ảo) đang hoạt động nào. Ngừng định tuyến lưu lượng truy cập internet qua máy chủ VPN, điều này có thể ảnh hưởng đến tốc độ kết nối hoặc quyền truy cập vào nội dung.
13. **Cấp Quyền Ứng dụng** - Cấp một quyền cụ thể cho một ứng dụng (như quyền truy cập vào bộ nhớ, máy ảnh hoặc vị trí). Cần thiết để một số chức năng của ứng dụng hoạt động chính xác.
14. **Khởi động lại Thiết bị** - Khởi động lại hoàn toàn điện thoại. Điều này có thể giúp giải quyết nhiều trục trặc phần mềm tạm thời bằng cách làm mới tất cả các dịch vụ và kết nối đang chạy.
## Phân loại Vấn đề Ban đầu

Xác định loại nào mô tả tốt nhất vấn đề của user:

1. **Vấn đề không có dịch vụ/Kết nối**: Điện thoại hiển thị "không có dịch vụ" hoặc không thể kết nối với mạng
2. **Vấn đề Dữ liệu Di động**: Không thể truy cập internet hoặc gặp tốc độ dữ liệu chậm
3. **Vấn đề Nhắn tin Hình ảnh/Nhóm (MMS)**: Không thể gửi hoặc nhận tin nhắn hình ảnh

Đối với nhiều vấn đề, hãy giải quyết kết nối cơ bản trước.
## Đường dẫn 1: Khắc phục sự cố không có dịch vụ / Không có kết nối
### Bước 1.0: Kiểm tra xem user có đang gặp sự cố không có dịch vụ hay không
Nếu dịch vụ available, thanh trạng thái sẽ không hiển thị 'no signal' hoặc 'airplane mode'.
- Kiểm tra thanh trạng thái
- Nếu thanh trạng thái hiển thị rằng dịch vụ available, user không gặp sự cố không có dịch vụ.
- Nếu thanh trạng thái hiển thị rằng dịch vụ không available, tiếp tục Bước 1.1
### Bước 1.1: Kiểm tra Chế độ Máy bay và Trạng thái Mạng
Kiểm tra kết nối điện thoại với mạng di động và Wi-Fi. Điều này sẽ cho biết Chế độ máy bay có bật hay không, cường độ tín hiệu và chi tiết kết nối khác.

**Nếu Chế độ Máy bay BẬT:**
- Tắt Chế độ Máy bay
- Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa

**Nếu Chế độ Máy bay TẮT:**
- Tiếp tục Bước 1.2
### Bước 1.2: Xác minh Trạng thái Thẻ SIM
Kiểm tra xem thẻ SIM có hoạt động chính xác không. Xác định xem nó có phải là bị mất, bị khóa hay đang hoạt động không.

**Nếu SIM hiển thị là MẤT:**
- Lắp lại thẻ SIM bằng cách tháo và lắp lại
- Kiểm tra xem thẻ SIM có ACTIVE không.
- Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa

**Nếu SIM bị KHÓA với PIN/PUK:**
- Leo thang cho hỗ trợ kỹ thuật để được hỗ trợ về bảo mật SIM

**Nếu SIM ACTIVE và đang hoạt động:**
- Tiếp tục Bước 1.3
### Bước 1.3: Thử đặt lại cài đặt APN
Nếu các vấn đề kết nối cơ bản vẫn tiếp diễn:

- Đặt lại cài đặt APN về mặc định
- Khởi động lại thiết bị
- Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa

**Nếu vẫn chưa giải quyết được:**
- Tiếp tục Bước 1.4
### Bước 1.4: Kiểm tra Tạm dừng Dòng dịch vụ
Không có dịch vụ có thể là do dòng dịch vụ bị tạm dừng.

**Nếu dòng dịch vụ bị tạm dừng:**
- Làm theo hướng dẫn trong chính sách chính để biết thêm thông tin về việc tạm dừng dòng dịch vụ và cách dỡ bỏ tạm dừng.
- Nếu bạn có thể dỡ bỏ tạm dừng:
    - Kiểm tra thanh trạng thái để xem dịch vụ đã được khôi phục chưa.
- Nếu bạn không thể dỡ bỏ tạm dừng:
    - Leo thang cho hỗ trợ kỹ thuật.

**Nếu vẫn chưa giải quyết được:**
- Leo thang cho hỗ trợ kỹ thuật
## Đường dẫn 2: Khắc phục sự cố Dữ liệu Di động không khả dụng hoặc chậm

Lưu ý: Đường dẫn này không đề cập đến các vấn đề dữ liệu wifi.
### Bước 2.0: Kiểm tra xem user có đang gặp sự cố dữ liệu hay không

Khi dữ liệu di động không khả dụng, bài kiểm tra tốc độ sẽ trả về 'no connection'.
Nếu dữ liệu đang available, bài kiểm tra tốc độ cũng sẽ trả về tốc độ dữ liệu. Bất kỳ tốc độ nào dưới 'Excellent' đều được coi là chậm.
- Đường dẫn 2.1 kiểm tra các vấn đề dữ liệu di động không khả dụng.
- Đường dẫn 2.2 kiểm tra các vấn đề dữ liệu chậm.
## Đường dẫn 2.1: Khắc phục sự cố Dữ liệu Di động không khả dụng
### Bước 2.1.0: Kiểm tra xem user có đang gặp sự cố dữ liệu di động không khả dụng hay không

- Chạy bài kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'no connection', dữ liệu di động không khả dụng.
    - Làm theo Đường dẫn 2.1.
    - Sau khi vấn đề được giải quyết, nếu tốc độ không phải là 'Excellent', hãy làm theo Đường dẫn 2.2.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động đang available.
    - Nếu tốc độ là 'Excellent', user không gặp sự cố dữ liệu di động.
    - Đối với bất kỳ tốc độ khác nào ('Poor', 'Fair', 'Good'), dữ liệu di động có thể chậm và bạn phải làm theo Đường dẫn 2.2.
### Bước 2.1.1: Xác minh Sự cố Dịch vụ
Kiểm tra xem điện thoại có dịch vụ di động không. Dữ liệu di động cần ít nhất một số kết nối mạng di động.

- Làm theo các bước khắc phục sự cố Đường dẫn 1 (Vấn đề không có dịch vụ / Không có kết nối) trước.
- Khi bạn đã xác nhận rằng dịch vụ đang available, hãy kiểm tra xem sự cố dữ liệu di động có còn tồn tại không.
    - Chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, tiếp tục Bước 2.1.2.
### Bước 2.1.2: Xác minh xem user có đang đi du lịch không
Kiểm tra xem user có ở bên ngoài khu vực dịch vụ thông thường của họ không.

**Nếu Người dùng không đi du lịch:**
- Tiếp tục Bước 2.1.3

**Nếu Người dùng đang đi du lịch:**
- Xác minh xem Chuyển vùng dữ liệu có được bật để cho phép sử dụng dữ liệu trên các mạng khác hay không.


**Nếu Chuyển vùng Dữ liệu TẮT:**
- Bật Chuyển vùng Dữ liệu
- Chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.

**Nếu Chuyển vùng Dữ liệu BẬT nhưng không hoạt động:**
- Xác minh rằng dòng dịch vụ liên quan đến số điện thoại mà user cung cấp đã được kích hoạt chuyển vùng.
    - Nếu dòng dịch vụ không được kích hoạt chuyển vùng, hãy kích hoạt nó miễn phí cho user
- Chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, tiếp tục Bước 2.1.3.

**Nếu Chuyển vùng Dữ liệu BẬT và được kích hoạt nhưng kết nối không hoạt động:**
- Tiếp tục Bước 2.1.3
### Bước 2.1.3: Kiểm tra Cài đặt Dữ liệu Di động
**Nếu Dữ liệu Di động TẮT:**
- Bật Dữ liệu Di động
- Chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, tiếp tục Bước 2.1.4.

**Nếu Dữ liệu Di động BẬT nhưng không hoạt động:**
- Tiếp tục Bước 2.1.4
### Bước 2.1.4: Kiểm tra Mức sử dụng Dữ liệu
Kiểm tra xem, đối với dòng dịch vụ liên quan đến số điện thoại mà user cung cấp, mức sử dụng dữ liệu của user đã vượt quá giới hạn dữ liệu của họ chưa.

**Nếu Mức sử dụng Dữ liệu đã VƯỢT QUÁ:**
- Kiểm tra xem user có cho phép thay đổi gói cước khác hoặc nạp thêm dữ liệu không.
- Làm theo hướng dẫn trong chính sách chính để biết thêm thông tin về việc nạp thêm dữ liệu và thay đổi gói cước.
- Nếu bạn có thể nạp thêm dữ liệu hoặc thay đổi gói cước có giới hạn dữ liệu cao hơn:
    - Chạy lại bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, chuyển cho hỗ trợ kỹ thuật.
- Nếu bạn không thể nạp thêm dữ liệu hoặc thay đổi gói cước có giới hạn dữ liệu cao hơn (không được phép hoặc user không muốn):
    - Leo thang cho hỗ trợ kỹ thuật.

**Nếu Mức sử dụng Dữ liệu KHÔNG VƯỢT QUÁ:**
- Chạy bài kiểm tra tốc độ và kiểm tra kết nối dữ liệu.
    - Nếu vẫn không có kết nối, chuyển cho hỗ trợ kỹ thuật.
## Đường dẫn 2.2: Khắc phục sự cố Dữ liệu Di động chậm
### Bước 2.2.0: Kiểm tra xem user có đang gặp sự cố dữ liệu chậm hay không
Khi dữ liệu di động đang available nhưng tốc độ là bất kỳ thứ gì khác 'Excellent', user đang gặp sự cố dữ liệu chậm.
- Chạy bài kiểm tra tốc độ.
- Nếu bài kiểm tra tốc độ trả về 'no connection', dữ liệu di động không khả dụng.
    - Làm theo Đường dẫn 2.1.
- Nếu bài kiểm tra tốc độ trả về tốc độ dữ liệu, dữ liệu di động đang available.
    - Nếu tốc độ là 'Excellent', user không gặp sự cố dữ liệu chậm.
    - Đối với bất kỳ tốc độ khác nào ('Poor', 'Fair', 'Good'), dữ liệu di động có thể chậm và bạn phải làm theo Đường dẫn 2.2.
### Bước 2.2.1: Kiểm tra Cài đặt Hạn chế Dữ liệu
Kiểm tra xem có cài đặt nào đang giới hạn mức sử dụng dữ liệu của họ không, như chế độ Trình tiết kiệm dữ liệu.

**Nếu Trình tiết kiệm Dữ liệu đang BẬT:**
- Tắt chế độ Trình tiết kiệm dữ liệu
- Chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Excellent' không.
    - Nếu không phải trường hợp này, tiếp tục Bước 6.
**Nếu Trình tiết kiệm Dữ liệu đang TẮT:**
- Tiếp tục Bước 6
### Bước 2.2.2: Kiểm tra Tùy chọn Chế độ Mạng
Kiểm tra xem loại mạng di động nào mà điện thoại ưu tiên. Sử dụng các chế độ cũ hơn như 2G/3G có thể làm giảm đáng kể tốc độ.

**Nếu được đặt thành các loại mạng cũ hơn (chỉ 2G/3G):**
- Thay đổi tùy chọn mạng sang tùy chọn bao gồm 5G
- Chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Excellent' không.
    - Nếu không phải trường hợp này, tiếp tục Bước 7.

**Nếu đã ở cài đặt tối ưu:**
- Tiếp tục Bước 7
### Bước 2.2.3: Kiểm tra VPN Đang hoạt động
Kiểm tra xem VPN (Mạng riêng ảo) có đang đang hoạt động không, điều này có thể ảnh hưởng đến chất lượng kết nối.

**Nếu VPN đang đang hoạt động:**
- Tắt kết nối VPN hiện tại
- Chạy lại bài kiểm tra tốc độ và kiểm tra xem tốc độ có cải thiện lên 'Excellent' không.
    - Nếu không phải trường hợp này, leo thang cho hỗ trợ kỹ thuật.

**Nếu không có VPN hoặc ngắt kết nối không giúp ích gì:**
- Leo thang cho hỗ trợ kỹ thuật.
## Đường dẫn 3: Khắc phục sự cố MMS (Nhắn tin Hình ảnh/Nhóm)
### Bước 3.0: Kiểm tra xem user có đang gặp sự cố MMS hay không
Khi MMS không hoạt động, user sẽ không thể gửi hoặc nhận tin nhắn hình ảnh.

- Kiểm tra xem có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định không.
    - Nếu việc này hoạt động, user không gặp sự cố MMS.
    - Nếu việc này không hoạt động, tiếp tục Bước 3.1.
### Bước 3.1: Xác minh Trạng thái Dịch vụ Mạng
Kiểm tra xem điện thoại có dịch vụ di động không. MMS cần ít nhất một số kết nối mạng di động.

- Làm theo các bước khắc phục sự cố Đường dẫn 1 (Vấn đề không có dịch vụ / Không có kết nối) trước.
- Sau khi bạn đã xác nhận rằng dịch vụ đang available, hãy kiểm tra xem sự cố còn tồn tại không:
    - Kiểm tra xem có thể gửi tin nhắn MMS bằng ứng dụng nhắn tin mặc định không.

**Nếu dịch vụ đang available:**
- Tiếp tục Bước 3.2
### Bước 3.2: Xác minh Trạng thái Dữ liệu Di động
Dữ liệu di động là cần thiết cho MMS.

- Sử dụng các bước khắc phục sự cố Đường dẫn 2.1 (Dữ liệu Di động không khả dụng) để kiểm tra xem kết nối dữ liệu di động có hoạt động không. Đừng lo lắng về tốc độ, hãy tập trung vào kết nối.
- Sau khi bạn đã xác nhận rằng kết nối dữ liệu di động đang hoạt động, hãy kiểm tra xem sự cố MMS có còn tồn tại không:
    - Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.
### Bước 3.3: Kiểm tra Công nghệ Mạng
Kiểm tra xem loại mạng di động nào mà điện thoại đang đã kết nối kết nối. MMS cần công nghệ ít nhất là 3G trở lên.

**Nếu đã kết nối với mạng 2G chỉ:**
- Thay đổi chế độ mạng để bao gồm ít nhất 3G/4G/5G
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu đang sử dụng mạng 3G trở lên:**
- Tiếp tục Bước 3.4
### Bước 3.4: Kiểm tra Trạng thái Wi-Fi Calling
Kiểm tra xem Wi-Fi Calling có được bật không, vì nó có thể can thiệp vào chức năng MMS.

**Nếu Wi-Fi Calling đang BẬT:**
- Tắt Wi-Fi Calling
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu Wi-Fi Calling đang TẮT hoặc tắt nó đi không giúp ích gì:**
- Tiếp tục Bước 3.5
### Bước 3.5: Xác minh Quyền Ứng dụng Nhắn tin
Kiểm tra xem ứng dụng nhắn tin mặc định có các quyền cần thiết không - cụ thể là cả quyền bộ nhớ và SMS.

**Nếu quyền bộ nhớ hoặc SMS đang bị mất:**
- Cấp cả hai quyền cần thiết cho ứng dụng nhắn tin
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu tất cả các quyền đã được cấp:**
- Tiếp tục Bước 3.6
### Bước 3.6: Kiểm tra Cài đặt APN
Kiểm tra các cài đặt kỹ thuật (APN) mà điện thoại sử dụng để kết nối với mạng dữ liệu di động của nhà mạng.

**Đặc biệt kiểm tra:**
- Cấu hình URL MMSC (phải có mặt để MMS hoạt động)

**Nếu URL MMSC đang bị mất:**
- Đặt lại cài đặt APN về mặc định của nhà mạng
- Thử gửi lại tin nhắn MMS bằng ứng dụng nhắn tin mặc định một lần nữa.

**Nếu các vấn đề vẫn tiếp diễn sau khi kiểm tra tất cả các điều trên:**
- Leo thang cho hỗ trợ kỹ thuật