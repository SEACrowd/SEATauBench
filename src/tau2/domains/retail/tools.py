"""ชุดเครื่องมือสำหรับโดเมนค้าปลีก."""

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
    """เครื่องมือทั้งหมดสำหรับโดเมนค้าปลีก."""

    db: RetailDB

    def __init__(self, db: RetailDB) -> None:
        super().__init__(db)

    def _get_order(self, order_id: str) -> Order:
        """ดึงคำสั่งซื้อจากฐานข้อมูล.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.

        คืนค่า:
            คำสั่งซื้อ.

        ข้อยกเว้น:
            ValueError: หากไม่พบคำสั่งซื้อ.
        """
        if order_id not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[order_id]

    def _get_user(self, user_id: str) -> User:
        """ดึงผู้ใช้จากฐานข้อมูล.

        อาร์กิวเมนต์:
            user_id: รหัสผู้ใช้ เช่น 'sara_doe_496'.

        คืนค่า:
            ผู้ใช้.

        ข้อยกเว้น:
            ValueError: หากไม่พบผู้ใช้.
        """
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    def _get_product(self, product_id: str) -> Product:
        """ดึงสินค้าจากฐานข้อมูล.

        อาร์กิวเมนต์:
            product_id: รหัสสินค้า เช่น '6086499569'. โปรดระวังว่ารหัสสินค้าจะแตกต่างจากรหัสรายการ.

        คืนค่า:
            สินค้า.

        ข้อยกเว้น:
            ValueError: หากไม่พบสินค้า.
        """
        if product_id not in self.db.products:
            raise ValueError("Product not found")
        return self.db.products[product_id]

    def _get_variant(self, product_id: str, variant_id: str) -> Variant:
        """ดึงตัวเลือกย่อย (variant) จากฐานข้อมูล.

        อาร์กิวเมนต์:
            product_id: รหัสสินค้า เช่น '6086499569'. โปรดระวังว่ารหัสสินค้าจะแตกต่างจากรหัสรายการ.
            variant_id: รหัสตัวเลือกย่อย เช่น '1008292230'.

        คืนค่า:
            ตัวเลือกย่อย (variant).

        ข้อยกเว้น:
            ValueError: หากไม่พบตัวเลือกย่อย.
        """
        product = self._get_product(product_id)
        if variant_id not in product.variants:
            raise ValueError("Variant not found")
        return product.variants[variant_id]

    def _get_payment_method(
        self, user_id: str, payment_method_id: str
    ) -> PaymentMethod:
        """ดึงวิธีการชำระเงินจากฐานข้อมูล.

        อาร์กิวเมนต์:
            payment_method_id: รหัสวิธีการชำระเงิน เช่น 'gift_card_0000000' หรือ 'credit_card_0000000'.

        คืนค่า:
            วิธีการชำระเงิน.

        ข้อยกเว้น:
            ValueError: หากไม่พบวิธีการชำระเงิน.
        """
        user = self._get_user(user_id)
        if payment_method_id not in user.payment_methods:
            raise ValueError("Payment method not found")
        return user.payment_methods[payment_method_id]

    def _is_pending_order(self, order: Order) -> bool:
        """ตรวจสอบว่าคำสั่งซื้อเป็น pending หรือไม่ นี่ไม่ใช่การตรวจสอบอย่างเคร่งครัด และไม่ได้ตั้งใจให้ใช้กับ modify_items ในคำสั่งซื้อ pending.

        อาร์กิวเมนต์:
            order: คำสั่งซื้อ.
        """
        return "pending" in order.status

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """
        คำนวณผลลัพธ์ของนิพจน์ทางคณิตศาสตร์.

        อาร์กิวเมนต์:
            expression: นิพจน์ทางคณิตศาสตร์ที่ต้องการคำนวณ เช่น '2 + 2'. นิพจน์สามารถประกอบด้วยตัวเลข ตัวดำเนินการ (+, -, *, /), วงเล็บ และช่องว่างได้.

        คืนค่า:
            ผลลัพธ์ของนิพจน์ทางคณิตศาสตร์.

        ข้อยกเว้น:
            ValueError: หากนิพจน์ไม่ถูกต้อง.
        """
        if not all(char in "0123456789+-*/(). " for char in expression):
            raise ValueError("Invalid characters in expression")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))

    @is_tool(ToolType.WRITE)
    def cancel_pending_order(self, order_id: str, reason: str) -> Order:
        """ยกเลิกคำสั่งซื้อ pending. หากคำสั่งซื้ออยู่ในสถานะ processed หรือ delivered จะไม่สามารถ cancelled ได้ ตัวแทนต้องอธิบายรายละเอียดการยกเลิกและขอการยืนยันจากผู้ใช้โดยชัดแจ้ง (yes/no) เพื่อดำเนินการต่อ หากผู้ใช้ยืนยัน สถานะคำสั่งซื้อจะถูกเปลี่ยนเป็น 'cancelled' และจะคืนเงินการชำระเงิน คืนเงินจะถูกเพิ่มเข้ายอดกิฟต์การ์ดของผู้ใช้อย่างทันทีหากการชำระเงินทำด้วยกิฟต์การ์ด มิฉะนั้นการคืนเงินจะใช้เวลา 5-7 วันทำการในการดำเนินการ ฟังก์ชันจะคืนรายละเอียดคำสั่งซื้อหลังการยกเลิก.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.
            reason: เหตุผลในการยกเลิก ซึ่งควรเป็น 'no longer needed' หรือ 'ordered by mistake'.

        คืนค่า:
            Order: รายละเอียดคำสั่งซื้อหลังการยกเลิก.
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
        """แลกเปลี่ยนรายการในคำสั่งซื้อ delivered เป็นรายการใหม่ที่เป็นประเภทสินค้ารายการเดียวกัน สำหรับคำสั่งซื้อ delivered การคืนหรือแลกสามารถทำได้เพียงครั้งเดียวโดยตัวแทน ตัวแทนต้องอธิบายรายละเอียดการแลกและขอการยืนยันจากผู้ใช้โดยชัดแจ้ง (yes/no) เพื่อดำเนินการต่อ.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.
            item_ids: รหัสรายการที่จะถูกแลก แต่ละรหัสเช่น '1008292230'. ในรายการอาจมีรายการซ้ำได้.
            new_item_ids: รหัสรายการที่แลกเป็น แต่ละรหัสเช่น '1008292230'. ในรายการอาจมีรายการซ้ำได้ ทุก new item id ควรตรงกับ item id ในตำแหน่งเดียวกันและเป็นของสินค้าประเภทเดียวกัน.
            payment_method_id: รหัสวิธีการชำระเงินที่ใช้ชำระหรือรับคืนสำหรับส่วนต่างราคาของสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000'. สามารถค้นหาจากรายละเอียดผู้ใช้หรือคำสั่งซื้อได้.

        คืนค่า:
            Order: รายละเอียดคำสั่งซื้อหลังการแลก.

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ใช่ delivered.
            ValueError: หากรายการที่จะแลก不存在.
            ValueError: หากรายการใหม่不存在หรือไม่ตรงกับรายการเดิม.
            ValueError: หากจำนวนรายการที่จะแลกไม่ตรงกัน.
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
        """ค้นหารหัสผู้ใช้โดยใช้ชื่อจริง นามสกุล และรหัสไปรษณีย์ หากไม่พบผู้ใช้ ฟังก์ชันจะส่งข้อความแสดงข้อผิดพลาด โดยปกติจะค้นหารหัสผู้ใช้จากอีเมลก่อน และเรียกฟังก์ชันนี้เฉพาะกรณีที่ไม่พบผู้ใช้จากอีเมลหรือผู้ใช้จำอีเมลไม่ได้

        อาร์กิวเมนต์:
            first_name: ชื่อของลูกค้า เช่น 'John'.
            last_name: นามสกุลของลูกค้า เช่น 'Doe'.
            zip: รหัสไปรษณีย์ของลูกค้า เช่น '12345'.

        คืนค่า:
            str: รหัสผู้ใช้หากพบ มิฉะนั้นเป็นข้อความแสดงข้อผิดพลาด.

        ข้อยกเว้น:
            ValueError: หากไม่พบผู้ใช้.
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
        """ค้นหารหัสผู้ใช้จากอีเมล หากไม่พบผู้ใช้ ฟังก์ชันจะส่งข้อความแสดงข้อผิดพลาด

        อาร์กิวเมนต์:
            email: อีเมลของผู้ใช้ เช่น 'something@example.com'.

        คืนค่า:
            str: รหัสผู้ใช้หากพบ มิฉะนั้นเป็นข้อความแสดงข้อผิดพลาด.

        ข้อยกเว้น:
            ValueError: หากไม่พบผู้ใช้.
        """
        for user_id, user in self.db.users.items():
            if user.email.lower() == email.lower():
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> Order:
        """รับสถานะและรายละเอียดของคำสั่งซื้อ.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.

        คืนค่า:
            Order: รายละเอียดคำสั่งซื้อ.

        ข้อยกเว้น:
            ValueError: หากไม่พบคำสั่งซื้อ.
        """
        order = self._get_order(order_id)
        return order

    @is_tool(ToolType.READ)
    def get_product_details(self, product_id: str) -> Product:
        """รับรายละเอียดสต็อกของสินค้า.

        อาร์กิวเมนต์:
            product_id: รหัสสินค้า เช่น '6086499569'. โปรดระวังว่ารหัสสินค้าจะแตกต่างจากรหัสรายการ.

        คืนค่า:
            Product: รายละเอียดสินค้า.

        ข้อยกเว้น:
            ValueError: หากไม่พบสินค้า.
        """
        product = self._get_product(product_id)
        return product

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> User:
        """รับรายละเอียดของผู้ใช้ รวมถึงคำสั่งซื้อของพวกเขา.

        อาร์กิวเมนต์:
            user_id: รหัสผู้ใช้ เช่น 'sara_doe_496'.

        คืนค่า:
            User: รายละเอียดผู้ใช้.

        ข้อยกเว้น:
            ValueError: หากไม่พบผู้ใช้.
        """
        user = self._get_user(user_id)
        return user

    @is_tool(ToolType.READ)
    def list_all_product_types(self) -> str:
        """แสดงชื่อและรหัสสินค้าของทุกประเภทสินค้า แต่ละประเภทสินค้ามีรายการต่างๆ หลายรายการที่มีรหัสรายการและตัวเลือกเฉพาะ มีเพียง 50 ประเภทสินค้าในร้าน

        คืนค่า:
            str: สตริง JSON ที่แมปชื่อสินค้าไปยังรหัสสินค้า โดยเรียงตามลำดับตัวอักษรของชื่อ.
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
        """แก้ไขที่อยู่จัดส่งของคำสั่งซื้อ pending. ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้โดยชัดแจ้ง (yes/no) เพื่อดำเนินการต่อ.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.
            address1: บรรทัดที่หนึ่งของที่อยู่ เช่น '123 Main St'.
            address2: บรรทัดที่สองของที่อยู่ เช่น 'Apt 1' หรือ ''.
            city: เมือง เช่น 'San Francisco'.
            state: รัฐ เช่น 'CA'.
            country: ประเทศ เช่น 'USA'.
            zip: รหัสไปรษณีย์ เช่น '12345'.

        คืนค่า:
            Order: รายละเอียดคำสั่งซื้อหลังการแก้ไข.

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ใช่ pending.
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
        """แก้ไขรายการในคำสั่งซื้อ pending เป็นรายการใหม่ที่เป็นประเภทสินค้ารายการเดียวกัน สำหรับคำสั่งซื้อ pending ฟังก์ชันนี้เรียกได้เพียงครั้งเดียว ตัวแทนต้องอธิบายรายละเอียดการเปลี่ยนแปลงและขอการยืนยันจากผู้ใช้โดยชัดแจ้ง (yes/no) เพื่อดำเนินการต่อ.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.
            item_ids: รหัสรายการที่จะแก้ไข แต่ละรหัสเช่น '1008292230'. ในรายการอาจมีรายการซ้ำได้.
            new_item_ids: รหัสรายการใหม่ที่จะเปลี่ยนเป็น แต่ละรหัสเช่น '1008292230'. ในรายการอาจมีรายการซ้ำได้ ทุก new item id ควรตรงกับ item id ในตำแหน่งเดียวกันและเป็นของสินค้าประเภทเดียวกัน.
            payment_method_id: รหัสวิธีการชำระเงินที่ใช้ชำระหรือรับคืนสำหรับส่วนต่างราคาของสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000'. สามารถค้นหาจากรายละเอียดผู้ใช้หรือคำสั่งซื้อได้.

        คืนค่า:
            Order: รายละเอียดคำสั่งซื้อหลังการแก้ไข.

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ใช่ pending.
            ValueError: หากรายการที่จะถูกแก้ไข不存在.
            ValueError: หากรายการใหม่不存在หรือไม่ตรงกับรายการเดิม.
            ValueError: หากจำนวนรายการที่จะถูกแก้ไขไม่ตรงกัน.
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
        """แก้ไขวิธีการชำระเงินของคำสั่งซื้อ pending. ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้โดยชัดแจ้ง (yes/no) เพื่อดำเนินการต่อ.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.
            payment_method_id: รหัสวิธีการชำระเงินที่ใช้ชำระหรือรับคืนสำหรับส่วนต่างราคาของสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000'. สามารถค้นหาจากรายละเอียดผู้ใช้หรือคำสั่งซื้อได้.

        คืนค่า:
            Order: รายละเอียดคำสั่งซื้อหลังการแก้ไข.

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ใช่ pending.
            ValueError: หากวิธีการชำระเงิน不存在.
            ValueError: หากประวัติการชำระเงินมีมากกว่าหนึ่งการชำระ.
            ValueError: หากวิธีการชำระเงินใหม่เหมือนกับวิธีปัจจุบัน.
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
        """แก้ไขที่อยู่เริ่มต้นของผู้ใช้ ตัวแทนต้องอธิบายรายละเอียดการแก้ไขและขอการยืนยันจากผู้ใช้โดยชัดแจ้ง (yes/no) เพื่อดำเนินการต่อ.

        อาร์กิวเมนต์:
            user_id: รหัสผู้ใช้ เช่น 'sara_doe_496'.
            address1: บรรทัดที่หนึ่งของที่อยู่ เช่น '123 Main St'.
            address2: บรรทัดที่สองของที่อยู่ เช่น 'Apt 1' หรือ ''.
            city: เมือง เช่น 'San Francisco'.
            state: รัฐ เช่น 'CA'.
            country: ประเทศ เช่น 'USA'.
            zip: รหัสไปรษณีย์ เช่น '12345'.

        คืนค่า:
            User: รายละเอียดผู้ใช้หลังการแก้ไข.

        ข้อยกเว้น:
            ValueError: หากไม่พบผู้ใช้.
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
        """คืนสินค้าบางรายการของคำสั่งซื้อ delivered. สถานะคำสั่งซื้อจะถูกเปลี่ยนเป็น 'return requested'. ตัวแทนต้องอธิบายรายละเอียดการคืนและขอการยืนยันจากผู้ใช้โดยชัดแจ้ง (yes/no) ในการดำเนินการต่อ ผู้ใช้จะได้รับอีเมลติดตามเพื่อแจ้งวิธีและสถานที่ในการส่งคืนสินค้า.

        อาร์กิวเมนต์:
            order_id: รหัสคำสั่งซื้อ เช่น '#W0000000'. โปรดระวังว่าเครื่องหมาย '#' อยู่ด้านหน้าของรหัสคำสั่งซื้อ.
            item_ids: รหัสรายการที่จะส่งคืน แต่ละรหัสเช่น '1008292230'. ในรายการอาจมีรายการซ้ำได้.
            payment_method_id: รหัสวิธีการชำระเงินที่ใช้ชำระหรือรับคืนสำหรับส่วนต่างราคาของสินค้า เช่น 'gift_card_0000000' หรือ 'credit_card_0000000'.
                             สามารถค้นหาจากรายละเอียดผู้ใช้หรือคำสั่งซื้อได้.

        คืนค่า:
            Order: รายละเอียดคำสั่งซื้อหลังการขอคืนสินค้า.

        ข้อยกเว้น:
            ValueError: หากคำสั่งซื้อไม่ใช่ delivered.
            ValueError: หากวิธีการชำระเงินไม่ใช่วิธีการชำระเงินต้นฉบับหรือกิฟต์การ์ด.
            ValueError: หากรายการที่จะส่งคืน不存在.
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
        โอนผู้ใช้ไปยังเจ้าหน้าที่มนุษย์ พร้อมสรุปปัญหาของผู้ใช้
        ให้โอนเฉพาะเมื่อ
         - ผู้ใช้ร้องขอเจ้าหน้าที่มนุษย์โดยชัดแจ้ง
         - ตามนโยบายและเครื่องมือที่มีอยู่ คุณไม่สามารถแก้ปัญหาของผู้ใช้ได้

        อาร์กิวเมนต์:
            summary: สรุปปัญหาของผู้ใช้.

        คืนค่า:
            ข้อความที่แสดงว่าผู้ใช้ถูกโอนไปยังเจ้าหน้าที่มนุษย์.
        """
        return "Transfer successful"


if __name__ == "__main__":
    from tau2.domains.retail.utils import RETAIL_DB_PATH

    retail = RetailTools(RetailDB.load(RETAIL_DB_PATH))
    print(retail.get_statistics())
