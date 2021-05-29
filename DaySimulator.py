import Constants
from Shopper import Shopper, Status
from datetime import datetime, timedelta
from ShopperHandler import ShopperHandler

class DaySimulator:
    def __init__(self, sp, empm, lanem):
        self.smart_products = sp 
        self.employee_manager = empm
        self.lane_manager = lanem
        self.shoppers = []
        self.handler = ShopperHandler(self.smart_products, self.lane_manager)
        self.clock = None

    def __reset_time(self, today):
        self.clock  = datetime(today.year, today.month, today.day, hour=8, minute=0)

    def simulate_day(self, today, next_truck, day_file):
        self.__reset_time(today)
        Constants.CURRENT_TSTEP = 0

        runtime = Constants.log()
        for t_step in range(Constants.DAY_END):
    
            # t_step - specific updates
            if  t_step == Constants.STORE_OPEN:
                self.lane_manager.open_starter_lanes()
            elif Constants.store_open(t_step) and t_step % 60 == 0:
                new_shoppers = [Shopper(t_step) for i in range(Constants.SHOPPER_ADD)]
                self.shoppers = self.shoppers + new_shoppers
            elif t_step == Constants.STORE_CLOSE:
                self.shoppers = [s for s in self.shoppers if s.get_status() != Status.INERT]
            if t_step == Constants.shift_change:
                self.lane_manager.shift_change()

            self.employee_manager.advance_employees(t_step, len(self.shoppers), today, next_truck)

            if t_step >= Constants.STORE_OPEN:
                # advance shoppers
                shopper_count = len(self.shoppers)
                index = 0
                while index < shopper_count:
                    sh = self.shoppers.pop(index)
                    self.handler.handle(sh, t_step)
                    if sh.get_status() != Status.DONE:
                        self.shoppers.insert(0, sh)
                        index += 1
                    else:
                        shopper_count -= 1
                if shopper_count > 0:
                    self.shoppers = [sh for sh in self.shoppers if sh.is_deleted() is False]
        
                # advance lanes
                self.lane_manager.manage()
                self.lane_manager.advance_lanes()

            # print day progress to day_file
            if today.month == Constants.START_CLOCK.month and today.day == Constants.START_CLOCK.day:
                print(f"-------------------------------------------------------------------------------------------------------------------------------------------- TIME STEP {t_step}", file=day_file)
                self.print_active_shoppers(day_file)
                self.lane_manager.print_active_lanes(day_file)
                self.smart_products[0].__print__(day_file)

            self.clock += timedelta(minutes=1)
            Constants.CURRENT_TSTEP += 1

        self.lane_manager.close_all_lanes()
        for emp in self.employee_manager.employees:
            if emp.is_cashier():
                emp.remove_cashier()
        self.shoppers = []

        Constants.delta(f"Day {(self.clock - Constants.START_CLOCK).days}", runtime)  # TODO: remove before submission
        return datetime.now() - runtime


    def print_active_shoppers(self, file):
        print("\n\n--- ACTIVE SHOPPERS ---", file=file)
        inert, shopping, queueing, checkout, done = 0, 0, 0, 0, 0
        for s in self.shoppers:
            if s.get_status() == Status.INERT:
                inert += 1
            elif s.get_status() == Status.SHOPPING:
                shopping += 1
            elif s.get_status() == Status.QUEUEING:
                queueing += 1
            elif s.get_status() == Status.CHECKOUT:
                checkout += 1
            elif s.get_status() == Status.DONE:
                done += 1

        total = Constants.SHOPPER_ADD * (self.clock.hour - Constants.START_CLOCK.hour + 1)
        deleted = total - inert - shopping - queueing - checkout - done
        print("shopper status: inert={}, shopping={}, queueing={}, checkout={}, done={}, departed={}"
                .format(inert, shopping, queueing, checkout, done, deleted), file=file)
