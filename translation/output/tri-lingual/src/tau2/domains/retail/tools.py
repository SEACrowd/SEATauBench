"""
Toolkit for mixed-language retail tool descriptions.
"""

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
    """
    All tools for the retail domain.
    """

    db: RetailDB

    def __init__(self, db: RetailDB) -> None:
        super().__init__(db)

    def _get_order(self, order_id: str) -> Order:
        """
        Get the order from the database.
        
        Args:
            order_id: The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.
        
        Returns:
            The order.
        
        Raises:
            ValueError: If the order is not found.
        """
        if order_id not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[order_id]

    def _get_user(self, user_id: str) -> User:
        """
        Get the user from the database.
        
        Args:
            user_id: The user id, such as 'sara_doe_496'.
        
        Returns:
            The user.
        
        Raises:
            ValueError: If the user is not found.
        """
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    def _get_product(self, product_id: str) -> Product:
        """
        Get the product from the database.
        
        Args:
            product_id: The product id, such as '6086499569'. Be careful the product id is different from the item id.
        
        Returns:
            The product.
        
        Raises:
            ValueError: If the product is not found.
        """
        if product_id not in self.db.products:
            raise ValueError("Product not found")
        return self.db.products[product_id]

    def _get_item(self, item_id: str) -> Variant:
        """Get the item from the database.

        Args:
            item_id: The item id, such as '6086499569'. Be careful the item id is different from the product id.

        Returns:
            The item.

        Raises:
            ValueError: If the item is not found.
        """
        for _, product in self.db.products.items():
            if item_id in product.variants:
                return product.variants[item_id]

        raise ValueError("Item not found")
    
    def _get_variant(self, product_id: str, variant_id: str) -> Variant:
        """
        Get the variant from the database.
        
        Args:
            product_id: The product id, such as '6086499569'. Be careful the product id is different from the item id.
            variant_id: The variant id, such as '1008292230'.
        
        Returns:
            The variant.
        
        Raises:
            ValueError: If the variant is not found.
        """
        product = self._get_product(product_id)
        if variant_id not in product.variants:
            raise ValueError("Variant not found")
        return product.variants[variant_id]

    def _get_payment_method(
        self, user_id: str, payment_method_id: str
    ) -> PaymentMethod:
        """
        Get the payment method from the database.
        
        Args:
            payment_method_id: The payment method id, such as 'gift_card_0000000' or 'credit_card_0000000'.
        
        Returns:
            The payment method.
        
        Raises:
            ValueError: If the payment method is not found.
        """
        user = self._get_user(user_id)
        if payment_method_id not in user.payment_methods:
            raise ValueError("Payment method not found")
        return user.payment_methods[payment_method_id]

    def _is_pending_order(self, order: Order) -> bool:
        """
        Check if the order is pending. This is not a strict check, and not meant to be used for modify_items in pending orders.
        
        Args:
            order: The order.
        """
        return "pending" in order.status

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """
        Calculate the result of a mathematical expression.
        
        Args:
            expression: The mathematical expression to calculate, such as '2 + 2'. The expression can contain numbers, operators (+, -, *, /), parentheses, and spaces.
        
        Returns:
            The result of the mathematical expression.
        
        Raises:
            ValueError: If the expression is invalid.
        """
        if not all(char in "0123456789+-*/(). " for char in expression):
            raise ValueError("Invalid characters in expression")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))

    @is_tool(ToolType.WRITE)
    def cancel_pending_order(self, order_id: str, reason: str) -> Order:
        """
        ยกเลิกคำสั่งซื้อ pending หากคำสั่งซื้อได้รับการดำเนินการหรือจัดส่งแล้ว จะไม่สามารถยกเลิกได้ เอเจนต์ต้องอธิบายรายละเอียดการยกเลิกและขอการยืนยันจากผู้ใช้อย่างชัดเจน (ใช่/ไม่) เพื่อดำเนินการต่อ หากผู้ใช้ยืนยัน สถานะคำสั่งซื้อจะถูกเปลี่ยนเป็น 'cancelled' และจะทำการคืนเงิน โดยเงินคืนจะถูกเพิ่มเข้ายอดคงเหลือบัตรของขวัญของผู้ใช้ทันที หากชำระด้วยบัตรของขวัญ มิฉะนั้นการคืนเงินอาจใช้เวลา 5-7 วันทำการ ฟังก์ชันจะส่งคืนรายละเอียดคำสั่งซื้อหลังการยกเลิก
        
        Args:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ด้านหน้ารหัสคำสั่งซื้อ
            reason: เหตุผลในการยกเลิก ซึ่งต้องเป็น 'no longer needed' หรือ 'ordered by mistake'
        
        Returns:
            Order: รายละเอียดคำสั่งซื้อหลังการยกเลิก
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
        """
        แลกเปลี่ยนสินค้าในคำสั่งซื้อที่จัดส่งแล้วเป็นสินค้าใหม่ที่เป็นประเภทผลิตภัณฑ์เดียวกัน สำหรับคำสั่งซื้อที่จัดส่งแล้ว การคืนหรือแลกเปลี่ยนสามารถทำได้เพียงครั้งเดียวโดยเอเจนต์ เอเจนต์ต้องอธิบายรายละเอียดการแลกเปลี่ยนและขอการยืนยันจากผู้ใช้อย่างชัดเจน (ใช่/ไม่) เพื่อดำเนินการต่อ
        
        Args:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ด้านหน้ารหัสคำสั่งซื้อ
            item_ids: รหัสรายการสินค้าที่ต้องการแลกเปลี่ยน แต่ละรายการเช่น '1008292230' อาจมีรายการซ้ำในลิสต์ได้
            new_item_ids: รหัสรายการสินค้าที่จะใช้แลกเปลี่ยน แต่ละรายการเช่น '1008292230' อาจมีรายการซ้ำในลิสต์ได้ รหัสรายการสินค้าใหม่แต่ละรายการต้องตรงกับรหัสรายการสินค้าเดิมในตำแหน่งเดียวกันและเป็นผลิตภัณฑ์เดียวกัน
            payment_method_id: รหัสวิธีชำระเงินที่ใช้ชำระหรือรับเงินคืนสำหรับส่วนต่างราคาสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000' สามารถดูได้จากรายละเอียดผู้ใช้หรือคำสั่งซื้อ
        
        Returns:
            Order: รายละเอียดคำสั่งซื้อหลังการแลกเปลี่ยน
        
        Raises:
            ValueError: หากคำสั่งซื้อยังไม่ถูกจัดส่ง
            ValueError: หากไม่มีสินค้าที่ต้องการแลกเปลี่ยน
            ValueError: หากสินค้าใหม่ไม่มีอยู่หรือไม่ตรงกับสินค้าเดิม
            ValueError: หากจำนวนสินค้าที่จะแลกเปลี่ยนไม่ตรงกัน
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
        """
        Tìm user id theo tên, họ và mã zip. Theo mặc định, hãy tìm user id theo email, và chỉ gọi hàm này nếu không tìm thấy người dùng bằng email hoặc người dùng không nhớ email.
        
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
        """
        Tìm user id theo email. Nếu không tìm thấy người dùng, hàm sẽ trả về một thông báo lỗi.
        
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
        """
        Get the status and details of an order.
        
        Args:
            order_id: The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.
        
        Returns:
            Order: The order details.
        
        Raises:
            ValueError: If the order is not found.
        """
        order = self._get_order(order_id)
        return order

    @is_tool(ToolType.READ)
    def get_product_details(self, product_id: str) -> Product:
        """
        Get the inventory details of a product.
        
        Args:
            product_id: The product id, such as '6086499569'. Be careful the product id is different from the item id.
        
        Returns:
            Product: The product details.
        
        Raises:
            ValueError: If the product is not found.
        """
        product = self._get_product(product_id)
        return product

    @is_tool(ToolType.READ)
    def get_item_details(self, item_id: str) -> Variant:
        """รับรายละเอียดสินค้าคงคลังของรายการสินค้า

        อาร์กิวเมนต์:
            item_id: รหัสรายการสินค้า เช่น '6086499569' โปรดระวังว่ารหัสรายการสินค้าแตกต่างจากรหัสสินค้า

        คืนค่า:
            Variant: รายละเอียดรายการสินค้า

        ข้อยกเว้น:
            ValueError: หากไม่พบรายการสินค้า
        """
        item = self._get_item(item_id)
        return item

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> User:
        """
        รับรายละเอียดของผู้ใช้ รวมถึงคำสั่งซื้อของผู้ใช้
        
        Args:
            user_id: รหัสผู้ใช้ เช่น 'sara_doe_496'
        
        Returns:
            User: รายละเอียดผู้ใช้
        
        Raises:
            ValueError: หากไม่พบผู้ใช้
        """
        user = self._get_user(user_id)
        return user

    @is_tool(ToolType.READ)
    def list_all_product_types(self) -> str:
        """
        Liệt kê tên và mã sản phẩm (product id) của tất cả các loại sản phẩm. Mỗi loại sản phẩm có nhiều mặt hàng khác nhau với mã mặt hàng (item id) và các tuỳ chọn riêng. Trong cửa hàng chỉ có 50 loại sản phẩm.
        
        Returns:
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
        """
        แก้ไขที่อยู่จัดส่งของคำสั่งซื้อ pending ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้อย่างชัดเจน (yes/no) ก่อนดำเนินการต่อ
        
        Args:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ที่ต้นรหัสคำสั่งซื้อ
            address1: บรรทัดแรกของที่อยู่ เช่น '123 Main St'
            address2: บรรทัดที่สองของที่อยู่ เช่น 'Apt 1' หรือ ''
            city: เมือง เช่น 'San Francisco'
            state: รัฐ เช่น 'CA'
            country: ประเทศ เช่น 'USA'
            zip: รหัสไปรษณีย์ เช่น '12345'
        
        Returns:
            Order: รายละเอียดคำสั่งซื้อหลังการแก้ไข
        
        Raises:
            ValueError: หากคำสั่งซื้อไม่ใช่ pending
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
        """
        Modify items in a pending order to new items of the same product type. For a pending order, this function can only be called once. The agent needs to explain the exchange detail and ask for explicit user confirmation (yes/no) to proceed.
        
        Args:
            order_id: The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.
            item_ids: The item ids to be modified, each such as '1008292230'. There could be duplicate items in the list.
            new_item_ids: The item ids to modify to, each such as '1008292230'. There could be duplicate items in the list. Each new item id should match the old item id in the same position and be of the same product.
            payment_method_id: The payment method id to pay or receive refund for the item price difference, such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details.
        
        Returns:
            Order: The order details after the modification.
        
        Raises:
            ValueError: If the order is not pending.
            ValueError: If the items to be modified do not exist.
            ValueError: If the new items do not exist or do not match the old items.
            ValueError: If the number of items to be modified does not match.
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
        """
        Sửa đổi phương thức thanh toán của một đơn hàng pending. Tác nhân cần giải thích chi tiết thay đổi và yêu cầu người dùng xác nhận rõ ràng (yes/no) để tiếp tục.
        
        Args:
            order_id: Mã đơn hàng, ví dụ '#W0000000'. Lưu ý có ký hiệu '#' ở đầu mã đơn hàng.
            payment_method_id: Mã phương thức thanh toán để thanh toán hoặc nhận hoàn tiền cho chênh lệch giá mặt hàng, ví dụ 'gift_card_0000000' hoặc 'credit_card_0000000'. Có thể tra cứu từ người dùng hoặc chi tiết đơn hàng.
        
        Returns:
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
        """
        Sửa đổi địa chỉ mặc định của một người dùng. Tác nhân cần giải thích chi tiết thay đổi và yêu cầu người dùng xác nhận rõ ràng (yes/no) để tiếp tục.
        
        Args:
            user_id: Mã người dùng, ví dụ 'sara_doe_496'.
            address1: Dòng đầu của địa chỉ, ví dụ '123 Main St'.
            address2: Dòng thứ hai của địa chỉ, ví dụ 'Apt 1' hoặc ''.
            city: Thành phố, ví dụ 'San Francisco'.
            state: Bang/tỉnh, ví dụ 'CA'.
            country: Quốc gia, ví dụ 'USA'.
            zip: Mã bưu chính, ví dụ '12345'.
        
        Returns:
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
        """
        Return some items from a delivered order. The order status will be changed to 'return requested'. The agent needs to explain the return detail and ask for explicit user confirmation (yes/no) to proceed. The user will receive a follow-up email about how and where to return the items.
        
        Args:
            order_id: The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.
            item_ids: The item ids to be returned, each such as '1008292230'. There could be duplicate items in the list.
            payment_method_id: The payment method id to pay or receive refund for the item price difference, such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details.
        
        Returns:
            Order: The order details after requesting the return.
        
        Raises:
            ValueError: If the order is not delivered.
            ValueError: If the payment method is not the original payment method or a gift card.
            ValueError: If the items to be returned do not exist.
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
        โอนผู้ใช้ไปยังเจ้าหน้าที่พร้อมสรุปปัญหาของผู้ใช้ ให้โอนเฉพาะกรณีที่
         - ผู้ใช้ร้องขอให้คุยกับเจ้าหน้าที่อย่างชัดเจน
         - ตามนโยบายและเครื่องมือที่มีอยู่ คุณไม่สามารถแก้ปัญหาของผู้ใช้ได้
        
        Args:
            summary: สรุปปัญหาของผู้ใช้
        
        Returns:
            ข้อความที่ระบุว่าผู้ใช้ถูกโอนไปยังเจ้าหน้าที่แล้ว
        """
        return "Transfer successful"


if __name__ == "__main__":
    from tau2.domains.retail.utils import RETAIL_DB_PATH

    retail = RetailTools(RetailDB.load(RETAIL_DB_PATH))
    print(retail.get_statistics())
