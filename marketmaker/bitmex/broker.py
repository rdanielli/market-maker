from marketmaker.bitmex import rest
from marketmaker.bitmex import settings
from marketmaker.bitmex import constants
from marketmaker.utils import dt

from time import sleep
import sys
from urllib2 import URLError


class BrokerInterface:
    def __init__(self):
        self.__settings = settings
        self.__constants = constants
        self.__dryRun = self.__settings.DRY_RUN
        self.__symbol = sys.argv[1] if len(sys.argv) > 1 else self.__settings.SYMBOL
        self.__api = rest.BitMEX(base_url=self.__settings.BASE_URL, symbol=self.__symbol, login=self.__settings.LOGIN, password=self.__settings.PASSWORD)

    def getConstants(self):
        return self.__constants

    def getSettings(self):
        return self.__settings

    def authenticate(self):
        if not self.__dryRun:
            self.__api.authenticate()

    def cancel_all_orders(self):
        if self.__dryRun:
            return

        print "Cancelling all existing orders."

        trade_data = self.__api.open_orders()
        #sleep(1)
        orders = trade_data

        for order in orders:
            print dt.timestamp_to_string(), "Cancelling:", order['side'], order['orderQty'], "@", order['price']
            while True:
                try:
                    self.__api.cancel(order['orderID'])
                    #sleep(1)
                except URLError as e:
                    print e.reason
                    sleep(10)
                except ValueError as e:
                    print e
                    sleep(10)
                else:
                    break

    def getInstrument(self):
        return self.__api.get_instrument()

    def getTicker(self):
        ticker = self.__api.ticker_data()

        if ticker["buy"] is not None:
            return {"last": float(ticker["last"]), "buy": float(ticker["buy"]), "sell": float(ticker["sell"]), "symbol": self.__symbol}
        raise Exception("Contract is not traded anymore. Update to current contract.")

    def getTradeData(self):
        if self.__dryRun:
            xbt = float(self.__settings.DRY_BTC)
            orders = []
        else:
            while True:
                try:
                    orders = self.__api.open_orders()
                    xbt = self.__api.funds()
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
            order = self.__api.buy(quantity, price)
        elif order_type == "Sell":
            order = self.__api.sell(quantity, price)
        else:
            print "Invalid order type"
            exit()

        return order