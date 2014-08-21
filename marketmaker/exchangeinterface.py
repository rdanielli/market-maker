from marketmaker.bitmex import broker
from marketmaker.utils import dt

from time import sleep
import sys
from urllib2 import URLError


class ExchangeInterface:
    def __init__(self, settings, dry_run=False):
        self.__settings = settings
        self.dry_run = dry_run
        self.symbol = sys.argv[1] if len(sys.argv) > 1 else self.__settings.SYMBOL
        self.bitmex = broker.BitMEX(base_url=self.__settings.BASE_URL, symbol=self.symbol, login=self.__settings.LOGIN, password=self.__settings.PASSWORD)

    def authenticate(self):
        if not self.dry_run:
            self.bitmex.authenticate()

    def cancel_all_orders(self):
        if self.dry_run:
            return

        print "Resetting current position. Cancelling all existing orders."

        trade_data = self.bitmex.open_orders(); sleep(1)
        orders = trade_data

        for order in orders:
            print dt.timestamp_to_string(), "Cancelling:", order['side'], order['orderQty'], "@", order['price']
            while True:
                try:
                    self.bitmex.cancel(order['orderID']); sleep(1)
                except URLError as e:
                    print e.reason
                    sleep(10)
                except ValueError as e:
                    print e
                    sleep(10)
                else:
                    break

    def get_instrument(self):
        return self.bitmex.get_instrument()

    def get_ticker(self):
        ticker = self.bitmex.ticker_data()

        if ticker["buy"] is not None:
            return {"last": float(ticker["last"]), "buy": float(ticker["buy"]), "sell": float(ticker["sell"]), "symbol": self.symbol}
        raise Exception("Contract is not traded anymore. Update to current contract.")

    def get_trade_data(self):
        if self.dry_run:
            xbt = float(self.__settings.DRY_BTC)
            orders = []
        else:
            while True:
                try:
                    orders = self.bitmex.open_orders()
                    xbt = self.bitmex.funds()
                    sleep(1)
                except URLError as e:
                    print e.reason
                    sleep(10)
                except ValueError as e:
                    print e
                    sleep(10)
                else:
                    break

        return {"xbt": xbt, "orders": orders}

    def place_order(self, price, quantity, order_type):
        if self.__settings.DRY_RUN:
            return {'orderID': 'dry_run_order', 'orderQty': quantity, 'price': price}

        if order_type == "Buy":
            order = self.bitmex.buy(quantity, price)
        elif order_type == "Sell":
            order = self.bitmex.sell(quantity, price)
        else:
            print "Invalid order type"
            exit()

        return order