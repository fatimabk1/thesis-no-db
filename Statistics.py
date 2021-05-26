from SmartProduct import SmartProduct
import csv
from enum import IntEnum
import Constants
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
        self.monthly_sold = []  # q sold per product --> {grp_id: {month: q, month: q}}

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
            self.daily_sold[data['grp_id']].append(data['data'])
            print(self.daily_sold[data['grp_id']])
            print("============= ============= ============= ============= =============")
            # print(json.dumps(self.daily_sold), indent=4)
        elif type == StatType.TOSS:
            self.daily_toss_count[data['grp_id']].append({data['date']: data['quantity']})
        elif type == StatType.REVENUE:
            self.daily_revenue[data['grp_id']].append({data['date']: data['quantity']})
        elif type == StatType.ORDER:
            self.inventory_order[data['grp_id']].append({data['date']: {'quantity': data['quantity'], 'cost': data['cost']}})
        else:
            print(f"Statistics.add_stat(): FATAL - invalid StatType {type}")
            exit(1)

    def __calculate_month_stats(self):
        # processing monthly_sold
        current_month = 0
        for grp in self.daily_sold:
            # for entry in self.daily_sold[grp]:
            #     print(entry)
            # exit()
            dates = [entry.keys() for entry in self.daily_sold[grp]]
            print(dates)
            exit()
            quantities = self.daily_sold[grp].values()
            for i in range(len(dates)):
                if dates[i].month == current_month:
                    self.monthly_sold[grp][current_month] += quantities[i]
                else:
                    current_month += 1
                    self.monthly_sold[grp][current_month] = quantities[i]
        for grp in self.monthly_sold:
            print(self.monthly_sold[grp])


    # TEST AND CONFIRM THIS WORKS BEFORE ADDING MORE
    def print_all_stats(self):
        self.__calculate_month_stats()

        with open('daily_sold.csv', 'w') as f:
            headers = ['product',]
            headers.append(self.daily_sold.keys())
            writer = csv.writer(f, delimiter=',')
            writer.writerow(headers)
            for grp in self.daily_sold:
                writer.writerow(self.daily_sold[grp].values())

        with open('monthly_sold.csv', 'w') as f:
            headers = ['product',]
            months = [m for m in self.daily_sold[0].keys()]
            headers.append(months)
            writer = csv.writer(f, delimiter=',')
            writer.writerow(headers)
            for grp in self.monthly_sold:
                writer.writerow(self.daily_sold[grp].values())

        # also print stats for profit over time
        # labor constant, inv order cost is variable, total revenue is variable
