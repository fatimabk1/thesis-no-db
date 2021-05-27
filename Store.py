from SmartProduct import SmartProduct
from LaneManager import LaneManager
from DaySimulator import DaySimulator
from ShopperHandler import ShopperHandler
from EmployeeManager import EmployeeManager
from Lane import Lane
from Product import Product
from Cost import Cost
import Constants
from datetime import date, datetime
from datetime import timedelta
import traceback
from Statistics import StatType, Statistics
# import beepy


class Store:
    def __init__(self):
        self.clock = Constants.START_CLOCK
        self.smart_products = []
        self.employees = []
        self.lanes = []
        self.shoppers = []
        self.next_truck = None
        self.stats = Statistics()

        # data collection for stats
        self.qtimes = []

        # aggregate objects
        self.employee_manager = EmployeeManager(self.employees, self.smart_products)
        self.employee_manager.create_employees(Constants.NUM_EMPLOYEES)
        self.lane_manager = LaneManager(self.employee_manager, self.lanes, self.shoppers)

        self.shopper_handler = ShopperHandler(
                                self.smart_products,
                                self.lane_manager,
                                self.qtimes)

        self.day_simulator = DaySimulator(
                                self.smart_products,
                                self.employee_manager,
                                self.lane_manager,
                                self.shopper_handler)
    
        self.setup()
    
    def get_today(self):
        return datetime(self.clock.year, self.clock.month, self.clock.day)
    
    def setup(self):
        # setup products & product_stats
        for grp_id in range(Constants.PRODUCT_COUNT):
            p = Product(grp_id)
            p.setup()
            sp = SmartProduct(p)
            self.smart_products.append(sp)
        
        # setup employees
        self.employee_manager.create_employees(Constants.NUM_EMPLOYEES)

        # setup lanes
        for i in range(Constants.MAX_LANES):
            ln = Lane()
            self.lanes.append(ln)
        today = datetime(self.clock.year, self.clock.month, self.clock.day)
        for sp in self.smart_products:
            sp.setup_starter_inventory(today)

    def simulate_year(self):
        runtime = Constants.log()
        month = self.clock.month
        day_time = []
        day_file, year_file = open('output/day.txt', 'w'), open('output/year.txt', 'w')

        Constants.CURRENT_DAY = 0
        for day in range(365):
            if self.clock.month != month:
                month = self.clock.month
                print(f"\n\n\n\t\t\t**** NEW MONTH: {month} ***\n\n\n", file=year_file)

            print(f"-------------------------------------------------------------------------------------------------------------------------------------------- DAY {day}: {self.clock.month}/{self.clock.day}/{self.clock.year}", file=year_file)
            
            # setup day
            for sp in self.smart_products:
                sp.reset()
                if day < 3:
                    sp.set_cushion()  # only set cushion while we are calibrating ideal daily value
            self.employee_manager.set_day_schedule()
            self.employee_manager.reset(self.get_today(), self.next_truck)

            t = self.day_simulator.simulate_day(self.get_today(), self.next_truck, day_file)
            print("Day ∆:", t, file=year_file)
            day_time.append(t)
            print("Avg day runtime: ", sum(day_time, timedelta(0)) / len(day_time), file=year_file)

            # order inventory
            if day!= 0 and day % (Constants.TRUCK_DAYS ) == 0:
                self.next_truck = self.get_today() + timedelta(days=Constants.TRUCK_DAYS)
                print("\n\t*** ORDERING INVENTORY", file=year_file)
                order_cost = sum([sprod.order_inventory(self.get_today()) for sprod in self.smart_products])
                if self.smart_products[0].pending['quantity'] > 0:
                    sublots = self.smart_products[0].pending['quantity'] / self.smart_products[0].product.get_sublot_quantity()
                    print(f"\t\tORDERED {sublots} inventories of GRP 0", file=year_file)
                self.next_truck = self.get_today() + timedelta(days=Constants.TRUCK_DAYS)
                print(f"\t> order available {self.next_truck.month}/{self.next_truck.day}/{self.next_truck.year}", file=year_file)

            # pay labor
            if day != 0 and day % 7 == 0:
                labor_payment = sum(emp.get_paycheck() for emp in self.employees)
                self.stats.add_stat(StatType.LABOR, [self.get_today(), labor_payment])
                print(f"\n\t\t\t*** LABOR PAYMENT = ${labor_payment} ***", file=year_file)
            else:
                self.stats.add_stat(StatType.LABOR, [self.get_today(), 0])

            # update stats object
            for sp in self.smart_products:
                stats = sp.get_today_stats()
                self.stats.add_stat(StatType.SOLD, [sp.product.get_id(), self.get_today(), stats['sold']])
                self.stats.add_stat(StatType.TOSS, [sp.product.get_id(), self.get_today(), stats['toss']])
                self.stats.add_stat(StatType.MISS, [sp.product.get_id(), self.get_today(), stats['miss']])
                self.stats.add_stat(StatType.REVENUE, [sp.product.get_id(), self.get_today(), stats['sold'] * sp.product.get_price()])
                self.stats.add_stat(StatType.ORDER, [sp.product.get_id(), self.get_today(), stats['order_cost']])

            self.smart_products[0].__print__(file=year_file)
            self.clock += timedelta(days=1)
            Constants.CURRENT_DAY += 1
            if day == 1:
                day_file.close()
            
            if day == 4:
                break
        
        self.stats.print_all_stats()
        print("One Year ∆:", datetime.now() - runtime, file=year_file)
        year_file.close()


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


# def print_all_stats(smart_products, print_time, day):
#     for sp in smart_products:
#         path = os.path.join('stats', print_time, f'SmartProduct_{sp.product.get_id()}')
#         pathlib.Path(path).mkdir(parents=True, exist_ok=True)
#         with open(path + f'/Day_{day}.txt', 'w') as f:
#             sp.print(sp.product.get_id(), f)


if __name__ == '__main__':
    t = Constants.log()
    try:
        store = Store()
        store.simulate_year()
        print("A Successful Year Complete!")
        print("Runtime: ∆ ", datetime.now() - t)
        # beepy.beep(sound=5)
    except Exception as e:
        print("Year simulation failed")
        print("Runtime: ∆ ", datetime.now() - t)
        # beepy.beep(sound=3)
        traceback.print_exc()
        print(e)
