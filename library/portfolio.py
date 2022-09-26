from library.order import Transaction


class Position:
    def __init__(self, stock: str, price: float, shares: float = 0) -> None:
        if stock is None:
            raise ValueError("Stock ticker must not be None")
        if price <= 0:
            raise ValueError("Price must not be Negative")

        self._stock = stock
        self._price = price
        self._shares = shares
        self._cost_per_share = price
        self._updates = 0

    @property
    def stock(self) -> str:
        return self._stock

    @property
    def shares(self) -> float:
        return self._shares

    @shares.setter
    def shares(self, shares: float) -> None:
        self._shares = shares

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, price: float) -> None:
        if price <= 0:
            raise ValueError("Price can not be Negative")

        self._price = price

    @property
    def cost_per_share(self) -> float:
        return self._cost_per_share

    @property
    def updates(self) -> int:
        return self._updates

    @updates.setter
    def updates(self, updates: int) -> None:
        self._updates = updates

    def add_transaction(self, txn: Transaction) -> None:
        if self._stock != txn.stock:
            raise ValueError("Transaction stock ticker must be the same as position ticker")

        if self._shares + txn.shares < 0:
            raise ValueError("Transaction can not sell more shares than current position")

        if txn.is_buy():
            total_cost = self._cost_per_share * self._shares + txn.price * txn.shares
            self._shares += txn.shares
            if self._shares > 1e-7:
                # for liquidate, don't need update cost per share
                self._cost_per_share = total_cost / self._shares
        else:
            # Future improvement includes using FIFO here
            self._shares += txn.shares

        self._price = txn.price

    def get_gain_or_loss(self) -> float:
        if self._shares > 0:
            return self._price / self._cost_per_share - 1
        return 0


class Portfolio:
    """
    A custom portfolio may be created by instantiating the Portfolio class and adding stocks, prices, and shares.
    This is demonstrated in the many of the unit tests in the component_tests.py file.
    """
    __cash = '**CASH**'

    def __init__(self, balance: float) -> None:
        if balance < 0:
            raise ValueError("Balance value must not be Negative")

        self._portfolio = {Portfolio.__cash: Position(Portfolio.__cash, 1.0, balance)}

    def update(self, price, ticker):
        if ticker in self._portfolio:
            self._portfolio[ticker].price = price
            self._portfolio[ticker].updates += 1
        else:
            self._portfolio[ticker] = Position(ticker, price, 0)
            self._portfolio[ticker].updates = 1

    @property
    def cash(self):
        return self._portfolio[Portfolio.__cash].shares

    @cash.setter
    def cash(self, cash: float):
        self._portfolio[Portfolio.__cash].shares = cash

    def adjust_cash(self, delta):
        self._portfolio[Portfolio.__cash].shares = self.cash + delta

    def __contains__(self, item):
        return item in self._portfolio

    def value_summary(self, date):
        value_sum = self.get_total_value()
        return '%s : Stock value: $%.2f, Cash: $%.2f, Total $%.2f' % (
            date, value_sum - self.cash, self.cash, value_sum)

    def get_total_value(self):
        total_value = 0
        for stock in self._portfolio.values():
            total_value += stock.shares * stock.price
        return total_value

    def get_value(self, ticker):
        return self.get_shares(ticker) * self.get_shares(ticker)

    def get_price(self, ticker):
        return self._portfolio[ticker].price

    def get_shares(self, ticker):
        return self._portfolio[ticker].shares

    def get_update_count(self, ticker):
        return self._portfolio[ticker].updates

    def set_shares(self, ticker, shares):  # TODO: retire set_shares
        self._portfolio[ticker].shares = shares

    def update_trade(self, txn: Transaction):
        # Assumes negative shares are sells, requires validation from Controller
        self._portfolio[txn.stock].add_transaction(txn)
        self._portfolio[Portfolio.__cash].shares = self.cash - (txn.price * txn.shares + txn.fee)

    def __str__(self):
        return self._portfolio.__str__()
