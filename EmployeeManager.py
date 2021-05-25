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

        # tracking products to work on, refreshed each t_step
        self.toss_tasks = []
        self.unload_tasks = []
        self.restock_tasks = []

        # index of next task to work on for employees with leftover capacity in the same t_step
        self.next_toss = 0
        self.next_unload = 0
        self.next_restock = 0


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

    def refresh_tasks(self, task, today, next_truck):
        if task == Constants.TASK_TOSS:
            self.toss_tasks = [sp for sp in self.smart_products if sp.has_work(task, today, next_truck)]
            self.toss_tasks.sort(key=lambda x: x.get_work(task, today, next_truck))
        elif task == Constants.TASK_RESTOCK:
            self.restock_tasks = [sp for sp in self.smart_products if sp.has_work(task, today, next_truck)]
            self.restock_tasks.sort(key=lambda x: x.get_work(task, today, next_truck))
        elif task == Constants.TASK_UNLOAD:
            if today == next_truck:
                self.unload_tasks = [sp for sp in self.smart_products if sp.has_work(task, today, next_truck)]
                self.unload_tasks.sort(key=lambda x: x.get_work(task, today, next_truck))
            else:
                self.unload_tasks = []
        else:
            print(f"EmployeeManager.refresh_task(): FATAL - invalid task {task}")
            exit(1)

    # wrapped incrementing of indices referring to array
    def __wrapped_increment(self, index: int, arr: list):
        if index == len(arr) - 1:
            return 0
        else:
            return index + 1


    # TODO: START HERE >>> 
    # infinite loop on restock, potential others when no work
    # workshop a starting inventory value

    def advance_employees(self, t_step, shopper_count, today, next_truck):

        # TODO:
        """
        Concerns:
        - there are more products than employees. We want to make sure that all products are handled 
        - Quick way to determine that there is no work to be done on any products
        - want to refresh the list of products that need work done each minute

        - refresh sorted list of all products, ordered by work value
            self.toss_tasks = []
            self.unload_tasks = []
            self.restock_tasks = []
            self.next_toss = 0
            self.next_unload = 0
            self.next_restock = 0
        - while task_list is not None:
            - while emp_
            - multiple employees work together on one product
            - remove product from list when complete

            loop through with grp and emp index


        1. At the top of task start, query each SmartProduct for work. If they have work, append to task list
        """

        # update working employees 
        if t_step == Constants.StoreStatus.SHIFT_CHANGE:
            self.current_shift = Constants.Shift.EVENING
            self.working_employees = [emp for emp in self.employees if emp.on_shift(self.current_shift)]

        available_emps = [emp for emp in self.working_employees if emp.is_cashier() is False]

        if t_step < Constants.STORE_OPEN:
            self.refresh_tasks(Constants.TASK_UNLOAD, today, next_truck)
            self.refresh_tasks(Constants.TASK_RESTOCK, today, next_truck)

            if self.unload_tasks and self.restock_tasks:
                # print("unloading and restocking")
                # split employees, have half work on unload and half work on restock
                count = int(len(available_emps) / 2)
                group_1 = available_emps[:count]
                group_2 = available_emps[count:]

                # unload
                # print("UNLOADING")
                emp_index = 0
                while(self.unload_tasks and emp_index != len(available_emps)):
                    emp_q = self.employees[emp_index].get_speed(Constants.TASK_UNLOAD)
                    emp_q -= self.unload_tasks[0].unload(emp_q)
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_UNLOAD)
                    # if product work is finished, remove from list
                    if self.unload_tasks[0].has_work(Constants.TASK_UNLOAD, today, next_truck) is False:
                        self.unload_tasks.pop(0)

                # restock
                # print("MORNING RESTOCKING")
                emp_index = 0
                while(self.restock_tasks and emp_index != len(available_emps)):
                    # print(f"len restock = {len(self.restock_tasks)}")
                    emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                    emp_q -= self.restock_tasks[0].restock(emp_q)
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                    # if product work is finished, remove from list
                    if self.restock_tasks[0].has_work(Constants.TASK_RESTOCK, today, next_truck) is False:
                        self.restock_tasks.pop(0)

            elif self.unload_tasks:
                # print("UNLOADING")
                emp_index = 0
                while(self.unload_tasks and emp_index != len(available_emps)):
                    emp_q = self.employees[emp_index].get_speed(Constants.TASK_UNLOAD)
                    emp_q -= self.unload_tasks[0].unload(emp_q)
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_UNLOAD)
                    # if product work is finished, remove from list
                    if self.unload_tasks[0].has_work(Constants.TASK_UNLOAD, today, next_truck) is False:
                        self.unload_tasks.pop(0)

            elif self.restock_tasks :
                emp_index = 0
                while(self.restock_tasks and emp_index != len(available_emps)):
                    # print(f"len restock = {len(self.restock_tasks)}")
                    emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                    emp_q -= self.restock_tasks[0].restock(emp_q)
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                    # if product work is finished, remove from list
                    if self.restock_tasks[0].has_work(Constants.TASK_RESTOCK, today, next_truck) is False:
                        self.restock_tasks.pop(0)

        # toss while the store is closed and empty
        elif t_step >= Constants.STORE_CLOSE and shopper_count == 0:
            self.refresh_tasks(Constants.TASK_TOSS, today, next_truck)
            emp_index = 0
            while(self.toss_tasks and emp_index != len(available_emps)):
                emp_q = self.employees[emp_index].get_speed(Constants.TASK_TOSS)
                emp_q -= self.toss_tasks[0].toss(emp_q, today)
                # if emp has extra capacity, help with next product
                if emp_q == 0:
                    emp_index += 1
                    emp_q = self.employees[emp_index].get_speed(Constants.TASK_TOSS)
                # if product work is finished, remove from list
                if self.toss_tasks[0].has_work(Constants.TASK_TOSS, today, next_truck) is False:
                    self.toss_tasks.pop(0)

        # restock while the store is open or customers are in the store
        elif (t_step >= Constants.STORE_OPEN and t_step < Constants.STORE_CLOSE) or shopper_count > 0:
            self.refresh_tasks(Constants.TASK_RESTOCK, today, next_truck)
            if self.restock_tasks:
                emp_index = 0
                emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                while(self.restock_tasks and emp_index != len(available_emps)):
                    # print(f"restocking grp {self.restock_tasks[0].product.get_id()} via emp {emp_index} with {emp_q} capacity  - current work is {self.restock_tasks[0].get_work(Constants.TASK_RESTOCK, today, next_truck)}")
                    emp_q -= self.restock_tasks[0].restock(emp_q)
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                    # if product work is finished, remove from list
                    if self.restock_tasks[0].has_work(Constants.TASK_RESTOCK, today, next_truck) is False:
                        self.restock_tasks.pop(0)

        else:
            print(f"Unaccounted for t_step {t_step}")
            exit(1)


    def print_active_employees(self):
        print("\t--- ACTIVE EMPLOYEES --- ")
        working = [emp for emp in self.employees["unavailable"] if emp.is_cashier()]
        working.sort(key=lambda x: x.action)
        [emp.print() for emp in working]

