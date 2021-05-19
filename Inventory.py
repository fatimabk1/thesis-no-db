from enum import IntEnum
# from Constants import delta, log


class StockType(IntEnum):
    PENDING = 0
    BACK = 1
    SHELF = 2
    CART = 3


class Inventory:

    def __init__(self, grp_id, shelf, back, pending, available, sell_by):
        self.grp_id = grp_id
        self.shelved_stock = shelf
        self.back_stock = back
        self.pending_stock = pending
        self.available = available  # truck -> back storage
        self.sell_by = sell_by
        self.deleted = False

    def print(self):
        print("<inv_{}: grp={}, shelved={}, back={}, pending={}, available={}, sell_by={}, deleted={}>"
              .format(id(self), self.grp_id,
                      self.shelved_stock, self.back_stock, self.pending_stock,
                      self.available, self.sell_by, self.deleted))

    def is_deleted(self):
        return self.deleted

    def get_pending(self):
        return self.pending_stock
    
    def get_back(self):
        return self.back_stock

    def get_shelf(self):
        return self.shelved_stock
    
    def get_sell_by(self):
        return self.sell_by

    def has_arrived(self, today):
        if self.available <= today:
            return True
        else:
            return False

    def is_expired(self, today):
        if self.sell_by <= today:
            return True
        else:
            return False

    def decrement(self, type, n):
        if type == StockType.PENDING:
            self.pending_stock -= n
        elif type == StockType.BACK:
            self.back_stock -= n
        elif type == StockType.SHELF:
            self.shelved_stock -= n
        else:
            print("ERROR: invalid stock type: ", type)
            exit(1)

        if (self.shelved_stock == 0
                and self.back_stock == 0
                and self.pending_stock == 0):
            self.deleted = True

    def increment(self, type, n):
        if type == StockType.PENDING:
            self.pending_stock += n
        elif type == StockType.BACK:
            self.back_stock += n
        elif type == StockType.SHELF:
            self.shelved_stock += n
