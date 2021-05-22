from Inventory import Inventory, StockType
from abc import ABC, abstractmethod

class AbstractTask:
    @abstractmethod
    def __init__(self):
        self.quantity = 0
        super().__init__()

    @abstractmethod
    def get_quantity(self):
        pass

    @abstractmethod
    def add(self, inv):
        pass

    @abstractmethod
    def remove(self, inv):
        pass
    
    @abstractmethod
    def do_task(self, quantity):
        pass


class TossTask(metaclass=AbstractTask):
    def __init__(self):
        self.lookup = {}  # date --> inv_lst 
    
    def get_quantity(self):
        return self.value()

    def add(self, inv):
        sell_by = inv.get_sell_by()
        if sell_by in self.lookup:
            self.lookup[sell_by].append(inv)
        else:
            self.quantity += inv.get_total()

    def add_list(self, inv_lst):
        inv_lst.sort(key=lambda x: x.get_sell_by())
        for inv in inv_lst:
            self.add(inv)

    def remove(self, inv, total):
        sell_by = inv.get_sell_by()
        if sell_by in self.lookup:
            self.lookup[sell_by].remove(inv)
            self.quantity -= total
            return inv
        else:
            print(f"TossTask.remove(): ERROR, sell_by {sell_by} not in lookup")
            exit(1)

    # def select(self):
    #     pass

    def has_work(self):
        if self.quantity > 0: 
            return True

    def do_task(self, emp_q):
        removed = []
        for inv in self.inv_lst:
            quantity = inv.get_total()
    
            # toss entire thing at once
            if quantity <= emp_q:
                self.remove(inv)
                removed.append(inv)
                emp_q -= quantity
            # partial toss
            else:
                # toss expired on shelf
                q = min(emp_q, inv.get_shelf())
                inv.decrement(StockType.SHELF, q)
                emp_q -= q
                quantity -= q
                if emp_q > 0 and quantity > 0:
                    q = min(emp_q, inv.get_back())
                    inv.decrement(StockType.BACK, q)
                    emp_q -= q
                    quantity -= q
                    if emp_q > 0 and quantity > 0:
                        q = min(emp_q, inv.get_pending())
                        inv.decrement(StockType.PENDING, q)
                        emp_q -= q
                        quantity -= q
                if inv.get_total() == 0:
                    self.remove(inv)
                    removed.append(inv)
        return removed, emp_q  # used to remove list of inv in all other lists

    


class UnloadTask(metaclass=AbstractTask):
    pass


class RestockTask(metaclass=AbstractTask):
    pass

    def select(self):
        if self.quantity == 0:
            return None
        else:
            return self.inv_lst.pop()


class RegularTask(metaclass=AbstractTask):
    pass


class AllTask(metaclass=AbstractTask):
    pass

"""
1. TASK:
    - inv_lst[]
    - quantity (total work to do)
    - do_task(q) --> updates inv & list quantity, returns q - work done
    - remove(inv)

2. Special wrapper for inventory items
    - Contents:
        - inv
        - list of list objects for that grp [toss, unload, restock, regular, all] --> initialized at wrapper creation
                --> toss will be a dictionary of sell_by dates w/list of inventories
                    > no order
                --> unload: order by sell_by
                --> restock: order by sell_by, fewest on shelf
        - current date
        - state
        - get_sell_by()
        - select()
            - decrement by 1
            - move from regular --> restock if not already there
            - update list_obj.quantity
        - toss()
            - remove from toss
            - remove from all
            - update list_obj.quantity
        - restock()
            - increment shelf / decrement back
            - update list_obj.quantity
        - unload()
            - increment back / decrement shelf
            - move from unload --> regular
            - update list_obj.quantity
        - update_state(today) --> called on all inv_wrappers in regular[]
            - moves any in all or restock --> toss
            - moves any / restock as needed

"""
