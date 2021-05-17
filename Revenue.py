
class Revenue:
    def __init__(self, stamp, value):
        self.stamp = stamp
        self.value = value

    def print(self):
        print("<Revenue_{}: timestamp='{}', value={}>"
              .format(self.id, self.stamp, self.value))
