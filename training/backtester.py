import datetime as dt
import logging
import sys
from multiprocessing import Process, Queue

import numpy as np
import pandas as pd
from pandas_datareader import DataReader

from library.algorithm import Algorithm
from library.order import Order
from library.portfolio import Portfolio


class OrderApi:
    def __init__(self):
        self._slippage_std = .01
        self._prob_of_failure = .0001
        self._fee_per_share = .005
        self._fixed_fee = 0
        self._allow_order_fail = False
        self._allow_volatile = False

    def process_order(self, order: Order):
        # Simulate the price volatility
        slippage = np.random.normal(0, self._slippage_std, size=1)[0] if self._allow_volatile else 0.

        # Simulate the order processing so that it may fail
        if (np.random.choice([False, True], p=[self._prob_of_failure, 1 - self._prob_of_failure], size=1)[0]) \
                or not self._allow_order_fail:
            return order.stock, order.price * (1 + slippage), order.quantity, self.calculate_fee(order)

    def calculate_fee(self, order: Order) -> float:
        return self._fee_per_share * abs(order.quantity) + self._fixed_fee


class DataSource:
    """
    Data source for the backtester. Must implement a "get_data" function
    which streams data from the data source.

    The basic DataSource included is built on top of pandas DataReader.
    This source may be modified to be any realtime data feed. The DataSource's single requirement is
    to fill a Queue class with data from the feed. The data should be in the form of a tuple
    (Timestamp/Id, Ticker str, Price float).
    """

    def __init__(self, source='yahoo', tickers=None, start=dt.datetime(2016, 1, 1),
                 end=dt.datetime.today()):
        if tickers is None:
            raise ValueError("tickers must not be None")
        self._source = []
        self._logger = logging.getLogger(__name__)
        self.set_source(source=source, tickers=tickers, start=start, end=end)

    @classmethod
    def process(cls, queue, source=None):
        source = cls() if source is None else source
        while True:
            data = source.get_data()
            if data is not None:
                queue.put(data)
                if data == 'POISON':
                    break

    def set_source(self, source, tickers, start, end):
        prices = pd.DataFrame()
        counter = 0
        for ticker in tickers:
            try:
                self._logger.info('Loading ticker %.0f%%' % (100.0 * counter / len(tickers)))
                prices[ticker] = DataReader(ticker, source, start, end).loc[:, 'Close']
            except Exception as e:
                self._logger.error(e)
                pass
            counter += 1

        history = []
        for row in prices.iterrows():
            timestamp = row[0]
            series = row[1]
            vals = series.values
            indx = series.index
            for k in range(0, len(vals), 1):
                if np.isfinite(vals[k]):
                    history.append((timestamp, indx[k], vals[k]))

        self._source = history
        self._logger.info('Loaded data!')

    def get_data(self):
        try:
            return self._source.pop(0)
        except IndexError:
            return 'POISON'


