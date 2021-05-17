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

    def get_cashier(self):
        # available = [emp for emp in self.working_employees if emp.is_cashier() is False]
        emp = next((emp for emp in self.working_employees if not emp.is_cashier()))
        emp.set_cashier()
        return emp

    def return_cashier(self, emp):
        emp.remove_cashier()
        assert(emp.is_cashier() is False), "return_cashier(): update failed"

    def advance_employees(self, t_step, today, task, task_lookup):
        if t_step == Constants.StoreStatus.SHIFT_CHANGE:
            self.current_shift = Constants.Shift.EVENING
            self.working_employees = [emp for emp in self.employees if emp.on_shift(self.current_shift)]

        if bool(task_lookup):
            # print("\t> calling dispatch()")
            self.inventory_manager.dispatch(task, task_lookup, self.working_employees, today)

    def print_active_employees(self):
        print("\t--- ACTIVE EMPLOYEES --- ")
        working = [emp for emp in self.employees["unavailable"] if emp.is_cashier()]
        working.sort(key=lambda x: x.action)
        [emp.print() for emp in working]

