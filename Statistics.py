import Constants
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.animation as anim
from datetime import datetime
import time
import random

# START HERE >>> Transitioning to Matplotlib
# 1. Make fake data array for each *axes* I want
# 2. Add figure, axes + data (x,y,z,categories,...) instantiation to __init__()
# 3. Create update function for figure according to https://stackoverflow.com/questions/10944621/dynamically-updating-plot-in-matplotlib
# 4. Test with fake data
# 5. Repeat for each graph
# 6. Weave functions throughout rest of the program for real data


class Visualization:
    def __init__(self):
        self.daily_money = {}
        self.setup()
    
    def setup(self):
        #Set up plot
        figure, ax = plt.subplots()
        lines, = ax.plot([],[], 'o')
        ax.set_xlabel('Time (Days)')
        ax.set_ylabel('Products Sold')
        ax.set_title('Products Sold Over Time')
        #Autoscale on unknown axis and known lims on the other
        # ax.set_autoscaley_on(True)
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 6000)
        ax.grid()
        self.daily_money["figure"] = figure
        self.daily_money["ax"] = ax
        self.daily_money["lines"] = lines
        self.daily_money["data_x"] = []
        self.daily_money["data_y"] = []

        # draw and show initial figure
        self.daily_money["figure"].canvas.draw()
        plt.show(block=False)  

    def update(self, x, y):
        #Update data (with the new _and_ the old points)
        self.daily_money["data_x"].append(x)
        self.daily_money["data_y"].append(y)
        self.daily_money["lines"].set_xdata(self.daily_money["data_x"])
        self.daily_money["lines"].set_ydata(self.daily_money["data_y"])
        #Need both of these in order to rescale
        self.daily_money["ax"].relim()
        self.daily_money["ax"].autoscale_view()
        #We need to draw *and* flush
        self.daily_money["figure"].canvas.draw()
        self.daily_money["figure"].canvas.flush_events()
        plt.show(block=False)
        plt.pause(1) 
        print("end pause")
    
    # def setup(self):
    #     figure, ax = plt.subplots()
    #     lines, = ax.plot([],[], 'o')
    #     ax.set_xlabel('Time (Days)')
    #     ax.set_ylabel('Products Sold')
    #     ax.set_title('Products Sold Over Time')
    #     ax.set_autoscaley_on(True)
    #     ax.grid()
    #     ax.set_xlim(0, 8)
    #     ax.set_ylim(0, 6000)
    #     ax.format_xdata = mdates.DateFormatter('%d')
    #     ax.xaxis.set_major_locator(mdates.DayLocator())
    #     self.daily_money["figure"] = figure
    #     self.daily_money["ax"] = ax
    #     self.daily_money["lines"] = lines
    #     self.daily_money["data_x"] = []
    #     self.daily_money["data_y"] = []
    #     plt.show()
    #     # plt.draw()

    # def update(self, x, y):
    #     self.daily_money['data_x'].append(x)
    #     self.daily_money['data_y'].append(y)
    #     self.daily_money['lines'].set_xdata(self.daily_money['data_x'])
    #     self.daily_money['lines'].set_ydata(self.daily_money['data_y'])
    #     # Need both of these in order to rescale
    #     self.daily_money['ax'].relim()
    #     self.daily_money['ax'].autoscale_view()
    #     #We need to draw *and* flush
    #     self.daily_money['figure'].canvas.draw()
    #     self.daily_money['figure'].canvas.flush_events()
    #     plt.draw()
    #     # plt.show()
    #     # plt.pause(0.01)

if __name__ == "__main__":
    vis = Visualization()
    time.sleep(0.5)
    for i in range(7):
        vis.update(i + 1, random.randint(0, 6000))
        time.sleep(0.5)
    print("ALL DONE")

# class Visualization:
#     def __init__(self):
#         # all dictionaries in the format: figure, ax, lines, data_x, data_y
#         self.daily_money = {}
#         self.aggregate_money = {}
#         self.daily_product = {}
#         self.aggregate_product = {}
#         self.daily_order = {}
#         self.aggregate_order = {}
#         self.customer = {}

