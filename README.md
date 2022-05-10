# Grocery Store Simulator
This is my senior thesis project for Yale’s B.S Computer Science, submitted in June of 2021. This project is a command line program that simulates running a grocery store for 365 days. Output includes a statistics file, as well as two additional files. One details the inner processes within a day (day.txt) and the other details processes that occur throughout the year (year.txt). Both day.txt and year.txt show runtimes for each day and the overall program.

## Key areas of learning:
- **Class design**. This is my first time designing a complicated program.
- **Python**. Significantly increased python competency, utilizing list comprehension and generators.
- **SQLAlchemy and Postgres**. Database is not included in final project due to (1) the huge impact on runtime and (2) because it was unecessary. I learned how to implement and use a database, as well as why a database did not make sense for this project. 
- **Runtime and efficiency**. A huge part of this project was eliminating uneccessary work and redundant work, finding alternatives for time-expensive work, and doing pre-work. Eliminating the database reduced runtime for the simulated year from more than 16 hours to less than 45 minutes in the final version.

My [class design diagram](https://drive.google.com/file/d/1YrIinfIRSj2gMMU-uGhS_9CUcBwa2YwI/view?usp=sharing) is best viewed in draw.io. It's no longer accurate since the database was eliminated and I did some restructuring, but it shows the class design and database integration from the first phase of the project.

## Run the Grocery Store Simulator
```
git clone https://github.com/fatimabk1/thesis.git
Python store.py
```

## File Overviews:

### Inventory.py:
- A sublot, with data including availability date, expiration date and quantities on the shelf, in back, or pending.
- Lots of products are divided into sublots, the smallest number of items grouped together within a lot shipment. For example, a sublot could be twenty cans of baked beans in a cardboard box. Stores can only purchase baked beans by lot, and a lot is made up of 100 sublots, for a total of 2000 cans per order.

## Product.py:
- All data about a product such as lot quantity, sublot quantity, order price, restock threshold, maximum amount that can be stored in back, expiration period, etc.

## SmartProduct.py:
- A list of all inventory for a Product.
- Orders inventory by calculating the number of lots to order based on available stock, ideal stock levels.
- Lots are divided into sublots, which is the same as an Inventory item.
- Ordered inventory is marked as pending with an availability date (the day the truck arrives carrying the goods).
- Creates a dictionary of all inventory expiring that day.
- Creates a dictionary of inventory that needs to be restocked at that time step (stock on shelves is below a certain value and there exists stock in the back).
- Creates a dictionary of inventory that is ready to be unloaded (pending inventory that is available).
- Has a select() function that shoppers call. Select() chooses the soonest expiring inventory of an opened sublot for the product the shopper wants to purchase.
- Has a do_work() function that employees call. Do_work() updates inventory items to reflect changes made by employees tossing, unloading and restocking.

## Shopper.py:
- Shoppers track their own data: queue time, cart size, id, browse time, status, total checkout cost, etc.
- Have a quota of items to purchase.
- Varied browse times before selecting each item.
- Randomly select an item.
- Released into the store at a random time within the simulation hour they are created.
- Can ‘hurry up’ - limiting themselves to finding three more items when the store is about to close.

## ShopperHandler.py:
- Handles shopper advancement based on shopper status.
- Inert shoppers: do nothing
- Shopping shoppers: reduce browse time by one minute or select an item if browse time is 0.
- Join the shortest queue if quota is 0.
- Queueing shoppers: update the tracked queue time 
- Done Shoppers: do nothing

## Lane.py:
- A queue of shoppers with an assigned employee for the cashiering task.
- Can update the assigned employee.
- Can checkout items within a minute according to employee checkout speed.
- Lanes carry out partial and continuous checkouts. Lanes can check out x items a minute can partly check out a customer or check out multiple customers.
- Can enqueue and dequeue shoppers.
	
## LaneManager.py:
- LaneManager is a list of all lanes, with a count of the number of (consecutive) open lanes.
- Shoppers are added to the shortest open lane.
- Shoppers are removed from the lane when done checking out.
- Lanes are expanded (closed lanes are opened) or collapsed (open lanes are closed) to maintain an acceptable queue time and lane length for customers. -Queuing customers are redistributed from closed lanes to the consecutive set of open lanes (starting from lane 0). Customers in the middle of checking out in a closed lane will finish checking out, but that lane will not accept new customers.
- Executes shift changes, replacing now off-duty cashiers with an on-duty employee.

## Employee.py:
- Have a checkout, unload and restock speed.
- Have a shift and task.
- Receive weekly paychecks.

## EmployeeManager.py:
- Creates all employees.
- Updates each employee’s shift.
- For a given time step, employees complete as many tasks as they can according to their speed. Employees can partially complete a task.
- Tasks (expired inventory to be tossed, inventory to be unloaded from the truck, inventory to be restocked) are refreshed based on which tasks are -relevant at the time of day.

## DaySimulator.py: 
- Creates new shoppers at the top of the hour, released into the store at a random minute.
- Opens the minimum number of lanes at the start of the day.
- Triggers lane shift change at certain times of day.
- Advances in one minute time step is one minute 
- Advances shoppers each time step 
- Advances lanes each time step and manages the number of open lanes for optimum queue times and lengths.
- Updates its clock 
- Regularly adds customers during open hours.
- As the store approaches closing time, shoppers are encouraged to ‘hurry up’ - reducing the number of items they attempt to purchase.
- After the store is closed (no longer accepting new customers), current customers finish shopping and checking out.

## Store.py: 
- Initializes the store with employees, shoppers, and products. 
- Starts the loop to simulate the full year. 
- Handles processes that are out of scope of DaySimulator.py such as paying employees, ordering new inventory as needed, updating the employee schedule, and updating the Statistics object.

## Statistics.py:
- Collects data on quantities sold daily and monthly, daily and monthly revenue, monthly labor costs, monthly revenue.
- Writes data to an output file.

