class Portfolio:
    """
    A custom portfolio may be created by instantiating the Portfolio class and adding stocks, prices, and shares.
    This is demonstrated in the many of the unit tests in the tests.py file.
    """

    def __init__(self, balance=10000):
        self._portfolio = {'**CASH**': {'Shares': balance, 'Price': 1.0, 'Updates': 1}}

    def update(self, price, ticker):
        if ticker in self._portfolio:
            self._portfolio[ticker]['Price'] = price
            self._portfolio[ticker]['Updates'] = self._portfolio[ticker]['Updates'] + 1
        else:
            self._portfolio[ticker] = {}
            self._portfolio[ticker]['Price'] = price
            self._portfolio[ticker]['Shares'] = 0
            self._portfolio[ticker]['Updates'] = 1

    @property
    def balance(self):
        return self._portfolio['**CASH**']['Shares']

    @balance.setter
    def balance(self, balance):
        self._portfolio['**CASH**']['Shares'] = balance

    def adjust_balance(self, delta):
        self._portfolio['**CASH**']['Shares'] = self.balance + delta

    def __contains__(self, item):
        return item in self._portfolio

    def value_summary(self, date):
        value_sum = self.get_total_value()
        return '%s : Stock value: $%.2f, Cash: $%.2f, Total $%.2f' % (date, value_sum - self.balance, self.balance, value_sum)

    def get_total_value(self):
        total_value = 0
        for stock in self._portfolio.values():
            total_value += stock['Shares'] * stock['Price']
        return total_value

    def get_value(self, ticker):
        return self.get_shares(ticker) * self.get_shares(ticker)

    def get_price(self, ticker):
        return self._portfolio[ticker]['Price']

    def get_shares(self, ticker):
        return self._portfolio[ticker]['Shares']

    def get_update_count(self, ticker):
        return self._portfolio[ticker]['Updates']

    def set_shares(self, ticker, shares):
        self._portfolio[ticker]['Shares'] = shares

    def update_shares(self, ticker, share_delta):
        self.set_shares(ticker, self.get_shares(ticker) + share_delta)

    def update_trade(self, ticker, share_delta, price, fee):
        # Assumes negative shares are sells, requires validation from Controller
        self.set_shares(ticker, self.get_shares(ticker) + share_delta)
        self.adjust_balance(-(price * share_delta + fee))

    def __str__(self):
        return self._portfolio.__str__()
