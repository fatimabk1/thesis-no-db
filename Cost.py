
class Cost:
    def __init__(self, stamp, value, ctype):
        self.stamp = stamp
        self.value = value
        self.ctype = ctype
        # ctype refers to cost type: "labor", "stock", or "overhead"


    def print(self):
        return "<Cost(id='{}', timestamp='{}', value={}, cost type={})>"\
            .format(id(self), self.stamp, self.value, self.ctype)


class Qtime:

    def __init__(self, lane, stamp, time):
        self.lane = lane
        self.stamp = stamp
        self.time = time

    def print(self):
        print("<Qtime_{}: queue_num={}, stamp ={}, time={}>"
              .format(id(self), self.lane, self.stamp, self.time))
