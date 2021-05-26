from SmartProduct import SmartProduct
import csv
from enum import IntEnum
import Constants
from datetime import datetime
import json


class StatType(IntEnum):
    SOLD = 0
    TOSS = 1
    MISS = 2
    REVENUE = 3
    ORDER = 4


class Statistics:
    def __init__(self):
        self.daily_sold = {}  # q sold per product per day --> {grp_id: {date: d, quantity: q}}
        self.monthly_sold = {}  # q sold per product --> {grp_id: {month: q, month: q}}

        self.daily_toss_count = {}  # q tossed per product per day
        self.monthly_toss_count = {} # q tossed per product per month

        self.daily_revenue = {} # daily income per product or just daily total income
        self.monthly_revenue = {}  # monthly income per product or just monthly total income

        self.inventory_order = {}  # inventory orders over time by product --> {grp_id: [(cost, quantity), (cost, quantity), ...]}
        self.__setup()

    def __setup(self):
        for i in range(Constants.PRODUCT_COUNT):
            self.daily_sold[i] = []
        # TODO: setup all dictionaries so only appending to lists in add_stat
        pass

    def add_stat(self, type, data):
        if type == StatType.SOLD:
            self.daily_sold[data[0]] += [(data[1], data[2])]  # list of (date, quantity) tuples
            # print(json.dumps(self.daily_sold), indent=4)
        elif type == StatType.TOSS:
            self.daily_toss_count[data['grp_id']] += [(data[0], data[1])]
        elif type == StatType.REVENUE:
            self.daily_revenue[data['grp_id']] += [(data[0], data[1])]
        elif type == StatType.ORDER:
            self.inventory_order[data['grp_id']] += [(data[0], data[1], data[2])]
        else:
            print(f"Statistics.add_stat(): FATAL - invalid StatType {type}")
            exit(1)

    def __calculate_month_stats(self):
        for grp in range(Constants.PRODUCT_COUNT):
            self.monthly_sold[grp] = {} # dictionary of (year, month) tuple --> quantity
        # processing monthly_sold
        for grp in self.daily_sold:
            for entry in self.daily_sold[grp]:
                yr_month = (entry[0].year, entry[0].month)
                if yr_month in self.monthly_sold[grp]:
                    self.monthly_sold[grp][yr_month] += entry[1]
                else:
                    self.monthly_sold[grp][yr_month] = entry[1]


    # TEST AND CONFIRM THIS WORKS BEFORE ADDING MORE
    def print_all_stats(self):
        self.__calculate_month_stats()
# datetime.datetime.strftime(mydate, '%Y, %m, %d, %H, %M, %S')
        with open('output/daily_sold.csv', 'w') as f:
            headers = ['product',]
            headers += [datetime.strftime(tpl[0], '%Y-%m-%d') for tpl in self.daily_sold[0]]
            writer = csv.writer(f, delimiter=',')
            writer.writerow(headers)
            print("\ndaily_sold [prod, date1, date2]")
            for grp in self.daily_sold:
                for grp in self.daily_sold:
                    row = [grp] + [tpl[1] for tpl in self.daily_sold[grp]]
                    print(row)
                    writer.writerow(row)

        with open('output/monthly_sold.csv', 'w') as f:
            headers = ['product',]
            months = [f"{tpl[0]}-{tpl[1]}" for tpl in self.monthly_sold[0].keys()]
            headers += months
            writer = csv.writer(f, delimiter=',')
            writer.writerow(headers)

            for grp in self.monthly_sold:
                row = [grp]
                row += self.monthly_sold[grp].values()
                writer.writerow(row)

        # also print stats for profit over time
        # labor constant, inv order cost is variable, total revenue is variable
