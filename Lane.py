from Constants import log, delta
from Shopper import Status
import Constants
# import Employee


class Lane:
    def __init__(self):
        self.queue = []
        self.employee = None
        self.items_per_min = None
        self.length = 0
        self.open_status = False

    def print(self, index, file):
        sid_list = [id(shopper) for shopper in self.queue]
        print("<Lane_{}: eid={}, speed={}, length={},"
              .format(index, id(self.employee), self.items_per_min, self.length),
              "\tqueue: ", sid_list, ">", file=file)

    def set_employee(self, emp):
        self.employee = emp
        self.items_per_min = emp.get_speed(Constants.TASK_CASHIER)

    def remove_employee(self):
        emp = self.employee
        self.employee = None
        self.items_per_min = None
        return emp

    def open(self):
        self.open_status = True
    
    def close(self):
        self.open_status = False

    def enq(self, shopper):
        self.queue.append(shopper)
        self.length += 1

    def deq(self):
        shopper = self.queue.pop(0)
        self.length -= 1
        return shopper
    
    def deq_right(self):
        shopper = self.queue.pop()
        self.length -= 1
        return shopper

    def insert_left(self, shopper):
        self.queue.insert(0, shopper)
        self.length += 1

    def get_speed(self):
        return self.items_per_min
    
    def get_length(self):
        return self.length

    def is_active(self):
        if self.length > 0 and self.employee is not None:
            return True
        else:
            return False

    def checkout(self):
        emp_q = self.get_speed()
        while self.length > 0 and emp_q > 0:
            sh = self.deq()
            # print("\t\t\tchecking out shopper {} with {} items".format(id(sh), sh.get_cart_count()))
            sh.set_status(Status.CHECKOUT)
            assert(sh.get_cart_count() != 0)
            scanned = min(sh.get_cart_count(), emp_q)
            sh.scan(scanned)
            emp_q -= scanned

            if sh.get_cart_count() == 0:
                sh.set_status(Status.DONE)
                # print("\t\t\t\t> Shopper done!")
            else:
                self.insert_left(sh)
                # print("\t\t\t\t> Shopper with a big cart - carrying over the transaction!")

    def is_open(self):
        return self.open_status

    def get_item_count(self):
        return sum(sh.get_cart_count() for sh in self.queue)
