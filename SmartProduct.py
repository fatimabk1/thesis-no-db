from Inventory import Inventory, StockType
from Task import TossTask, UnloadTask, RegularTask, RestockTask, AllTask


class SmartProduct:
    def __init__(self, grp, sublot_quantity):
        self.grp = grp
        self.sublot_quantity = sublot_quantity
        self.toss_list = TossTask()
        self.unload_list = UnloadTask()  # AKA total pending stock
        self.restock_list = RestockTask()  # partial shelf --> if select() returns None, select from waiting_list() & move inv to restock
        # self.waiting_list = RegularTask()  # remaining inv ordered by sell_by
        self.all_list = AllTask()
    
    def select(self):
        selection = self.restock_list.select()
        if selection is None:
            selection = self.waiting_list.select()  # TODO: write function 
            if selection is not None:
                selection.decrement(StockType.SHELF, 1)
                self.restock_list.add(selection)
            else:
                print("SmartProduct.select() error: no inventory in waiting_list")
                exit(1) 
        return selection
    
    # TODO: How to signify no work is left to do?
    def toss(self, emp_q):
        while(emp_q > 0 and self.toss_list.has_work()):
            emp_q = self.toss_list.do_work(emp_q)
        return emp_q

    # TODO: conversion for major unloading?
    # 1. Change unload_speed to 5-10 (lots)
    # 2. Do conversion to/from in unload()
    def unload(self, unload_speed):
        quantity = unload_speed * self.num_sublots() * self.get_sublot_quantity()
        while(quantity > 0 and self.unload_list.has_work()):
            quantity = self.unload_list.do_work(quantity)
        return quantity

    def restock(self, emp_q):
        while(emp_q > 0):
            emp_q = self.restock_list.do_work(emp_q)
        return emp_q

    def add(self, inv):
        pass

    def add_inventory_list(self, inv_lst):
        inv_lst.sort(key=lambda x: x.get_sell_by())
        for inv in inv_lst:
            self.add(inv)


# START >>> working out how smartproduct interacts with Task / List objects.
# Also how this works with Tasks vs List, Who does what
# Also need to think through having lists for tracking inventory on shelf for selecting
#       --> have SmartProduct keep a pointer to inv to select from?
# Need to make a separate updated setup_starter_inventory() function



"""
8. SMART PRODUCT:
    - contents:
        - toss_list : task()
        - unload_list: task()
        - restock_list: task() --> all inv where select() has been called 
        - regular_list: task()
        - all_list: task()
    - functions:
        - select() --> update inv, update lists
        - toss(emp_q) --> update inv, update lists -- returns remaining emp_q
        - unload(emp_q) --> update inv, update lists -- returns remaining emp_q
        - restock(emp_q) --> unload(emp_q) --> update inv, update lists -- returns remaining emp_q

"""
