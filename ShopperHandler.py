import Constants
import random
from Shopper import Status
from Revenue import Revenue
from Cost import Qtime
from Inventory import StockType


class ShopperHandler:
    def __init__(self, sp, lm, qt):
        self.next = None
        self.smart_products = sp
        # self.product_weights = None  
        self.lane_manager = lm
        self.qtimes = qt

    def handle(self, shopper, t_step, today):
        if shopper.get_status() == Status.INERT:
            self.__handle_inert(shopper, t_step)
        elif shopper.get_status() == Status.SHOPPING:
            self.__handle_shopper(shopper, t_step, today)
        elif shopper.get_status() == Status.QUEUEING:
            self.__handle_queueing(shopper)
        elif shopper.get_status() == Status.DONE:
            self.__handle_done(shopper, today)
        else:
            status = shopper.get_status()
            assert(status == Status.CHECKOUT or status == Status.QUEUE_READY), f"ShopperHandler Error | unexpected status: {str(status)}"

    def __handle_inert(self, shopper, t_step):
        if t_step % 60 == shopper.get_start_min():
            shopper.set_status(Status.SHOPPING)
            shopper.reset_browse(t_step)

    # @profile
    def __handle_shopper(self, shopper, t_step, today):
        if shopper.get_quota() == 0:
            self.lane_manager.queue_shopper(shopper)
            shopper.set_status(Status.QUEUEING)
        else:
            if t_step >= Constants.StoreStatus.CLOSED - 15:
                shopper.hurry_up()

            if shopper.is_selecting():
                grp_id = int(random.random() * Constants.PRODUCT_COUNT)
                self.smart_products[grp_id].select()
                price = self.smart_products[grp_id].product.get_price()
                shopper.add_item(grp_id, price, t_step)
            else:
                shopper.decrement_browse_mins()

    def __handle_queueing(self, shopper):
        shopper.increment_qtime()

    def __handle_done(self, shopper, today):
        qt = Qtime(lane=shopper.lane, stamp=today, time=shopper.get_qtime())
        self.qtimes.append(qt)
