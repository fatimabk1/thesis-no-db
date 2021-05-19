from Employee import Employee
import Constants
from Constants import Shift


class EmployeeManager:

    def __init__(self, employees, inv_man):
        self.employees = employees
        self.working_employees = None
        self.inventory_manager = inv_man
        self.schedule = [Shift.OFF, Shift.MORNING, Shift.MORNING, Shift.MORNING,
                         Shift.EVENING, Shift.EVENING, Shift.EVENING]
        self.task_list = []
        self.refresh = True

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

    def get_cashier(self):
        # available = [emp for emp in self.working_employees if emp.is_cashier() is False]
        emp = next((emp for emp in self.working_employees if not emp.is_cashier()))
        emp.set_cashier()
        return emp

    def return_cashier(self, emp):
        emp.remove_cashier()
        assert(emp.is_cashier() is False), "return_cashier(): update failed"

    def advance_employees(self, t_step, today, shopper_count):
        # update working employees 
        if t_step == Constants.StoreStatus.SHIFT_CHANGE:
            self.current_shift = Constants.Shift.EVENING
            self.working_employees = [emp for emp in self.employees if emp.on_shift(self.current_shift)]

        # remove inventories marked as 'deleted'
        # for grp in self.inventory_manager.inventory_lookup:
        #     self.inventory_manager.inventory_lookup[grp] = [inv for inv in self.inventory_manager.inventory_lookup[grp]
        #                                                     if inv.is_deleted() is False]

        # ------------------------------------------------------------------------------------------------ refresh & do tasks
        # unload and/or restock before the store opens
        if t_step == Constants.STORE_OPEN:
            task_1, task_lookup_1 = Constants.TASK_UNLOAD, self.inventory_manager.get_unload_list(today)
            task_2, task_lookup_2 = Constants.TASK_RESTOCK, self.inventory_manager.get_restock_list()
            count = int(len(self.working_employees) / 2)
            group_1 = self.working_employees[:count]
            group_2 = self.working_employees[count:]

            if bool(task_lookup_1) and bool(task_lookup_2):
                self.inventory_manager.dispatch(task_1, task_lookup_1, group_1, today)
                self.inventory_manager.dispatch(task_2, task_lookup_2, group_2, today)
                self.task_list = [task_1, task_lookup_1, task_2, task_lookup_2]
            elif bool(task_lookup_1):
                self.inventory_manager.dispatch(task_1, task_lookup_1, self.working_employees, today)
                self.task_list = [task_1, task_lookup_1]
            else:
                self.inventory_manager.dispatch(task_2, task_lookup_2, self.working_employees, today)
                self.task_list = [task_2, task_lookup_2]

        # toss while the store is closed and empty
        elif t_step >= Constants.STORE_CLOSE and shopper_count == 0 and self.refresh:
            task, task_lookup = Constants.TASK_TOSS, self.inventory_manager.get_toss_list(today)
            if bool(task_lookup):
                self.inventory_manager.dispatch(task, task_lookup, self.working_employees, today)
                self.task_list = [task, task_lookup]
            self.refresh = False
        
        # restock while the store is open or customers are in the store
        elif t_step > Constants.STORE_OPEN and t_step < Constants.STORE_CLOSE and t_step % 30 == 0:
            task, task_lookup = Constants.TASK_RESTOCK, self.inventory_manager.get_restock_list()
            if bool(task_lookup):
                self.inventory_manager.dispatch(task, task_lookup, self.working_employees, today)
                self.task_list = [task, task_lookup]

        # ------------------------------------------------------------------------------------------------ do tasks in existing list
        else:
            if len(self.task_list) == 4:
                task_1, task_lookup_1 = self.task_list[0], self.task_list[1]
                task_2, task_lookup_2 = self.task_list[2], self.task_list[3]
                count = int(len(self.working_employees) / 2)
                group_1 = self.working_employees[:count]
                group_2 = self.working_employees[count:]

                if bool(task_lookup_1) and bool(task_lookup_2):
                    # remove inventories marked as 'deleted'
                    for grp in task_lookup_1:
                        task_lookup_1[grp]["inventory"] = [inv for inv in task_lookup_1[grp]["inventory"] if inv.is_deleted() is False]
                    for grp in task_lookup_2:
                        task_lookup_2[grp]["inventory"] = [inv for inv in task_lookup_2[grp]["inventory"] if inv.is_deleted() is False]

                    self.inventory_manager.dispatch(task_1, task_lookup_1, group_1, today)
                    self.inventory_manager.dispatch(task_2, task_lookup_2, group_2, today)
                    self.task_list = [task_1, task_lookup_1, task_2, task_lookup_2]
            else:
                assert(len(self.task_list) == 0 or len(self.task_list) == 2), f"advance_employees(): {len(self.task_list)} is an invalid number of tasks"
                if len(self.task_list) == 0:
                    return
                task, task_lookup = self.task_list[0], self.task_list[1]
                # remove inventories marked as 'deleted'
                for grp in task_lookup:
                    task_lookup[grp]["inventory"] = [inv for inv in task_lookup[grp]["inventory"] if inv.is_deleted() is False]
                if bool(task_lookup):
                    self.inventory_manager.dispatch(task, task_lookup, self.working_employees, today)


    def print_active_employees(self):
        print("\t--- ACTIVE EMPLOYEES --- ")
        working = [emp for emp in self.employees["unavailable"] if emp.is_cashier()]
        working.sort(key=lambda x: x.action)
        [emp.print() for emp in working]

