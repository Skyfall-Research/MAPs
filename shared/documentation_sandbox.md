## Game Mechanics

The goal of the game is to maximize your amusement park's value within a set number of days. As the manager of the park, you perform one action at the start of each day. The park then opens, and guests interact with the park for a full day.

There are three difficulty modes in the game (*Easy*, *Medium*, and *Hard*):
- **Easy:** All attractions are available from the beginning. Short time horizon (50 days).
- **Medium:** Only yellow attractions are available from the beginning; other attractions must be researched. Medium time horizon (100 days).
- **Hard:** Coming soon.

There are seven primary components to the game. We provide a high-level overview here, followed by detailed descriptions of each:
- **The Park:** Defined by a square grid (defaults to 20x20) and contains all other components. The amusement park has an entrance and an exit connected by a path. Your park also has a *rating* that reflects guest satisfaction, park upkeep, and overall park quality.
- **Terrain:** There are three kinds of terrain -- Paths, Water, and Empty.
- **Rides:** Rides are one of two types of attractions you can place in your amusement park. They are the core of the park and draw guests in. There are three subtypes of rides: Carousels, Ferris Wheels, and Roller Coasters.
- **Shops:** Shops are the second type of attraction. They allow you to cater to your guests' needs. There are three subtypes of shops: Drink, Food, and Specialty. Drink shops quench guests’ thirst; Food shops satisfy their hunger; Specialty shops provide unique services.
- **Staff:** Staff can be hired to maintain your park. There are three subtypes of staff: Janitors, Mechanics, and Specialists. Janitors keep the park clean, Mechanics repair rides, and Specialists perform a variety of support tasks.
- **Subclasses & Research:** Each ride, shop, and staff subtype has four subclasses—yellow, blue, green, and red. In Easy mode these are unlocked from the start; in Medium and Hard modes, higher subclasses must be unlocked through research.
- **Guests:** The people your park is built for! Guests interact with your park, spending money to purchase ride tickets, food, drinks, and more.

---

### Terrain
- **Empty tiles:** Blank tiles on which something can be built.
- **Path tiles:** Used by guests to move around your park. All attractions must be placed on an empty tile adjacent to a path tile.
- **Water tiles:** Each water tile adjacent to a ride increases that ride's excitement by 1.

In Hard mode, terrain can be terraformed. Paths can be built ($1000) and removed ($2500). Water tiles can similarly be added ($5000) and removed ($10000).

---

### Rides
Rides are the core of your amusement park. They are the primary driver in determining how many guests visit your park, they improve guest happiness, and contribute to the overall value of the park. Rides have several key attributes:
- **Capacity:** How many guests can fit on the ride at one time. Capacity also affects how frequently the ride operates. The cumulative capacity of your park is also a key factor in how many guests visit the park.
- **Excitement:** How thrilling the ride is. Higher excitement scores increase guest happiness and park rating.
- **Intensity:** How intense the ride experience is. Keeping the average intensity balanced (around 5) ensures your park caters to a wide range of guests and improves your rating.
- **Ticket price:** The amount guests must pay to ride. If a guest cannot afford the ticket, they are rejected, which decreases their happiness.
- **Cost per operation:** The amount it costs each time the ride runs.

> **TIP:** Building multiple rides of the same kind (i.e., identical subtype and subclass) yields diminishing returns for your park rating. Diversifying your attractions will lead to a higher overall rating.

Rides only operate if guests have boarded. After the first guest boards, rides wait a few turns to allow more guests to join. This waiting time is longer for rides with higher capacity but decreases as more guests board. A full ride always operates immediately.

Rides may break down after operating. When broken, they are out of service and will turn away guests, negatively affecting their happiness and your park rating.  
> **TIP:** Hire mechanics to fix broken rides promptly.

There are three subtypes of rides:
- **Carousels:** Cheap to build and operate, and they rarely break down. However, they provide limited excitement and capacity.
- **Ferris Wheels:** Intermediate rides with the highest capacities among all subtypes.
- **Roller Coasters:** Expensive but high-value rides that offer the highest excitement and intensity scores, at the cost of frequent breakdowns.

