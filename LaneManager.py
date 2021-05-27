import sys
import Constants


class LaneManager:
    def __init__(self, emp_man, lanes, shoppers):
        self.employee_manager = emp_man
        self.lanes = lanes
        self.shoppers = shoppers
        self.num_open = 0
        self.manage_delay = 0

    def __close(self, ln):
        # print("\t\t\tclosing lane")
        emp = ln.remove_employee()
        self.employee_manager.return_cashier(emp)
        assert(emp.is_cashier() is False), "LaneManager.__close(): return_cashier failed"
        ln.close()

    def __open(self, ln):
        # print("\t\t\topening lane")
        emp = self.employee_manager.get_cashier()
        ln.set_employee(emp)
        ln.open()

    def __shortest(self):
        min_index, min_count = 0, self.lanes[0].length
        for i in range(self.num_open):
            if self.lanes[i].length < min_count:
                min_index = i
                min_count = self.lanes[i].length
        return min_index

    def advance_lanes(self):
        for index, ln in enumerate(self.lanes):
            if ln.is_active():
                ln.checkout()
            elif index >= self.num_open and ln.is_open() is True:
                self.__close(ln)

    def queue_shopper(self, shopper):
        index = self.__shortest()
        self.lanes[index].enq(shopper)
        # print("\t\t\tqueueing shopper ", id(shopper), " to lane ", index)

    def shift_change(self):
        for ln in self.lanes:
            if ln.is_open() and ln.get_employee().on_shift() is False:
                old_emp = ln.remove_employee()
                self.employee_manager.return_cashier(old_emp)
                assert(old_emp.is_cashier() is False), "shift_change(): update failed"
                new_emp = self.employee_manager.get_cashier()
                ln.set_employee(new_emp)

    # average time to check out last person in each lane
    def __longest_qtime(self):
        # if self.num_open == 0:
        #     return 0
        minutes = 0
        for index, ln in enumerate(self.lanes):
            if index < self.num_open:
                minutes += ln.get_item_count() / ln.get_speed()
        return minutes / self.num_open

    def manage(self):
        if self.manage_delay is not None:
            self.manage_delay += 1
            if self.manage_delay == Constants.QTIME_RANGE:
                self.manage_delay = None
        else:
            num_shoppers = sum(ln.get_length() for ln in self.lanes)
            qlen = sum(ln.get_length() for ln in self.lanes) / self.num_open
            qtime = self.__longest_qtime()

            open_condition = (qtime > Constants.QTIME_MAX and num_shoppers > self.num_open
                              and self.num_open < Constants.MAX_LANES)
            close_condition = ((num_shoppers < round(self.num_open / 2)
                or qtime < Constants.QTIME_MIN) and self.num_open > Constants.MIN_LANES)

            if open_condition:
                self.num_open = self.__expand(qlen, qtime)
            elif close_condition:
                self.num_open = self.__collapse(qlen)

            Constants.MANAGE_DELAY = 0
        return self.num_open

    def __collapse(self, qlen):
        # print("COLLAPSING LANES")
        assert (self.num_open > Constants.MIN_LANES)
        # calculate number of lanes to remove
        if qlen == 0:   # remove 2/3 of lanes
            num_removed = 2 * round(self.num_open / 3)
        elif qlen == 1:  # remove 1/2 of lanes
            num_removed = round(self.num_open / 2)
        else:  # remove 1/5 of lanes
            num_removed = round(self.num_open / 5)
            # num_removed = round(self.num_open % qlen)

        num_remaining = self.num_open - num_removed

        # CHECK MINIMUM BOUNDS
        if num_remaining < Constants.MIN_LANES:
            self.num_open = Constants.MIN_LANES
        else:
            self.num_open = num_remaining
        return self.num_open

    def __expand(self, qlen, qtime):
        # print("EXPANDING LANES")
        assert (self.num_open != Constants.MAX_LANES)
        ideal_qlen = None
        num_new_lanes = None

        # calculate number of lanes to add
        if qlen == 0:
            return self.num_open
        elif qlen == 1:
            num_new_lanes = round(self.num_open / 3)
            ideal_qlen = 1
        else:
            wait_per_person = qtime / (qlen - 1)
            ideal_qlen = round(Constants.QTIME_IDEAL / wait_per_person)
            delta_qlen = qlen - ideal_qlen
            assert(delta_qlen != 0)
            excess_ppl = delta_qlen * self.num_open
            if ideal_qlen == 0 or ideal_qlen == 1 or qlen < 3:
                num_shoppers = sum(ln.get_length() for ln in self.lanes)
                num_new_lanes = num_shoppers - self.num_open
            else:
                num_new_lanes = round(excess_ppl / ideal_qlen)

        # check max bounds
        num_new_lanes = min(num_new_lanes, Constants.MAX_LANES - self.num_open)

        # open new lanes
        qcount_old = self.num_open
        for i in range(num_new_lanes):
            self.__open(self.lanes[self.num_open])
            self.num_open += 1
        assert(self.num_open <= Constants.MAX_LANES)

        # redistribute customers
        new_lane_index = qcount_old
        old_lane_index = 0
        for i in range(qcount_old):
            old_lane = self.lanes[i]
            if old_lane.length == 1:  # no need to redistribute
                continue

            if ideal_qlen:
                # redistribute to new lanes while they have space
                while old_lane.length > ideal_qlen and new_lane_index < self.num_open:
                    sid = old_lane.deq_right()
                    new_lane = self.lanes[new_lane_index]
                    new_lane.insert_left(sid)

                    if(new_lane.length >= ideal_qlen):
                        new_lane_index += 1

                # redistribute remaining customers to all lanes one-by-one
                while old_lane.length > ideal_qlen:
                    # print("\t[length={} > {}=ideal_qlen]"
                        # .format(old_lane.length, ideal_qlen))
                    if i == old_lane_index:
                        old_lane_index += 1
                        # print("\nold_lane_index = ", old_lane_index)
                        break
                    sid = old_lane.deq_right()
                    new_lane = self.lanes[old_lane_index]
                    self.__open(new_lane)
                    new_lane.enq(sid)
                    old_lane_index += 1
            else:
                sys.exit("FATAL: ideal_qlen is None")

        return self.num_open

    def open_starter_lanes(self):
        for i in range(Constants.MIN_LANES):
            self.__open(self.lanes[i])
            self.num_open += 1
    
    def close_all_lanes(self):
        for ln in self.lanes:
            if ln.is_open():
                self.__close(ln)
                self.num_open -= 1

    def print_active_lanes(self, file):
        print("\n\n--- ACTIVE LANES ---", file=file)
        [ln.print(index, file) for index, ln in enumerate(self.lanes) if ln.is_open()]
        print("\n\n", file=file)
