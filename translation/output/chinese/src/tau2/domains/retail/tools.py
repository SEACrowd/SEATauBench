"""零售领域的工具包。"""

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
    """零售领域的所有工具。"""

    db: RetailDB

    def __init__(self, db: RetailDB) -> None:
        super().__init__(db)

    def _get_order(self, order_id: str) -> Order:
        """从数据库中获取订单。

        Args:
            order_id: 订单 ID，例如“#W0000000”。注意订单 ID 开头有一个“#”符号。

        Returns:
            订单。

        Raises:
            ValueError: 如果未找到该订单。
        """
        if order_id not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[order_id]

    def _get_user(self, user_id: str) -> User:
        """从数据库中获取用户。

        Args:
            user_id: 用户 ID，例如“sara_doe_496”。

        Returns:
            用户。

        Raises:
            ValueError: 如果未找到该用户。
        """
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    def _get_product(self, product_id: str) -> Product:
        """从数据库中获取商品。

        Args:
            product_id: 商品 ID，例如“6086499569”。注意商品 ID 与条目 ID 不同。

        Returns:
            商品。

        Raises:
            ValueError: 如果未找到该商品。
        """
        if product_id not in self.db.products:
            raise ValueError("Product not found")
        return self.db.products[product_id]

    def _get_item(self, item_id: str) -> Variant:
        """从数据库中获取商品条目。

        参数：
            item_id：条目 ID，例如“6086499569”。请注意条目 ID 与商品 ID 不同。

        返回：
            商品条目。

        异常：
            ValueError：如果未找到该条目。
        """
        for _, product in self.db.products.items():
            if item_id in product.variants:
                return product.variants[item_id]

        raise ValueError("Item not found")
    def _get_variant(self, product_id: str, variant_id: str) -> Variant:
        """从数据库中获取变体。

        Args:
            product_id: 商品 ID，例如“6086499569”。注意商品 ID 与条目 ID 不同。
            variant_id: 变体 ID，例如“1008292230”。

        Returns:
            变体。

        Raises:
            ValueError: 如果未找到该变体。
        """
        product = self._get_product(product_id)
        if variant_id not in product.variants:
            raise ValueError("Variant not found")
        return product.variants[variant_id]

    def _get_payment_method(
        self, user_id: str, payment_method_id: str
    ) -> PaymentMethod:
        """从数据库中获取支付方式。

        Args:
            payment_method_id: 支付方式 ID，例如“gift_card_0000000”或“credit_card_0000000”。

        Returns:
            支付方式。

        Raises:
            ValueError: 如果未找到该支付方式。
        """
        user = self._get_user(user_id)
        if payment_method_id not in user.payment_methods:
            raise ValueError("Payment method not found")
        return user.payment_methods[payment_method_id]

    def _is_pending_order(self, order: Order) -> bool:
        """检查订单是否为 pending。这不是严格检查，也不打算用于在 pending 订单中执行 modify_items。

        Args:
            order: 订单。
        """
        return "pending" in order.status

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """
        计算一个数学表达式的结果。

        参数：
            expression：要计算的数学表达式，例如“2 + 2”。表达式可以包含数字、运算符（+、-、*、/）、括号以及空格。

        返回：
            数学表达式的结果。

        异常：
            ValueError：如果表达式无效。
        """
        if not all(char in "0123456789+-*/(). " for char in expression):
            raise ValueError("Invalid characters in expression")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))

    @is_tool(ToolType.WRITE)
    def cancel_pending_order(self, order_id: str, reason: str) -> Order:
        """取消一个 pending 订单。如果订单已处理或已送达，
        则无法取消。客服需要说明取消的具体细节，
        并询问用户是否明确确认（是/否）继续操作。若用户确认，
        订单状态将更改为“cancelled”，并退还款项。
        如果使用礼品卡付款，退款将立即计入用户的礼品卡余额；
        否则退款处理可能需要 5–7 个工作日。
        函数会在取消后返回订单详情。

        参数：
            order_id：订单编号，例如“#W0000000”。请注意订单编号开头有一个“#”符号。
            reason：取消原因，必须为“no longer needed”或“ordered by mistake”。

        返回：
            Order：取消后的订单详情。
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
        """将已送达订单中的商品换成同一产品类型的新商品。
        对于已送达订单，退货或换货只能由客服执行一次。
        客服需要说明换货的具体细节，并询问用户是否明确确认（是/否）继续操作。

        参数：
            order_id：订单编号，例如“#W0000000”。请注意订单编号开头有一个“#”符号。
            item_ids：要换出的商品 item id 列表，每个例如“1008292230”。列表中可能包含重复的商品。
            new_item_ids：要换入的商品 item id 列表，每个例如“1008292230”。
                         列表中可能包含重复的商品。每个新 item id 需要与相同位置的旧 item id 对应，且属于同一产品。
            payment_method_id：用于支付或接收商品差价退款的支付方式 id，
                             例如“gift_card_0000000”或“credit_card_0000000”。这些可以从用户或订单详情中查询。

        返回：
            Order：换货后的订单详情。

        异常：
            ValueError：如果订单未送达。
            ValueError：如果要换出的商品不存在。
            ValueError：如果新商品不存在或与旧商品不匹配。
            ValueError：如果要换货的商品数量不匹配。
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
        """通过名、姓和邮编查找用户 id。如果未找到用户，函数
        将返回错误信息。默认情况下通过邮箱查找用户 id，只有在
        通过邮箱未找到用户或用户不记得邮箱时才调用此函数。

        参数：
            first_name：客户的名，例如“John”。
            last_name：客户的姓，例如“Doe”。
            zip：客户的邮政编码，例如“12345”。

        返回：
            str：如果找到则返回用户 id，否则返回错误信息。

        异常：
            ValueError：如果未找到用户。
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
        """通过邮箱查找用户 id。如果未找到用户，函数将返回错误信息。

        参数：
            email：用户的邮箱，例如“something@example.com”。

        返回：
            str：如果找到则返回用户 id，否则返回错误信息。

        异常：
            ValueError：如果未找到用户。
        """
        for user_id, user in self.db.users.items():
            if user.email.lower() == email.lower():
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> Order:
        """获取订单的状态和详情。

        参数：
            order_id：订单编号，例如“#W0000000”。请注意订单编号开头有一个“#”符号。

        返回：
            Order：订单详情。

        异常：
            ValueError：如果未找到订单。
        """
        order = self._get_order(order_id)
        return order

    @is_tool(ToolType.READ)
    def get_product_details(self, product_id: str) -> Product:
        """获取某个产品的库存详情。

        参数：
            product_id：产品 id，例如“6086499569”。请注意 product id 与 item id 不同。

        返回：
            Product：产品详情。

        异常：
            ValueError：如果未找到产品。
        """
        product = self._get_product(product_id)
        return product

    @is_tool(ToolType.READ)
    def get_item_details(self, item_id: str) -> Variant:
        """获取商品条目的库存详情。

        参数：
            item_id：条目 ID，例如“6086499569”。请注意条目 ID 与商品 ID 不同。

        返回：
            Variant：商品条目详情。

        异常：
            ValueError：如果未找到该条目。
        """
        item = self._get_item(item_id)
        return item

    @is_tool(ToolType.READ)
    def get_user_details(self, user_id: str) -> User:
        """获取用户详情，包括其订单信息。

        参数：
            user_id：用户 id，例如“sara_doe_496”。

        返回：
            User：用户详情。

        异常：
            ValueError：如果未找到用户。
        """
        user = self._get_user(user_id)
        return user

    @is_tool(ToolType.READ)
    def list_all_product_types(self) -> str:
        """列出所有产品类型的名称和产品ID。
        每种产品类型都有多种不同的商品，每个商品都有唯一的商品ID和选项。
        商店中一共有50种产品类型。

        返回：
            str：一个JSON字符串，将产品名称映射到其产品ID，并按名称字母顺序排序。
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
        """修改一个pending订单的收货地址。客服需要说明修改详情，并要求用户明确确认（yes/no）后才能继续。

        参数：
            order_id：订单ID，例如“#W0000000”。注意订单ID开头有一个“#”符号。
            address1：地址第一行，例如“123 Main St”。
            address2：地址第二行，例如“Apt 1”或“”。
            city：城市，例如“San Francisco”。
            state：州/省，例如“CA”。
            country：国家，例如“USA”。
            zip：邮编，例如“12345”。

        返回：
            Order：修改后的订单详情。

        抛出：
            ValueError：如果订单不是pending。
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
        """将一个pending订单中的商品更换为相同产品类型的新商品。对于pending订单，此函数只能调用一次。客服需要说明换货详情，并要求用户明确确认（yes/no）后才能继续。

        参数：
            order_id：订单ID，例如“#W0000000”。注意订单ID开头有一个“#”符号。
            item_ids：要修改的商品ID，每个例如“1008292230”。列表中可能有重复商品。
            new_item_ids：要替换成的商品ID，每个例如“1008292230”。列表中可能有重复商品。每个新商品ID应与相同位置的原商品ID对应，并且属于同一产品。
            payment_method_id：用于支付或接收商品差价退款的支付方式ID，例如“gift_card_0000000”或“credit_card_0000000”。这些可以从用户信息或订单详情中查到。

        返回：
            Order：修改后的订单详情。

        抛出：
            ValueError：如果订单不是pending。
            ValueError：如果要修改的商品不存在。
            ValueError：如果新商品不存在或与原商品不匹配。
            ValueError：如果要修改的商品数量不匹配。
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
        """修改一个pending订单的支付方式。客服需要说明修改详情，并要求用户明确确认（yes/no）后才能继续。

        参数：
            order_id：订单ID，例如“#W0000000”。注意订单ID开头有一个“#”符号。
            payment_method_id：用于支付或接收商品差价退款的支付方式ID，例如“gift_card_0000000”或“credit_card_0000000”。这些可以从用户信息或订单详情中查到。

        返回：
            Order：修改后的订单详情。

        抛出：
            ValueError：如果订单不是pending。
            ValueError：如果支付方式不存在。
            ValueError：如果支付记录中有多笔支付。
            ValueError：如果新的支付方式与当前支付方式相同。
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
        """修改用户的默认地址。客服需要说明修改详情，并要求用户明确确认（yes/no）后才能继续。

        参数：
            user_id：用户ID，例如“sara_doe_496”。
            address1：地址第一行，例如“123 Main St”。
            address2：地址第二行，例如“Apt 1”或“”。
            city：城市，例如“San Francisco”。
            state：州/省，例如“CA”。
            country：国家，例如“USA”。
            zip：邮编，例如“12345”。

        返回：
            User：修改后的用户详情。

        抛出：
            ValueError：如果未找到用户。
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
        """退回一个已送达订单中的部分商品。
        订单状态将更改为“return requested”。
        客服需要说明退货详情，并要求用户明确确认（yes/no）后才能继续。
        用户将收到后续邮件，告知如何以及将商品退到哪里。

        参数：
            order_id：订单ID，例如“#W0000000”。注意订单ID开头有一个“#”符号。
            item_ids：要退货的商品ID，每个例如“1008292230”。列表中可能有重复商品。
            payment_method_id：用于支付或接收商品差价退款的支付方式ID，例如“gift_card_0000000”或“credit_card_0000000”。
                             这些可以从用户信息或订单详情中查到。

        返回：
            Order：发起退货请求后的订单详情。

        抛出：
            ValueError：如果订单不是已送达状态。
            ValueError：如果支付方式不是原始支付方式或礼品卡。
            ValueError：如果要退货的商品不存在。
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
        将用户转接给人工客服，并附上用户问题的摘要。
        仅在以下情况下转接：
         -  用户明确要求人工客服
         -  根据政策和可用工具，你无法解决用户的问题。

        参数：
            summary：用户问题的摘要。

        返回：
            一条消息，表示用户已被转接至人工客服。
        """
        return "Transfer successful"


if __name__ == "__main__":
    from tau2.domains.retail.utils import RETAIL_DB_PATH

    retail = RetailTools(RetailDB.load(RETAIL_DB_PATH))
    print(retail.get_statistics())