#         self.min_x = 0
#         self.max_x = 300
#         self.figure = None
#         self.ax = None
#         self.lines = None
#         self.data_x = []
#         self.data_y = []
#         self.setup_plots()


#     def setup_plots(self):
#         # FIGURE 1 - DAILY REVENUE: DOLLARS X TIME / SCATTERPLOT
#         # TODO: axis labels, grid lines every month
#         figure, ax = plt.subplots()
#         lines, = ax.plot([],[], 'o')
#         ax.set_xlabel('Time (Days)')
#         ax.set_ylabel('Products Sold')
#         ax.set_title('Products Sold Over Time')
#         ax.set_autoscaley_on(True)
#         ax.grid()
#         ax.set_xlim(0, 8)
#         ax.format_xdata = mdates.DateFormatter('%d')
#         ax.xaxis.set_major_locator(mdates.DayLocator())
#         # plt.show()
#         # ax.xaxis.set_major_locator(mdates.)
#         # ax.format_ydata = lambda x: f'${x:.2f}'
#         # ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # major tick every 3 months
#         # ax.xaxis.set_minor_locator(mdates.MonthLocator())  # minor tick every month
#         # datemin = datetime(2019, 9, 15)
#         # datemax = datetime(2019, 9, 30)
#         # ax.set_xlim(datemin, datemax)
#         # ax.set_ylim(0, 100000)
#         # figure.autofmt_xdate()
    
#         self.daily_money["figure"] = figure
#         self.daily_money["ax"] = ax
#         self.daily_money["lines"] = lines
#         self.daily_money["data_x"] = []
#         self.daily_money["data_y"] = []

#     def update_money(self, x, y):
#         print(f"logging ({x}, {y})")
#         # x = x - Constatnts.
#         # x = mdates.date2num(x)
#         # print(f"date: {x}")
#         self.daily_money['data_x'].append(x)
#         self.daily_money['data_y'].append(y)
#         self.daily_money['lines'].set_xdata(self.daily_money['data_x'])
#         self.daily_money['lines'].set_ydata(self.daily_money['data_y'])
#         # Need both of these in order to rescale
#         self.daily_money['ax'].relim()
#         self.daily_money['ax'].autoscale_view()
#         #We need to draw *and* flush
#         self.daily_money['figure'].canvas.draw()
#         self.daily_money['figure'].canvas.flush_events()
#         plt.show()

#     def update(self, x, y):
#         pass


# class AnimatedPlot(self, x, y):
    

# if __name__ == '__main__':
#     data_x = np.arange(1,300)
#     data_y = np.arange(50, 1000, 3)

#     vis = Visualization()
#     ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)
#     plt.show()

#     points = len(data_y)
#     for i in range(points):
#         animate()
    



        # FIGURE 2 - AGGREGATE MONEY: Dollars x Time, Area Graph
            # PLOT 1 - MONTHLY REVENUE
            # PLOT 2 - MONTHLY PROFIT (REVENUE - CAPITAL - LABOR - FIXED)
            # PLOT 3 - MONTHLY CAPITAL
            # PLOT 4 - MONTHLY REVENUE / LABOR 

        # FIGURE 3 - INDIVIDUAL PRODUCT DATA: TIME VS (GRP, QUANTITY)
            # PLOT 1 - PRODUCT SOLD
            # PLOT 2 - PRODUCT MISSED
            # PLOT 3 - PRODUCT LOSS

        # FIGURE 4 - AGGREGATE PRODUCT DATA: TIME VS (GRP, QUANTITY)
            # PLOT 1 - MONTHLY PRODUCT SOLD
            # PLOT 2 - MONTHLY PRODUCT MISSED
            # PLOT 3 - MONTHLY PRODUCT LOSS

        # FIGURE 5 - ORDER DATA: TIME X (GRP, QUANTITY)

        # FIGURE 6 - MONTHLY ORDER DATA: TIME X (GRP, QUANTITY)

        # FIGURE 7 - CUSTOMER DATA: IN-STORE VS (QUEUE TIME, CHECKOUT, OVERALL)
