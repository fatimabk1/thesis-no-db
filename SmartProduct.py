from Inventory import Inventory, StockType
from Product import Product
import Constants
from math import floor, av

# A queue-like data structure with accessibility & editability of a list
# Manages its own inventory, tasks, and ordering
class SmartProduct:
    def __init__(self, prod: Product):
        self.product = prod
        self.miss_count = 0  # number of attempts to select a product but no stock on shelves
        self.toss_count = 0  # number of products thrown out because they are expired
        self.sold = {'today': 0, 'one_ago': 0, 'two_ago': 0}
        self.ideal_daily = self.product.max_shelf()
        self.cusion = 0.2 * self.ideal_daily

        # inventory is listed in order of sell_by + first-in/first_out
        self.inventory_list = []

        # indices for sublists of inventory and total sum of shelf, back, and pending respectively
        # start index is index of first inv in sublist, end index is one past last inv in sublist
        self.any_shelf = {'start': 0, 'end': 0, 'quantity': 0}
        self.any_back = {'start': 0, 'end': 0, 'quantity': 0}
        self.pending = {'start': 0, 'end': 0, 'quantity': 0}
        self.toss_lookup = {}   # {sell_by_date: {'start': x, 'end': x, 'quantity': x}}

    def reset(self):
        if 0 not in self.sold.items():
            self.ideal_daily = sum(self.sold['today'], self.sold['one_ago'], self.sold['two_ago']) / 3
            if self.toss_count > 10:
                self.cushion -= int(self.toss_count / 2)
        self.miss_count = 0
        self.toss_count = 0
        self.sold['two_ago'] = self.sold['one_ago']
        self.sold['one_ago'] = self.sold['today']
        self.sold['today'] = 0

    def __pop(self):
        # list still starts at 0, all other indices reduced by 1
        inv = self.inventory_list.pop()
        assert(inv.get_total() == 0), "SmartProduct.__pop(): FATAL: attempt to pop a non-empty inventory" 

        # update indices for all stock type sublists
        self.any_shelf['end'] -= 1
        self.any_back['start'] -= 1
        self.any_back['end'] -= 1

        # update indices for all expiration sublists
        sell_by = inv.get_sell_by()
        dates = self.toss_lookup.keys()
        removed = []
        for date in dates:
            self.toss_lookup[sell_by]['end'] -= 1
            if self.toss_lookup[sell_by]['end'] == self.toss_lookup[sell_by]['start']:
                removed.append(date)
        (self.toss_lookup.pop(date, None) for date in removed)

    def __push(self, inv):
        # add to inventory list and pending sublist
        pending_q = inv.get_pending()
        self.inventory_list.append(inv)
        self.pending['end'] += 1
        self.pending['quantity'] += pending_q

        # add to toss_lookup
        sell_by = inv.get_sell_by()
        if sell_by in self.toss_lookup:
            self.toss_lookup['quantity'] += pending_q
            self.toss_lookup['end'] += 1
        else:
            self.toss_lookup['quantity'] = pending_q
            list_len = len(self.inventory_list)
            if list_len == 0:
                self.toss_lookup['start'] = 0
                self.toss_lookup['end'] =  1
            else:
                self.toss_lookup['start'] = list_len - 1
                self.toss_lookup['end'] = list_len

    def push_list(self, inv_lst, arrival):
        # sanity check - making sure we don't have pending inventory from different dates
        if self.pending_date != arrival:
            assert(self.pending['start'] == self.pending['end'] and self.pending['start'] == len(self.inventory_list)), "SmartProduct.push_list(): FATAL: new truck arrived but old truck is still being unloaded"
        else:
            inv_lst.sort(key=lambda x: x.get_sell_by())
            (self.__push(inv) for inv in inv_lst)

    def select(self):
        if self.any_shelf['quantity'] > 0:
            inv = self.inventory_list[self.any_shelf['start']]
            inv.decrement(StockType.SHELF, 1)
            self.any_shelf['quantity'] -= 1
            self.sold['today'] += 1
            if inv.is_deleted():
                self.__pop()
        else:
            self.miss_count += 1
            self.product.set_order_amount(self.product.get_order_amount() + 1)

    def has_work(self, task, today):
        if task == Constants.TASK_UNLOAD and self.pending['quantity'] > 0:
            return True
        elif task == Constants.TASK_RESTOCK:
            max_shelf = self.product.get_max_shelf()
            curr_shelf = self.any_shelf['quantity']
            curr_back = self.any_back['quantity']
            work = min(max_shelf - curr_shelf, curr_back)
            if work:
                return True
        elif (task == Constants.TASK_TOSS
                and today in self.toss_lookup
                and self.toss_lookup[today]['quantity'] > 0):
            return True
        else:
            return False

    # toss as many inventories / partial inventories as possible exhausing emp_q
    def toss(self, emp_q, today):
        start = self.toss_lookup[today]['start']
        end = self.toss_lookup[today]['end']
        removed = []
        while(start != end and emp_q > 0 and self.toss_lookup[today]['quantity'] > 0):
            inv = self.inventory_list[start]
            shelf, back, pending = inv.get_shelf(), inv.get_back(), inv.get_pending()
            diff = self.__toss_one(inv, emp_q)
            emp_q -= diff
            self.toss_lookup[today]['quantity'] -= diff
            if inv.is_deleted():
                removed.append(inv)
            else:  # partial toss
                # update any_shelf and any_back
                if inv.get_shelf() == 0 and shelf > 0:
                    self.any_shelf['start'] += 1  # shelf queue pop
                if inv.get_back() == 0 and back > 0:
                    self.any_back['start'] += 1  # back queue pop
            start += 1
        (self.__pop(inv) for inv in removed)
        return emp_q

    # Toss as much as possible of inv, given employee capacity 
    def __toss_one(self, inv, emp_q):
        quantity = inv.get_total()
        if inv.get_pending() > 0:
            print("SmartProduct.__toss_one(): FATAL: attempt to toss an expired product that has not arrived.")
            exit(1)

        # toss entire thing at once
        if quantity <= emp_q:
            inv.decrement(StockType.SHELF, inv.get_shelf())
            inv.decrement(StockType.BACK, inv.get_back())
            return quantity
        # partial toss
        else:
            diff = 0
            # toss expired on shelf
            q = min(emp_q, inv.get_shelf())
            inv.decrement(StockType.SHELF, q)
            emp_q -= q
            quantity -= q
            diff += q

            # toss expired in back stock
            if emp_q > 0 and quantity > 0:
                q = min(emp_q, inv.get_back())
                inv.decrement(StockType.BACK, q)
                emp_q -= q
                quantity -= q
                diff += q
                print("Smartproduct.__toss_one(): WARNING throwing out expired product in back")

            return diff

    def unload(self, unload_speed):
        if self.pending['quantity'] == 0:
            print("SmartProduct.unload(): ERROR, attempt to unload nonexistent product")
            exit(1)
            return unload_speed
        else:
            emp_q = unload_speed * self.product.get_num_sublots() * self.product.get_sublot_quantity()
            start = self.pending['start']
            end = self.pending['end']

            while(start != end and emp_q > 0 and self.pending['quantity'] > 0):
                inv = self.inventory_list[start]
                expected_quantity = inv.get_total()
                diff = self.__unload_one(inv, emp_q)
                assert(diff == expected_quantity), f"SmartProduct.unload(): FATAL - employee did not unload a full lot. Unloaded {diff}, expected {expected_quantity}"
                emp_q -= diff
                self.pending['quantity'] -= diff

                # update indices for any_back and pending
                if diff > 0:
                    self.any_back['end'] += 1  # back queue push
                    self.any_back['quantity'] += diff
                    self.pending['start'] -= 1  # unload queue pop
                start += 1
            
            assert(emp_q == 0), "unload(): FATAL - employee did not unload a full lot"
            return 0
            # convert emp_q back to units of lots
            emp_q = emp_q / (self.product.get_num_sublots() * self.product.get_sublot_quantity())
            if emp_q < 0.5:
                return 0
            else:
                return 1

    def __unload_one(self, inv, emp_q):
        q = min(emp_q, inv.get_pending())
        inv.increment(StockType.BACK, q)
        inv.decrement(StockType.PENDING, q)
        return q

    def restock(self, emp_q):
        start = self.restock['start']
        end = self.restock['end']

        max_shelf = self.product.get_max_shelf()
        curr_shelf = self.any_shelf['quantity']
        curr_back = self.any_back['quantity']

        work = min(max_shelf - curr_shelf, curr_back)
        while(start != end and emp_q > 0 and work > 0):
            inv = self.inventory_list[start]
            shelf, back = inv.get_shelf(), inv.get_back()
            diff = self.__restock_one(inv, emp_q, work)
            emp_q -= diff
            work -= diff

            self.any_shelf['quantity'] += diff
            self.any_back['quantity'] -= diff
            if shelf == 0 and diff > 0:
                self.any_shelf['end'] += 1  # shelf queue push
            if inv.get_back() == 0 and back > 0:
                self.any_back['start'] += 1  # back queue pop
            start += 1
        return emp_q

    def __restock_one(self, inv, emp_q, work):
        q = min(inv.get_back(), emp_q, work)
        inv.increment(StockType.SHELF, q)
        inv.decrement(StockType.BACK, q)
        return q

    def add_inventory_list(self, inv_lst):
        inv_lst.sort(key=lambda x: x.get_sell_by())
        for inv in inv_lst:
            self.add(inv)

    # Collect pending list and pass through add_inventory_list()
    def order_inventory(self, today):
        cost = 0
        arrival = today + Constants.TRUCK_DAYS
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
        cost = self.product.get_lot_price() * num_lots
        return cost, inv_lst

    def __create_pending(self, num_sublots, arrival, today):
        # return pending_lst or None
        pending_q = self.product.get_sublot_quantity()
        pending_inv = []
        for i in range(num_sublots):
            sell = today + self.product.get_sell_by()
            inv = Inventory(self.product.grp_id, 0, 0, pending_q, arrival, sell)
            pending_inv.append(inv)
        return pending_inv

