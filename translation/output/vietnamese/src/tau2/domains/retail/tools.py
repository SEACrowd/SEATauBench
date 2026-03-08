"""Bộ công cụ cho lĩnh vực bán lẻ."""

import json
from typing import List

from tau2.domains.retail.data_model import (
    GiftCard,
    Order,
    OrderPayment,
    PaymentMethod,
    Product,
    RetailDB,
    User,
    UserAddress,
    Variant,
)
from tau2.domains.retail.utils import RETAIL_DB_PATH
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class RetailTools(ToolKitBase):  # Tools
    """Tất cả các công cụ cho lĩnh vực bán lẻ."""

    db: RetailDB

    def __init__(self, db: RetailDB) -> None:
        super().__init__(db)

    def _get_order(self, order_id: str) -> Order:
        """Lấy đơn hàng từ cơ sở dữ liệu.

        Args:
            order_id: ID đơn hàng, chẳng hạn như '#W0000000'. Lưu ý có ký hiệu '#' ở đầu ID đơn hàng.

        Returns:
            Đơn hàng.

        Raises:
            ValueError: Nếu không tìm thấy đơn hàng.
        """
        if order_id not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[order_id]

    def _get_user(self, user_id: str) -> User:
        """Lấy người dùng từ cơ sở dữ liệu.

        Args:
            user_id: ID người dùng, chẳng hạn như 'sara_doe_496'.

        Returns:
            Người dùng.

        Raises:
            ValueError: Nếu không tìm thấy người dùng.
        """
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    def _get_product(self, product_id: str) -> Product:
        """Lấy sản phẩm từ cơ sở dữ liệu.

        Args:
            product_id: ID sản phẩm, chẳng hạn như '6086499569'. Lưu ý ID sản phẩm khác với ID mặt hàng.

        Returns:
            Sản phẩm.

        Raises:
            ValueError: Nếu không tìm thấy sản phẩm.
        """
        if product_id not in self.db.products:
            raise ValueError("Product not found")
        return self.db.products[product_id]

    def _get_variant(self, product_id: str, variant_id: str) -> Variant:
        """Lấy biến thể từ cơ sở dữ liệu.

        Args:
            product_id: ID sản phẩm, chẳng hạn như '6086499569'. Lưu ý ID sản phẩm khác với ID mặt hàng.
            variant_id: ID biến thể, chẳng hạn như '1008292230'.

        Returns:
            Biến thể.

        Raises:
            ValueError: Nếu không tìm thấy biến thể.
        """
        product = self._get_product(product_id)
        if variant_id not in product.variants:
            raise ValueError("Variant not found")
        return product.variants[variant_id]

    def _get_payment_method(
        self, user_id: str, payment_method_id: str
    ) -> PaymentMethod:
        """Lấy phương thức thanh toán từ cơ sở dữ liệu.

        Args:
            payment_method_id: ID phương thức thanh toán, chẳng hạn như 'gift_card_0000000' hoặc 'credit_card_0000000'.

        Returns:
            Phương thức thanh toán.

        Raises:
            ValueError: Nếu không tìm thấy phương thức thanh toán.
        """
        user = self._get_user(user_id)
        if payment_method_id not in user.payment_methods:
            raise ValueError("Payment method not found")
        return user.payment_methods[payment_method_id]

    def _is_pending_order(self, order: Order) -> bool:
        """Kiểm tra xem đơn hàng có phải là pending hay không. Đây không phải là kiểm tra nghiêm ngặt và không предназнач dùng cho modify_items trong các đơn hàng pending.

        Args:
            order: Đơn hàng.
        """
        return "pending" in order.status

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """
        Tính kết quả của một biểu thức toán học.

        Args:
            expression: Biểu thức toán học cần tính, chẳng hạn như '2 + 2'. Biểu thức có thể chứa số, toán tử (+, -, *, /), dấu ngoặc đơn và khoảng trắng.

        Returns:
            Kết quả của biểu thức toán học.

        Raises:
            ValueError: Nếu biểu thức không hợp lệ.
        """
        if not all(char in "0123456789+-*/(). " for char in expression):
            raise ValueError("Invalid characters in expression")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))

    @is_tool(ToolType.WRITE)
    def cancel_pending_order(self, order_id: str, reason: str) -> Order:
        """Hủy một đơn hàng pending. Nếu đơn hàng đã được xử lý hoặc đã giao,
        thì không thể hủy. Nhân viên cần giải thích chi tiết việc hủy
        và yêu cầu người dùng xác nhận rõ ràng (có/không) để tiếp tục. Nếu người dùng xác nhận,
        trạng thái đơn hàng sẽ được đổi thành 'cancelled' và khoản thanh toán sẽ được hoàn tiền.
        Khoản hoàn sẽ được cộng ngay vào số dư thẻ quà tặng của người dùng nếu thanh toán
        được thực hiện bằng thẻ quà tặng; nếu không, việc hoàn tiền sẽ mất 5-7 ngày làm việc để xử lý.
        Hàm trả về chi tiết đơn hàng sau khi hủy.

        Args:
            order_id: Mã đơn hàng, chẳng hạn như '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.
            reason: Lý do hủy, phải là 'no longer needed' hoặc 'ordered by mistake'.

        Returns:
            Order: Chi tiết đơn hàng sau khi hủy.
        """
        # check order exists and is pending
        order = self._get_order(order_id)
        if order.status != "pending":
            raise ValueError("Non-pending order cannot be cancelled")

        # check reason
        if reason not in {"no longer needed", "ordered by mistake"}:
            raise ValueError("Invalid reason")

        # handle refund
        refunds = []
        for payment in order.payment_history:
            payment_id = payment.payment_method_id
            refund = OrderPayment(
                transaction_type="refund",
                amount=payment.amount,
                payment_method_id=payment_id,
            )
            refunds.append(refund)
            user = self._get_user(order.user_id)
            payment_method = self._get_payment_method(user.user_id, payment_id)
            if isinstance(payment_method, GiftCard):  # refund to gift card immediately
                payment_method.balance += payment.amount
                payment_method.balance = round(payment_method.balance, 2)

        # update order status
        order.status = "cancelled"
        order.cancel_reason = reason
        order.payment_history.extend(refunds)

        return order

    @is_tool(ToolType.WRITE)
    def exchange_delivered_order_items(
        self,
        order_id: str,
        item_ids: List[str],
        new_item_ids: List[str],
        payment_method_id: str,
    ) -> Order:
        """Đổi các mặt hàng trong một đơn hàng đã giao sang các mặt hàng mới cùng loại sản phẩm.
        Với đơn hàng đã giao, việc trả hàng hoặc đổi hàng chỉ có thể được nhân viên thực hiện một lần.
        Nhân viên cần giải thích chi tiết việc đổi và yêu cầu người dùng xác nhận rõ ràng (có/không) để tiếp tục.

        Args:
            order_id: Mã đơn hàng, chẳng hạn như '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.
            item_ids: Các mã mặt hàng cần đổi, mỗi mã như '1008292230'. Danh sách có thể có các mặt hàng trùng lặp.
            new_item_ids: Các mã mặt hàng dùng để đổi sang, mỗi mã như '1008292230'.
                         Danh sách có thể có các mặt hàng trùng lặp. Mỗi mã mặt hàng mới phải khớp với mã mặt hàng
                         ở cùng vị trí và thuộc cùng một sản phẩm.
            payment_method_id: Mã phương thức thanh toán dùng để thanh toán hoặc nhận hoàn tiền cho chênh lệch giá mặt hàng,
                             chẳng hạn như 'gift_card_0000000' hoặc 'credit_card_0000000'. Các mã này có thể được tra cứu
                             từ thông tin người dùng hoặc chi tiết đơn hàng.

        Returns:
            Order: Chi tiết đơn hàng sau khi đổi.

        Raises:
            ValueError: Nếu đơn hàng chưa được giao.
            ValueError: Nếu các mặt hàng cần đổi không tồn tại.
            ValueError: Nếu các mặt hàng mới không tồn tại hoặc không khớp với các mặt hàng cũ.
            ValueError: Nếu số lượng mặt hàng cần đổi không khớp.
        """
        # check order exists and is delivered
        order = self._get_order(order_id)
        if order.status != "delivered":
            raise ValueError("Non-delivered order cannot be exchanged")

        # check the items to be exchanged exist. There can be duplicate items in the list.
        all_item_ids = [item.item_id for item in order.items]
        for item_id in item_ids:
            if item_ids.count(item_id) > all_item_ids.count(item_id):
                raise ValueError(f"Number of {item_id} not found.")

        # check new items exist and match old items and are available
        if len(item_ids) != len(new_item_ids):
            raise ValueError("The number of items to be exchanged should match.")

        diff_price = 0
        for item_id, new_item_id in zip(item_ids, new_item_ids):
            item = next((item for item in order.items if item.item_id == item_id), None)
            if item is None:
                raise ValueError(f"Item {item_id} not found")
            product_id = item.product_id
            variant = self._get_variant(product_id, new_item_id)
            if not variant.available:
                raise ValueError(f"New item {new_item_id} not found or available")

            old_price = item.price
            new_price = variant.price
            diff_price += new_price - old_price

        diff_price = round(diff_price, 2)

        # check payment method exists and can cover the price difference if gift card
        payment_method = self._get_payment_method(order.user_id, payment_method_id)

        if isinstance(payment_method, GiftCard) and payment_method.balance < diff_price:
            raise ValueError(
                "Insufficient gift card balance to pay for the price difference"
            )

        # modify the order
        order.status = "exchange requested"
        order.exchange_items = sorted(item_ids)
        order.exchange_new_items = sorted(new_item_ids)
        order.exchange_payment_method_id = payment_method_id
        order.exchange_price_difference = diff_price

        return order

    @is_tool(ToolType.READ)
    def find_user_id_by_name_zip(
        self, first_name: str, last_name: str, zip: str
    ) -> str:
        """Tìm user id theo tên, họ và mã zip. Nếu không tìm thấy người dùng, hàm
        sẽ trả về một thông báo lỗi. Theo mặc định, hãy tìm user id theo email, và chỉ gọi hàm này
        nếu không tìm thấy người dùng bằng email hoặc người dùng không nhớ email.

        Args:
            first_name: Tên của khách hàng, chẳng hạn như 'John'.
            last_name: Họ của khách hàng, chẳng hạn như 'Doe'.
            zip: Mã zip của khách hàng, chẳng hạn như '12345'.

        Returns:
            str: User id nếu tìm thấy, nếu không thì là thông báo lỗi.

        Raises:
            ValueError: Nếu không tìm thấy người dùng.
        """
        for user_id, user in self.db.users.items():
            if (
                user.name.first_name.lower() == first_name.lower()
                and user.name.last_name.lower() == last_name.lower()
                and user.address.zip == zip
            ):
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def find_user_id_by_email(self, email: str) -> str:
        """Tìm user id theo email. Nếu không tìm thấy người dùng, hàm sẽ trả về một thông báo lỗi.

        Args:
            email: Email của người dùng, chẳng hạn như 'something@example.com'.

        Returns:
            str: User id nếu tìm thấy, nếu không thì là thông báo lỗi.

        Raises:
            ValueError: Nếu không tìm thấy người dùng.
        """
        for user_id, user in self.db.users.items():
            if user.email.lower() == email.lower():
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> Order:
        """Lấy trạng thái và chi tiết của một đơn hàng.

        Args:
            order_id: Mã đơn hàng, chẳng hạn như '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.

        Returns:
            Order: Chi tiết đơn hàng.

        Raises:
            ValueError: Nếu không tìm thấy đơn hàng.
        """
        order = self._get_order(order_id)
        return order

    @is_tool(ToolType.READ)
    def get_product_details(self, product_id: str) -> Product:
        """Lấy chi tiết tồn kho của một sản phẩm.

        Args:
            product_id: Mã sản phẩm, chẳng hạn như '6086499569'. Lưu ý mã sản phẩm khác với mã mặt hàng (item id).

        Returns:
            Product: Chi tiết sản phẩm.

        Raises:
            ValueError: Nếu không tìm thấy sản phẩm.
        """
        product = self._get_product(product_id)
        return product

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> User:
        """Lấy chi tiết của một người dùng, bao gồm các đơn hàng của họ.

        Args:
            user_id: User id, chẳng hạn như 'sara_doe_496'.

        Returns:
            User: Chi tiết người dùng.

        Raises:
            ValueError: Nếu không tìm thấy người dùng.
        """
        user = self._get_user(user_id)
        return user

    @is_tool(ToolType.READ)
    def list_all_product_types(self) -> str:
        """Liệt kê tên và mã sản phẩm (product id) của tất cả các loại sản phẩm.
        Mỗi loại sản phẩm có nhiều mặt hàng khác nhau với mã mặt hàng (item id) và các tuỳ chọn riêng.
        Trong cửa hàng chỉ có 50 loại sản phẩm.

        Trả về:
            str: Một chuỗi JSON ánh xạ tên sản phẩm tới mã sản phẩm của chúng, được sắp xếp theo thứ tự chữ cái theo tên.
        """
        product_dict = {
            product.name: product.product_id for product in self.db.products.values()
        }
        return json.dumps(product_dict, sort_keys=True)

    @is_tool(ToolType.WRITE)
    def modify_pending_order_address(
        self,
        order_id: str,
        address1: str,
        address2: str,
        city: str,
        state: str,
        country: str,
        zip: str,
    ) -> Order:
        """Sửa đổi địa chỉ giao hàng của một đơn hàng pending. Tác nhân cần giải thích chi tiết thay đổi và yêu cầu người dùng xác nhận rõ ràng (yes/no) để tiếp tục.

        Args:
            order_id: Mã đơn hàng, ví dụ '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.
            address1: Dòng đầu của địa chỉ, ví dụ '123 Main St'.
            address2: Dòng thứ hai của địa chỉ, ví dụ 'Apt 1' hoặc ''.
            city: Thành phố, ví dụ 'San Francisco'.
            state: Bang/tỉnh, ví dụ 'CA'.
            country: Quốc gia, ví dụ 'USA'.
            zip: Mã bưu chính, ví dụ '12345'.

        Trả về:
            Order: Chi tiết đơn hàng sau khi sửa đổi.

        Raises:
            ValueError: Nếu đơn hàng không ở trạng thái pending.
        """
        # Check if the order exists and is pending
        order = self._get_order(order_id)
        if not self._is_pending_order(order):
            raise ValueError("Non-pending order cannot be modified")

        # Modify the address
        order.address = UserAddress(
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            country=country,
            zip=zip,
        )
        return order

    @is_tool(ToolType.WRITE)
    def modify_pending_order_items(
        self,
        order_id: str,
        item_ids: List[str],
        new_item_ids: List[str],
        payment_method_id: str,
    ) -> Order:
        """Sửa đổi các mặt hàng trong một đơn hàng pending sang các mặt hàng mới cùng loại sản phẩm. Đối với một đơn hàng pending, hàm này chỉ có thể được gọi một lần. Tác nhân cần giải thích chi tiết việc đổi hàng và yêu cầu người dùng xác nhận rõ ràng (yes/no) để tiếp tục.

        Args:
            order_id: Mã đơn hàng, ví dụ '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.
            item_ids: Các mã mặt hàng cần được sửa đổi, mỗi mã ví dụ '1008292230'. Danh sách có thể có mặt hàng trùng lặp.
            new_item_ids: Các mã mặt hàng mới để thay thế, mỗi mã ví dụ '1008292230'. Danh sách có thể có mặt hàng trùng lặp. Mỗi mã mặt hàng mới phải khớp với mã mặt hàng ở cùng vị trí và thuộc cùng một sản phẩm.
            payment_method_id: Mã phương thức thanh toán để thanh toán hoặc nhận hoàn tiền cho chênh lệch giá mặt hàng, ví dụ 'gift_card_0000000' hoặc 'credit_card_0000000'. Có thể tra cứu từ người dùng hoặc chi tiết đơn hàng.

        Trả về:
            Order: Chi tiết đơn hàng sau khi sửa đổi.

        Raises:
            ValueError: Nếu đơn hàng không ở trạng thái pending.
            ValueError: Nếu các mặt hàng cần sửa đổi không tồn tại.
            ValueError: Nếu các mặt hàng mới không tồn tại hoặc không khớp với các mặt hàng cũ.
            ValueError: Nếu số lượng mặt hàng cần sửa đổi không khớp.
        """

        # Check if the order exists and is pending
        order = self._get_order(order_id)
        if order.status != "pending":
            raise ValueError("Non-pending order cannot be modified")

        # Check if the items to be modified exist. There can be duplicate items in the list.
        all_item_ids = [item.item_id for item in order.items]
        for item_id in item_ids:
            if item_ids.count(item_id) > all_item_ids.count(item_id):
                raise ValueError(f"{item_id} not found")

        # Check new items exist, match old items, and are available
        if len(item_ids) != len(new_item_ids):
            raise ValueError("The number of items to be exchanged should match")

        diff_price = 0
        for item_id, new_item_id in zip(item_ids, new_item_ids):
            if item_id == new_item_id:
                raise ValueError(
                    "The new item id should be different from the old item id"
                )
            item = next((item for item in order.items if item.item_id == item_id), None)
            if item is None:
                raise ValueError(f"Item {item_id} not found")
            product_id = item.product_id
            variant = self._get_variant(product_id, new_item_id)
            if not variant.available:
                raise ValueError(f"New item {new_item_id} not found or available")

            old_price = item.price
            new_price = variant.price
            diff_price += new_price - old_price

        # Check if the payment method exists
        payment_method = self._get_payment_method(order.user_id, payment_method_id)

        # If the new item is more expensive, check if the gift card has enough balance
        if isinstance(payment_method, GiftCard) and payment_method.balance < diff_price:
            raise ValueError("Insufficient gift card balance to pay for the new item")

        # Handle the payment or refund
        order.payment_history.append(
            OrderPayment(
                transaction_type="payment" if diff_price > 0 else "refund",
                amount=abs(diff_price),
                payment_method_id=payment_method_id,
            )
        )
        if isinstance(payment_method, GiftCard):
            payment_method.balance -= diff_price
            payment_method.balance = round(payment_method.balance, 2)

        # Modify the order
        for item_id, new_item_id in zip(item_ids, new_item_ids):
            item = next((item for item in order.items if item.item_id == item_id), None)
            if item is None:
                raise ValueError(f"Item {item_id} not found")
            item.item_id = new_item_id
            item.price = variant.price
            item.options = variant.options
        order.status = "pending (item modified)"

        return order

    @is_tool(ToolType.WRITE)
    def modify_pending_order_payment(
        self,
        order_id: str,
        payment_method_id: str,
    ) -> Order:
        """Sửa đổi phương thức thanh toán của một đơn hàng pending. Tác nhân cần giải thích chi tiết thay đổi và yêu cầu người dùng xác nhận rõ ràng (yes/no) để tiếp tục.

        Args:
            order_id: Mã đơn hàng, ví dụ '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.
            payment_method_id: Mã phương thức thanh toán để thanh toán hoặc nhận hoàn tiền cho chênh lệch giá mặt hàng, ví dụ 'gift_card_0000000' hoặc 'credit_card_0000000'. Có thể tra cứu từ người dùng hoặc chi tiết đơn hàng.

        Trả về:
            Order: Chi tiết đơn hàng sau khi sửa đổi.

        Raises:
            ValueError: Nếu đơn hàng không ở trạng thái pending.
            ValueError: Nếu phương thức thanh toán không tồn tại.
            ValueError: Nếu lịch sử thanh toán có nhiều hơn một khoản thanh toán.
            ValueError: Nếu phương thức thanh toán mới trùng với phương thức hiện tại.
        """
        order = self._get_order(order_id)

        # Check if the order exists and is pending
        if not self._is_pending_order(order):
            raise ValueError("Non-pending order cannot be modified")

        # Check if the payment method exists
        payment_method = self._get_payment_method(order.user_id, payment_method_id)

        # Check that the payment history should only have one payment
        if (
            len(order.payment_history) != 1
            or order.payment_history[0].transaction_type != "payment"
        ):
            raise ValueError("There should be exactly one payment for a pending order")

        # Check that the payment method is different
        if order.payment_history[0].payment_method_id == payment_method_id:
            raise ValueError(
                "The new payment method should be different from the current one"
            )

        amount = order.payment_history[0].amount

        # Check if the new payment method has enough balance if it is a gift card
        if isinstance(payment_method, GiftCard) and payment_method.balance < amount:
            raise ValueError("Insufficient gift card balance to pay for the order")

        # Modify the payment method
        order.payment_history.extend(
            [
                OrderPayment(
                    transaction_type="payment",
                    amount=amount,
                    payment_method_id=payment_method_id,
                ),
                OrderPayment(
                    transaction_type="refund",
                    amount=amount,
                    payment_method_id=order.payment_history[0].payment_method_id,
                ),
            ]
        )

        # If payment is made by gift card, update the balance
        if isinstance(payment_method, GiftCard):
            payment_method.balance -= amount
            payment_method.balance = round(payment_method.balance, 2)

        # If refund is made to a gift card, update the balance
        old_payment_method = self._get_payment_method(
            order.user_id, order.payment_history[0].payment_method_id
        )
        if isinstance(old_payment_method, GiftCard):
            old_payment_method.balance += amount
            old_payment_method.balance = round(old_payment_method.balance, 2)

        return order

    @is_tool(ToolType.WRITE)
    def modify_user_address(
        self,
        user_id: str,
        address1: str,
        address2: str,
        city: str,
        state: str,
        country: str,
        zip: str,
    ) -> User:
        """Sửa đổi địa chỉ mặc định của một người dùng. Tác nhân cần giải thích chi tiết thay đổi và yêu cầu người dùng xác nhận rõ ràng (yes/no) để tiếp tục.

        Args:
            user_id: Mã người dùng, ví dụ 'sara_doe_496'.
            address1: Dòng đầu của địa chỉ, ví dụ '123 Main St'.
            address2: Dòng thứ hai của địa chỉ, ví dụ 'Apt 1' hoặc ''.
            city: Thành phố, ví dụ 'San Francisco'.
            state: Bang/tỉnh, ví dụ 'CA'.
            country: Quốc gia, ví dụ 'USA'.
            zip: Mã bưu chính, ví dụ '12345'.

        Trả về:
            User: Chi tiết người dùng sau khi sửa đổi.

        Raises:
            ValueError: Nếu không tìm thấy người dùng.
        """
        user = self._get_user(user_id)
        user.address = UserAddress(
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            country=country,
            zip=zip,
        )
        return user

    @is_tool(ToolType.WRITE)
    def return_delivered_order_items(
        self,
        order_id: str,
        item_ids: List[str],
        payment_method_id: str,
    ) -> Order:
        """Trả lại một số mặt hàng của một đơn hàng đã được giao.
        Trạng thái đơn hàng sẽ được chuyển thành 'return requested'.
        Tác nhân cần giải thích chi tiết việc trả hàng và yêu cầu người dùng xác nhận rõ ràng (yes/no) để tiếp tục.
        Người dùng sẽ nhận email tiếp theo hướng dẫn cách và nơi trả lại mặt hàng.

        Args:
            order_id: Mã đơn hàng, ví dụ '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.
            item_ids: Các mã mặt hàng cần trả lại, mỗi mã ví dụ '1008292230'. Danh sách có thể có mặt hàng trùng lặp.
            payment_method_id: Mã phương thức thanh toán để thanh toán hoặc nhận hoàn tiền cho chênh lệch giá mặt hàng, ví dụ 'gift_card_0000000' hoặc 'credit_card_0000000'.
                             Có thể tra cứu từ người dùng hoặc chi tiết đơn hàng.

        Trả về:
            Order: Chi tiết đơn hàng sau khi yêu cầu trả hàng.

        Raises:
            ValueError: Nếu đơn hàng không ở trạng thái delivered.
            ValueError: Nếu phương thức thanh toán không phải là phương thức thanh toán gốc hoặc thẻ quà tặng.
            ValueError: Nếu các mặt hàng cần trả lại không tồn tại.
        """
        order = self._get_order(order_id)
        if order.status != "delivered":
            raise ValueError("Non-delivered order cannot be returned")

        # Check if the payment method exists and is either the original payment method or a gift card
        user = self._get_user(order.user_id)
        payment_method = self._get_payment_method(user.user_id, payment_method_id)

        if (
            not isinstance(payment_method, GiftCard)
            and payment_method_id != order.payment_history[0].payment_method_id
        ):
            raise ValueError("Payment method should be the original payment method")

        # Check if the items to be returned exist (there could be duplicate items in either list)
        all_item_ids = [item.item_id for item in order.items]
        for item_id in item_ids:
            if item_ids.count(item_id) > all_item_ids.count(item_id):
                raise ValueError("Some item not found")

        # Update the order status
        order.status = "return requested"
        order.return_items = sorted(item_ids)
        order.return_payment_method_id = payment_method_id

        return order

    # @is_tool(ToolType.THINK)
    # def think(self, thought: str) -> str:
    #     """
    #     Use the tool to think about something.
    #     It will not obtain new information or change the database, but just append the thought to the log.
    #     Use it when complex reasoning or some cache memory is needed.

    #     Args:
    #         thought: A thought to think about.

    #     Returns:
    #         Empty string
    #     """
    #     return ""

    @is_tool(ToolType.GENERIC)
    def transfer_to_human_agents(self, summary: str) -> str:
        """
        Chuyển người dùng tới một nhân viên hỗ trợ, kèm theo bản tóm tắt vấn đề của người dùng.
        Chỉ chuyển nếu
         -  người dùng yêu cầu rõ ràng được gặp nhân viên hỗ trợ
         -  dựa trên chính sách và các công cụ sẵn có, bạn không thể giải quyết vấn đề của người dùng.

        Args:
            summary: Tóm tắt vấn đề của người dùng.

        Trả về:
            Một thông điệp cho biết người dùng đã được chuyển tới một nhân viên hỗ trợ.
        """
        return "Transfer successful"


if __name__ == "__main__":
    from tau2.domains.retail.utils import RETAIL_DB_PATH

    retail = RetailTools(RetailDB.load(RETAIL_DB_PATH))
    print(retail.get_statistics())
