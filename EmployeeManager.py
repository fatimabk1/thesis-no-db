from Employee import Employee
import Constants
from Constants import Shift
import bisect


class EmployeeManager:

    def __init__(self, employees, sp):
        self.employees = employees
        self.working_employees = None
        self.smart_products = sp
        self.schedule = [Shift.OFF, Shift.MORNING, Shift.MORNING, Shift.MORNING,
                         Shift.EVENING, Shift.EVENING, Shift.EVENING]
        self.current_shift = Constants.Shift.MORNING

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

    def reset(self, today, next_truck):
        self.toss_work = sum(sp.get_work(Constants.TASK_TOSS, today, next_truck) for sp in self.smart_products)
        if today == next_truck:
            self.unload_work = sum(sp.get_work(Constants.TASK_UNLOAD, today, next_truck) for sp in self.smart_products)
        else:
            self.unload_work = 0
        self.restock_work = sum(sp.get_work(Constants.TASK_RESTOCK, today, next_truck) for sp in self.smart_products)

    def get_cashier(self):
        emp = next((emp for emp in self.working_employees if not emp.is_cashier()))
        emp.set_cashier()
        return emp

    def return_cashier(self, emp):
        emp.remove_cashier()
        assert(emp.is_cashier() is False), "return_cashier(): update failed"

    def refresh_tasks(self, task, today, next_truck):
        # print("> REFRESHING tasks")
        if task == Constants.TASK_TOSS:
            self.toss_tasks = []
            for sp in self.smart_products:
                work = sp.get_work(task, today, next_truck)
                if work > 0:
                    self.toss_tasks.append([sp, work])
            # print(f"\t toss tasks = {len(self.toss_tasks)}")
            # self.toss_tasks.sort(key=lambda x: x[1])
        elif task == Constants.TASK_RESTOCK:
            self.restock_tasks = []
            for sp in self.smart_products:
                work = sp.get_work(task, today, next_truck)
                if work > 0:
                    self.restock_tasks.append([sp, work])
            # print(f"\t restock tasks = {len(self.restock_tasks)}")
            self.restock_tasks.sort(key=lambda x: x[1])
        elif task == Constants.TASK_UNLOAD:
            if today == next_truck:
                self.unload_tasks = []
                for sp in self.smart_products:
                    work = sp.get_work(task, today, next_truck)
                    if work > 0:
                        self.unload_tasks.append([sp, work])
                # print(f"\t unload tasks = {len(self.unload_tasks)}")
                # self.unload_tasks.sort(key=lambda x: x[1])
            else:
                self.unload_tasks = []
                # print("\tunload tasks = 0 -- not truck today")
        else:
            print(f"EmployeeManager.refresh_task(): FATAL - invalid task {task}")
            exit(1)


    def advance_employees(self, t_step, shopper_count, today, next_truck):
        # print("> ADVANCING EMPLOYEES")
        # update working employees 
        if t_step == Constants.SHIFT_CHANGE:
            self.current_shift = Constants.Shift.EVENING
            self.working_employees = [emp for emp in self.employees if emp.on_shift(self.current_shift)]

        available_emps = [emp for emp in self.working_employees if emp.is_cashier() is False]

        if t_step < Constants.STORE_OPEN:
            self.refresh_tasks(Constants.TASK_UNLOAD, today, next_truck)
            self.refresh_tasks(Constants.TASK_RESTOCK, today, next_truck)

            if self.unload_tasks and self.restock_tasks:
                # split employees, have half work on unload and half work on restock
                count = int(len(available_emps) / 2)
                group_1 = available_emps[:count]
                group_2 = available_emps[count:]

                # unload
                emp_index = 0
                emp_q = group_1[emp_index].get_speed(Constants.TASK_UNLOAD)
                while(self.unload_tasks and emp_index != len(group_1)):
                    sp = self.unload_tasks[0][0]
                    work_done = sp.unload(emp_q)
                    self.unload_tasks[0][1] -= work_done
                    # convert emp_q back to units of lots
                    emp_q -= int(work_done / (sp.product.get_num_sublots() * sp.product.get_sublot_quantity()))
                    # if emp has extra capacity, help with next product, else get next employee
                    if emp_q == 0:
                        emp_index += 1
                        if emp_index == len(group_1):
                            break
                        emp_q = group_1[emp_index].get_speed(Constants.TASK_UNLOAD)
                        # emp_q = group_1[emp_index].get_speed(Constants.TASK_UNLOAD)
                    # if product work is finished, remove from list
                    if self.unload_tasks[0][1] == 0:
                        self.unload_tasks.pop(0)

                # restock
                emp_index = 0
                emp_q = group_2[emp_index].get_speed(Constants.TASK_RESTOCK)
                while(self.restock_tasks and emp_index != len(group_2)):
                    print(f"restocking grp {self.restock_tasks[0][0].product.get_id()}: quantity[{self.restock_tasks[0][1]}] via emp {emp_index} with emp_q {emp_q}")
                    work_done = self.restock_tasks[0][0].restock(emp_q)
                    print(f"\t work done = {work_done}")
                    emp_q -= work_done
                    self.restock_tasks[0][1] -= work_done
                    print(f"\tupdated quantity = {self.restock_tasks[0][1]}")
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        if emp_index == len(group_2):
                            break
                        emp_q = group_2[emp_index].get_speed(Constants.TASK_RESTOCK)
                    # if product work is finished, remove from list
                    if self.restock_tasks[0][1] == 0:
                        self.restock_tasks.pop(0)

            elif self.unload_tasks:
                emp_index = 0
                emp_q = self.employees[emp_index].get_speed(Constants.TASK_UNLOAD)
                while(self.unload_tasks and emp_index != len(available_emps)):
                    sp = self.unload_tasks[0][0]
                    work_done = sp.unload(emp_q)
                    self.unload_tasks[0][1] -= work_done
                    # convert emp_q back to units of lots
                    emp_q -= int(work_done / (sp.product.get_num_sublots() * sp.product.get_sublot_quantity()))
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        if emp_index == len(self.employees):
                            break
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_UNLOAD)
                    # if product work is finished, remove from list
                    if self.unload_tasks[0][1] == 0:
                        self.unload_tasks.pop(0)

            elif self.restock_tasks:
                emp_index = 0
                emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                while(self.restock_tasks and emp_index != len(available_emps)):
                    print(f"restocking grp {self.restock_tasks[0][0].product.get_id()}: quantity[{self.restock_tasks[0][1]}] via emp {emp_index} with emp_q {emp_q}")
                    work_done = self.restock_tasks[0][0].restock(emp_q)
                    print(f"\t work done = {work_done}")
                    emp_q -= work_done
                    self.restock_tasks[0][1] -= work_done
                    print(f"\tupdated quantity = {self.restock_tasks[0][1]}")
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        if emp_index == len(self.employees):
                            break
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                    # if product work is finished, remove from list
                    if self.restock_tasks[0][1] == 0:
                        self.restock_tasks.pop(0)

        # toss while the store is closed and empty
        elif t_step >= Constants.STORE_CLOSE and shopper_count == 0:
            self.refresh_tasks(Constants.TASK_TOSS, today, next_truck)
            emp_index = 0
            emp_q = self.employees[emp_index].get_speed(Constants.TASK_TOSS)
            while(self.toss_tasks and emp_index != len(available_emps)):
                work_done = self.toss_tasks[0][0].toss(emp_q, today)
                emp_q -= work_done
                self.toss_tasks[0][1] -= work_done
                # if emp has extra capacity, help with next product
                if emp_q == 0:
                    emp_index += 1
                    if emp_index == len(self.employees):
                            break
                    emp_q = self.employees[emp_index].get_speed(Constants.TASK_TOSS)
                # if product work is finished, remove from list
                if self.toss_tasks[0][1] == 0:
                    self.toss_tasks.pop(0)

        # restock while the store is open or customers are in the store
        elif (t_step >= Constants.STORE_OPEN and t_step < Constants.STORE_CLOSE) or shopper_count > 0:
            self.refresh_tasks(Constants.TASK_RESTOCK, today, next_truck)
            if self.restock_tasks:
                emp_index = 0
                emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                while(self.restock_tasks and emp_index != len(available_emps)):
                    work_done = self.restock_tasks[0][0].restock(emp_q)
                    emp_q -= work_done
                    self.restock_tasks[0][1] -= work_done
                    # if emp has extra capacity, help with next product
                    if emp_q == 0:
                        emp_index += 1
                        if emp_index == len(self.employees):
                            break
                        emp_q = self.employees[emp_index].get_speed(Constants.TASK_RESTOCK)
                    # if product work is finished, remove from list
                    if self.restock_tasks[0][1] == 0:
                        self.restock_tasks.pop(0)

        else:
            print(f"Unaccounted for t_step {t_step}")
            exit(1)


    def print_active_employees(self):
        print("\t--- ACTIVE EMPLOYEES --- ")
        working = [emp for emp in self.employees["unavailable"] if emp.is_cashier()]
        working.sort(key=lambda x: x.action)
        [emp.print() for emp in working]

