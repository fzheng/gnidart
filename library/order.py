class Order:
    def __init__(self, stock: str, price: float, shares: float) -> None:
        if stock is None:
            raise ValueError("Stock ticker must not be None")
        if price <= 0.0:
            raise ValueError("Stock price must be Positive")
        if abs(shares) < 1e-7:
            raise ValueError("Shares cannot be Zero")

        self._stock = stock
        self._price = price
        self._shares = shares  # negative shares means sell

    @property
    def stock(self) -> str:
        return self._stock

    @property
    def price(self) -> float:
        return self._price

    @property
    def shares(self) -> float:
        return self._shares

    def is_buy(self) -> bool:
        return self._shares > 0


class Transaction(Order):
    def __init__(self, stock: str, price: float, shares: float, fee: float) -> None:
        super().__init__(stock, price, shares)

        if fee < 0:
            raise ValueError("Fee cannot be Negative")

        self._fee = fee

    @property
    def fee(self) -> float:
        return self._fee
