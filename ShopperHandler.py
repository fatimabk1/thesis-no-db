import datetime
import Constants
import random
from Shopper import Status
from abc import ABC, abstractmethod
from Revenue import Revenue
from Cost import Qtime
from Inventory import StockType
from datetime import date


class ShopperHandler:
    def __init__(self, products, inv_lookup, ps, lm, rev, qt, clk):
        self.next = None
        self.products = products
        self.inv_lookup = inv_lookup  # reference to Store's inv_lookup
        self.product_stats = ps
        self.lane_manager = lm
        self.revenues = rev
        self.qtimes = qt
        self.clock = clk

    def handle(self, shopper, t_step, today):
        ret = None
        if shopper.get_status() == Status.INERT:
            # t = Constants.log()
            ret = self.__handle_inert(shopper, t_step)
            # Constants.delta("handle_inert()", t)
        elif shopper.get_status() == Status.SHOPPING:
            # t = Constants.log()
            ret = self.__handle_shopper(shopper, t_step, today)
            # Constants.delta("handle_shopper", t)
        elif shopper.get_status() == Status.QUEUEING:
            # t = Constants.log()
            ret = self.__handle_queueing(shopper)
            # Constants.delta("handle_queueing", t)
        elif shopper.get_status() == Status.DONE:
            # t = Constants.log()
            ret = self.__handle_done(shopper, today)
            # Constants.delta("handle_done()", t)
        else:
            status = shopper.get_status()
            assert(status == Status.CHECKOUT or status == Status.QUEUE_READY), f"ShopperHandler Error | unexpected status: {str(status)}"
        return ret

    def __handle_inert(self, shopper, t_step):
        if t_step % 60 == shopper.get_start_min():
            shopper.set_status(Status.SHOPPING)
            shopper.reset_browse(t_step)
            return None

    # @profile
    def __handle_shopper(self, shopper, t_step, today):
        if shopper.get_quota() == 0:
            self.lane_manager.queue_shopper(shopper)
            shopper.set_status(Status.QUEUEING)
        else:
            if t_step >= Constants.StoreStatus.CLOSED - 15:
                shopper.hurry_up()

            if shopper.is_selecting():
                # t = Constants.log()
                grp_id = int(random.random() * Constants.PRODUCT_COUNT)
                # Constants.delta("random grp_id", t)
                # t = Constants.log()
                inv = next((inv for inv in self.inv_lookup[grp_id]
                        if inv.shelved_stock > 0), None)
                # Constants.delta("next inv - selecting", t)

                if inv is None:
                    # t = Constants.log()
                    print("WARNING_ShoppingHandler(): product {} out of stock".format(grp_id))  # , file=Constants.err_file
                    if today in self.product_stats[grp_id]["oos"]:
                        self.product_stats[grp_id]["oos"][today] += 1
                    else:
                        self.product_stats[grp_id]["oos"][today] = 1
                    [print("{} out of stock".format(grp))  # , file=Constants.err_file
                        for grp in self.product_stats
                        if self.product_stats[grp]["shelf"] == 0]
                    # Constants.delta("inv is none", t)
                    return None
                else:
                    # t = Constants.log()
                    inv.decrement(StockType.SHELF, 1)
                    # TODO:
                    # if inv.is_deleted():
                    #     print("I'm deleted!")
                    #     self.inv_lookup[inv.grp_id].remove(inv)
                    #     assert inv not in self.inv_lookup[inv.grp_id]
                    price = self.products[grp_id].get_price()
                    shopper.add_item(grp_id, price, t_step)
                    self.product_stats[grp_id]["shelf"] -= 1
                    self.product_stats[grp_id]["sold"][0] += 1
                    return inv
                    # Constants.delta("inv updates", t)
            else:
                shopper.decrement_browse_mins()
                return None

    def __handle_queueing(self, shopper):
        shopper.increment_qtime()
        return None

    def __handle_done(self, shopper, today):
        # shopper.set_deleted()
        rev = Revenue(stamp=today, value=shopper.get_total())
        self.revenues.append(rev)
        qt = Qtime(lane=shopper.lane, stamp=today, time=shopper.get_qtime())
        self.qtimes.append(qt)
        return None
        # shopper.print()
        # print(len(self.shoppers))
        # exit(1)
