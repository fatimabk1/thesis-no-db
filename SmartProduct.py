from Inventory import Inventory, StockType
from Product import Product
import Constants
from datetime import datetime, timedelta
from math import floor
import sys

# A queue-like data structure with accessibility & editability of a list
# Manages its own inventory, tasks, and ordering
class SmartProduct:
    def __init__(self, prod: Product):
        self.product = prod
        self.miss_count = 0  # number of attempts to select a product but no stock on shelves
        self.toss_count = 0  # number of products thrown out because they are expired
        self.sold = {'today': 0, 'one_ago': 0, 'two_ago': 0}
        self.ideal_daily = prod.get_max_shelf()
        self.cushion = 0.2 * self.ideal_daily

        # inventory is listed in order of sell_by + first-in/first_out
        self.inventory_list = []

        # indices for sublists of inventory and total sum of shelf, back, and pending respectively
        # start index is index of first inv in sublist, end index is one past last inv in sublist
        self.any_shelf = {'start': 0, 'end': 0, 'quantity': 0}
        self.any_back = {'start': 0, 'end': 0, 'quantity': 0}
        self.pending = {'start': 0, 'end': 0, 'quantity': 0}
        self.toss_lookup = {}   # {sell_by_date: {'start': x, 'end': x, 'quantity': x}}

    def get_today_stats(self):
        return {
            'sold': self.sold['today'],
            'toss': self.toss_count,
            'miss': self.miss_count
        }

    def reset(self):
        if 0 not in self.sold.items():
            self.ideal_daily = sum(self.sold['today'], self.sold['one_ago'], self.sold['two_ago']) / 3
            if self.toss_count > 10:
                self.cushion -= int(self.toss_count / 2)
        else: 
            self.ideal_daily = self.sold['today']
        self.miss_count = 0
        self.toss_count = 0
        self.sold['two_ago'] = self.sold['one_ago']
        self.sold['one_ago'] = self.sold['today']
        self.sold['today'] = 0

    def __pop(self):
        # list still starts at 0, all other indices reduced by 1
        # self.special_print("POPPING")
        inv = self.inventory_list[0]
        if inv.get_total() != 0:
            print(f"\nSmartProduct.__pop(): FATAL: attempt to pop a non-empty inventory - contains {inv.get_total()} items")
            inv.print(0)
            exit(1)

        # update indices for all stock type sublists
        self.__index_decrement('end', self.any_shelf)
        self.__index_decrement('start', self.any_back)
        self.__index_decrement('end', self.any_back)
        self.__index_decrement('start', self.pending)
        self.__index_decrement('end', self.pending)

        # update indices for all expiration sublists
        dates = self.toss_lookup.keys()
        removed = []
        for date in dates:
            self.__index_decrement('start', self.toss_lookup[date])
            self.__index_decrement('end', self.toss_lookup[date])
            if self.toss_lookup[date]['end'] == self.toss_lookup[date]['start']:
                removed.append(date)
        for date in removed:
            self.toss_lookup.pop(date, None) 
        self.inventory_list.pop(0)

        # self.__print__()

    def __push(self, inv):
        # self.special_print("PUSHING")
        self.inventory_list.append(inv)
        pending_q = inv.get_pending()
        list_len = len(self.inventory_list)

        # update pending 
        self.__index_increment('end', self.pending, list_len)
        self.pending['quantity'] += pending_q

        # update toss_lookup
        sell_by = inv.get_sell_by()
        if sell_by in self.toss_lookup:
            self.toss_lookup[sell_by]['quantity'] += pending_q
            self.__index_increment('end', self.toss_lookup[sell_by], list_len)
        else:
            self.toss_lookup[sell_by] = {'quantity': pending_q,
                                         'start': len(self.inventory_list) - 1,
                                         'end': len(self.inventory_list)}
        # self.__print__()

    def push_list(self, inv_lst, arrival):
        # sanity check - making sure we don't have pending inventory from different dates
        if self.pending_date != arrival:
            assert(self.pending['start'] == self.pending['end'] and self.pending['start'] == len(self.inventory_list)), "\nSmartProduct.push_list(): FATAL: new truck arrived but old truck is still being unloaded"
        else:
            inv_lst.sort(key=lambda x: x.get_sell_by())
            (self.__push(inv) for inv in inv_lst)

    def select(self):
        # self.special_print("SELECTING!")
        if self.any_shelf['quantity'] > 0:
            inv = self.inventory_list[self.any_shelf['start']]
            if inv.get_shelf() == 0:
                print("\nSmartProduct.select(): FATAL - attempt to select from empty shelf")
                print(f"start = {self.any_shelf['start']}, end = {self.any_shelf['end']}, quantity = {self.any_shelf['quantity']}")
                inv.print(self.inventory_list.index(inv))
                print("\n\t>any_shelf contents:")
                start, end = self.any_shelf['start'], self.any_shelf['end']
                while(start != end):
                    self.inventory_list[start].print(start)
                    start += 1
                exit(1)

            inv.decrement(StockType.SHELF, 1)
            self.any_shelf['quantity'] -= 1
            self.sold['today'] += 1
            if inv.is_deleted():
                self.__pop()
            # self.__print__()
        else:
            print(f"No stock on shelves for product {self.product.get_id()} - MISS")
            exit(1)
            self.miss_count += 1
            self.product.set_order_amount(self.product.get_order_amount() + 1)

    # caution around array index bounds
    def __index_decrement(self, key, d: dict):
        if key in d and d[key] != 0:
            d[key] -= 1
    
    # caution around array index bounds
    def __index_increment(self, key, d:dict, list_len: int):
        if key in d and d[key] == list_len:
            print("\nSmartProduct.__index_increment(): FATAL - attempt to increment index past list length")
            exit(1)
        elif key in d:
            d[key] += 1

    def get_work(self, task, today, next_truck):
        if task == Constants.TASK_UNLOAD:
            if next_truck and next_truck == today:
                return self.pending['quantity']
            else:
                return 0
        elif task == Constants.TASK_TOSS:
            if today in self.toss_lookup:
                return self.toss_lookup[today]['quantity']
            else:
                return 0
        elif task == Constants.TASK_RESTOCK:
            max_shelf = self.product.get_max_shelf()
            curr_shelf = self.any_shelf['quantity']
            curr_back = self.any_back['quantity']
            work = min(max_shelf - curr_shelf, curr_back)
            return work
        else:
            print(f"SmartProduct.get_work(): Invalid task {task}")
            exit(1)

    def has_work(self, task, today, next_truck):
        if task == Constants.TASK_UNLOAD and self.pending['quantity'] > 0:
            return True
        elif task == Constants.TASK_RESTOCK:
             if self.get_work(task, today, next_truck) > 0:
                return True
        elif (task == Constants.TASK_TOSS
                and today in self.toss_lookup
                and self.toss_lookup[today]['quantity'] > 0):
            return True
        return False

    def unload(self, unload_speed):
        # self.special_print("UNLOADING")
        if self.pending['quantity'] == 0:
            print(f"SmartProduct.unload({self.product.get_id()}): ERROR, attempt to unload nonexistent product")
            exit(1)
            return unload_speed
        else:
            emp_q = unload_speed * self.product.get_num_sublots() * self.product.get_sublot_quantity()
            start = self.pending['start']
            end = self.pending['end']

            total_unload = 0
            while(start != end and emp_q > 0 and self.pending['quantity'] > 0):
                inv = self.inventory_list[start]
                expected_quantity = inv.get_total()
                diff = self.__unload_one(inv, emp_q)
                assert(diff % expected_quantity == 0), f"\nSmartProduct.unload(): FATAL - employee did not unload a full lot. Unloaded {diff}, expected {expected_quantity}"
                emp_q -= diff
                total_unload += diff
                self.pending['quantity'] -= diff
                self.any_back['quantity'] += diff
 
                # update indices for any_back and pending
                if diff > 0:
                    list_len = len(self.inventory_list)
                    self.__index_increment('end', self.any_back, list_len)  # back queue push
                    self.__index_increment('start', self.pending, list_len)  # unload queue pop
                start += 1

            # convert emp_q back to units of lots
            total_unload = int(total_unload / (self.product.get_num_sublots() * self.product.get_sublot_quantity()))
            # self.__print__()
        return total_unload

    def __unload_one(self, inv, emp_q):
        q = min(emp_q, inv.get_pending())
        inv.increment(StockType.BACK, q)
        inv.decrement(StockType.PENDING, q)
        return q

    def restock(self, emp_q):
        # self.special_print("RESTOCKING")
        start = self.any_back['start']
        end = self.any_back['end']

        max_shelf = self.product.get_max_shelf()
        curr_shelf = self.any_shelf['quantity']
        curr_back = self.any_back['quantity']
        sublot_q = self.product.get_sublot_quantity()

        work = min(max_shelf - curr_shelf, curr_back)
        # self.special_print(f"restock work = min({max_shelf - curr_shelf}, {curr_back})")
        diff = 0
        total_restock = 0
        while(start != end and emp_q > 0 and work > 0):
            inv = self.inventory_list[start]
            back_prev = inv.get_back()
            diff = self.__restock_one(inv, emp_q, work)
            assert(diff != 0), "\nrestock(): FATAL - employee restocked a value of 0"
            # self.special_print(f"\trestocked {diff}")
            emp_q -= diff
            work -= diff
            total_restock += diff

            self.any_shelf['quantity'] += diff
            self.any_back['quantity'] -= diff
            list_len = len(self.inventory_list)
            if back_prev == sublot_q and diff > 0:
                self.__index_increment('end', self.any_shelf, list_len)  # shelf queue push
            if inv.get_back() == 0 and diff > 0:
                self.__index_increment('start', self.any_back, list_len)  # back queue pop
            start += 1
        # self.__print__()
        return total_restock

    def __restock_one(self, inv, emp_q, work):
        q = min(inv.get_back(), emp_q, work)
        inv.increment(StockType.SHELF, q)
        inv.decrement(StockType.BACK, q)
        # self.special_print(f"\t> restocked {q}")
        return q

     # toss as many inventories / partial inventories as possible exhausing emp_q

    def toss(self, emp_q, today):
        if today not in self.toss_lookup:
            return emp_q
        
        # self.special_print("TOSSING -- situation before start")
        # self.__print__()

        start = self.toss_lookup[today]['start']
        end = self.toss_lookup[today]['end']
        removed = []
        diff = 0
        total_toss = 0

        while(start != end and emp_q > 0 and self.toss_lookup[today]['quantity'] > 0):
            inv = self.inventory_list[start]
            shelf_prev, back_prev = inv.get_shelf(), inv.get_back()
            diff = self.__toss_one(inv, emp_q, today)

            emp_q -= diff
            total_toss += diff
            self.toss_lookup[today]['quantity'] -= diff
    
            if inv.is_deleted():
                removed.append(inv)
            else:  # partial toss
                if inv.get_shelf() == 0 and shelf_prev > 0:
                    self.__index_decrement('end', self.any_shelf)
                if inv.get_back() == 0 and back_prev > 0:
                    self.__index_increment('start', self.any_back)  # back queue pop

            start += 1
        
        # self.special_print("PRE-POP:")
        # self.__print__()
        for inv in removed:
            self.__pop()
        # self.special_print("POST-POP (aka final situation after tossing)")
        # self.__print__()
        return total_toss

    # Toss as much as possible of inv, given employee capacity 
    def __toss_one(self, inv, emp_q, today):
        quantity = inv.get_total()
        if inv.get_pending() > 0:
            print("\nSmartProduct.__toss_one(): FATAL: attempt to toss an expired product that has not arrived.")
            exit(1)

        inv.print(self.inventory_list.index(inv))
        assert(inv.get_sell_by() == today), f"\nSmartProduct.__toss_one({self.product.get_id()}): FATAL - attempt to toss unexpired product"

        if self.product.get_id() == 0:
            print("> pre-toss:")
            inv.print(self.inventory_list.index(inv))

        # toss entire thing at once
        if quantity <= emp_q:
            q = inv.get_shelf()
            inv.decrement(StockType.SHELF, q)
            self.any_shelf['quantity'] -= q

            q = inv.get_shelf()
            inv.decrement(StockType.BACK, q)
            self.any_back['quantity'] -= q
            
            self.toss_count += 1
            if self.product.get_id() == 0:
                print("> post-toss:")
                inv.print(self.inventory_list.index(inv))
            return quantity
        # partial toss
        else:
            diff = 0
            # toss expired on shelf
            q = min(emp_q, inv.get_shelf())
            inv.decrement(StockType.SHELF, q)
            self.any_shelf['quantity'] -= q
            emp_q -= q
            quantity -= q
            diff += q

            # toss expired in back stock
            if emp_q > 0 and quantity > 0:
                q = min(emp_q, inv.get_back())
                inv.decrement(StockType.BACK, q)
                self.any_back['quantity'] -= q
                emp_q -= q
                quantity -= q
                diff += q
                self.toss_count += 1
                print(f"Smartproduct.__toss_one({self.product.get_id()}): WARNING throwing out expired product in back")

            if self.product.get_id() == 0:
                print("> post-toss:")
                inv.print(self.inventory_list.index(inv))
            return diff

    def add_inventory_list(self, inv_lst):
        inv_lst.sort(key=lambda x: x.get_sell_by())
        for inv in inv_lst:
            self.__push(inv)

    # Collect pending list and pass through add_inventory_list()
    def order_inventory(self, today):
        cost = 0
        arrival = today + timedelta(days=Constants.TRUCK_DAYS)
        curr_back = self.any_back['quantity']
        curr_shelf = self.any_shelf['quantity']
        if curr_back + curr_shelf < self.ideal_daily * Constants.TRUCK_DAYS + self.cushion:
            amount = self.ideal_daily * Constants.TRUCK_DAYS + self.cushion
            cost, pending_lst = self.__order(amount, arrival, today)
            if pending_lst:
                self.add_inventory_list(pending_lst)
        return cost

    def __order(self, amount, arrival, today):
        # cost, return pending_lst or None
        lot_q = self.product.get_lot_quantity()
        num_lots = int(floor(amount / lot_q))
        assert(num_lots >= 1)
        sublots = int(num_lots * self.product.get_num_sublots())
        inv_lst = self.__create_pending(sublots, arrival, today)
        if self.product.get_id() == 0:
                    print(f"\t\tORDERED {sublots} inventories of GRP 0")
        cost = self.product.get_lot_price() * num_lots
        return cost, inv_lst

    def __create_pending(self, num_sublots, arrival, today):
        # return pending_lst or None
        pending_q = self.product.get_sublot_quantity()
        pending_inv = []
        for i in range(num_sublots):
            sell = today + timedelta(days=self.product.get_sell_by())
            inv = Inventory(self.product.grp_id, 0, 0, pending_q, arrival, sell)
            pending_inv.append(inv)
        return pending_inv

    def setup_starter_inventory(self, today):
        # order enough stock to completely fill shelves + 1/2 of back stock
        arrival = today
        amount = self.product.get_max_shelf() * Constants.TRUCK_DAYS
        cost, pending_lst = self.__order(amount, arrival, today)
        if pending_lst:
            self.add_inventory_list(pending_lst)

        # unload & restock
        self.unload(1000)
        self.restock(1000000)
        return cost

    def __print__(self):
        # print for smartproduct 0 if nothing is passed
        # and print for the smartproduct if an prod_id is passed

        if self.product.get_id() == 0:
            actual_shelf = sum(inv.get_shelf() for inv in self.inventory_list)
            actual_back = sum(inv.get_back() for inv in self.inventory_list)
            actual_pending = sum(inv.get_pending() for inv in self.inventory_list)


            print(f"<SmartProduct_{self.product.get_id()}_{Constants.CURRENT_DAY}_{Constants.CURRENT_TSTEP}:>"\
                f"\n\t> inventory_list: {len(self.inventory_list)} inventories"\
                f"\n\t> sublot_quantity = {self.product.get_sublot_quantity()}"\
                f"\n\t> any_shelf[start: {self.any_shelf['start']}, end: {self.any_shelf['end']}, quantity: {self.any_shelf['quantity']}]  ---> ACTUAL: {actual_shelf}"\
                f"\n\t> any_back[start: {self.any_back['start']}, end: {self.any_back['end']}, quantity: {self.any_back['quantity']}]  ---> ACTUAL: {actual_back}"\
                f"\n\t> pending[start: {self.pending['start']}, end: {self.pending['end']}, quantity: {self.pending['quantity']}]  ---> ACTUAL: {actual_pending}"\
                f"\n\t> miss_count = {self.miss_count}"\
                # f"\n\t> toss_work = {self.get_work(Constants.TASK_TOSS, today, next_truck)}"\
                # f"\n\t> unload_work = {self.get_work(Constants.TASK_UNLOAD, today, next_truck)}"\
                # f"\n\t> restock_work = {self.get_work(Constants.TASK_RESTOCK, today, next_truck)}"\
                f"\n\t> toss_count (# inventories) = {self.toss_count}"\
                f"\n\t> sold['today': {self.sold['today']}, 'one_ago': {self.sold['one_ago']}, 'two_ago': {self.sold['two_ago']}"\
                f"\n\t> toss: ")
            for dt in self.toss_lookup:
                print(f"\t   {dt} --- start: {self.toss_lookup[dt]['start']}, end: {self.toss_lookup[dt]['end']}, quantity: {self.toss_lookup[dt]['quantity']}")
            for index, inv in enumerate(self.inventory_list):
                inv.print(index)
            
            assert(actual_shelf == self.any_shelf['quantity'] and actual_back == self.any_back['quantity'] and actual_pending == self.pending['quantity'])

    def special_print(self, msg):
        if self.product.get_id() == 0:
            print(msg)

