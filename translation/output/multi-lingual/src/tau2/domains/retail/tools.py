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
        """
        Batalkan pesanan pending. Jika pesanan sudah diproses atau dikirim, pesanan tidak dapat dibatalkan. Agen perlu menjelaskan detail pembatalan dan meminta konfirmasi pengguna secara eksplisit (ya/tidak) untuk melanjutkan. Jika pengguna mengonfirmasi, status pesanan akan diubah menjadi 'cancelled' dan pembayaran akan dikembalikan. Pengembalian dana akan langsung ditambahkan ke saldo kartu hadiah pengguna jika pembayaran dilakukan menggunakan kartu hadiah; jika tidak, pengembalian dana akan memerlukan 5-7 hari kerja untuk diproses. Fungsi mengembalikan detail pesanan setelah pembatalan.
        
        Args:
            order_id: ID pesanan, seperti '#W0000000'. Hati-hati, ada simbol '#' di awal ID pesanan.
            reason: Alasan pembatalan, yang harus berupa 'no longer needed' atau 'ordered by mistake'.
        
        Returns:
            Order: Detail pesanan setelah pembatalan.
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
        ค้นหารหัสผู้ใช้จากชื่อ นามสกุล และรหัสไปรษณีย์ โดยปกติควรค้นหารหัสผู้ใช้จากอีเมลก่อน และเรียกใช้ฟังก์ชันนี้เฉพาะเมื่อไม่พบผู้ใช้จากอีเมลหรือผู้ใช้จำอีเมลไม่ได้
        
        Args:
            first_name: ชื่อของลูกค้า เช่น 'John'
            last_name: นามสกุลของลูกค้า เช่น 'Doe'
            zip: รหัสไปรษณีย์ของลูกค้า เช่น '12345'
        
        Returns:
            str: รหัสผู้ใช้หากพบ มิฉะนั้นเป็นข้อความแสดงข้อผิดพลาด
        
        Raises:
            ValueError: หากไม่พบผู้ใช้
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
        Find user id by email. If the user is not found, this function returns an error.
        
        Args:
            email: The email of the user, such as 'something@example.com'.
        
        Returns:
            str: The user id if found; otherwise an error message.
        
        Raises:
            ValueError: If the user is not found.
        """
        for user_id, user in self.db.users.items():
            if user.email.lower() == email.lower():
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> Order:
        """
        Lấy trạng thái và chi tiết của một đơn hàng.
        
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
        """
        Dapatkan detail inventaris sebuah produk.
        
        Args:
            product_id: ID produk, seperti '6086499569'. Hati-hati, ID produk berbeda dari ID item.
        
        Returns:
            Product: Detail produk.
        
        Raises:
            ValueError: Jika produk tidak ditemukan.
        """
        product = self._get_product(product_id)
        return product
    
    @is_tool(ToolType.READ)
    def get_item_details(self, item_id: str) -> Variant:
        """Get the inventory details of an item.

        Args:
            item_id: The item id, such as '6086499569'. Be careful the item id is different from the product id.

        Returns:
            Variant: The item details.

        Raises:
            ValueError: If the item is not found.
        """
        item = self._get_item(item_id)
        return item

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> User:
        """
        Lấy chi tiết của một người dùng, bao gồm các đơn hàng của họ.
        
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
        """
        แสดงรายการชื่อและรหัสผลิตภัณฑ์ของประเภทสินค้าทั้งหมด แต่ละประเภทสินค้ามีรายการสินค้าที่แตกต่างกันพร้อมรหัสสินค้าและตัวเลือกเฉพาะ ในร้านมีประเภทสินค้าเพียง 50 ประเภท
        
        Returns:
            str: สตริง JSON ที่แมปชื่อสินค้าไปยังรหัสผลิตภัณฑ์ โดยเรียงตามตัวอักษรตามชื่อ
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
        Ubah alamat pengiriman untuk pesanan pending. Agen perlu menjelaskan detail perubahan dan meminta konfirmasi eksplisit dari pengguna (ya/tidak) untuk melanjutkan.
        
        Args:
            order_id: ID pesanan, seperti '#W0000000'. Perhatikan ada simbol '#' di awal ID pesanan.
            address1: Baris pertama alamat, seperti '123 Main St'.
            address2: Baris kedua alamat, seperti 'Apt 1' atau ''.
            city: Kota, seperti 'San Francisco'.
            state: Negara bagian, seperti 'CA'.
            country: Negara, seperti 'USA'.
            zip: Kode pos, seperti '12345'.
        
        Returns:
            Order: Detail pesanan setelah perubahan.
        
        Raises:
            ValueError: Jika pesanan tidak pending.
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
        Ubah metode pembayaran untuk pesanan pending. Agen perlu menjelaskan detail perubahan dan meminta konfirmasi eksplisit dari pengguna (ya/tidak) untuk melanjutkan.
        
        Args:
            order_id: ID pesanan, seperti '#W0000000'. Perhatikan ada simbol '#' di awal ID pesanan.
            payment_method_id: ID metode pembayaran untuk membayar atau menerima pengembalian dana atas selisih harga item, seperti 'gift_card_0000000' atau 'credit_card_0000000'. Ini dapat dilihat dari pengguna atau detail pesanan.
        
        Returns:
            Order: Detail pesanan setelah perubahan.
        
        Raises:
            ValueError: Jika pesanan tidak pending.
            ValueError: Jika metode pembayaran tidak ada.
            ValueError: Jika riwayat pembayaran memiliki lebih dari satu pembayaran.
            ValueError: Jika metode pembayaran baru sama dengan yang saat ini.
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
        แก้ไขที่อยู่เริ่มต้นของผู้ใช้ ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้อย่างชัดเจน (yes/no) ก่อนดำเนินการต่อ
        
        Args:
            user_id: รหัสผู้ใช้ เช่น 'sara_doe_496'
            address1: บรรทัดแรกของที่อยู่ เช่น '123 Main St'
            address2: บรรทัดที่สองของที่อยู่ เช่น 'Apt 1' หรือ ''
            city: เมือง เช่น 'San Francisco'
            state: รัฐ เช่น 'CA'
            country: ประเทศ เช่น 'USA'
            zip: รหัสไปรษณีย์ เช่น '12345'
        
        Returns:
            User: รายละเอียดผู้ใช้หลังการแก้ไข
        
        Raises:
            ValueError: หากไม่พบผู้ใช้
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
        Chuyển người dùng tới một nhân viên hỗ trợ, kèm theo bản tóm tắt vấn đề của người dùng. Chỉ chuyển nếu
         - người dùng yêu cầu rõ ràng được gặp nhân viên hỗ trợ
         - dựa trên chính sách và các công cụ sẵn có, bạn không thể giải quyết vấn đề của người dùng.
        
        Args:
            summary: Tóm tắt vấn đề của người dùng.
        
        Returns:
            Một thông điệp cho biết người dùng đã được chuyển tới một nhân viên hỗ trợ.
        """
        return "Transfer successful"


if __name__ == "__main__":
    from tau2.domains.retail.utils import RETAIL_DB_PATH

    retail = RetailTools(RetailDB.load(RETAIL_DB_PATH))
    print(retail.get_statistics())
