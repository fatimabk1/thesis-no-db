import csv
from enum import IntEnum
import Constants
from datetime import datetime


class StatType(IntEnum):
    SOLD = 0
    REVENUE = 1
    ORDER_QUANTITY = 2
    ORDER_COST = 3
    LABOR = 4
    PROFIT = 5
    TOSS = 6
    MISS = 7


class Statistics:
    def __init__(self):
        self.daily_sold = {}  # q sold per product per day --> {grp_id: [(date, quantity), (date, quantity), ...]}
        self.monthly_sold = {}  # q sold per product --> {grp_id: {month: q, month: q, ...}}

        self.daily_revenue = {} # daily income per product or just daily total income --> {grp_id: [(date, rev), (date, rev), ...]}
        self.monthly_revenue = {}  # monthly income per product or just monthly total income --> {grp_id: {month: rev, month: rev, ...}}

        self.daily_order_cost = {}  # inventory orders by date by product --> {grp_id: [(date, cost), (date, cost), ...]}
        self.monthly_order_cost = {} # inventory orders by month by product --> {grp_id: {month: cost, month: cost, ...}}

        self.daily_order_quantity = {}  # inventory orders by date by product --> {grp_id: [(date, quantity), (date, quantity), ...]}
        self.monthly_order_quantity = {} # inventory orders by month by product --> {grp_id: {month: quantity, month: quantity, ...}}

        self.monthly_labor = {}  #  -->  {(year, month): cost, (year, month): cost, ...}
        self.monthly_profit = {}  # sum of revenue for all grp - labor costs that month - total order costs [by month]
        # --> {grp_id: {month: profit, month: profit, month: profit, ...}}

        self.__setup()

    def __setup(self):
        for i in range(Constants.PRODUCT_COUNT):
            self.daily_sold[i] = []
            self.daily_revenue[i] = []
            self.daily_order_cost[i] = []
            self.daily_order_quantity[i] = []
            self.monthly_sold[i] = {}
            self.monthly_revenue[i] = {}
            self.monthly_order_cost[i] = {}
            self.monthly_order_quantity[i] = {}

    def add_stat(self, type: StatType, data: list):
        if type == StatType.SOLD:
            self.daily_sold[data[0]] += [(data[1], data[2])]  # list of (date, quantity) tuples
        elif type == StatType.ORDER_QUANTITY:
            self.daily_order_quantity[data[0]] += [(data[1], data[2])]  # list of (date, quantity) tuples
        elif type == StatType.REVENUE:
            self.daily_revenue[data[0]] += [(data[1], data[2])] # list of (date, rev) tuples
        elif type == StatType.ORDER_COST:
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
                    (self.daily_revenue, self.monthly_revenue),
                    (self.daily_order_cost, self.monthly_order_cost),
                    (self.daily_order_quantity, self.monthly_order_quantity)] 
        for tpl in stat_lst:
            for grp in tpl[0]:
                for entry in tpl[0][grp]:
                    yr_month = (entry[0].year, entry[0].month)
                    if yr_month in tpl[1][grp]:
                        tpl[1][grp][yr_month] += entry[1]
                    else:
                        tpl[1][grp][yr_month] = entry[1]

    def print_all_stats(self):
        self.__calculate_month_stats()

        # write all daily stats files
        self.write_daily_stats(StatType.SOLD, 'daily_sold')
        self.write_daily_stats(StatType.REVENUE, 'daily_revenue')
        self.write_daily_stats(StatType.ORDER_COST, 'daily_order_cost')
        self.write_daily_stats(StatType.ORDER_QUANTITY, 'daily_order_quantity')

        # write all monthly stats files
        self.write_monthly_stats(StatType.SOLD, 'monthly_sold')
        self.write_monthly_stats(StatType.REVENUE, 'monthly_revenue')
        self.write_monthly_stats(StatType.ORDER_COST, 'monthly_order_cost')
        self.write_monthly_stats(StatType.ORDER_QUANTITY, 'monthly_order_quantity')
        self.write_monthly_stats(StatType.PROFIT, 'monthly_profit')


    def write_daily_stats(self, typ: StatType, filename: str):
        value_format = None
        quantity_format = "{:.0f}"
        money_format = "{:.2f}"

        if typ == StatType.SOLD:
            data = self.daily_sold
            value_format = quantity_format
        elif typ == StatType.ORDER_QUANTITY:
            data = self.daily_order_quantity
            value_format = quantity_format
        elif typ == StatType.REVENUE:
            data = self.daily_revenue
            value_format = money_format
        elif typ == StatType.ORDER_COST:
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
        elif typ == StatType.REVENUE:
            data = self.monthly_revenue
            value_format = money_format
        elif typ == StatType.ORDER_QUANTITY:
            data = self.monthly_order_quantity
            value_format = money_format
        elif typ == StatType.ORDER_COST:
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
                # calculate monthly_profit
                row = [grp]
                row += [value_format.format(value) for value in data[grp].values()]
                writer.writerow(row)
        else:
            headers.pop(0)
            f = open(f'output/{filename}.csv', 'w')
            writer = csv.writer(f, delimiter=',')
            writer.writerow(['month', 'revenue', 'labor', 'inventory cost', 'profit'])
            dates = self.monthly_revenue[0].keys()
            for dt in dates:
                total_monthly_revenue = sum(self.monthly_revenue[grp][dt] for grp in self.monthly_revenue) 
                total_monthly_order_cost = sum(self.monthly_order_cost[grp][dt] for grp in self.monthly_order_cost)
                total_monthly_labor = self.monthly_labor[dt]
                self.monthly_profit[dt] = total_monthly_revenue - self.monthly_labor[dt] - total_monthly_order_cost
                writer.writerow([dt, total_monthly_revenue, total_monthly_labor, total_monthly_order_cost, self.monthly_profit[dt]]) 
            f.close()
