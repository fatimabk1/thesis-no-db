from datetime import date, timedelta
from math import floor
import Constants
from Cost import Cost
from Inventory import Inventory, StockType
import functools


class InventoryManager:

    def __init__(self, inventory_lookup, products, prod_stats, cost):
        self.inventory_lookup = inventory_lookup
        self.products = products
        self.product_stats = prod_stats
        self.cost = cost
    
    def print_inv_lookup(self):
        for grp in self.inventory_lookup:
            print("\n > Product ", grp)
            inv_lst = self.inventory_lookup[grp]
            inv_lst.sort(key=lambda x: x.get_sell_by())
            inv_lst.sort(key=lambda x: x.get_shelf(), reverse=True)
            print("\n> Product_{}".format(grp))
            for i, inv in enumerate(inv_lst):
                inv.print()

    def order_inventory(self, today):
        order_cost = 0
        # order inventory
        for prod in self.products:
            # print("\tordering inventory --> grp ", prod.grp_id)
            curr_back = self.product_stats[prod.grp_id]["back"]
            if curr_back < prod.get_order_threshold():
                amount = prod.get_order_amount(curr_back)
                if prod.grp_id == 0:
                    print(f"\t   > GRP_{prod.grp_id} order quantity = {amount}")
                assert(amount > 0)
                cost = self.__order_grp(prod, amount, today)
                order_cost += cost
            c = Cost(today, order_cost, "stock")
            self.cost.append(c)
        # print("\n")
        
        # sort by sell_by, shelf --> order preserved in all other uses
        for grp in self.inventory_lookup:
            self.inventory_lookup[grp].sort(key=lambda x: x.get_sell_by())
            self.inventory_lookup[grp].sort(key=lambda x: x.get_shelf(), reverse=True)

    def __order_grp(self, product, quantity, today):
        lot_q = product.get_lot_quantity()
        num_lots = int(floor(quantity / lot_q))
        assert(num_lots >= 1)
        sublots = int(num_lots * product.get_num_sublots())
        self.__create_pending(product, sublots, today)
        total_q = num_lots * lot_q
        self.product_stats[product.grp_id]["pending"] += total_q
        return product.lot_price * num_lots

    def __create_pending(self, product, num_sublots, today):
        pending_q = product.get_sublot_quantity()
        available = today + timedelta(days=Constants.TRUCK_DAYS)
        for i in range(num_sublots):
            sell = product.get_sell_by()
            inv = Inventory(product.grp_id, 0, 0, pending_q, available, sell)
            self.inventory_lookup[inv.grp_id].append(inv)
        self.inventory_lookup[inv.grp_id]

    def dispatch(self, task, lookup, employees, today):
        speeds = [emp.get_speed(task) for emp in employees]

        if task == Constants.TASK_UNLOAD:
            # available == today, pending > 0, sort: sell_by ASC, 
            for grp in lookup:
                inv_lst = lookup[grp]["inventory"]
                if len(inv_lst) == 0:
                    continue

                # do work while there is work to do and employees to do it
                prod = self.products[grp]
                quantity = lookup[grp]["quantity"]
                while(quantity > 0 and speeds):
                    emp_q = speeds.pop() * prod.get_lot_quantity()
                    diff = self.__unload(quantity, inv_lst, emp_q)
                    quantity -= diff
                    self.product_stats[grp]["pending"] -= diff
                    self.product_stats[grp]["back"] += diff

                    # update emp_q
                    emp_q -= diff
                emp_q = emp_q / prod.get_lot_quantity()
                if emp_q > 0:
                    speeds.insert(0, emp_q)
                lookup[grp]["quantity"] = quantity

        elif task == Constants.TASK_RESTOCK:
            # back_stock > 0, sort: sell_by ASC, shelf DESC
            for grp in lookup:
                inv_lst = lookup[grp]["inventory"]
                if len(inv_lst) == 0:
                    continue

                # do work while there is work to do and employees to do it
                prod = self.products[grp]
                quantity = lookup[grp]["quantity"]
                while(quantity > 0 and speeds):
                    emp_q = speeds.pop()
                    diff = self.__restock(quantity, inv_lst, emp_q)
                    emp_q -= diff
                    quantity -= diff
                    self.product_stats[grp]["back"] -= diff
                    self.product_stats[grp]["shelf"] += diff
                    if emp_q > 0:
                        speeds.insert(0, emp_q)
                lookup[grp]["quantity"] = quantity

        else:  # Task.TOSS
            # sell_by < today
            for grp in lookup:
                inv_lst = lookup[grp]["inventory"]
                if len(inv_lst) == 0:
                    continue

                prod = self.products[grp]
                quantity = lookup[grp]["quantity"]
                print(f"\t> GRP_{grp}: quantity = {quantity}")
                while(quantity > 0 and speeds):
                    emp_q = speeds.pop()
                    diff = self.__toss(quantity, inv_lst, emp_q)
                    emp_q -= diff
                    quantity -= diff
                    self.product_stats[grp]["toss"] += diff
                    if emp_q > 0:
                        speeds.insert(0, emp_q)
                lookup[grp]["quantity"] = quantity
        
        # remove completed tasks
        for prod in self.products:
            if prod.grp_id in lookup and lookup[prod.grp_id]["quantity"] == 0:
                del lookup[prod.grp_id]

    def __unload(self, quantity, inv_lst, emp_q):
        # skip through inventory that has already been unloaded
        index = 0
        while(inv_lst[index].get_pending() == 0):
            index += 1
            assert(index != len(inv_lst)), "__unload(): all inventory already handled"

        unload_count = 0
        while(quantity > 0 and unload_count != emp_q):
            inv = inv_lst[index]
            q = min(emp_q,
                    inv.get_pending(),
                    quantity)
            inv.increment(StockType.BACK, q)
            inv.decrement(StockType.PENDING, q)
            quantity -= q
            unload_count += q
            index += 1
            if index == len(inv_lst):
                break
        return unload_count

    def __restock(self, quantity, inv_lst, emp_q):
        # skip through inventory that's already been restocked
        index = 0
        while(inv_lst[index].get_back() == 0):
            index += 1
            assert(index != len(inv_lst)), "__unload(): all inventory already handled"

        restock_count = 0
        # restock remaining inventory within employee capacity
        while(quantity > 0 and restock_count != emp_q):
            inv = inv_lst[index]
            q = min(emp_q,
                    inv.get_back(),
                    quantity)
            inv.increment(StockType.SHELF, q)
            inv.decrement(StockType.BACK, q)
            quantity -= q
            restock_count += q
            index += 1
            if index == len(inv_lst):
                break
        return restock_count
    
    def __toss(self, quantity, inv_lst, emp_q):
        # skip inventory that has already been tossed
        index = 0
        while(inv_lst[index].is_deleted()):
            index += 1
            assert(index != len(inv_lst)), "__toss(): all inventory already handled"

        toss_count = 0
        removed_inventory = []
        while(quantity > 0 and toss_count != emp_q):
            inv = inv_lst[index]
            assert(inv in self.inventory_lookup[inv.grp_id])

            # toss expired on shelf
            q = min(emp_q, inv.get_shelf(), quantity)
            inv.decrement(StockType.SHELF, q)
            quantity -= q
            self.product_stats[inv.grp_id]["shelf"] -= q
            toss_count += q

            # toss expired in back
            if(quantity > 0 and toss_count != emp_q and inv.is_deleted() is False):
                q = min(emp_q, inv.get_back(), quantity)
                inv.decrement(StockType.BACK, q)
                quantity -= q
                self.product_stats[inv.grp_id]["back"] += q
                toss_count += q

                # toss expired in pending / on truck
                if(quantity > 0 and toss_count != emp_q and inv.is_deleted() is False):
                    q = min(emp_q, inv.get_pending(), quantity)
                    inv.decrement(StockType.PENDING, q)
                    quantity -= q
                    self.product_stats[inv.grp_id]["pending"] += q
                    toss_count += q
            
            if inv.is_deleted() is True:
                removed_inventory.append(inv)
            
            index += 1
            if index == len(inv_lst):
                break
        (self.inventory_lookup[inv.grp_id].remove(inv) for inv in removed_inventory)
        return toss_count

    def get_unload_list(self, today):
        lookup = {}
        for grp_id in self.inventory_lookup:
            inv_lst = [inv for inv in self.inventory_lookup[grp_id]
                       if inv.has_arrived(today)
                       and inv.get_pending() > 0]
            total_pending = sum(inv.get_pending() for inv in inv_lst)
            if total_pending > 0:
                lookup[grp_id] = {"quantity": total_pending, "inventory": inv_lst}
                if grp_id == 0:
                    print(f"GRP_0 in unload list with quantity = {total_pending}")
        return lookup

    def get_restock_list(self):
        lookup = {}
        for grp in self.inventory_lookup:
            prod = self.products[grp]
            curr_shelf = self.product_stats[grp]["shelf"]
            curr_back = self.product_stats[grp]["back"]

            if curr_shelf < prod.get_max_shelf():
                inv_lst = [inv for inv in self.inventory_lookup[grp]
                          if inv.back_stock > 0]
                quantity = min(prod.get_max_shelf() - curr_shelf,
                            curr_back)
                if quantity > 0:
                    lookup[grp] = {"quantity": quantity, "inventory": inv_lst}
                else:
                    print("\t\t> RESTOCK_ERROR: grp_{} HAS {} SHELF SPACE, BUT ONLY {} IN BACK_STOCK"
                        .format(grp, prod.get_max_shelf() - curr_shelf, curr_back))
                    print("\t\t\tproduct_stats[{}] -> shelf = {}, back = {}, pending = {}"
                    .format(grp, curr_shelf, curr_back, self.product_stats[grp]["pending"]))
                    # self.products[grp].print()
        return lookup

    def get_toss_list(self, today):
        lookup = {}
        for grp_id in self.inventory_lookup:
            inv_lst = [inv for inv in self.inventory_lookup[grp_id]
                      if inv.is_expired(today)]
            quantity = sum([inv.get_shelf() + inv.get_back() + inv.get_pending() for inv in inv_lst])
            if quantity != 0:
                lookup[grp_id] = {"quantity": quantity, "inventory": inv_lst}
        return lookup

    def refresh_tasks(self, t_step, today):
        task_lookup = None
        task = None
        if t_step < Constants.STORE_OPEN:
            task_lookup = self.get_unload_list(today)
            task = Constants.TASK_UNLOAD
        elif t_step < Constants.STORE_CLOSE:
            task_lookup = self.get_restock_list()
            task = Constants.TASK_RESTOCK
        else:
            task_lookup = self.get_toss_list(today)
            task = Constants.TASK_TOSS
        return task, task_lookup

    def print_stock_status(self):
        print("\n\t--- STOCK ---")
        for grp in self.product_stats:
             print("GRP_{}: shelf={}, back={}, pending={}"
                .format(grp, self.product_stats[grp]['shelf'],
                        self.product_stats[grp]['back'],
                        self.product_stats[grp]['pending']))

    def setup_starter_inventory(self, today):
        original_td = Constants.TRUCK_DAYS
        Constants.TRUCK_DAYS = 0
        # order enough stock to completely fill shelves + 1/2 of back stock
        for prod in self.products:
            quantity = prod.get_max_shelf() + prod.get_max_back() / 2
            self.__order_grp(prod, quantity, today)
        Constants.TRUCK_DAYS = original_td

        # unload all pending stock to back
        for grp in self.inventory_lookup:
            inv_lst = self.inventory_lookup[grp]
            for inv in inv_lst:
                n = inv.get_pending()
                inv.increment(StockType.BACK, n)
                inv.decrement(StockType.PENDING, n)
                self.product_stats[grp]['back'] += n
                self.product_stats[grp]['pending'] -=n

        # transfer 1/2 of all back stock to shelf
        for grp in self.inventory_lookup:
            inv_lst = self.inventory_lookup[grp]
            inv_lst.sort(key=lambda x: x.get_sell_by())
            inv_lst.sort(key=lambda x: x.get_shelf(), reverse=True)
            shelf_goal = self.products[grp].get_max_shelf()

            # print(f"\n\tRESTOCKING {grp}")
            index = 0
            while shelf_goal > 0:
                # print(f"index = {index}, shelf_goal = {shelf_goal}")
                assert(index != len(inv_lst)), f"setup_starter_inventory: all inventory already restocked at index {index} with shelf_goal at {shelf_goal}"
                inv = inv_lst[index]
                n = inv.get_back()
                inv.increment(StockType.SHELF, n)
                inv.decrement(StockType.BACK, n)
                self.product_stats[grp]['shelf'] += n
                self.product_stats[grp]['back'] -=n
                shelf_goal -= n
                index += 1
                assert(shelf_goal >= 0), f"setup_starter_inventory: invalid shelf_goal {shelf_goal}"
                if shelf_goal == 0:
                    break
        

