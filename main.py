from Store import Store
import sys


# POA:
# 1. Process input: # products, runtime, product preference distribution, numpy seed
# format as follows: ./storesimulator -p #products, -r runtime -d distribution -s seed
# 2. Setup interesting behavior
# 3. Simulate for time input --> output data into CSV files for easy processing
# 4. Visualize data w/graphs etc. for analysis


if __name__ == '__main__':
    # default
    num_products = 1000
    runtime = 3 * 365  # 3 years
    distribution = None
    seed = None

    # process paramaters
    argv = sys.argv
    index = 1
    while(index < len(argv)):
        if argv[index] == '-p':
            pass
        elif argv[index] == '-r':
            pass
        elif argv[index] == '-d':
            pass
        elif argv[index] == '-s':
            pass
        else:
            sys.exit("Invalid input. Expected ./storesimulator [-p <number_of_products> -r <runtime_in_months> -d <distribution> -s <seed>] ")


    store = Store()
    store.simulate_year()
    store.visualize()
