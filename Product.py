import random
from datetime import datetime, timedelta, date
from enum import IntEnum
import random
import Constants
from Constants import CLOCK, TRUCK_DAYS


def make_sell_by():
    return round(random.triangular(14, 365, 30))


class ModelSold:
    def __init__(self, grp, date, n):
        self.grp_id = grp
        self.date = date
        self.sold = n


# CHECK: enum database type class works?
class Price(IntEnum):
    REGULAR = 0
    SALE = 1


class Product:
    def __init__(self, grp, cat):
        # basic info
        self.grp_id = grp
        self.category = cat
        self.max_shelf = None
        self.max_back = None
        self.restock_threshold = None

        # selection info
        self.regular_price = None
        self.sale_price = None
        self.price_status = Price.REGULAR

        # order info
        self.lot_price = None
        self.lot_quantity = None
        self.sublots = None
        self.sublot_quantity = None
        self.sell_by_days = None
        self.order_threshold = None
        self.order_amount = None

    def print(self):
        print("<grp_{}: cat={}, max_shelf={}, max_back={}, restock_t={}, price={}, sale={}, p_stat={}, lot_p={}, lot_q={}, sublots={}, sublot_q={}, order_t={}, order_q={}, sell={}"
        .format(self.grp_id, self.category, self.max_shelf, self.max_back, self.restock_threshold, self.regular_price, self.sale_price,
                self.price_status, self.lot_price, self.lot_quantity, self.sublots, self.sublot_quantity, self.order_threshold, self.order_amount, self.sell_by_days))

    # -------------------------------------------- getters and setters
    def get_id(self):
        return self.grp_id
    
    def get_lot_quantity(self):
        return self.lot_quantity

    def get_num_sublots(self):
        return self.sublots

    def get_sublot_quantity(self):
        return self.sublot_quantity

    def get_lot_price(self):
        return self.lot_price

    def get_price(self):
        if self.price_status == Price.REGULAR:
            return self.regular_price
        else:
            return self.sale_price

    def get_max_back(self):
        return self.max_back

    def get_max_shelf(self):
        return self.max_shelf

    def get_order_amount(self):
        return self.order_amount

    def set_order_amount(self, val):
        self.order_amount = val

    def get_order_threshold(self):
        return self.order_threshold

    def get_restock_threshold(self):
        return self.restock_threshold

    def set_sale(self):
        self.price_status = Price.SALE

    def set_regular(self):
        self.price_status = Price.REGULAR

    # @profile
    def get_sell_by(self):
        # noise = timedelta(days=int(random.random() * 5) - 2)
        # today = datetime(CLOCK.year, CLOCK.month, CLOCK.day)
        return timedelta(days=(self.sell_by_days + int(random.random() * 5) - 2))

    def setup(self):
        # self.sublot_quantity = random.choice([10, 20, 50])
        self.sublot_quantity = 50
        # lot_quantity between 400 and 10,000 --> 100
        self.sublots = 10
        self.lot_quantity = self.sublot_quantity * self.sublots  # 500
        

        self.max_shelf = self.lot_quantity * 2  # 1000
        self.max_back = self.max_shelf * 10  # 10000
        self.order_threshold = round(self.max_back/2)
        self.restock_threshold = round((self.max_shelf / 2))
        self.order_amount = None

        self.price_status = Price.REGULAR
        self.regular_price = round(random.uniform(1, 22), 2)
        self.sale_price = round(
            (self.regular_price - (0.08 * self.regular_price)), 2)
        self.lot_price = round(
            (self.regular_price
             + random.choice([0.01, 0.02, 0.03, 0.04, 0.05]))
            * self.lot_quantity, 2)

        self.sell_by_days = round(random.uniform(21, 90))
