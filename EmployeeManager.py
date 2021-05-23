from Employee import Employee
# import heapq
import Constants
from Constants import Shift


class EmployeeManager:

    def __init__(self, employees, sp):
        self.employees = employees
        self.working_employees = None
        self.smart_products = sp
        self.schedule = [Shift.OFF, Shift.MORNING, Shift.MORNING, Shift.MORNING,
                         Shift.EVENING, Shift.EVENING, Shift.EVENING]
        self.task_list = []

        # tracking the next grp to work on
        self.next_grp_toss = 0 
        self.next_grp_restock = 0
        self.next_grp_unload = 0
        self.refreshed = True  # True if we switch

    def create_employees(self, n):
        assert(n % 7 == 0)
        group_size = n / 7
        group = 0
        for i in range(n):
            if i != 0 and i % group_size == 0:
                group += 1
            emp = Employee(group)
            self.employees.append(emp)
        return self.employees

    def set_day_schedule(self):
        for emp in self.employees:
            emp.set_shift(self.schedule[emp.group])

        # update schedule for next day
        shift = self.schedule.pop(0)
        self.schedule.append(shift)
        self.working_employees = [emp for emp in self.employees if emp.shift == Constants.Shift.MORNING]
        self.current_shift = Constants.Shift.MORNING
        self.refresh = True

    def get_task_start(self, task):
        if task == Constants.TASK_UNLOAD:
            return self.last_grp_unload
        elif task == Constants.TASK_RESTOCK:
            return self.last_grp_restock
        elif task == Constants.TASK_TOSS:
            return self.last_grp_toss
        else:
            print(f"get_task_start(): Invalid task {task}")

    def reset(self, today, next_truck):
        (grp.reset() for grp in self.smart_products)
        self.toss_work = sum(sp.get_work(Constants.TASK_TOSS, today, next_truck) for sp in self.smart_products)
        if today == next_truck:
            self.unload_work = sum(sp.get_work(Constants.TASK_UNLOAD, today, next_truck) for sp in self.smart_products)
        else:
            self.unload_work = 0
        self.restock_work = sum(sp.get_work(Constants.TASK_RESTOCK, today, next_truck) for sp in self.smart_products)

    def get_cashier(self):
        # available = [emp for emp in self.working_employees if emp.is_cashier() is False]
        emp = next((emp for emp in self.working_employees if not emp.is_cashier()))
        emp.set_cashier()
        return emp

    def return_cashier(self, emp):
        emp.remove_cashier()
        assert(emp.is_cashier() is False), "return_cashier(): update failed"

    def advance_employees(self, t_step, shopper_count, today):

        # update working employees 
        if t_step == Constants.StoreStatus.SHIFT_CHANGE:
            self.current_shift = Constants.Shift.EVENING
            self.working_employees = [emp for emp in self.employees if emp.on_shift(self.current_shift)]

        if t_step < Constants.STORE_OPEN:

            if self.unload_work > 0 and self.restock_work > 0:
                # split employees, have half work on unload and half work on restock
                count = int(len(self.working_employees) / 2)
                group_1 = self.working_employees[:count]
                group_2 = self.working_employees[count:]

                # unload
                start = self.next_grp_unload
                for emp in group_1:
                    self.smart_products[start].unload(emp.get_speed(Constants.TASK_UNLOAD))
                    start += 1
                    if start == Constants.PRODUCT_COUNT:
                        start = 0
                self.next_grp_unload = start
                
                # restock
                start = self.next_grp_restock
                for emp in group_2:
                    self.smart_products[start].restock(emp.get_speed(Constants.TASK_RESTOCK))
                    start += 1
                    if start == Constants.PRODUCT_COUNT:
                        start = 0
                self.next_grp_restock = start

            elif self.unload_work > 0:
                start = self.next_grp_unload
                for emp in self.employees:
                    self.smart_products[start].unload(emp.get_speed(Constants.TASK_UNLOAD))
                    start += 1
                    if start == Constants.PRODUCT_COUNT:
                        start = 0
                self.next_grp_unload = start

            else:
                start = self.next_grp_restock
                for emp in self.employees:
                    self.smart_products[start].restock(emp.get_speed(Constants.TASK_RESTOCK))
                    start += 1
                    if start == Constants.PRODUCT_COUNT:
                        start = 0
                self.next_grp_restock = start
          
        # toss while the store is closed and empty
        elif t_step >= Constants.STORE_CLOSE and shopper_count == 0:
            start = self.next_grp_toss
            for emp in self.employees:
                self.smart_products[start].toss(emp.get_speed(Constants.TASK_TOSS), today)
                start += 1
                if start == Constants.PRODUCT_COUNT:
                    start = 0
            self.next_grp_toss = start

        # restock while the store is open or customers are in the store
        elif (t_step >= Constants.STORE_OPEN and t_step < Constants.STORE_CLOSE) or shopper_count > 0:
            start = self.next_grp_restock
            for emp in self.employees:
                self.smart_products[start].restock(emp.get_speed(Constants.TASK_RESTOCK))
                start += 1
                if start == Constants.PRODUCT_COUNT:
                    start = 0
            self.next_grp_restock = start
        
        else:
            print(f"Unaccounted for t_step {t_step}")
            exit(1)


    def print_active_employees(self):
        print("\t--- ACTIVE EMPLOYEES --- ")
        working = [emp for emp in self.employees["unavailable"] if emp.is_cashier()]
        working.sort(key=lambda x: x.action)
        [emp.print() for emp in working]

