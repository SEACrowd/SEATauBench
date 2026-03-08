"""ชุดเครื่องมือสำหรับโดเมนค้าปลีก"""

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
    """เครื่องมือทั้งหมดสำหรับโดเมนค้าปลีก"""

    db: RetailDB

    def __init__(self, db: RetailDB) -> None:
        super().__init__(db)

    def _get_order(self, order_id: str) -> Order:
        """ดึงข้อมูลคำสั่งซื้อจากฐานข้อมูล

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ที่ต้นรหัสคำสั่งซื้อ

        คืนค่า:
            คำสั่งซื้อ

        ข้อยกเว้น:
            ValueError: หากไม่พบคำสั่งซื้อ
        """
        if order_id not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[order_id]

    def _get_user(self, user_id: str) -> User:
        """ดึงข้อมูลผู้ใช้จากฐานข้อมูล

        อาร์กิวเมนต์:
            user_id: รหัสผู้ใช้ เช่น 'sara_doe_496'

        คืนค่า:
            ผู้ใช้

        ข้อยกเว้น:
            ValueError: หากไม่พบผู้ใช้
        """
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    def _get_product(self, product_id: str) -> Product:
        """ดึงข้อมูลสินค้าออกจากฐานข้อมูล

        อาร์กิวเมนต์:
            product_id: รหัสสินค้า เช่น '6086499569' โปรดระวังว่ารหัสสินค้าต่างจากรหัสรายการสินค้า

        คืนค่า:
            สินค้า

        ข้อยกเว้น:
            ValueError: หากไม่พบสินค้า
        """
        if product_id not in self.db.products:
            raise ValueError("Product not found")
        return self.db.products[product_id]

    def _get_variant(self, product_id: str, variant_id: str) -> Variant:
        """ดึงข้อมูลตัวเลือกย่อย (variant) จากฐานข้อมูล

        อาร์กิวเมนต์:
            product_id: รหัสสินค้า เช่น '6086499569' โปรดระวังว่ารหัสสินค้าต่างจากรหัสรายการสินค้า
            variant_id: รหัสตัวเลือกย่อย (variant) เช่น '1008292230'

        คืนค่า:
            ตัวเลือกย่อย (variant)

        ข้อยกเว้น:
            ValueError: หากไม่พบตัวเลือกย่อย (variant)
        """
        product = self._get_product(product_id)
        if variant_id not in product.variants:
            raise ValueError("Variant not found")
        return product.variants[variant_id]

    def _get_payment_method(
        self, user_id: str, payment_method_id: str
    ) -> PaymentMethod:
        """ดึงข้อมูลวิธีชำระเงินจากฐานข้อมูล

        อาร์กิวเมนต์:
            payment_method_id: รหัสวิธีชำระเงิน เช่น 'gift_card_0000000' หรือ 'credit_card_0000000'

        คืนค่า:
            วิธีชำระเงิน

        ข้อยกเว้น:
            ValueError: หากไม่พบวิธีชำระเงิน
        """
        user = self._get_user(user_id)
        if payment_method_id not in user.payment_methods:
            raise ValueError("Payment method not found")
        return user.payment_methods[payment_method_id]

    def _is_pending_order(self, order: Order) -> bool:
        """ตรวจสอบว่าคำสั่งซื้อเป็น pending หรือไม่ การตรวจสอบนี้ไม่เข้มงวด และไม่ได้มีไว้เพื่อใช้กับ modify_items ในคำสั่งซื้อ pending

        อาร์กิวเมนต์:
            order: คำสั่งซื้อ
        """
        return "pending" in order.status

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """
        คำนวณผลลัพธ์ของนิพจน์ทางคณิตศาสตร์

        Args:
            expression: นิพจน์ทางคณิตศาสตร์ที่ต้องการคำนวณ เช่น '2 + 2' นิพจน์สามารถมีตัวเลข ตัวดำเนินการ (+, -, *, /) วงเล็บ และช่องว่างได้

        Returns:
            ผลลัพธ์ของนิพจน์ทางคณิตศาสตร์

        Raises:
            ValueError: หากนิพจน์ไม่ถูกต้อง
        """
        if not all(char in "0123456789+-*/(). " for char in expression):
            raise ValueError("Invalid characters in expression")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))

    @is_tool(ToolType.WRITE)
    def cancel_pending_order(self, order_id: str, reason: str) -> Order:
        """ยกเลิกคำสั่งซื้อ pending หากคำสั่งซื้อได้รับการดำเนินการหรือจัดส่งแล้ว
        จะไม่สามารถยกเลิกได้ เอเจนต์ต้องอธิบายรายละเอียดการยกเลิก
        และขอการยืนยันจากผู้ใช้อย่างชัดเจน (ใช่/ไม่) เพื่อดำเนินการต่อ หากผู้ใช้ยืนยัน
        สถานะคำสั่งซื้อจะถูกเปลี่ยนเป็น 'cancelled' และจะทำการคืนเงิน
        โดยเงินคืนจะถูกเพิ่มเข้ายอดคงเหลือบัตรของขวัญของผู้ใช้ทันที หากการชำระเงิน
        ทำด้วยบัตรของขวัญ มิฉะนั้นการคืนเงินจะใช้เวลา 5-7 วันทำการในการดำเนินการ
        ฟังก์ชันจะส่งคืนรายละเอียดคำสั่งซื้อหลังการยกเลิก

        Args:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ด้านหน้ารหัสคำสั่งซื้อ
            reason: เหตุผลในการยกเลิก ซึ่งควรเป็นอย่างใดอย่างหนึ่งระหว่าง 'no longer needed' หรือ 'ordered by mistake'

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
        """แลกเปลี่ยนสินค้าในคำสั่งซื้อที่จัดส่งแล้วเป็นสินค้าใหม่ที่เป็นประเภทผลิตภัณฑ์เดียวกัน
        สำหรับคำสั่งซื้อที่จัดส่งแล้ว การคืนหรือแลกเปลี่ยนสามารถทำได้เพียงครั้งเดียวโดยเอเจนต์
        เอเจนต์ต้องอธิบายรายละเอียดการแลกเปลี่ยนและขอการยืนยันจากผู้ใช้อย่างชัดเจน (ใช่/ไม่) เพื่อดำเนินการต่อ

        Args:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ด้านหน้ารหัสคำสั่งซื้อ
            item_ids: รหัสรายการสินค้าที่ต้องการแลกเปลี่ยน แต่ละรายการเช่น '1008292230' อาจมีรายการซ้ำในลิสต์ได้
            new_item_ids: รหัสรายการสินค้าที่จะใช้แลกเปลี่ยน แต่ละรายการเช่น '1008292230'
                         อาจมีรายการซ้ำในลิสต์ได้ รหัสรายการสินค้าใหม่แต่ละรายการควรตรงกับรหัสรายการสินค้าเดิม
                         ในตำแหน่งเดียวกันและเป็นผลิตภัณฑ์เดียวกัน
            payment_method_id: รหัสวิธีชำระเงินที่ใช้ชำระหรือรับเงินคืนสำหรับส่วนต่างราคาสินค้า
                             เช่น 'gift_card_0000000' หรือ 'credit_card_0000000' สามารถค้นหาได้
                             จากรายละเอียดผู้ใช้หรือคำสั่งซื้อ

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
        """ค้นหารหัสผู้ใช้จากชื่อ นามสกุล และรหัสไปรษณีย์ หากไม่พบผู้ใช้ ฟังก์ชัน
        จะส่งคืนข้อความแสดงข้อผิดพลาด โดยค่าเริ่มต้นให้ค้นหารหัสผู้ใช้จากอีเมล และเรียกใช้ฟังก์ชันนี้
        เฉพาะเมื่อไม่พบผู้ใช้ด้วยอีเมลหรือผู้ใช้จำอีเมลไม่ได้

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
        """ค้นหารหัสผู้ใช้ด้วยอีเมล หากไม่พบผู้ใช้ ฟังก์ชันจะส่งคืนข้อความแสดงข้อผิดพลาด

        Args:
            email: อีเมลของผู้ใช้ เช่น 'something@example.com'

        Returns:
            str: รหัสผู้ใช้หากพบ มิฉะนั้นเป็นข้อความแสดงข้อผิดพลาด

        Raises:
            ValueError: หากไม่พบผู้ใช้
        """
        for user_id, user in self.db.users.items():
            if user.email.lower() == email.lower():
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> Order:
        """รับสถานะและรายละเอียดของคำสั่งซื้อ

        Args:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ด้านหน้ารหัสคำสั่งซื้อ

        Returns:
            Order: รายละเอียดคำสั่งซื้อ

        Raises:
            ValueError: หากไม่พบคำสั่งซื้อ
        """
        order = self._get_order(order_id)
        return order

    @is_tool(ToolType.READ)
    def get_product_details(self, product_id: str) -> Product:
        """รับรายละเอียดสินค้าคงคลังของผลิตภัณฑ์

        Args:
            product_id: รหัสผลิตภัณฑ์ เช่น '6086499569' โปรดระวังว่ารหัสผลิตภัณฑ์แตกต่างจากรหัสรายการสินค้า

        Returns:
            Product: รายละเอียดผลิตภัณฑ์

        Raises:
            ValueError: หากไม่พบผลิตภัณฑ์
        """
        product = self._get_product(product_id)
        return product

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> User:
        """รับรายละเอียดของผู้ใช้ รวมถึงคำสั่งซื้อของผู้ใช้

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
        """แสดงรายการชื่อและรหัสผลิตภัณฑ์ (product id) ของประเภทสินค้าทั้งหมด
        แต่ละประเภทสินค้ามีรายการสินค้าที่หลากหลาย โดยแต่ละรายการมีรหัสสินค้า (item id) และตัวเลือกที่ไม่ซ้ำกัน
        ในร้านมีประเภทสินค้าอยู่เพียง 50 ประเภทเท่านั้น

        ส่งคืน:
            str: สตริง JSON ที่แมปชื่อสินค้าไปยังรหัสผลิตภัณฑ์ของสินค้า โดยจัดเรียงตามตัวอักษรตามชื่อ
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
        """แก้ไขที่อยู่จัดส่งของคำสั่งซื้อ pending ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้อย่างชัดเจน (yes/no) ก่อนดำเนินการต่อ

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ที่ต้นรหัสคำสั่งซื้อ
            address1: บรรทัดแรกของที่อยู่ เช่น '123 Main St'
            address2: บรรทัดที่สองของที่อยู่ เช่น 'Apt 1' หรือ ''
            city: เมือง เช่น 'San Francisco'
            state: รัฐ เช่น 'CA'
            country: ประเทศ เช่น 'USA'
            zip: รหัสไปรษณีย์ เช่น '12345'

        ส่งคืน:
            Order: รายละเอียดคำสั่งซื้อหลังการแก้ไข

        ข้อยกเว้น:
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
        """แก้ไขรายการสินค้าในคำสั่งซื้อ pending ให้เป็นสินค้าใหม่ที่อยู่ในประเภทสินค้าเดียวกัน สำหรับคำสั่งซื้อ pending ฟังก์ชันนี้สามารถเรียกใช้ได้เพียงครั้งเดียว ตัวแทนต้องอธิบายรายละเอียดการเปลี่ยนสินค้าและขอการยืนยันจากผู้ใช้อย่างชัดเจน (yes/no) ก่อนดำเนินการต่อ

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ที่ต้นรหัสคำสั่งซื้อ
            item_ids: รหัสรายการสินค้าที่ต้องการแก้ไข แต่ละรายการเช่น '1008292230' อาจมีรายการซ้ำในลิสต์ได้
            new_item_ids: รหัสรายการสินค้าที่ต้องการแก้ไขเป็น แต่ละรายการเช่น '1008292230' อาจมีรายการซ้ำในลิสต์ได้ รหัสรายการสินค้าใหม่แต่ละตัวต้องตรงกับรหัสรายการสินค้าในตำแหน่งเดียวกันและเป็นสินค้าในผลิตภัณฑ์เดียวกัน
            payment_method_id: รหัสวิธีชำระเงินที่ใช้ชำระหรือรับเงินคืนสำหรับส่วนต่างราคาสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000' โดยสามารถดูได้จากผู้ใช้หรือรายละเอียดคำสั่งซื้อ

        ส่งคืน:
            Order: รายละเอียดคำสั่งซื้อหลังการแก้ไข

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ใช่ pending
            ValueError: หากไม่มีรายการสินค้าที่ต้องการแก้ไข
            ValueError: หากไม่มีสินค้าใหม่ หรือสินค้าใหม่ไม่ตรงกับสินค้าเดิม
            ValueError: หากจำนวนรายการสินค้าที่ต้องการแก้ไขไม่ตรงกัน
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
        """แก้ไขวิธีชำระเงินของคำสั่งซื้อ pending ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้อย่างชัดเจน (yes/no) ก่อนดำเนินการต่อ

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ที่ต้นรหัสคำสั่งซื้อ
            payment_method_id: รหัสวิธีชำระเงินที่ใช้ชำระหรือรับเงินคืนสำหรับส่วนต่างราคาสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000' โดยสามารถดูได้จากผู้ใช้หรือรายละเอียดคำสั่งซื้อ

        ส่งคืน:
            Order: รายละเอียดคำสั่งซื้อหลังการแก้ไข

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ใช่ pending
            ValueError: หากไม่มีวิธีชำระเงินดังกล่าว
            ValueError: หากประวัติการชำระเงินมีมากกว่าหนึ่งรายการชำระเงิน
            ValueError: หากวิธีชำระเงินใหม่เหมือนกับวิธีปัจจุบัน
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
        """แก้ไขที่อยู่เริ่มต้นของผู้ใช้ ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้อย่างชัดเจน (yes/no) ก่อนดำเนินการต่อ

        อาร์กิวเมนต์:
            user_id: รหัสผู้ใช้ เช่น 'sara_doe_496'
            address1: บรรทัดแรกของที่อยู่ เช่น '123 Main St'
            address2: บรรทัดที่สองของที่อยู่ เช่น 'Apt 1' หรือ ''
            city: เมือง เช่น 'San Francisco'
            state: รัฐ เช่น 'CA'
            country: ประเทศ เช่น 'USA'
            zip: รหัสไปรษณีย์ เช่น '12345'

        ส่งคืน:
            User: รายละเอียดผู้ใช้หลังการแก้ไข

        ข้อยกเว้น:
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
        """คืนสินค้าบางรายการจากคำสั่งซื้อที่จัดส่งแล้ว
        สถานะคำสั่งซื้อจะถูกเปลี่ยนเป็น 'return requested'
        ตัวแทนต้องอธิบายรายละเอียดการคืนสินค้าและขอการยืนยันจากผู้ใช้อย่างชัดเจน (yes/no) ก่อนดำเนินการต่อ
        ผู้ใช้จะได้รับอีเมลติดตามผลเกี่ยวกับวิธีและสถานที่ในการคืนสินค้า

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000' โปรดระวังว่ามีสัญลักษณ์ '#' อยู่ที่ต้นรหัสคำสั่งซื้อ
            item_ids: รหัสรายการสินค้าที่ต้องการคืน แต่ละรายการเช่น '1008292230' อาจมีรายการซ้ำในลิสต์ได้
            payment_method_id: รหัสวิธีชำระเงินที่ใช้ชำระหรือรับเงินคืนสำหรับส่วนต่างราคาสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000'
                             โดยสามารถดูได้จากผู้ใช้หรือรายละเอียดคำสั่งซื้อ

        ส่งคืน:
            Order: รายละเอียดคำสั่งซื้อหลังจากส่งคำขอคืนสินค้า

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ได้ถูกจัดส่งแล้ว
            ValueError: หากวิธีชำระเงินไม่ใช่วิธีชำระเงินเดิมหรือไม่ใช่บัตรของขวัญ
            ValueError: หากไม่มีรายการสินค้าที่ต้องการคืน
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
        โอนผู้ใช้ไปยังเจ้าหน้าที่ (human agent) พร้อมสรุปปัญหาของผู้ใช้
        ให้โอนเฉพาะกรณีที่
         -  ผู้ใช้ร้องขอให้คุยกับเจ้าหน้าที่อย่างชัดเจน
         -  ตามนโยบายและเครื่องมือที่มีอยู่ คุณไม่สามารถแก้ปัญหาของผู้ใช้ได้

        อาร์กิวเมนต์:
            summary: สรุปปัญหาของผู้ใช้

        ส่งคืน:
            ข้อความที่ระบุว่าผู้ใช้ถูกโอนไปยังเจ้าหน้าที่แล้ว
        """
        return "Transfer successful"


if __name__ == "__main__":
    from tau2.domains.retail.utils import RETAIL_DB_PATH

    retail = RetailTools(RetailDB.load(RETAIL_DB_PATH))
    print(retail.get_statistics())
