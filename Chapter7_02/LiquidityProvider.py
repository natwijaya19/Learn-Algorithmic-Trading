from collections import deque
from random import randrange, sample, seed


class LiquidityProvider:
    order_id: int
    orders: list[dict[str, str | int]] = []

    def __init__(self, lp_2_gateway: deque = None):
        self.orders = []
        self.order_id = 0
        seed(0)
        self.lp_2_gateway = lp_2_gateway

    def lookup_orders(self, id: int) -> tuple[dict[str, str | int] | None, int | None]:
        """
        This method is used to lookup orders in the order book
        """
        count = 0
        for o in self.orders:
            if o["id"] == id:
                return o, count
            count += 1
        return None, None

    def insert_manual_order(self, order: dict[str, str | int]):
        """
        This method is used to insert orders in the order book
        """
        if self.lp_2_gateway is None:
            print("simulation mode")
            return order
        self.lp_2_gateway.append(order.copy())

    def read_tick_data_from_data_source(self):
        pass

    def generate_random_order(self):
        price: int = randrange(8, 12)
        quantity: int = randrange(1, 10) * 100
        side: str = sample(["buy", "sell"], 1)[0]
        order_id: int = randrange(0, self.order_id + 1)
        o: tuple[int, int] | tuple[None, None] = self.lookup_orders(order_id)

        new_order: bool = False
        if o is None:
            action = "new"
            new_order = True
        else:
            action = sample(["modify", "delete"], 1)[0]

        ord: dict[str, str | int] = {
            "id": self.order_id,
            "price": price,
            "quantity": quantity,
            "side": side,
            "action": action,
        }

        if not new_order:
            self.order_id += 1
            self.orders.append(ord)

        if not self.lp_2_gateway:
            print("simulation mode")
            return ord
        self.lp_2_gateway.append(ord.copy())
