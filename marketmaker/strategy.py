from datetime import datetime
from time import sleep
import random
import sys


from marketmaker.utils import dt


class OrderStrategy:
    """Class containing the order logic

    :param broker: a broker class
    :type broker: :class:'marketmaker.broker'

    """
    def __init__(self, broker):
        self.__broker = broker
        self.__settings = self.__broker.getSettings()
        self.__constants = self.__broker.getConstants()
        self.__instrument = self.__broker.getInstrument()

        if self.__settings.DRY_RUN:
            print "Initializing dry run. Orders printed below represent what would be posted to BitMEX."
        else:
            print "Order Manager initializing, connecting to BitMEX. Dry run disabled, executing real trades."

        print "Using symbol %s." % self.__settings.SYMBOL
        self.__broker.authenticate()
        self.start_time = datetime.now()

    def exit(self):
        self.__broker.cancel_all_orders()

    def reset(self):
        self.__broker.cancel_all_orders()
        self.orders = {}

        ticker = self.get_ticker()

        trade_data = self.__broker.getTradeData()
        self.start_xbt = trade_data["xbt"]
        print dt.timestamp_to_string(), "Current XBT Balance: %.6f" % self.start_xbt

        # Sanity check:
        if self.get_position(-1) >= ticker["sell"] or self.get_position(1) <= ticker["buy"]:
            print self.get_position(-1), ticker["sell"], self.get_position(1), ticker["buy"]
            print "Sanity check failed, exchange data is screwy"
            exit()

        self.place_initial_orders()

        if self.__settings.DRY_RUN:
            exit()

    def place_initial_orders(self):
        for i in range(1, self.__settings.ORDER_PAIRS + 1):
            self.place_order(-i, "Buy")
            self.place_order(i, "Sell")
            #sleep(1)

    def get_ticker(self):
        ticker = self.__broker.getTicker()
        midpoint = (ticker["buy"] + ticker["sell"])/2
        self.start_position_buy = midpoint
        self.start_position_sell = midpoint
        print dt.timestamp_to_string(), 'Current Ticker:', ticker
        return ticker

    def get_position(self, index):
        start_position = self.start_position_sell if index > 0 else self.start_position_buy
        return round(start_position * (1+self.__settings.INTERVAL)**index, self.__constants.USD_DECIMAL_PLACES)

    def place_order(self, index, order_type):
        position = self.get_position(index)

        quantity = self.__settings.ORDER_SIZE + round(random.uniform(-10,10))
        price = position

        order = self.__broker.place_order(price, quantity, order_type)
        print dt.timestamp_to_string(), order_type.capitalize() + ":", quantity, \
            "@", price, "id:", order["orderID"], \
            "value: %.6f XBT" % (self.__instrument["multiplier"] * price * quantity / self.__constants.XBt_TO_XBT), \
            "margin: %.6f XBT" % (self.__instrument["multiplier"] * price * quantity * self.__instrument["initMargin"] / self.__constants.XBt_TO_XBT)

        self.orders[index] = order

    def check_orders(self):
        trade_data = self.__broker.getTradeData()
        self.get_ticker()
        order_ids = [o["orderID"] for o in trade_data["orders"]]
        old_orders = self.orders.copy()
        print_status = False

        # If an order fills, reset it
        for index, order in old_orders.iteritems():
            if order["orderID"] not in order_ids:
                print "Order filled, id: %s, price: %.2f, quantity: %d" % (order["orderID"], order["price"],order["orderQty"])
                del self.orders[index]
                if order["side"] == "Buy":
                    self.place_order(index, "Sell")
                else:
                    self.place_order(-index, "Buy")
                print_status = True

        num_buys = 0
        num_sells = 0

        # Count our buys & sells
        for order in self.orders.itervalues():
            if order["side"] == "Buy":
                num_buys += 1
            else:
                num_sells += 1

        # If we're missing buys, refill
        if num_buys < self.__settings.ORDER_PAIRS:
            low_index = min(self.orders.keys())
            if num_buys == 0:
                # No buy orders left, so leave a gap
                low_index -= 1
            for i in range(1, self.__settings.ORDER_PAIRS - num_buys + 1):
                self.place_order(low_index-i, "Buy")

        # If we're missing sells, refill
        if num_sells < self.__settings.ORDER_PAIRS:
            high_index = max(self.orders.keys())
            if num_sells == 0:
                # No sell orders left, so leave a gap
                high_index += 1
            for i in range(1, self.__settings.ORDER_PAIRS - num_sells + 1):
                self.place_order(high_index+i, "Sell")

        if print_status:
            xbt = trade_data["xbt"]
            print "Profit: %.6f" % (xbt - self.start_xbt), "XBT. Run Time:", datetime.now() - self.start_time


    def run_loop(self):
        self.reset()
        while True:
            sleep(5)
            try:
                self.check_orders()
                sys.stdout.write(".")
                sys.stdout.flush()
            except (KeyboardInterrupt, SystemExit):
                print "Shutting down, cancelling open orders"
                self.exit()
