import Constants
from Shopper import Shopper, Status
from datetime import datetime, timedelta

class DaySimulator:
    def __init__(self, invm, empm, lanem, handler, ps, vis):
        self.inventory_manager = invm
        self.employee_manager = empm
        self.lane_manager = lanem
        self.shoppers = []
        self.handler = handler
        self.product_stats = ps
        self.vis = vis
        self.clock = None

    def __reset_time(self, today):
        self.clock  = datetime(today.year, today.month, today.day, hour=8, minute=0)

    def simulate_day(self, today):
        self.__reset_time(today)

        runtime = Constants.log()
        task, task_lookup = self.inventory_manager.refresh_tasks(0, today)
        for t_step in range(Constants.DAY_END):
            # print("-------------------- TIME STEP ", t_step)
            # t_step - specific updates
            if  t_step == Constants.StoreStatus.OPEN:
                # Constants.print_stock(5, self.product_stats, "OPN")
                t = Constants.log()
                self.lane_manager.open_starter_lanes()
                Constants.delta("open_starter_lanes()", t)
            elif Constants.store_open(t_step) and t_step % 60 == 0:
                t = Constants.log()
                new_shoppers = [Shopper(t_step) for i in range(300)]
                self.shoppers = self.shoppers + new_shoppers
                Constants.delta("add shoppers", t)
            elif t_step == Constants.StoreStatus.CLOSED:
                # Constants.print_stock(5, self.product_stats, "CLS")
                t = Constants.log()
                self.shoppers = [s for s in self.shoppers if s.get_status() != Status.INERT]
                Constants.delta("filter out inert shopper after store close", t)
            if t_step == Constants.shift_change:
                t = Constants.log()
                self.lane_manager.shift_change()
                Constants.delta("lane_manager.shift_change()", t)

            if t_step % 30 == 0 and t_step != 0:
                t = Constants.log()
                task, task_lookup = self.inventory_manager.refresh_tasks(t_step, today)
                Constants.delta("refresh tasks", t)
                # print(f"> refreshing tasks: {task}")
            t = Constants.log()
            self.employee_manager.advance_employees(t_step, today, task, task_lookup)
            Constants.delta("advance_employees()", t)
           
            if t_step > Constants.StoreStatus.OPEN:
                # advance shoppers
                t = Constants.log()
                shopper_count = len(self.shoppers)
                index = 0
                while index < shopper_count:
                    sh = self.shoppers.pop(index)
                    self.handler.handle(sh, t_step, today)
                    if sh.get_status() != Status.DONE:
                        self.shoppers.insert(0, sh)
                        index += 1
                    else:
                        shopper_count -= 1
                Constants.delta("advance shoppers", t)

                # advance lanes
                t = Constants.log()
                self.lane_manager.manage()
                Constants.delta("manage lanes()", t)
                t = Constants.log()
                self.lane_manager.advance_lanes()
                Constants.delta("advance lanes()", t)

            self.clock += timedelta(minutes=1)

        # clean up and reset for the next day
        t = Constants.log()
        self.lane_manager.close_all_lanes()
        for emp in self.employee_manager.employees:
            if emp.is_cashier():
                emp.remove_cashier()
        self.shoppers = []
        Constants.delta("cleanup and reset for the next day", t)

        # print("\n\n A SUCCESSFUL DAY~")
        Constants.delta("A Day", runtime)


def print_active_shoppers(shoppers):
    print("\n\n--- ACTIVE SHOPPERS ---")
    inert, shopping, queueing, checkout, done = 0, 0, 0, 0, 0
    for s in shoppers:
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
    print("shopper status: inert={}, shopping={}, queueing={}, checkout={}, done={}"
            .format(inert, shopping, queueing, checkout, done))
