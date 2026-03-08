"""Toolkit untuk domain ritel."""

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
    """Semua alat untuk domain ritel."""

    db: RetailDB

    def __init__(self, db: RetailDB) -> None:
        super().__init__(db)

    def _get_order(self, order_id: str) -> Order:
        """Ambil pesanan dari basis data.

        Argumen:
            order_id: ID pesanan, seperti '#W0000000'. Perhatikan ada simbol '#' di awal ID pesanan.

        Mengembalikan:
            Pesanan.

        Menaikkan:
            ValueError: Jika pesanan tidak ditemukan.
        """
        if order_id not in self.db.orders:
            raise ValueError("Order not found")
        return self.db.orders[order_id]

    def _get_user(self, user_id: str) -> User:
        """Ambil pengguna dari basis data.

        Argumen:
            user_id: ID pengguna, seperti 'sara_doe_496'.

        Mengembalikan:
            Pengguna.

        Menaikkan:
            ValueError: Jika pengguna tidak ditemukan.
        """
        if user_id not in self.db.users:
            raise ValueError("User not found")
        return self.db.users[user_id]

    def _get_product(self, product_id: str) -> Product:
        """Ambil produk dari basis data.

        Argumen:
            product_id: ID produk, seperti '6086499569'. Perhatikan ID produk berbeda dari ID item.

        Mengembalikan:
            Produk.

        Menaikkan:
            ValueError: Jika produk tidak ditemukan.
        """
        if product_id not in self.db.products:
            raise ValueError("Product not found")
        return self.db.products[product_id]

    def _get_variant(self, product_id: str, variant_id: str) -> Variant:
        """Ambil varian dari basis data.

        Argumen:
            product_id: ID produk, seperti '6086499569'. Perhatikan ID produk berbeda dari ID item.
            variant_id: ID varian, seperti '1008292230'.

        Mengembalikan:
            Varian.

        Menaikkan:
            ValueError: Jika varian tidak ditemukan.
        """
        product = self._get_product(product_id)
        if variant_id not in product.variants:
            raise ValueError("Variant not found")
        return product.variants[variant_id]

    def _get_payment_method(
        self, user_id: str, payment_method_id: str
    ) -> PaymentMethod:
        """Ambil metode pembayaran dari basis data.

        Argumen:
            payment_method_id: ID metode pembayaran, seperti 'gift_card_0000000' atau 'credit_card_0000000'.

        Mengembalikan:
            Metode pembayaran.

        Menaikkan:
            ValueError: Jika metode pembayaran tidak ditemukan.
        """
        user = self._get_user(user_id)
        if payment_method_id not in user.payment_methods:
            raise ValueError("Payment method not found")
        return user.payment_methods[payment_method_id]

    def _is_pending_order(self, order: Order) -> bool:
        """Periksa apakah pesanan pending. Ini bukan pemeriksaan yang ketat, dan tidak dimaksudkan untuk digunakan untuk modify_items pada pesanan pending.

        Argumen:
            order: Pesanan.
        """
        return "pending" in order.status

    @is_tool(ToolType.GENERIC)
    def calculate(self, expression: str) -> str:
        """
        Hitung hasil dari sebuah ekspresi matematika.

        Args:
            expression: Ekspresi matematika yang akan dihitung, seperti '2 + 2'. Ekspresi dapat berisi angka, operator (+, -, *, /), tanda kurung, dan spasi.

        Returns:
            Hasil dari ekspresi matematika.

        Raises:
            ValueError: Jika ekspresi tidak valid.
        """
        if not all(char in "0123456789+-*/(). " for char in expression):
            raise ValueError("Invalid characters in expression")
        return str(round(float(eval(expression, {"__builtins__": None}, {})), 2))

    @is_tool(ToolType.WRITE)
    def cancel_pending_order(self, order_id: str, reason: str) -> Order:
        """Batalkan pesanan pending. Jika pesanan sudah diproses atau dikirim,
        pesanan tidak dapat dibatalkan. Agen perlu menjelaskan detail pembatalan
        dan meminta konfirmasi pengguna secara eksplisit (ya/tidak) untuk melanjutkan. Jika pengguna mengonfirmasi,
        status pesanan akan diubah menjadi 'cancelled' dan pembayaran akan dikembalikan.
        Pengembalian dana akan langsung ditambahkan ke saldo kartu hadiah pengguna jika pembayaran
        dilakukan menggunakan kartu hadiah; jika tidak, pengembalian dana akan memerlukan 5-7 hari kerja untuk diproses.
        Fungsi mengembalikan detail pesanan setelah pembatalan.

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
        """Tukar item dalam pesanan yang sudah dikirim menjadi item baru dengan jenis produk yang sama.
        Untuk pesanan yang sudah dikirim, pengembalian atau penukaran hanya dapat dilakukan satu kali oleh agen.
        Agen perlu menjelaskan detail penukaran dan meminta konfirmasi pengguna secara eksplisit (ya/tidak) untuk melanjutkan.

        Args:
            order_id: ID pesanan, seperti '#W0000000'. Hati-hati, ada simbol '#' di awal ID pesanan.
            item_ids: ID item yang akan ditukar, masing-masing seperti '1008292230'. Bisa ada item duplikat dalam daftar.
            new_item_ids: ID item pengganti, masing-masing seperti '1008292230'.
                         Bisa ada item duplikat dalam daftar. Setiap ID item baru harus sesuai dengan ID item
                         pada posisi yang sama dan merupakan produk yang sama.
            payment_method_id: ID metode pembayaran untuk membayar atau menerima pengembalian dana atas selisih harga item,
                             seperti 'gift_card_0000000' atau 'credit_card_0000000'. Ini dapat dilihat
                             dari detail pengguna atau pesanan.

        Returns:
            Order: Detail pesanan setelah penukaran.

        Raises:
            ValueError: Jika pesanan belum dikirim.
            ValueError: Jika item yang akan ditukar tidak ada.
            ValueError: Jika item baru tidak ada atau tidak cocok dengan item lama.
            ValueError: Jika jumlah item yang akan ditukar tidak sesuai.
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
        """Temukan ID pengguna berdasarkan nama depan, nama belakang, dan kode pos. Jika pengguna tidak ditemukan, fungsi
        akan mengembalikan pesan kesalahan. Secara default, temukan ID pengguna melalui email, dan hanya panggil fungsi ini
        jika pengguna tidak ditemukan melalui email atau tidak dapat mengingat email.

        Args:
            first_name: Nama depan pelanggan, seperti 'John'.
            last_name: Nama belakang pelanggan, seperti 'Doe'.
            zip: Kode pos pelanggan, seperti '12345'.

        Returns:
            str: ID pengguna jika ditemukan; jika tidak, pesan kesalahan.

        Raises:
            ValueError: Jika pengguna tidak ditemukan.
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
        """Temukan ID pengguna berdasarkan email. Jika pengguna tidak ditemukan, fungsi akan mengembalikan pesan kesalahan.

        Args:
            email: Email pengguna, seperti 'something@example.com'.

        Returns:
            str: ID pengguna jika ditemukan; jika tidak, pesan kesalahan.

        Raises:
            ValueError: Jika pengguna tidak ditemukan.
        """
        for user_id, user in self.db.users.items():
            if user.email.lower() == email.lower():
                return user_id
        raise ValueError("User not found")

    @is_tool(ToolType.READ)
    def get_order_details(self, order_id: str) -> Order:
        """Dapatkan status dan detail sebuah pesanan.

        Args:
            order_id: ID pesanan, seperti '#W0000000'. Hati-hati, ada simbol '#' di awal ID pesanan.

        Returns:
            Order: Detail pesanan.

        Raises:
            ValueError: Jika pesanan tidak ditemukan.
        """
        order = self._get_order(order_id)
        return order

    @is_tool(ToolType.READ)
    def get_product_details(self, product_id: str) -> Product:
        """Dapatkan detail inventaris sebuah produk.

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
    def get_user_details(self, user_id: str) -> User:
        """Dapatkan detail seorang pengguna, termasuk pesanan mereka.

        Args:
            user_id: ID pengguna, seperti 'sara_doe_496'.

        Returns:
            User: Detail pengguna.

        Raises:
            ValueError: Jika pengguna tidak ditemukan.
        """
        user = self._get_user(user_id)
        return user

    @is_tool(ToolType.READ)
    def list_all_product_types(self) -> str:
        """Cantumkan nama dan id produk dari semua jenis produk.
        Setiap jenis produk memiliki berbagai item yang berbeda dengan id item dan opsi yang unik.
        Hanya ada 50 jenis produk di toko.

        Returns:
            str: Sebuah string JSON yang memetakan nama produk ke ID produknya, diurutkan secara alfabet berdasarkan nama.
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
        """Ubah alamat pengiriman untuk pesanan pending. Agen perlu menjelaskan detail perubahan dan meminta konfirmasi eksplisit dari pengguna (ya/tidak) untuk melanjutkan.

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
        """Ubah item dalam pesanan pending menjadi item baru dengan jenis produk yang sama. Untuk pesanan pending, fungsi ini hanya dapat dipanggil sekali. Agen perlu menjelaskan detail penukaran dan meminta konfirmasi eksplisit dari pengguna (ya/tidak) untuk melanjutkan.

        Args:
            order_id: ID pesanan, seperti '#W0000000'. Perhatikan ada simbol '#' di awal ID pesanan.
            item_ids: ID item yang akan diubah, masing-masing seperti '1008292230'. Bisa ada item duplikat dalam daftar.
            new_item_ids: ID item pengganti, masing-masing seperti '1008292230'. Bisa ada item duplikat dalam daftar. Setiap ID item baru harus sesuai dengan ID item pada posisi yang sama dan merupakan produk yang sama.
            payment_method_id: ID metode pembayaran untuk membayar atau menerima pengembalian dana atas selisih harga item, seperti 'gift_card_0000000' atau 'credit_card_0000000'. Ini dapat dilihat dari pengguna atau detail pesanan.

        Returns:
            Order: Detail pesanan setelah perubahan.

        Raises:
            ValueError: Jika pesanan tidak pending.
            ValueError: Jika item yang akan diubah tidak ada.
            ValueError: Jika item baru tidak ada atau tidak cocok dengan item lama.
            ValueError: Jika jumlah item yang akan diubah tidak sesuai.
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
        """Ubah metode pembayaran untuk pesanan pending. Agen perlu menjelaskan detail perubahan dan meminta konfirmasi eksplisit dari pengguna (ya/tidak) untuk melanjutkan.

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
        """Ubah alamat default seorang pengguna. Agen perlu menjelaskan detail perubahan dan meminta konfirmasi eksplisit dari pengguna (ya/tidak) untuk melanjutkan.

        Args:
            user_id: ID pengguna, seperti 'sara_doe_496'.
            address1: Baris pertama alamat, seperti '123 Main St'.
            address2: Baris kedua alamat, seperti 'Apt 1' atau ''.
            city: Kota, seperti 'San Francisco'.
            state: Negara bagian, seperti 'CA'.
            country: Negara, seperti 'USA'.
            zip: Kode pos, seperti '12345'.

        Returns:
            User: Detail pengguna setelah perubahan.

        Raises:
            ValueError: Jika pengguna tidak ditemukan.
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
        """Kembalikan beberapa item dari pesanan yang telah diterima.
        Status pesanan akan diubah menjadi 'return requested'.
        Agen perlu menjelaskan detail pengembalian dan meminta konfirmasi eksplisit dari pengguna (ya/tidak) untuk melanjutkan.
        Pengguna akan menerima email tindak lanjut tentang cara dan ke mana mengembalikan item.

        Args:
            order_id: ID pesanan, seperti '#W0000000'. Perhatikan ada simbol '#' di awal ID pesanan.
            item_ids: ID item yang akan dikembalikan, masing-masing seperti '1008292230'. Bisa ada item duplikat dalam daftar.
            payment_method_id: ID metode pembayaran untuk membayar atau menerima pengembalian dana atas selisih harga item, seperti 'gift_card_0000000' atau 'credit_card_0000000'.
                             Ini dapat dilihat dari pengguna atau detail pesanan.

        Returns:
            Order: Detail pesanan setelah meminta pengembalian.

        Raises:
            ValueError: Jika pesanan belum diterima.
            ValueError: Jika metode pembayaran bukan metode pembayaran asli atau kartu hadiah.
            ValueError: Jika item yang akan dikembalikan tidak ada.
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
        Alihkan pengguna ke agen manusia, beserta ringkasan masalah pengguna.
        Hanya alihkan jika
         -  pengguna secara eksplisit meminta agen manusia
         -  berdasarkan kebijakan dan alat yang tersedia, Anda tidak dapat menyelesaikan masalah pengguna.

        Args:
            summary: Ringkasan masalah pengguna.

        Returns:
            Sebuah pesan yang menyatakan pengguna telah dialihkan ke agen manusia.
        """
        return "Transfer successful"


if __name__ == "__main__":
    from tau2.domains.retail.utils import RETAIL_DB_PATH

    retail = RetailTools(RetailDB.load(RETAIL_DB_PATH))
    print(retail.get_statistics())
