from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from tau2.domains.retail.utils import RETAIL_DB_PATH
from tau2.environment.db import DB


class Variant(BaseModel):
    """เป็นตัวแทนของตัวแปรเฉพาะของผลิตภัณฑ์ พร้อมตัวเลือก ความพร้อมใช้งาน และราคา"""

    item_id: str = Field(description="รหัสระบุเฉพาะของตัวแปร")
    options: Dict[str, str] = Field(
        description="พจนานุกรมที่แมปชื่อของตัวเลือกกับค่า (เช่น {'color': 'blue', 'size': 'large'})"
    )
    available: bool = Field(description="ระบุว่าสินค้ารูปแบบนี้มีสต็อกอยู่ในขณะนี้หรือไม่")
    price: float = Field(description="ราคาของรูปแบบสินค้านี้")


class Product(BaseModel):
    """เป็นตัวแทนของผลิตภัณฑ์พร้อมตัวแปรของมัน"""

    name: str = Field(description="ชื่อสินค้า")
    product_id: str = Field(description="รหัสระบุเฉพาะของสินค้า")
    variants: Dict[str, Variant] = Field(
        description="พจนานุกรมของรูปแบบสินค้าที่มีรหัสรูปแบบเป็นคีย์"
    )


class UserName(BaseModel):
    """เป็นตัวแทนของชื่อเต็มของผู้ใช้"""

    first_name: str = Field(description="ชื่อจริงของผู้ใช้")
    last_name: str = Field(description="นามสกุลของผู้ใช้")


class UserAddress(BaseModel):
    """เป็นตัวแทนของที่อยู่ทางกายภาพ"""

    address1: str = Field(description="บรรทัดที่อยู่หลัก")
    address2: str = Field(description="บรรทัดที่อยู่เพิ่มเติม")
    city: str = Field(description="ชื่อเมือง")
    country: str = Field(description="ชื่อประเทศ")
    state: str = Field(description="ชื่อรัฐหรือจังหวัด")
    zip: str = Field(description="รหัสไปรษณีย์")


class PaymentMethodBase(BaseModel):
    source: str = Field(description="ประเภทของวิธีชำระเงิน")
    id: str = Field(description="รหัสระบุเฉพาะของวิธีชำระเงิน")


class CreditCard(PaymentMethodBase):
    source: Literal["credit_card"] = Field(
        description="ระบุว่านี่เป็นวิธีการชำระเงินด้วยบัตรเครดิต"
    )
    brand: str = Field(description="แบรนด์บัตรเครดิต (เช่น visa, mastercard)")
    last_four: str = Field(description="4 หลักสุดท้ายของบัตรเครดิต")


class Paypal(PaymentMethodBase):
    source: Literal["paypal"] = Field(description="ระบุว่านี่เป็นวิธีการชำระเงินผ่าน paypal")


class GiftCard(PaymentMethodBase):
    source: Literal["gift_card"] = Field(
        description="ระบุว่านี่เป็นวิธีการชำระเงินด้วยบัตรของขวัญ"
    )
    balance: float = Field(description="มูลค่าของบัตรของขวัญ")
    id: str = Field(description="รหัสระบุเฉพาะของบัตรของขวัญ")


PaymentMethod = Union[CreditCard, GiftCard, Paypal]


class User(BaseModel):
    """เป็นตัวแทนของผู้ใช้ที่มีข้อมูลส่วนบุคคล วิธีการชำระเงิน และประวัติคำสั่งซื้อ"""

    user_id: str = Field(description="รหัสระบุเฉพาะของผู้ใช้")
    name: UserName = Field(description="ชื่อเต็มของผู้ใช้")
    address: UserAddress = Field(description="ที่อยู่หลักของผู้ใช้")
    email: str = Field(description="ที่อยู่อีเมลของผู้ใช้")
    payment_methods: Dict[str, PaymentMethod] = Field(
        description="พจนานุกรมของวิธีการชำระเงินที่มีคีย์เป็นรหัสวิธีการชำระเงิน"
    )
    orders: List[str] = Field(description="รายการรหัสคำสั่งซื้อที่เกี่ยวข้องกับผู้ใช้รายนี้")


class OrderFullfilment(BaseModel):
    """เป็นตัวแทนของรายละเอียดการจัดส่งสำหรับรายการในคำสั่งซื้อ"""

    tracking_id: list[str] = Field(description="รายการหมายเลขติดตามการจัดส่ง")
    item_ids: list[str] = Field(description="รายการรหัสสินค้าที่รวมอยู่ในการจัดส่งนี้")


class OrderItem(BaseModel):
    """เป็นตัวแทนของรายการในคำสั่งซื้อ"""

    name: str = Field(description="ชื่อสินค้า")
    product_id: str = Field(description="รหัสสินค้า")
    item_id: str = Field(description="รหัสของตัวเลือกสินค้าที่เฉพาะเจาะจง")
    price: float = Field(description="ราคาของสินค้าขณะทำการซื้อ")
    options: Dict[str, str] = Field(description="ตัวเลือกที่เลือกสำหรับสินค้านี้")


OrderPaymentType = Literal["payment", "refund"]


class OrderPayment(BaseModel):
    """เป็นตัวแทนของธุรกรรมการชำระเงินหรือการคืนเงินสำหรับคำสั่งซื้อ"""

    transaction_type: OrderPaymentType = Field(
        description="ประเภทของธุรกรรม (การชำระเงินหรือการคืนเงิน)"
    )
    amount: float = Field(description="จำนวนเงินของธุรกรรม")
    payment_method_id: str = Field(description="รหัสวิธีการชำระเงินที่ใช้")


