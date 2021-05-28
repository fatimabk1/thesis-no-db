import csv
from enum import IntEnum
import Constants
from datetime import datetime


class StatType(IntEnum):
    SOLD = 0
    TOSS = 1
    MISS = 2
    REVENUE = 3
    ORDER = 4
    LABOR = 5
    PROFIT = 6


class Statistics:
    def __init__(self):
        self.daily_sold = {}  # q sold per product per day --> {grp_id: [(date, quantity), (date, quantity), ...]}
        self.monthly_sold = {}  # q sold per product --> {grp_id: {month: q, month: q, ...}}

        self.daily_toss = {}  # q tossed per product per day --> {grp_id: [(date, quantity), (date, quantity), ...]}
        self.monthly_toss = {} # q tossed per product per month --> {grp_id: {month: q, month: q, ...}}

        self.daily_miss = {}  # q missed per product per day --> {grp_id: [(date, quantity), (date, quantity), ...]}
        self.monthly_miss = {}  # q missed per product per month --> {grp_id: {month: q, month: q, ...}}

        self.daily_revenue = {} # daily income per product or just daily total income --> {grp_id: [(date, rev), (date, rev), ...]}
        self.monthly_revenue = {}  # monthly income per product or just monthly total income --> {grp_id: {month: rev, month: rev, ...}}

        self.daily_order_cost = {}  # inventory orders by date by product --> {grp_id: [(date, cost), (date, cost), ...]}
        self.monthly_order_cost = {} # inventory orders by month by product --> {grp_id: {month: cost, month: cost, ...}}

        self.monthly_labor = {}  #  -->  {(year, month): cost, (year, month): cost, ...}
        self.monthly_profit = {}  # sum of revenue for all grp - labor costs that month - total order costs [by month]
        # --> {grp_id: {month: profit, month: profit, month: profit, ...}}

        self.__setup()

    def __setup(self):
        for i in range(Constants.PRODUCT_COUNT):
            self.daily_sold[i] = []
            self.daily_toss[i] = []
            self.daily_miss[i] = []
            self.daily_revenue[i] = []
            self.daily_order_cost[i] = []
            self.monthly_sold[i] = {}
            self.monthly_toss[i] = {}
            self.monthly_miss[i] = {}
            self.monthly_revenue[i] = {}
            self.monthly_order_cost[i] = {}

    def add_stat(self, type: StatType, data: list):
        if type == StatType.SOLD:
            self.daily_sold[data[0]] += [(data[1], data[2])]  # list of (date, quantity) tuples
        elif type == StatType.TOSS:
            self.daily_toss[data[0]] += [(data[1], data[2])]  # list of (date, quantity) tuples
        elif type == StatType.MISS:
            self.daily_miss[data[0]] += [(data[1], data[2])]  # list of (date, quantity) tuples
        elif type == StatType.REVENUE:
            self.daily_revenue[data[0]] += [(data[1], data[2])] # list of (date, rev) tuples
        elif type == StatType.ORDER:
            self.daily_order_cost[data[0]] += [(data[1], data[2])] # list of (date, cost) tuples
        elif type == StatType.LABOR:
            yr_month = (data[0].year, data[0].month)
            if data[1] in self.monthly_labor:
                self.monthly_labor[yr_month] += data[1]
            else:
                self.monthly_labor[yr_month] = data[1]
        else:
            print(f"Statistics.add_stat(): FATAL - invalid StatType {type}")
            exit(1)

    def __calculate_month_stats(self):
        for grp in range(Constants.PRODUCT_COUNT):
            self.monthly_sold[grp] = {} # dictionary of (year, month) tuple --> quantity
        stat_lst = [(self.daily_sold, self.monthly_sold),
                    (self.daily_toss, self.monthly_toss),
                    (self.daily_miss, self.monthly_miss),
                    (self.daily_revenue, self.monthly_revenue),
                    (self.daily_order_cost, self.monthly_order_cost)] 
        for tpl in stat_lst:
            for grp in tpl[0]:
                for entry in tpl[0][grp]:
                    yr_month = (entry[0].year, entry[0].month)
                    if yr_month in tpl[1][grp]:
                        tpl[1][grp][yr_month] += entry[1]
                    else:
                        tpl[1][grp][yr_month] = entry[1]
        
        # calculate monthly_profit
        dates = self.monthly_revenue[0].keys()
        for dt in dates:
            total_monthly_revenue = sum(self.monthly_revenue[grp][dt] for grp in self.monthly_revenue) 
            total_monthly_order_cost = sum(self.monthly_order_cost[grp][dt] for grp in self.monthly_order_cost) 
            self.monthly_profit[dt] = total_monthly_revenue - self.monthly_labor[dt] - total_monthly_order_cost

    def print_all_stats(self):
        self.__calculate_month_stats()

        # write all daily stats files
        self.write_daily_stats(StatType.SOLD, 'daily_sold')
        self.write_daily_stats(StatType.TOSS, 'daily_toss')
        self.write_daily_stats(StatType.MISS, 'daily_miss')
        self.write_daily_stats(StatType.REVENUE, 'daily_revenue')
        self.write_daily_stats(StatType.ORDER, 'daily_order_cost')

        # write all monthly stats files
        self.write_monthly_stats(StatType.SOLD, 'monthly_sold')
        self.write_monthly_stats(StatType.TOSS, 'monthly_toss')
        self.write_monthly_stats(StatType.MISS, 'monthly_miss')
        self.write_monthly_stats(StatType.REVENUE, 'monthly_revenue')
        self.write_monthly_stats(StatType.ORDER, 'monthly_order_cost')
        self.write_monthly_stats(StatType.PROFIT, 'monthly_profit')

    def write_daily_stats(self, typ: StatType, filename: str):
        value_format = None
        quantity_format = "{:.0f}"
        money_format = "{:.2f}"

        if typ == StatType.SOLD:
            data = self.daily_sold
            value_format = quantity_format
        elif typ == StatType.TOSS:
            data = self.daily_toss
            value_format = quantity_format
        elif typ == StatType.MISS:
            data = self.daily_miss
            value_format = quantity_format
        elif typ == StatType.REVENUE:
            data = self.daily_revenue
            value_format = money_format
        elif typ == StatType.ORDER:
            data = self.daily_order_cost
            value_format = money_format
        else:
            print(f"Statistics.write_daily_stats(): FATAL - invalid stat type {type}")
            exit(1)

        headers = ['product']
        headers += [datetime.strftime(tpl[0], '%Y-%m-%d') for tpl in self.daily_sold[0]]

        f = open(f'output/{filename}.csv', 'w')
        writer = csv.writer(f, delimiter=',')
        writer.writerow(headers)
        for grp in data:
            row = [grp] + [value_format.format(entry[1]) for entry in data[grp]]
            writer.writerow(row)
        f.close()

    def write_monthly_stats(self, typ: StatType, filename: str):
        data = None
        value_format = None
        quantity_format = "{:.0f}"
        money_format = "{:.2f}"

        if typ == StatType.SOLD:
            data = self.monthly_sold
            value_format = quantity_format
        elif typ == StatType.TOSS:
            data = self.monthly_toss
            value_format = quantity_format
        elif typ == StatType.MISS:
            data = self.monthly_miss
            value_format = quantity_format
        elif typ == StatType.REVENUE:
            data = self.monthly_revenue
            value_format = money_format
        elif typ == StatType.ORDER:
            data = self.monthly_order_cost
            value_format = money_format
        elif typ == StatType.PROFIT:
            data = self.monthly_profit
            value_format = money_format
        else:
            print(f"Statistics.write_daily_stats(): FATAL - invalid stat type {typ}")
            exit(1)

        headers = ['product']
        months = [f"{tpl[0]}-{tpl[1]}" for tpl in self.monthly_sold[0].keys()]
        headers += months

        if typ != StatType.PROFIT:
            f = open(f'output/{filename}.csv', 'w')
            writer = csv.writer(f, delimiter=',')
            writer.writerow(headers)
            for grp in data:  # data e.g., self.monthly_sold
                row = [grp]
                row += [value_format.format(value) for value in data[grp].values()]
                writer.writerow(row)
            f.close()
        else:
            headers.pop(0)
            f = open(f'output/{filename}.csv', 'w')
            writer = csv.writer(f, delimiter=',')
            writer.writerow(headers)
            writer.writerow([value_format.format(value) for value in data.values()])
            f.close()


