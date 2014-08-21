
from marketmaker.exchangeinterface import ExchangeInterface
from marketmaker.ordermanager import OrderManager
from marketmaker.bitmex import settings, constants


print 'Version: %s\n' % constants.VERSION


interface = ExchangeInterface(dry_run=True, settings=settings)


om = OrderManager(settings, interface)
om.run_loop()