OrderStatus = Literal[
    "processed",
    "pending",
    "pending (item modified)",
    "delivered",
    "cancelled",
    "exchange requested",
    "return requested",
]

CancelReason = Literal["no longer needed", "ordered by mistake"]


class BaseOrder(BaseModel):
    """เป็นตัวแทนของคำสั่งซื้อพร้อมรายการ สถานะ รายละเอียดการจัดส่ง และรายละเอียดการชำระเงิน"""

    order_id: str = Field(description="ตัวระบุเฉพาะของคำสั่งซื้อ")
    user_id: str = Field(description="ตัวระบุเฉพาะของผู้ใช้")
    address: UserAddress = Field(description="ที่อยู่ของผู้ใช้")
    items: List[OrderItem] = Field(description="รายการสินค้าที่อยู่ในคำสั่งซื้อ")
    status: OrderStatus = Field(description="สถานะของคำสั่งซื้อ")
    fulfillments: List[OrderFullfilment] = Field(description="การจัดส่งของคำสั่งซื้อ")
    payment_history: List[OrderPayment] = Field(description="การชำระเงินของคำสั่งซื้อ")
    cancel_reason: Optional[CancelReason] = Field(
        description="เหตุผลในการยกเลิกคำสั่งซื้อ อาจเป็น 'ไม่ต้องการแล้ว' หรือ 'สั่งผิด'",
        default=None,
    )
    exchange_items: Optional[List[str]] = Field(
        description="สินค้าที่จะแลกเปลี่ยน", default=None
    )
    exchange_new_items: Optional[List[str]] = Field(
        description="สินค้าที่แลกมา", default=None
    )
    exchange_payment_method_id: Optional[str] = Field(
        description="รหัสวิธีการชำระเงินสำหรับการแลกเปลี่ยน", default=None
    )
    exchange_price_difference: Optional[float] = Field(
        description="ส่วนต่างของราคาสำหรับการแลกเปลี่ยน", default=None
    )
    return_items: Optional[List[str]] = Field(description="สินค้าที่จะส่งคืน", default=None)
    return_payment_method_id: Optional[str] = Field(
        description="รหัสวิธีการชำระเงินสำหรับการคืนเงิน", default=None
    )


class Order(BaseModel):
    """เป็นตัวแทนของคำสั่งซื้อพร้อมรายการ สถานะ รายละเอียดการจัดส่ง และรายละเอียดการชำระเงิน"""

    order_id: str = Field(description="ตัวระบุเฉพาะของคำสั่งซื้อ")
    user_id: str = Field(description="ตัวระบุเฉพาะของผู้ใช้")
    address: UserAddress = Field(description="ที่อยู่ของผู้ใช้")
    items: List[OrderItem] = Field(description="รายการสินค้าที่อยู่ในคำสั่งซื้อ")
    status: OrderStatus = Field(description="สถานะของคำสั่งซื้อ")
    fulfillments: List[OrderFullfilment] = Field(description="การจัดส่งของคำสั่งซื้อ")
    payment_history: List[OrderPayment] = Field(description="การชำระเงินของคำสั่งซื้อ")
    cancel_reason: Optional[CancelReason] = Field(
        description="เหตุผลในการยกเลิกคำสั่งซื้อ ควรเป็น 'ไม่ต้องการแล้ว' หรือ 'สั่งผิด'",
        default=None,
    )
    exchange_items: Optional[List[str]] = Field(
        description="รายการที่จะถูกแลกเปลี่ยน", default=None
    )
    exchange_new_items: Optional[List[str]] = Field(
        description="รายการที่แลกเป็น", default=None
    )
    exchange_payment_method_id: Optional[str] = Field(
        description="รหัสวิธีการชำระเงินสำหรับการแลกเปลี่ยน", default=None
    )
    exchange_price_difference: Optional[float] = Field(
        description="ส่วนต่างราคาสำหรับการแลกเปลี่ยน", default=None
    )
    return_items: Optional[List[str]] = Field(description="รายการที่จะส่งคืน", default=None)
    return_payment_method_id: Optional[str] = Field(
        description="รหัสวิธีการชำระเงินสำหรับการคืน", default=None
    )


class RetailDB(DB):
    """ฐานข้อมูลที่เก็บข้อมูลที่เกี่ยวข้องกับการค้าปลีกทั้งหมด รวมถึงสินค้า ผู้ใช้ และคำสั่งซื้อ"""

    products: Dict[str, Product] = Field(
        description="พจนานุกรมของสินค้าทั้งหมด จัดเก็บโดยใช้รหัสสินค้าเป็นดัชนี"
    )
    users: Dict[str, User] = Field(
        description="พจนานุกรมของผู้ใช้ทั้งหมด จัดเก็บโดยใช้รหัสผู้ใช้เป็นดัชนี"
    )
    orders: Dict[str, Order] = Field(
        description="พจนานุกรมของคำสั่งซื้อทั้งหมด จัดเก็บโดยใช้รหัสคำสั่งซื้อเป็นดัชนี"
    )

    def get_statistics(self) -> dict[str, Any]:
        """รับสถิติของฐานข้อมูล"""
        num_products = len(self.products)
        num_users = len(self.users)
        num_orders = len(self.orders)
        total_num_items = sum(
            len(product.variants) for product in self.products.values()
        )
        return {
            "num_products": num_products,
            "num_users": num_users,
            "num_orders": num_orders,
            "total_num_items": total_num_items,
        }


def get_db():
    return RetailDB.load(RETAIL_DB_PATH)


if __name__ == "__main__":
    db = get_db()
    print(db.get_statistics())