def quantity_reduce(x, y):
    print(f"x: {x}, {type(x)} | y: {y}, {type(y)}")
    return (x.get_shelf() + x.get_back() + x.get_pending()
            + y.get_shelf() + y.get_back() + y.get_pending())


# >>>>> NEXT:
# 2. inv_lst is None in Shopper.step() line 156
# 3. make max # of shoppers at start of program:
#   > reset at start of day
#   > release x shopper at each hour
#   > add attribute for released or not

    # def dispatch(self, task, lookup, emp_q, today):
        # t = Constants.log()
        # print("\tDISPATCH")
        # keys = list(lookup.keys())
        # for grp in keys:
        #     td_grp = Constants.log()
        #     if emp_q == 0:
        #         return

        #     if lookup[grp]["quantity"] == 0:
        #         continue
            
        #     # filter restock inv_list in dispatch once,
        #     inv_lst = [inv for inv in task["inventory"]
        #                if inv.get_back() > 0]

        #     if task == Constants.TASK_UNLOAD:
        #         # available == today, pending > 0, sort: sell_by ASC, 
        #         print("\tunloading grp ", grp)
        #         prod = self.products[grp]
        #         # emp_q --> # of lots an emp can unload
        #         emp_q = emp_q * prod.get_lot_quantity()
        #         diff = self.__unload(lookup[grp], emp_q, today)
        #         self.product_stats[grp]["pending"] -= diff
        #         self.product_stats[grp]["back"] += diff
        #         emp_q -= diff
        #         emp_q = int(emp_q / prod.get_lot_quantity())
        #     elif task == Constants.TASK_RESTOCK:
        #         # back_stock > 0, sort: sell_by ASC, shelf DESC
        #         print("\trestocking grp ", grp)
        #         diff = self.__restock(lookup[grp], emp_q)
        #         self.product_stats[grp]["back"] -= diff
        #         self.product_stats[grp]["shelf"] += diff
        #         emp_q -= diff
        #     else:
        #         # sell_by < today
        #         assert(task == Constants.TASK_TOSS)
        #         print("\ttossing grp ", grp)
        #         diff = self.__toss(lookup[grp], emp_q)
        #         emp_q -= diff
        #     Constants.delta("dispatch() -> grp", td_grp)
        # Constants.delta("dispatch()", t)