class Controller:
    def __init__(self, portfolio=None, algorithm=None):
        self._logger = logging.getLogger(__name__)
        self._portfolio = Portfolio() if portfolio is None else portfolio
        self._algorithm = Algorithm() if algorithm is None else algorithm
        self._order_api = OrderApi()

    @classmethod
    def backtest(cls, queue, controller=None):
        controller = cls() if controller is None else controller
        try:
            while True:
                if not queue.empty():
                    o = queue.get()
                    # controller._logger.debug(o)

                    if o == 'POISON':
                        break

                    timestamp = o[0]
                    ticker = o[1]
                    price = o[2]

                    # Update pricing
                    controller.process_pricing(ticker=ticker, price=price)

                    # Generate Orders
                    orders = controller._algorithm.generate_orders(timestamp, controller._portfolio)

                    # Process orders
                    if len(orders) > 0:
                        for order in orders:
                            controller.process_order(order)

                        controller._logger.info(controller._portfolio.value_summary(timestamp))
                        print(controller._portfolio.value_summary(timestamp))

        except Exception as e:
            print(e)
        finally:
            controller._logger.info(controller._portfolio.value_summary(None))
            print(controller._portfolio.value_summary(None))

    def process_order(self, order):
        success = False
        receipt = self._order_api.process_order(order)
        if receipt is not None:
            success = self.process_receipt(receipt)

        if order is None:
            self._logger.info(('{order_type} failed: %s' % order).format(
                order_type='Sell' if order is not None and order.quantity < 0 else 'Buy'))
            print(('{order_type} failed: %s' % order).format(
                order_type='Sell' if order is not None and order.quantity < 0 else 'Buy'))
        elif success is False:
            self._logger.info(
                ('{order_type} failed: %s at $%s for %s shares' % (order.stock, order.price, order.quantity)).format(
                    order_type='Sell' if order is not None and order.quantity < 0 else 'Buy'))
            print(('{order_type} failed: %s at $%s for %s shares' % (order.stock, order.price, order.quantity)).format(
                order_type='Sell' if order is not None and order.quantity < 0 else 'Buy'))

    def process_receipt(self, receipt):
        ticker = receipt[0]
        price = receipt[1]
        share_delta = receipt[2]
        fee = receipt[3]
        temp = self._portfolio.balance - (price * share_delta + fee)
        if temp > 0:
            if share_delta < 0 and -share_delta > self._portfolio.get_shares(ticker):
                # Liquidate
                share_delta = -self._portfolio.get_shares(ticker)
                fee = self._order_api.calculate_fee(Order(ticker, price, share_delta))
                if fee > abs(share_delta * price):
                    return False

            self._portfolio.update_trade(ticker=ticker, price=price, share_delta=share_delta, fee=fee)
            if share_delta > 0:
                self._logger.debug(
                    'Bought %s for %.1f shares at $%.2f with fee $%.2f' % (ticker, share_delta, price, fee))
                print('Bought %s for %.1f shares at $%.2f with fee $%.2f' % (ticker, share_delta, price, fee))
            else:
                self._logger.debug(
                    'Sold %s for %.1f shares at $%.2f with fee $%.2f' % (ticker, -share_delta, price, fee))
                print('Sold %s for %.1f shares at $%.2f with fee $%.2f' % (ticker, -share_delta, price, fee))

            return True

        return False

    def process_pricing(self, ticker, price):
        self._portfolio.update(price=price, ticker=ticker)
        self._algorithm.update(stock=ticker, price=price)


class Backtester:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._settings = {}

        self._default_settings = {
            'Portfolio': Portfolio(),
            'Algorithm': Algorithm(),
            'Source': 'yahoo',
            'Start_Day': dt.datetime(2022, 1, 1),
            'End_Day': dt.datetime.today(),
            'Tickers': ['AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL']
        }

    def set_portfolio(self, portfolio):
        self._settings['Portfolio'] = portfolio

    def set_algorithm(self, algorithm):
        self._settings['Algorithm'] = algorithm

    def set_source(self, source):
        self._settings['Source'] = source

    def set_start_date(self, date):
        self._settings['Start_Day'] = date

    def set_end_date(self, date):
        self._settings['End_Day'] = date

    def set_stock_universe(self, stocks):
        self._settings['Tickers'] = stocks

    def get_setting(self, setting):
        return self._settings[setting] if setting in self._settings else self._default_settings[setting]

    def backtest(self):
        # Initiate run
        q = Queue()
        ds = DataSource(
            source=self.get_setting('Source'),
            start=self.get_setting('Start_Day'),
            end=self.get_setting('End_Day'),
            tickers=self.get_setting('Tickers'),
        )
        c = Controller(
            portfolio=self.get_setting('Portfolio'),
            algorithm=self.get_setting('Algorithm'),
        )

        p = Process(target=DataSource.process, args=(q, ds))
        p1 = Process(target=Controller.backtest, args=(q, c))

        p.start()
        p1.start()
        p.join()
        p1.join()


if __name__ == '__main__':
    # filepath = 'run.log'
    # if os.path.exists(filepath):
    #     os.remove(filepath)
    #

    # Setup Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level=logging.DEBUG)
    root_logger.addHandler(logging.StreamHandler(sys.stdout))

    # root_logger.addHandler(logging.FileHandler(filename=filepath))
    # multiprocessing_logging.install_mp_handler()

    b = Backtester()
    b.backtest()
