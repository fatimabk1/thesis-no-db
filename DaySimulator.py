import Constants
from Shopper import Shopper, Status
from datetime import datetime, timedelta

class DaySimulator:
    def __init__(self, sp, empm, lanem, handler):
        self.smart_products = sp  # TODO: REMOVE AFTER CHECKING sp.print()
        self.employee_manager = empm
        self.lane_manager = lanem
        self.shoppers = []
        self.handler = handler
        self.clock = None

    def __reset_time(self, today):
        self.clock  = datetime(today.year, today.month, today.day, hour=8, minute=0)

    def simulate_day(self, today, next_truck):
        self.__reset_time(today)
        self.smart_products[0].print(0, today, next_truck)

        runtime = Constants.log()
        for t_step in range(Constants.DAY_END):
            # print("-------------------- TIME STEP ", t_step)
            # step_time = Constants.log()
            # t_step - specific updates
            if  t_step == Constants.STORE_OPEN:
                self.lane_manager.open_starter_lanes()
            elif Constants.store_open(t_step) and t_step % 60 == 0:
                new_shoppers = [Shopper(t_step) for i in range(300)]
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
                    self.handler.handle(sh, t_step, today)
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
            # Constants.delta("T_STEP", step_time)
            self.clock += timedelta(minutes=1)

        # clean up and reset for the next day
        self.smart_products[0].print(t_step, today, next_truck)
        # self.lane_manager.print_active_lanes()
        self.lane_manager.close_all_lanes()
        for emp in self.employee_manager.employees:
            if emp.is_cashier():
                emp.remove_cashier()
        self.shoppers = []

        Constants.delta("A Day", runtime)
        return datetime.now() - runtime


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


            # refresh tasks every 30 mins and at changes in task type
            # unload: daystart - store open
            # restock: store open-close
            # toss: store close - day end


            # TODO: 
            # 1. UNLOAD & RESTOCK EVERY MORNING - split employees in two groups and do both?
            # 2. REFRESH DAYTIME RESTOCK EVERY 30 MINS
            # 3 BEGIN TOSS AFTER STORE CLOSE & ALL SHOPPERS GONE - when len(self.shoppers) == 0
            # 4. IF ANY TIME LEFT, RESTOCK --> 3 & 4: split employees in two groups and do both

            # RESTRUCTURING:
            # 1. Pull multiple task lists as needed.
            # 2. Divide emps into multiple groups
            # 3. Call dispatch with one task group & emp group.
            # 4. Move all the task/task_lookup stuff

            # refresh task list
            # if t_step == Constants.DAY_START:
            #     # do unload and restock
            #     task, task_lookup = self.inventory_manager.get_unload_list()
            #     task, task_lookup = self.inventory_manager.get_restock_list()
            #     group_1 = 
            # elif t_step == Constants.STORE_OPEN:
            #     pass
            # elif t_step == Constants.STORE_CLOSE and len(self.shoppers) == 0:
            #     task, task_lookup = None, None


            # if t_step % 30 == 0 or t_step == Constants.DAY_START or t_step == Constants.STORE_OPEN or t_step == Constants.STORE_CLOSE:

            #     task, task_lookup = self.inventory_manager.refresh_tasks(t_step, today)

            #     # if nothing to unload, restock in the morning
            #     if task == Constants.TASK_UNLOAD and bool(task_lookup) is False:
            #         task = Constants.TASK_RESTOCK
            #         task_lookup = self.inventory_manager.get_restock_list()
                
                # start tossing products if store closed & 

            # update inventory lookup and task_lookup to remove inventories marked as 'deleted
            # for grp in task_lookup:
            #     task_lookup[grp]["inventory"] = [inv for inv in task_lookup[grp]["inventory"] if inv.is_deleted() is False]
            # for grp in self.inventory_manager.inventory_lookup:
            #     self.inventory_manager.inventory_lookup[grp] = [inv for inv in self.inventory_manager.inventory_lookup[grp]
            #                                                     if inv.is_deleted() is False]
