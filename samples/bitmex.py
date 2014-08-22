from marketmaker.bitmex import broker
from marketmaker.ordermanager import OrderManager



exchange = broker.BrokerInterface()

om = OrderManager(exchange)


om.exit()

#om.run_loop()

