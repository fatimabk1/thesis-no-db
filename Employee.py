import random
from enum import IntEnum
from Constants import Shift
import Constants

# a specific job an employee is doing
class Action(IntEnum):
    CASHIER = 0
    OTHER = 1
    OFF = 2


class Employee:
    def __init__(self, group):
        self.shift = None
        self.group = group
        self.action = Action.OTHER
        self.lane = False
        self.checkout_speed = int(random.random() * (Constants.CHECKOUT_MAX - Constants.CHECKOUT_MIN + 1)) + Constants.CHECKOUT_MIN  # items per min
        self.stock_speed = int(random.random() * (Constants.STOCK_MAX + 1 - Constants.STOCK_MIN)) + Constants.STOCK_MIN  # items per min
        self.unload_speed = int(random.random() * (Constants.UNLOAD_MAX + 1 - Constants.UNLOAD_MIN)) + Constants.UNLOAD_MIN  # lots per min
        self.hourly_wage = int(random.random() * (Constants.WAGE_MAX + 1 - Constants.WAGE_MIN)) + Constants.WAGE_MIN

    def print(self):
        shift = None
        if self.shift == Shift.MORNING:
            shift = "MORNING"
        elif self.shift == Shift.EVENING:
            shift = "EVENING"
        else:
            shift = "OFF"

        print("<Employee_{}: shift={}, action={}, lane={}, checkout_speed={}"
              .format(id(self), shift, self.action,
                      self.lane, self.checkout_speed) +
              ", stock_speed={}, unload_speed={}, wage={:.2f}>"
              .format(self.stock_speed, self.unload_speed, self.hourly_wage))

    def get_speed(self, task):
        if task == Constants.TASK_CASHIER:
            return self.checkout_speed
        elif task == Constants.TASK_RESTOCK or task == Constants.TASK_TOSS:
            return self.stock_speed
        elif task == Constants.TASK_UNLOAD:
            return self.unload_speed
        else:
            print("ERROR: Employee.get_speed() given an invalid task")
            exit(1)

    def set_cashier(self):
        self.lane = True
        self.action = Action.CASHIER

    def remove_cashier(self):
        self.lane = False
        self.action = Action.OTHER
    
    def is_cashier(self):
        return self.lane

    def calculate_wages(self):
        hours = self.time_worked / 60
        minutes = self.time_worked % 60
        wage = round(self.hourly_wage * hours +
                     round(self.hourly_wage * (minutes / 60), 2), 2)
        return wage
    
    def set_shift(self, shift):
        self.shift = shift

    def on_shift(self, current_shift):
        return self.shift == current_shift

    def get_paycheck(self):
        # employees work 6 shifts a week
        # each shift is 7 hours
        return 6 * 7 * self.hourly_wage