For the exact parameters of each ride, see [All Rides](#all-rides).

---

### Shops
Shops are necessary to adequately cater to guest needs, and provide additional value to a park. Shops have several key attributes:
- **Order quantity:** The amount of inventory purchased at the start of each day. Unsold inventory is lost at the end of the day.
- **Item cost:** The cost of purchasing one unit of inventory.
- **Item price:** The price guests pay for one unit of inventory.

At the start of each day, shops are stocked according to their order quantity at the item cost. If there are insufficient funds to fully restock all shops, partial stocking will occur. If a shop runs out of inventory during the day, it will go out of service, turning away guests and lowering their happiness and your park rating.  
> **TIP:** Leave enough funds after your action so your shops can be adequately restocked.  
> **TIP:** Order quantity can be updated using the *modify* action.

There are three subtypes of shops:
- **Drink:** Sells beverages that quench guests’ thirst.
- **Food:** Sells food that satisfies guests’ hunger.
- **Specialty:** Provides unique services based on subclass:
  - Yellow (Souvenir Shops): Boosts guest happiness.
  - Blue (Info Booths): Informs guests about attractions and their prices.
  - Green (ATMs): Allows guests to withdraw additional funds.
  - Red (Billboards): Encourages guests to seek food and ATMs.

By default, guests do not actively seek out Specialty Shops; they visit them only if they pass by.  
> **TIP:** Place specialty shops in high-traffic areas to increase the likelihood of guest interaction.

For exact parameters of each shop, see [All Shops](#all-shops).

---

### Staff
Staff are necessary for the smooth operation of your park, ensuring attractions run properly and guests remain satisfied. Multiple staff can occupy and work on the same tile at any given time. All staff have a daily salary, and some incur additional operating costs when performing tasks.

There are three subtypes of staff:
- **Janitors:** Move through the park toward dirty areas. When on dirty tiles, they clean them. Each cleaning action incurs an operating cost.
- **Mechanics:** Move toward rides that are broken down. When they reach a tile with a broken ride, they repair it. The time and operating cost of repairs depend on the ride’s building cost and the mechanic(s) performing the repair.
- **Specialists:** Perform different roles based on subclass:
  - Yellow (Clowns): Increases the happiness of guests waiting in line.
  - Blue (Stockers): Restocks shops with low inventory.
  - Green (Park Criers): Informs guests about out-of-service or dirty attractions, as well as current line wait time for rides.
  - Red (Vendors): Provides food and drink to guests waiting in line.

For exact parameters of all staff members, see [All Employees](#all-employees).

---

### Subclasses & Research
Each ride, shop, and staff subtype has four subclasses, ordered by price: yellow (cheapest), blue, green, and red (most expensive). Generally, more expensive subclasses provide greater benefits. However, at times cheaper subclasses may better suit your needs.

In Easy mode, all attractions are available from the start and research is disabled. In Medium and Hard modes, you begin with only yellow subclasses and must perform research to unlock the rest. To do this, you must set your research speed (none/slow/medium/fast) and topics (ride/shop/staff subtypes). Research continues daily until you change your settings, run out of funds, or unlock all available subclasses for the chosen topics. If funds run out or all topics are complete, research speed automatically reverts to *none*. Progress is paused, not lost. Research performed provides a small amount of added value to the park in the form of intellectual property, but this value does not increase with research speed.

Research unlocks subclasses in the following order: blue → green → red. Once a subclass is unlocked, research continues to the next topic in your list.

> **TIP:** If for example, you wanted to unlock the red roller coaster as quickly as possible, set the research speed to *fast* and select only “roller coaster” as your research topic.

Research speed costs:
- **none:** $0/day — research halted.
- **slow:** $2000/day.
- **medium:** $8000/day.
- **fast:** $32000/day.

The default setting is a research speed of *none* and all attraction subtypes selected as topics.

---

### Guests
Guests are the heart of your park. The number of guests who visit depends on your park’s rating and capacity.

**Capacity** determines both how many guests can be in the park at once and how many potential guests consider visiting. Capacity is determined entirely by the cumulative capacity of your rides.  
> **TIP:** Since only rides increase capacity, a park with no rides will receive no visitors.

**Park Rating** determines the likelihood that potential guests decide to enter. New guests cannot enter if the park is already at capacity. Park rating increases with the total excitement of the rides and when guests leave the park happy. Park rating decreases when attractions are frequently out of service, the park is dirty, or the average ride intensity is too high or too low.  
> **TIP:** Park ratings are calculated at the start of each day. In some cases, it may take a full day for the action you have taken to effect the park. In these cases, the park rating will only be reflected the subsequent day (two days after the action).

Each guest brings a certain amount of money. When they run out of funds or energy, they leave. Each guest also has hunger, thirst, happiness, and energy levels. Hunger and thirst increase over time, while happiness slowly decreases. Hungry guests seek food shops, thirsty guests seek drink shops, and unhappy guests seek rides. If any of these needs become critical, the guest’s happiness drops and they may leave the park.
> **TIP:** A guest's hunger and thirst will continue to increase as they wait in lines. Proximity to food and drink options is especially important for high capacity rides that have longer lines.

Guests favor novelty, preferring kinds of attractions they haven’t visited before. They also favor nearby attractions but never visit the same attraction twice in a row. Visiting a ride they can’t afford or that’s out of service reduces their happiness.

Unhappy guests are more likely to litter, reducing cleanliness. Visiting dirty tiles or attractions decreases happiness further. If a ride is too dirty, guests may turn away.

In Hard mode, guests may have **preferences**, meaning they only enjoy certain attraction types. Visiting a ride that doesn’t match their preference reduces their happiness. Providing guests with information through an Info Booth (blue Specialty Shop) allows them to identify attractions that suit them.

> **TIP:** You can learn more about guests by surveying them using the *SurveyGuest* action. This reveals why guests left, their needs at departure, and more. You can survey up to 25 guests at a cost of $500 per guest.

### Park Value

The total value of the park is the sum of the total money, the money that would be made by selling all constructed attractions, and a flat amount per day of research (the value of the discovered intellectual property). Each day of slow, medium, and fast research adds $1500, $3000, and $6000 respectively to the park's value.

## All Rides

Note: Any existing ride can be sold for 66.0% of its building cost. A ride that breaks down incurs a cost equal to 4.5% of its building cost to repair.

### Carousels

**Yellow**
- Building Cost: 250
- Cost per Operation: 1
- Capacity: 6
- Max Ticket Price: 4
- Excitement: 1
- Intensity: 1
- Breakdown Rate: 0.001

**Blue**
- Building Cost: 1500
- Cost per Operation: 2
- Capacity: 14
- Max Ticket Price: 6
- Excitement: 4
- Intensity: 3
- Breakdown Rate: 0.002

**Green**
- Building Cost: 11500
- Cost per Operation: 30
- Capacity: 26
- Max Ticket Price: 14
- Excitement: 3
- Intensity: 4
- Breakdown Rate: 0.003

**Red**
- Building Cost: 24000
- Cost per Operation: 12
- Capacity: 24
- Max Ticket Price: 24
- Excitement: 8
- Intensity: 5
- Breakdown Rate: 0.005

### Ferris Wheels

**Yellow**
- Building Cost: 600
- Cost per Operation: 10
- Capacity: 10
- Max Ticket Price: 5
- Excitement: 2
- Intensity: 2
- Breakdown Rate: 0.006

**Blue**
- Building Cost: 7500
- Cost per Operation: 20
- Capacity: 20
- Max Ticket Price: 7
- Excitement: 5
- Intensity: 3
- Breakdown Rate: 0.009

**Green**
- Building Cost: 50000
- Cost per Operation: 55
- Capacity: 40
- Max Ticket Price: 15
- Excitement: 4
- Intensity: 6
- Breakdown Rate: 0.024

**Red**
- Building Cost: 75000
- Cost per Operation: 75
- Capacity: 30
- Max Ticket Price: 28
- Excitement: 9
- Intensity: 8
- Breakdown Rate: 0.032

### Roller Coasters

**Yellow**
- Building Cost: 1000
- Cost per Operation: 8
- Capacity: 4
- Max Ticket Price: 10
- Excitement: 3
- Intensity: 4
- Breakdown Rate: 0.01

**Blue**
- Building Cost: 18000
- Cost per Operation: 25
- Capacity: 12
- Max Ticket Price: 20
- Excitement: 7
- Intensity: 7
- Breakdown Rate: 0.02

**Green**
- Building Cost: 60000
- Cost per Operation: 45
- Capacity: 28
- Max Ticket Price: 34
- Excitement: 6
- Intensity: 9
- Breakdown Rate: 0.025

**Red**
- Building Cost: 100000
- Cost per Operation: 100
- Capacity: 22
- Max Ticket Price: 50
- Excitement: 10
- Intensity: 10
- Breakdown Rate: 0.04

## All Shops

Note: Any existing shop can be sold for 66.0% of its building cost.

### Drink Shops

**Yellow**
- Building Cost: 100
- Item Cost: 0
- Max Item Price: 3
- Thirst Reduction: 0.24

**Blue**
- Building Cost: 2250
- Item Cost: 1
- Max Item Price: 6
- Thirst Reduction: 0.6

**Green**
- Building Cost: 17500
- Item Cost: 3
- Max Item Price: 17
- Thirst Reduction: 0.96
- Happiness Boost: 0.4

*In addition to quenching thirst, green drink shops additionally provide a boost to guest happiness.*

**Red**
- Building Cost: 48000
- Item Cost: 5
- Max Item Price: 25
- Thirst Reduction: 0.72
- Energy Boost: 20
- Caffeinated Steps: 50

*Red drinks caffeinate guests, which boosts a guest's energy and allows them to move twice as fast*

### Food Shops

**Yellow**
- Building Cost: 200
- Item Cost: 1
- Max Item Price: 5
- Hunger Reduction: 0.2

**Blue**
- Building Cost: 3600
- Item Cost: 2
- Max Item Price: 9
- Hunger Reduction: 0.5

**Green**
- Building Cost: 28000
- Item Cost: 4
- Max Item Price: 18
- Hunger Reduction: 0.8
- Thirst Reduction: 0.4

*Green food shops both satiate hunger and quench thirst.*

**Red**
- Building Cost: 60000
- Item Cost: 8
- Max Item Price: 34
- Hunger Reduction: 1.0
- Happiness Boost: 0.6

*Red food shops sell luxury food. This greatly satiates hunger and increases happiness*

### Specialty Shops

**TIP:** Guests will not target specialty shops, and will only visit specialty shops if the walk adjacent to one.

**Yellow (Souvenir Shop)**
- Building Cost: 250
- Item Cost: 4
- Max Item Price: 15
- Happiness Boost: 0.5

*These provide a happiness boost to guests that buy them the first time, but this happiness boost diminishes with each subsequent souvenir purchased.*

**Blue (Information Booth)**
- Building Cost: 10000
- Item Cost: 2
- Max Item Price: 5

*These provide information to guests about the attractions in the park and ensures that guests only visit rides that fall within their budget and preferences.*

**Green (ATM)**
- Building Cost: 50000
- Item Cost: 3
- Max Item Price: 5
- Money Withdrawal: 64

*ATMs allow guests to withdraw more money. The amount of money withdrawn decreases exponentially with every subsequent withdrawal, to a minimum of 16*

**Red (Billboard)**
- Building Cost: 10000
- Item Cost: 0
- Max Item Price: 0
- Thirst Boost: 0.25
- Hunger Boost: 0.25

*Billboards make guests more hungry, thirsty, and happy. They will additionally reset the visit count of attractions (meaning that guests are more likely to revisit attractions), and, if the guest has less than $25, will direct the guest to an ATM.*


## All Employees

Employees perform up to 500 actions per day. For example, moving to an adjacent tile costs a move action.

### Janitors

Janitors clean a tile up to their cleaning threshold before moving to the next tile to clean. In addition to their salary, janitors incur $1 per cleaning action in cleaning supplies. 

**Yellow**
- Daily Salary: 25
- Clean Rate: 0.028
- Cleaning Threshold: 0.85

**Blue**
- Daily Salary: 100
- Clean Rate: 0.075
- Cleaning Threshold: 0.95

*Blue, green, and red janitors move at double speed.*

**Green**
- Daily Salary: 500
- Clean Rate: 0.2
- Cleaning Threshold: 1.0

**Red**
- Daily Salary: 2000
- Clean Rate: 0.35
- Cleaning Threshold: 1.2

*Red janitors perform preventative cleaning, allowing them to clean a tile to 1.2; normally tiles have a maximum cleanliness of 1.0*

### Mechanics

**Yellow**
- Daily Salary: 15
- Repair Rate: 2

**Blue**
- Daily Salary: 100
- Repair Rate: 8

*Blue, green, and red mechanics move at double speed.*

**Green**
- Daily Salary: 250
- Repair Rate: 20

**Red**
- Daily Salary: 1000
- Repair Rate: 50

*Red mechanics also perform preventative maintenance -- this allows them to partially repair a ride before it breaks down, further reducing the time required for repairs.*

### Specialists

**Yellow (Clown)**
- Daily Salary: 60
- Happiness Boost: 0.25

*Clowns move between different rides, increasing the happiness of guests waiting in line.*

**Blue (Stocker)**
- Daily Salary: 350
- Stocking Rate: 0.1
- Max Inventory: 100
- Idle Ticks: 30
- Restock Threshold: 0.25

*Stockers restock the inventory of shops when the proportion of the shop's remaining inventory drops below the Restock Threshold. When this happens a stocker will move to an entrance or exit, purchase 10.0% of the daily order quantity, and take it to the shop. Stockers can carry at most 100 units of inventory and will not order more than this quantity. Stockers will stop making new purchases in the last 30 actions of the day to prevent them from restocking a shop immediately before closing.*

**Green (Crier)**
- Daily Salary: 250

*Criers move between attractions, providing guests about information related to the cleanliness and operation (i.e., if an attraction is out of service) of attractions, as well as current line wait times. This prevents guests from visiting out of service attractions, and makes them more likely to visit cleaner attractions and those with shorter wait times.*

**Red (Vendor)**
- Daily Salary: 300
- Hunger Reduction: 0.3
- Thirst Reduction: 0.4

*Vendors move between rides, providing food and drink to guests waiting in line. Vendors do not incur additional costs or make additional profits from their activities.*

## Action Space 

Actions must be written as python function calls with keyword arguments.
These action functions must be in the following format: 

```python
action_name(param_1=<param1_value>, param_2=<param1_value>, ... )
```

The full list of available actions, including the action names, parameters, and a description of what they do is below:  
  
---  
  
**place**  
*Description*: Place an entity (ride or shop or staff) in the amusement park  
*Parameters*:  
  - x: The x position of the entity  
  - y: The y position of the entity  
  - type: The type of entity. Must be one of ride or shop or staff  
  - subtype: The subtype of the entity to be placed. For rides, must be one of carousel, ferris wheel, or roller coaster. For shops, must be one of drink, food, or specialty. For staff, must be one of janitor, mechanic, or specialist  
  - subclass: The specific instance of the entity to be placed. Must be one of yellow, blue, green, or red  
  - price: The price of the ticket or item. Only for rides and shops.  
  - order_quantity: The maximum order_quantity of inventory. Only for shops.  
  
---  
**move**  
*Description*: Move an entity (ride or shop or staff) in the amusement park  
*Parameters*:  
  - type: The type of entity. Must be one of ride or shop or staff  
  - subtype: The subtype of the entity to be moved. For rides, must be one of carousel, ferris wheel, or roller coaster. For shops, must be one of drink, food, or specialty. For staff, must be one of janitor, mechanic, or specialist  
  - subclass: The specific instance of the entity to be moved. Must be one of yellow, blue, green, or red  
  - x: The current x position of the entity  
  - y: The current y position of the entity  
  - new_x: The new x position  
  - new_y: The new y position  
  
---  
**remove**  
*Description*: Remove an entity (ride or shop or staff). If the entity is a ride or shop, it will be sold for a price.  
*Parameters*:  
  - type: The type of entity. Must be one of ride or shop or staff  
  - subtype: The subtype of the entity to be removed. For rides, must be one of carousel, ferris wheel, or roller coaster. For shops, must be one of drink, food, or specialty. For staff, must be one of janitor, mechanic, or specialist  
  - subclass: The specific instance of the entity to be removed. Must be one of yellow, blue, green, or red  
  - x: The x position of the entity  
  - y: The y position of the entity  
  
---  
**modify**  
*Description*: Change the price and (as applicable) order_quantity of inventory for an attraction  
*Parameters*:  
  - type: The type of attraction. Must be one of ride or shop  
  - x: The x position of the attraction  
  - y: The y position of the attraction  
  - price: The new price  
  - order_quantity: The new maximum order_quantity of inventory. Only for shops.  
  
---  
**set_research**  
*Description*: Set the research speed and topic(s) for the amusement park. Only available in medium or hard difficulty.  
*Parameters*:  
  - research_speed: The research speed. Must be one of none, slow, medium, or fast  
  - research_topics: The topics(s) of research. Must be a subset of ['carousel', 'ferris_wheel', 'roller_coaster', 'drink', 'food', 'specialty']  
  
---  
**survey_guests**  
*Description*: Retrieve a sample of information from guests  
*Parameters*:  
  - num_guests: The number of guests to survey  
  
---  
**add_path**  
*Description*: Add a path tile to the amusement park. Only available in hard difficulty.  
*Parameters*:  
  - x: The x position of the path tile  
  - y: The y position of the path tile  
  
---  
**remove_path**  
*Description*: Remove a path tile from the amusement park. Only available in hard difficulty.  
*Parameters*:  
  - x: The x position of the path tile  
  - y: The y position of the path tile  
  
---  
**add_water**  
*Description*: Add a water tile to the amusement park. Only available in hard difficulty.  
*Parameters*:  
  - x: The x position of the water tile  
  - y: The y position of the water tile  
  
---  
**remove_water**  
*Description*: Remove a water tile from the amusement park. Only available in hard difficulty.  
*Parameters*:  
  - x: The x position of the water tile  
  - y: The y position of the water tile  
  
---  
**wait**  
*Description*: runs the day without any new action  
*Parameters*:  
  No parameters  
  
---  

    
## Sandbox Mode

The game can be placed in sandbox mode to help with learning or exploring the environment. In sandbox mode, players have access to new actions that are useful for experimenting with the game. These actions are likewise written as python function calls (see [Action Space](#action-space)).

When in sandbox mode, the game permits the player to perform 100 normal actions and an unlimited number of sandbox actions.

### Sandbox Action Space

The full list of available sandbox actions, including the action names, parameters, and a description of what they do is below:  
  
---  
  
**undo_day**  
*Description*: Undo the last day, reverting to the previous state.  
*Parameters*:  
  No parameters  
  
---  
**max_money**  
*Description*: Set the park's money to the maximum value ($99,999,999).  
*Parameters*:  
  No parameters  
  
---  
**max_research**  
*Description*: Unlock all attractions and staff.  
*Parameters*:  
  No parameters  
  
---  
**reset**  
*Description*: Reset the park to initial state  
*Parameters*:  
  No parameters  
  
---  
**change_settings**  
*Description*: Change the park's difficulty and layout settings, and reset the park using the new settings.  
*Parameters*:  
  - difficulty: The difficulty level. Must be one of easy or medium  
  - layout: The park layout. Must be one of ['diagonal_squares', 'the_ladder', 'two_paths', 'the_line', 'the_fork'].  
  
---  
