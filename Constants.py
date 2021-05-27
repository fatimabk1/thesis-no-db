from datetime import datetime, timedelta
from enum import IntEnum
import sys
import os

# --------------------------------------------------------------------- PRINTING STATISTICS 
# def print_stock(grp, smart_products):
#     grp = smart_products[grp]
#     print(
#         f"GRP_{grp}:"\
#         f"\tPENDING={grp.pending['quantity']}"\
#         f"\tBACK={grp.any_back['quantity']}"\
#         f"\tSHELF={grp.any_shelf['quantity']}"\
#         f"\tSOLD={grp.sold['today']}"\
#         f"\tTOSS= {grp.toss_count}"\
#         f"\tMISS = {grp.miss_count}")
CURRENT_DAY = 0
CURRENT_TSTEP = 0

START_CLOCK = datetime(2011, 12, 30, 10, 0)
DAY_START = 0  
STORE_OPEN = 2 * 60  # 120 --  2 hrs, 10am public open, morning steps: 0 - 120
STORE_CLOSE = 12 * 60  # 720 --  10 hrs, 8PM public close, day steps: 120 - 720
DAY_END = 14 * 60  # 840 --  2 hrs, 10pm public close, evening steps: 720 - 840


err_file = open('issues.txt', 'w')

# --------------------------------------------------------------------- GENERAL
TRUCK_DAYS = 2
EOD_FLAG = False
PRODUCT_COUNT = 1000  # total # of products in db 3k
CATEGORY_COUNT = 10  # total # of categories in db 100
# PRODUCTS_PER_CATEGORY = int(PRODUCT_COUNT / CATEGORY_COUNT) 3000
PRODUCTS_PER_CATEGORY = 100
SHOPPER_ADD = 300

# store time flags
CURRENT_SHIFT = None

# runtime
HOURS_PER_DAY = 14
day_steps = HOURS_PER_DAY * 60
HOURS_RUN = 1					# hours to run simulation
RUN_TIME = HOURS_RUN * 60		# HOURS_RUN converted to minutes


# values correspond to the t_step at which the store opens, closes, etc.
class StoreStatus(IntEnum):
    OPEN = 2 * 60  # 8-10AM --> pre-open
    SHIFT_CHANGE = 7 * 60  # 3PM --> shift change
    CLOSING_SOON = 11 * 60  # 7PM --> 1 hr closing warning
    CLOSED = 12 * 60  # 8-10PM --> post-close

def closing_soon(t_step):
    if t_step >= StoreStatus.CLOSING_SOON  and t_step < StoreStatus.CLOSED:
        return True
    else:
        return False 

def store_open(t_step):
    if t_step >= StoreStatus.OPEN and t_step < StoreStatus.CLOSED:
        return True


# pre-open, employees work from 8am - 10am, 2hrs
# store hours: 10am - 8pm, 10 hrs
# post-close, employees work from 8pm - 10pm, 2 hrs
# shift 1: 8am - 3pm
# shift 2: 3pm - 10pm
# shift change: 3pm, 7hrs in


class Day(IntEnum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


days = [Day.SUNDAY, Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY,
        Day.THURSDAY, Day.FRIDAY, Day.SATURDAY]
NUM_DAYS = 7	 # 7 days in a week
DAY_START = 10	 # store opens at 10:00 am


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

# initally min=10, max=50
SHOPPER_MIN = 10                # min number of items a shopper will attempt to purchase
SHOPPER_MAX = 60                # max number of items a shopper will attempt to purchase
NUM_EMPLOYEES = 147

WAGE_MIN = 8
WAGE_MAX = 18


# specific times an employee works
class Shift(IntEnum):
    MORNING = 0  # 8am - 3pm, 7 hours
    EVENING = 1  # 3pm - 10pm, 7 hours
    OFF = 2


def shift_change(t_step):
    if t_step == day_steps / 2:
    # shift change halfway through day, at 3:00pm
    # if clock.hour == 15 and clock.minute == 00:
        return True
    return False


# --------------------------------------------------------------------- performance monitoring
LOGGING = True
curr = None


tracking = []


class Performance:
    def __init__(self, msg, val, step=None):
        self.step = step
        self.message = msg
        self.value = val

    def print(self):
        step = str(self.step)
        while len(step) < 3:
            step = '0' + step
        print(step + " -- " + self.message,
              self.value,
              file=sys.stderr)


def log(message=None):
    if LOGGING:
        curr = datetime.now()
        if message:
            message += ": "
            print(message, curr)
        return curr


def delta(message, prev, step=None):
    if LOGGING:
        curr = datetime.now()
        diff = curr - prev
        message += " ∆: "
        print(message, diff)
        if step is None:
            if len(tracking) == 0:
                step == 0
            else:
                step = tracking[len(tracking) - 1].step
        p = Performance(message, diff, step)
        tracking.append(p)
        assert(len(tracking) > 0)
        if diff > timedelta(seconds=10):
            exit(1)
        # if diff > timedelta(seconds=5):
            # print("day_simulator() runtime is longer than 5 seconds")
            # print("calculating stats:\n\n")
            # print_tracking()
            # exit(1)


# def avg_datetime(lst):
#     total = timedelta(0)
#     for td in lst:
#         total += td
#     sum_of_time = sum(map(datetime.datetime.timestamp, lst)

def calculate_stats():
    stats = {}
    for perf in tracking:
        if perf.message not in stats:
            stats[perf.message] = {'lst': [], 'min': -1, 'max': -1, 'avg': -1}
        stats[perf.message]['lst'].append(perf.value)

    for msg in stats:
        stats[msg]['lst'].sort(reverse=True)
        stats[msg]['min'] = stats[msg]['lst'][len(stats[msg]['lst']) - 1]
        stats[msg]['max'] = stats[msg]['lst'][0]
        stats[msg]['sum'] = sum(stats[msg]['lst'], timedelta(0))
        stats[msg]['count'] = len(stats[msg]['lst'])
        total = timedelta(0)
        for td in stats[msg]['lst']:
            total += td
        stats[msg]['avg'] = total / len(stats[msg]['lst'])
    return stats


def print_tracking():
    i = 0
    while os.path.exists("stats/{}.txt".format(i)):
        i += 1
    f = open("stats/{}.txt".format(i), 'w')

    stats = calculate_stats()
    print("\n\n\t ~~~ STATISTICS ~~~\n")
    for msg in sorted(stats):
        print(msg, file=f)
        print("max = ", stats[msg]['max'], file=f)
        print("min = ", stats[msg]['min'], file=f)
        print("avg = ", stats[msg]['avg'], file=f)
        print("sum = ", stats[msg]['sum'], file=f)
        print("count = ", stats[msg]['count'], file=f)
        print("\n", file=f)
    f.close()
