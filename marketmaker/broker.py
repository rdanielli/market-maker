from abc import abstractmethod, ABCMeta

from marketmaker import observer

class BaseBroker(observer.Subject):
    """Base class for brokers.

    .. note::

        This is a base class and should not be used directly.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        self.__orderEvent = observer.Event()

    def notifyOrderEvent(self, orderEvent):
        self.__orderEvent.emit(self, orderEvent)

    # Handlers should expect 2 parameters:
    # 1: broker instance
    # 2: OrderEvent instance
    def getOrderUpdatedEvent(self):
        return self.__orderEvent

    @abstractmethod
    def getCash(self, includeShort=True):
        """
        Returns the available cash.

        :param includeShort: Include cash from short positions.
        :type includeShort: boolean.
        """
        raise NotImplementedError()

    @abstractmethod
    def getShares(self, instrument):
        """Returns the number of shares for an instrument."""
        raise NotImplementedError()

    @abstractmethod
    def getPositions(self):
        """Returns a dictionary that maps instruments to shares."""
        raise NotImplementedError()

    @abstractmethod
    def getActiveOrders(self, instrument=None):
        """Returns a sequence with the orders that are still active.

        :param instrument: An optional instrument identifier to return only the active orders for the given instrument.
        :type instrument: string.
        """
        raise NotImplementedError()

    @abstractmethod
    def submitOrder(self, order):
        """Submits an order.

        :param order: The order to submit.
        :type order: :class:`Order`.

        .. note::
            * After this call the order is in SUBMITTED state and an event is not triggered for this transition.
            * Calling this twice on the same order will raise an exception.
        """
        raise NotImplementedError()


    @abstractmethod
    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        """Creates a Market order.
        A market order is an order to buy or sell a stock at the best available price.
        Generally, this type of order will be executed immediately. However, the price at which a market order will be executed
        is not guaranteed.

        :param action: The order action.
        :type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: Order quantity.
        :type quantity: int/float.
        :param onClose: True if the order should be filled as close to the closing price as possible (Market-On-Close order). Default is False.
        :type onClose: boolean.
        :rtype: A :class:`MarketOrder` subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        """Creates a Limit order.
        A limit order is an order to buy or sell a stock at a specific price or better.
        A buy limit order can only be executed at the limit price or lower, and a sell limit order can only be executed at the
        limit price or higher.

        :param action: The order action.
        :type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
        :param instrument: Instrument identifier.
        :type instrument: string.
        :param limitPrice: The order price.
        :type limitPrice: float
        :param quantity: Order quantity.
        :type quantity: int/float.
        :rtype: A :class:`LimitOrder` subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def createStopOrder(self, action, instrument, stopPrice, quantity):
        """Creates a Stop order.
        A stop order, also referred to as a stop-loss order, is an order to buy or sell a stock once the price of the stock
        reaches a specified price, known as the stop price.
        When the stop price is reached, a stop order becomes a market order.
        A buy stop order is entered at a stop price above the current market price. Investors generally use a buy stop order
        to limit a loss or to protect a profit on a stock that they have sold short.
        A sell stop order is entered at a stop price below the current market price. Investors generally use a sell stop order
        to limit a loss or to protect a profit on a stock that they own.

        :param action: The order action.
        :type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: The trigger price.
        :type stopPrice: float
        :param quantity: Order quantity.
        :type quantity: int/float.
        :rtype: A :class:`StopOrder` subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        """Creates a Stop-Limit order.
        A stop-limit order is an order to buy or sell a stock that combines the features of a stop order and a limit order.
        Once the stop price is reached, a stop-limit order becomes a limit order that will be executed at a specified price
        (or better). The benefit of a stop-limit order is that the investor can control the price at which the order can be executed.

        :param action: The order action.
        :type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: The trigger price.
        :type stopPrice: float
        :param limitPrice: The price for the limit order.
        :type limitPrice: float
        :param quantity: Order quantity.
        :type quantity: int/float.
        :rtype: A :class:`StopLimitOrder` subclass.
        """
        raise NotImplementedError()

    @abstractmethod
    def cancelOrder(self, order):
        """Requests an order to be canceled. If the order is filled an Exception is raised.

        :param order: The order to cancel.
        :type order: :class:`Order`.
        """
        raise NotImplementedError()
