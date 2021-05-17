from Constants import CLOCK
from Inventory import Inventory, StockType
from datetime import date, timedelta


# test Inventory.py
def test_inventory(inv_lst):
    [inv.print() for inv in inv_lst]
    print("\n")
    [inv.increment(StockType.PENDING, 10) for inv in inv_lst]
    [inv.print() for inv in inv_lst]
    print("\n")
    [inv.decrement(StockType.SHELF, 5) for inv in inv_lst]
    [inv.print() for inv in inv_lst]


if __name__ == '__main__':
    inv_lst = []
    today = date(CLOCK.year, CLOCK.month, CLOCK.day)
    sell_by = today + timedelta(days=7)
    for i in range(50):
        inv = Inventory(i, i, i, i, today, sell_by)
        inv_lst.append(inv)
    
    

    # test InventoryManager.py
