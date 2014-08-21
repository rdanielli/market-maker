# -*- coding: utf-8 -*-
from time import sleep
import sys
from urllib2 import URLError
from datetime import datetime
import random

import settings
from marketmaker import constants
from marketmaker.broker import bitmex


def timestamp_string():
    return "["+datetime.now().strftime("%I:%M:%S %p")+"]"

class ExchangeInterface:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.symbol = sys.argv[1] if len(sys.argv) > 1 else settings.SYMBOL
        self.bitmex = bitmex.BitMEX(base_url=settings.BASE_URL, symbol=self.symbol, login=settings.LOGIN, password=settings.PASSWORD)

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
            print timestamp_string(), "Cancelling:", order['side'], order['orderQty'], "@", order['price']
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

        return {"last": float(ticker["last"]), "buy": float(ticker["buy"]), "sell": float(ticker["sell"]), \
            "symbol": self.symbol}

    def get_trade_data(self):
        if self.dry_run:
            xbt = float(settings.DRY_BTC)
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
        if settings.DRY_RUN:
            return {'orderID': 'dry_run_order', 'orderQty': quantity, 'price': price}

        if order_type == "Buy":
            order = self.bitmex.buy(quantity, price)
        elif order_type == "Sell":
            order = self.bitmex.sell(quantity, price)
        else:
            print "Invalid order type"
            exit()

        return order

class OrderManager:
    def __init__(self):
        if settings.DRY_RUN:
            print "Initializing dry run. Orders printed below represent what would be posted to BitMEX."
        else:
            print "Order Manager initializing, connecting to BitMEX. Dry run disabled, executing real trades."


        self.exchange = ExchangeInterface(settings.DRY_RUN)
        print "Using symbol %s." % self.exchange.symbol
        self.exchange.authenticate()
        self.start_time = datetime.now()
        self.instrument = self.exchange.get_instrument()
        self.reset()

    def exit(self):
        self.exchange.cancel_all_orders()

    def reset(self):
        self.exchange.cancel_all_orders()
        self.orders = {}

        ticker = self.get_ticker()
   
        trade_data = self.exchange.get_trade_data()
        self.start_xbt = trade_data["xbt"]
        print timestamp_string(), "Current XBT Balance: %.6f" % self.start_xbt

        # Sanity check:
        if self.get_position(-1) >= ticker["sell"] or self.get_position(1) <= ticker["buy"]:
            print self.start_position
            print self.get_position(-1), ticker["sell"], self.get_position(1), ticker["buy"]
            print "Sanity check failed, exchange data is screwy"
            exit()

        for i in range(1, settings.ORDER_PAIRS + 1):
            self.place_order(-i, "Buy")
            self.place_order(i, "Sell")
            sleep(1)

        if settings.DRY_RUN:
            exit()

    def get_ticker(self):
        ticker = self.exchange.get_ticker()
        midpoint = (ticker["buy"] + ticker["sell"])/2
        self.start_position_buy = midpoint
        self.start_position_sell = midpoint
        print timestamp_string(), 'Current Ticker:', ticker
        return ticker

    def get_position(self, index):
        start_position = self.start_position_sell if index > 0 else self.start_position_buy
        return round(start_position * (1+settings.INTERVAL)**index, constants.USD_DECIMAL_PLACES)

    def place_order(self, index, order_type):
        position = self.get_position(index)

        quantity = settings.ORDER_SIZE + round(random.uniform(-10,10))
        price = position

        order = self.exchange.place_order(price, quantity, order_type)
        print timestamp_string(), order_type.capitalize() + ":", quantity, \
            "@", price, "id:", order["orderID"], \
            "value: %.6f XBT" % (self.instrument["multiplier"] * price * quantity / constants.XBt_TO_XBT), \
            "margin: %.6f XBT" % (self.instrument["multiplier"] * price * quantity * self.instrument["initMargin"] / constants.XBt_TO_XBT)

        self.orders[index] = order

    def check_orders(self):
        trade_data = self.exchange.get_trade_data()
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
        if num_buys < settings.ORDER_PAIRS:
            low_index = min(self.orders.keys())
            if num_buys == 0:
                # No buy orders left, so leave a gap
                low_index -= 1
            for i in range(1, settings.ORDER_PAIRS - num_buys + 1):
                self.place_order(low_index-i, "Buy")

        # If we're missing sells, refill
        if num_sells < settings.ORDER_PAIRS:
            high_index = max(self.orders.keys())
            if num_sells == 0:
                # No sell orders left, so leave a gap
                high_index += 1
            for i in range(1, settings.ORDER_PAIRS - num_sells + 1):
                self.place_order(high_index+i, "Sell")

        if print_status:
            xbt = trade_data["xbt"]
            print "Profit: %.6f" % (xbt - self.start_xbt), "XBT. Run Time:", datetime.now() - self.start_time


    def run_loop(self):
        while True:
            sleep(5)
            try:
                self.check_orders()
                sys.stdout.write(".")
                sys.stdout.flush()
            except (KeyboardInterrupt, SystemExit):
                print "Shutting down, cancelling open orders"
                self.exit()


print 'Version: %s\n' % constants.VERSION
om = OrderManager()
om.run_loop()

