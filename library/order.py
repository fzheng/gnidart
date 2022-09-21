class Order:
    def __init__(self, stock: str, price: float, quantity: float) -> None:
        if stock is None:
            raise ValueError("Stock ticker must not be None")
        if price <= 0.0:
            raise ValueError("Stock price must be Positive")
        if abs(quantity) < 1e-4:
            raise ValueError("Quantity cannot be Zero")

        self._stock = stock
        self._price = price
        self._quantity = quantity  # negative quantity means sell

    @property
    def stock(self):
        return self._stock

    @property
    def price(self):
        return self._price

    @property
    def quantity(self):
        return self._quantity
