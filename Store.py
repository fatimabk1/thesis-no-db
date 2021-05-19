from Statistics import Visualization
from InventoryManager import InventoryManager
from LaneManager import LaneManager
from DaySimulator import DaySimulator
from InventoryManager import InventoryManager
from ShopperHandler import ShopperHandler
from EmployeeManager import EmployeeManager
from Lane import Lane
from Product import Product
from Cost import Cost
import Constants
from Constants import log, delta
from datetime import date, datetime
from Statistics import Visualization
from datetime import timedelta
import traceback
import beepy


class Store:
    def __init__(self):
        self.clock = datetime(2019, 9, 15, 10, 0)
        self.products = []
        self.inventory_lookup = {}
        self.employees = []
        self.lanes = []
        self.shoppers = []
        self.vis = Visualization() 

        # START HERE >>>
        # 4. TODO: add code to make product selection a distribution  --> AT END OF PROJECT
        #       --> likelihood of selecting grp x should correlate w/amt stocked.
        #           If less is stocked, it's less popular --> fewer total purchases
        #           --> customers are less likely to purchase grp x than grp y

        # data collection for stats
        self.product_stats = {}  # {grp_id: {"shelf": #, "back": #, "pending": #, "sold": [today, today - 1, today - 2] , "oos": #}}
        self.revenues = []
        self.costs = []
        self.qtimes = []

        # aggregate objects
        self.inventory_manager = InventoryManager(self.inventory_lookup,
                                self.products, self.product_stats, self.costs)
        self.employee_manager = EmployeeManager(self.employees, self.inventory_manager)
        self.employee_manager.create_employees(Constants.NUM_EMPLOYEES)
        self.lane_manager = LaneManager(self.employee_manager, self.lanes, self.shoppers)

        self.shopper_handler = ShopperHandler(
                                self.products,
                                self.inventory_lookup,
                                self.product_stats,
                                self.lane_manager,
                                self.revenues,
                                self.qtimes,
                                self.clock)

        self.day_simulator = DaySimulator(
                                self.inventory_manager,
                                self.employee_manager,
                                self.lane_manager,
                                self.shopper_handler,
                                self.product_stats,
                                self.vis)
    
        self.setup()
    
    def get_today(self):
        return datetime(self.clock.year, self.clock.month, self.clock.day)
    
    def setup(self):
        # setup products & product_stats
        category = 0
        for grp_id in range(Constants.PRODUCT_COUNT):
            if grp_id !=0 and grp_id % Constants.CATEGORY_COUNT == 0:
                category += 1
            p = Product(grp_id, category)
            p.setup()
            self.product_stats[grp_id] = {
                "shelf": 0,  # total current shelved stock
                "back": 0,  # total current back stock
                "pending": 0,  # total current pending stock
                "sold": [0, 0, 0],  # list of stock sold each day for three days [today, yesterday, two-days-ago]
                "oos": {}  # dictionary of dates & # of misses
                }
            self.inventory_lookup[grp_id] = []
            self.products.append(p)
        
        # setup employees
        self.employee_manager.create_employees(Constants.NUM_EMPLOYEES)

        # setup lanes
        for i in range(Constants.MAX_LANES):
            ln = Lane()
            self.lanes.append(ln)
        today = datetime(self.clock.year, self.clock.month, self.clock.day)
        self.inventory_manager.setup_starter_inventory(today)
        # self.inventory_manager.print_stock_status()

    def simulate_year(self):
        runtime = Constants.log()
        month = self.clock.month
        for i in range(365):
            if self.clock.month != month:
                month = self.clock.month
                print(f"\n\n\n\t\t\t**** NEW MONTH: {month} ***\n\n\n")
            print(f"-------------------------------------------------------------------------------------------------- DAY {i}: {self.clock.month}/{self.clock.day}/{self.clock.year}")
            # setup day
            self.employee_manager.set_day_schedule()
            for grp in self.product_stats:
                sold = self.product_stats[grp]["sold"]
                if(len(sold) == 3):
                    sold.pop()
                sold.insert(0, 0)
                self.product_stats[grp]["oos"][self.get_today()] = 0
                self.product_stats[grp]["toss"] = 0
                self.products[grp].set_order_threshold(sold)
            self.day_simulator.simulate_day(self.get_today())
            inv_lst = self.inventory_lookup[0]
            expected_toss = sum(inv.get_shelf() + inv.get_back() + inv.get_pending()
                                for inv in inv_lst if inv.is_expired(self.get_today()))
            Constants.print_stock(0, self.products, self.product_stats, expected_toss)
            # self.update_daily_statistics()

            # order inventory
            if i!= 0 and i % (Constants.TRUCK_DAYS + 2) == 0:
                print("\n\t*** ORDERING INVENTORY")
                self.inventory_manager.order_inventory(self.get_today())
                ready = self.get_today() + timedelta(days=Constants.TRUCK_DAYS)
                print(f"\t> order available {ready.month}/{ready.day}/{ready.year}")

            # pay employees
            # TODO: fix so employees paid regularly on day / end of month
            if i!= 0 and i % 7 == 0:
                # return
                # emps work 6 days a week, x hrs each shift, at $x an hour
                labor_payment = sum(emp.get_paycheck() for emp in self.employees)
                print(f"\n\t\t\t*** LABOR PAYMENT = ${labor_payment} ***")
                # c = Cost(today, labor_payment, 'labor')
                # self.cost.append(c)
            # update clock
            self.clock += timedelta(days=1)
        Constants.delta("A Year", runtime)


    def update_daily_statistics(self):
        q_sold = 0
        for grp in self.product_stats:
            if len(self.product_stats[grp]['sold']) == 0:
                continue
            else:
                q_sold += self.product_stats[grp]['sold'][-1]
        self.vis.update(self.get_today(), q_sold)


    def update_monthly_statistics(self):
        pass

    def test_day(self):
        t = datetime.now()
        for key in self.inventory_lookup:
            # print("\n > Product ", key)
            # take advantage of sort stability. Sort by secondary key, then primary
            self.inventory_lookup[key].sort(key=lambda x: x.get_sell_by())
            self.inventory_lookup[key].sort(key=lambda x:x.get_shelf(), reverse=True)
            # for i in range(len(self.inventory_lookup[key])):
            #     self.inventory_lookup[key][i].print()
            #     if i == 100:
            #         break

        today = date(self.clock.year, self.clock.month, self.clock.day)
        self.employee_manager.set_day_schedule()

        # update order_threshold according to recent sales data
        for grp in self.product_stats:
            sold = self.product_stats[grp]["sold"]
            if(len(sold) == 3):
                sold.pop()
            sold.insert(0, 0)
            self.product_stats[grp]["oos"][today] = 0
            self.products[grp - 1].set_order_threshold(sold)

        # self.inventory_manager.print_stock_status()

        # print("Hello hello hello")
        # for grp in self.inventory_lookup:
        #     inv_lst = self.inventory_lookup[grp]
        #     back, pending, shelf = 0, 0, 0
        #     for inv in inv_lst:
        #         back += inv.get_back()
        #         shelf += inv.get_shelf()
        #         pending += inv.get_pending()
        #     assert(back == self.product_stats[grp]['back']), f"MISMATCH STOCK STATS: back = {back} != {self.product_stats[grp]['back']} = stats_back"
        #     if back > 0:
        #         print(f"\n\tGRP {grp} inventory with back stock")
        #         for inv in inv_lst:
        #             if inv.get_back() > 0:
        #                 inv.print()

        #     assert(shelf == self.product_stats[grp]['shelf']), f"MISMATCH STOCK STATS: shelf = {shelf} != {self.product_stats[grp]['shelf']} = stats_shelf"
        #     assert(pending == self.product_stats[grp]['pending']), f"MISMATCH STOCK STATS: pending = {pending} != {self.product_stats[grp]['pending']} = stats_pending"
        # print("\nGood Job!")
        # exit(0)
        self.day_simulator.simulate_day(today)
        # self.inventory_manager.print_stock_status()
        print("All Done!")
        print("Runtime: ∆ ", datetime.now() - t)


if __name__ == '__main__':
    try:
        t = Constants.log()
        store = Store()
        store.simulate_year()
        print("A Successful Year Complete!")
        print("Runtime: ∆ ", datetime.now() - t)
        beepy.beep(sound=5)
    except Exception as e:
        beepy.beep(sound=3)
        traceback.print_exc()
        print(e)
