from marketmaker.bitmex import broker
from marketmaker import strategy



myBroker = broker.BrokerInterface()

om = strategy.OrderStrategy(myBroker)


om.reset()
#om.check_orders()

om.exit()

#om.run_loop()

