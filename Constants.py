from datetime import datetime
from enum import IntEnum

# --------------------------------------------------------------------- SIMULATE_DAY AND STORE CONSTANTS 

CURRENT_DAY = 0
CURRENT_TSTEP = 0

START_CLOCK = datetime(2011, 12, 30, 10, 0)
DAY_START = 0  
STORE_OPEN = 2 * 60  # 120 -->  2 hrs, 10am public open, morning steps: 0 - 120
SHIFT_CHANGE = 7 * 60  # 420 -- 7 hrs, 3PM shift change
CLOSING_SOON = 11 * 60  # 660 --> 11 hr, 7PM closing warning
STORE_CLOSE = 12 * 60  # 720 -->  10 hrs, 8PM public close, day steps: 120 - 720
DAY_END = 14 * 60  # 840 -->  14 hrs, 10pm public close, evening steps: 720 - 840

TRUCK_DAYS = 2
PRODUCT_COUNT = 1000  # total # of products in db 3k
SHOPPER_ADD = 300

# runtime
day_steps = 14 * 60  # each day is 14 hours

def closing_soon(t_step):
    if t_step >= CLOSING_SOON  and t_step < STORE_CLOSE:
        return True
    else:
        return False 

def store_open(t_step):
    if t_step >= STORE_OPEN and t_step < STORE_CLOSE:
        return True


# --------------------------------------------------------------------- LANES
CHECKOUT_MIN = 7
CHECKOUT_MAX = 12

MANAGE_FREQUENCY = 1  # manage() evaluates average lane qtime and qlen every MANAGE_FREQUENCY minutes
MANAGE_DELAY = None  # after manage() is executed, manage is not called again for at least MANAGE_DELAY minutes

QTIME_RANGE = 7  # average queue time is calculated over the last QTIME_RANGE minutes
QTIME_IDEAL = 8  # the ideal amount of time a consumer is willing to wait in line (close to max, but not quite), in minutes
QTIME_MIN = 4  # if the avg qtime is less than this value, need to close some lanes
QTIME_MAX = 12  # if the avg qtime is greater than this value, need to open more lanes

QLEN_MAX = 5  # if avg_qlen > QLEN_MAX --> open more lanes
QLEN_MIN = 2  # if avg_qlen < QLEN_MIN --> close some lanes
RESTOCK_THRESHOLD = 100  # if shelved_stock falls below this value, restock from back_stock


# --------------------------------------------------------------------- EMPLOYEE
TASK_UNLOAD = 0
TASK_RESTOCK = 1
TASK_TOSS = 2
TASK_CASHIER = 3

STOCK_MIN = 40  # max toss/restock per t_step
STOCK_MAX = 100
UNLOAD_MIN = 2  # in terms of lots
UNLOAD_MAX = 5

MAX_LANES = 30				    # max possible lanes
MIN_LANES = 2					# num of open lanes at start

SHOPPER_MIN = 10                # min number of items a shopper will attempt to purchase
SHOPPER_MAX = 60                # max number of items a shopper will attempt to purchase
NUM_EMPLOYEES = 147

WAGE_MIN = 8
WAGE_MAX = 18

CURRENT_SHIFT = None

# specific times an employee works
class Shift(IntEnum):
    MORNING = 0  # 8am - 3pm, 7 hours
    EVENING = 1  # 3pm - 10pm, 7 hours
    OFF = 2


def shift_change(t_step):
    if t_step == day_steps / 2:
        return True
    return False

# --------------------------------------------------------------------- performance monitoring

def log(message=None):
    curr = datetime.now()
    if message:
        message += ": "
        print(message, curr)
    return curr


def delta(message, prev):
    curr = datetime.now()
    diff = curr - prev
    message += " ∆: "
    print(message, diff)

