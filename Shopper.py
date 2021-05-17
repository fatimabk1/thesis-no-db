import random
from enum import IntEnum
import Constants

class Status(IntEnum):
    INERT = 0
    SHOPPING = 1
    QUEUE_READY = 2
    QUEUEING = 3
    CHECKOUT = 4
    DONE = 5


class Shopper:
    def __init__(self, t_step):
        self.start_min = int(random.random() * 59) + 1
        self.browse_mins = None
        self.quota = set_quota(t_step)
        self.cart_count = 0
        self.lane = None
        self.qtime = 0
        self.status = Status.INERT
        self.total = 0.00
        # self.deleted = False

    def print(self):
        stat_string = ""
        if self.status == Status.INERT:
            stat_string = "INERT"
        elif self.status == Status.SHOPPING:
            stat_string = "SHOPPING"
        elif self.status == Status.QUEUEING:
            stat_string = "QUEUEING"
        elif self.status == Status.QUEUE_READY:
            stat_string = "QUEUE_READY"
        elif self.status == Status.CHECKOUT:
            stat_string = "CHECKOUT"
        elif self.status == Status.DONE:
            stat_string = "DONE"
        else:
            stat_string = "INVALID"

        browse, cart, ln, qt = self.browse_mins, self.cart_count, self.lane, self.qtime
        if self.browse_mins is None:
            browse = "NONE"
        if self.cart_count is None:
            cart = "NONE"
        if self.lane is None:
            ln = "NONE"
        if self.qtime is None:
            qt = "NONE"

        print("<shopper_{}_{}: start={}, browse={}, quota={}, cart_count={}, lane={}, qtime={}, total={}>"
              .format(id(self), stat_string, self.start_min,
                      browse, self.quota, cart,
                      ln, qt, self.total))

    def get_status(self):
        return self.status

    def set_status(self, stat):
        self.status = stat

    def reset_browse(self, t_step):
        if Constants.closing_soon(t_step):
            self.browse_mins = int(random.random() * 3) + 1  # 1-3
        else:
            self.browse_mins = int(random.random() * 4) + 2 # 2-5

    def increment_qtime(self):
        self.qtime += 1
    
    def get_qtime(self):
        return self.qtime

    def set_lane(self, ln_index):
        if self.lane is None:
            self.qtime = 0
        self.lane = ln_index
    
    def get_cart_count(self):
        return self.cart_count

    def scan(self, n):
        self.cart_count -= n
    
    def get_start_min(self):
        return self.start_min

    def get_quota(self):
        return self.quota
    
    def get_total(self):
        return self.total
    
    # def set_deleted(self):
    #     self.deleted = True
    
    # def is_deleted(self):
    #     return self.deleted
    
    def is_selecting(self):
        if self.status == Status.SHOPPING and self.browse_mins == 1:
            return True
        else:
            return False

    def decrement_browse_mins(self):
        self.browse_mins -= 1
    
    def add_item(self, grp, price, t_step):
        self.quota -= 1
        self.reset_browse(t_step)
        if grp is not None:
            self.cart_count += 1
            self.total += price
    
    def hurry_up(self):
        if self.quota > 3:
            self.quota = 3

def set_quota(t_step):
    if Constants.closing_soon(t_step):
        start = round(Constants.SHOPPER_MIN / 3)
        end = round(Constants.SHOPPER_MAX / 3)
        numbers = end - start + 1
        return int(random.random() * numbers) + start
    else:
        start = Constants.SHOPPER_MIN
        end = Constants.SHOPPER_MAX
        numbers = end - start + 1
        return int(random.random() * numbers) + start
