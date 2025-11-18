## Game Mechanics

The goal of the game is to maximize your amusement park's value within a set number of days. As the manager of the park, you perform one action at the start of each day. The park then opens, and guests interact with the park for a full day.

There are three difficulty modes in the game (*Easy*, *Medium*, and *Hard*):
- **Easy:** All attractions are available from the beginning. Short time horizon (50 days).
- **Medium:** Only yellow attractions are available from the beginning; other attractions must be researched. Medium time horizon (100 days).
- **Hard:** Coming soon.

There are seven primary components to the game. We provide a high-level overview here, followed by detailed descriptions of each:
- **The Park:** Defined by a square grid (defaults to {{park_size}}x{{park_size}}) and contains all other components. The amusement park has an entrance and an exit connected by a path. Your park also has a *rating* that reflects guest satisfaction, park upkeep, and overall park quality.
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

In Hard mode, terrain can be terraformed. Paths can be built (${{path_addition_cost}}) and removed (${{path_removal_cost}}). Water tiles can similarly be added (${{water_addition_cost}}) and removed (${{water_removal_cost}}).

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
- **none:** ${{research.speed_cost.none}}/day — research halted.
- **slow:** ${{research.speed_cost.slow}}/day.
- **medium:** ${{research.speed_cost.medium}}/day.
- **fast:** ${{research.speed_cost.fast}}/day.

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

> **TIP:** You can learn more about guests by surveying them using the *SurveyGuest* action. This reveals why guests left, their needs at departure, and more. You can survey up to {{max_guests_to_survey}} guests at a cost of ${{per_guest_survey_cost}} per guest.

### Park Value

The total value of the park is the sum of the total money, the money that would be made by selling all constructed attractions, and a flat amount per day of research (the value of the discovered intellectual property). Each day of slow, medium, and fast research adds $1500, $3000, and $6000 respectively to the park's value.

## All Rides

Note: Any existing ride can be sold for {{sell_percentage}}% of its building cost. A ride that breaks down incurs a cost equal to {{ride_repair_cost_percentage}}% of its building cost to repair.

### Carousels

**Yellow**
- Building Cost: {{rides.carousel.yellow.building_cost}}
- Cost per Operation: {{rides.carousel.yellow.cost_per_operation}}
- Capacity: {{rides.carousel.yellow.capacity}}
- Max Ticket Price: {{rides.carousel.yellow.max_ticket_price}}
- Excitement: {{rides.carousel.yellow.excitement}}
- Intensity: {{rides.carousel.yellow.intensity}}
- Breakdown Rate: {{rides.carousel.yellow.breakdown_rate}}

**Blue**
- Building Cost: {{rides.carousel.blue.building_cost}}
- Cost per Operation: {{rides.carousel.blue.cost_per_operation}}
- Capacity: {{rides.carousel.blue.capacity}}
- Max Ticket Price: {{rides.carousel.blue.max_ticket_price}}
- Excitement: {{rides.carousel.blue.excitement}}
- Intensity: {{rides.carousel.blue.intensity}}
- Breakdown Rate: {{rides.carousel.blue.breakdown_rate}}

**Green**
- Building Cost: {{rides.carousel.green.building_cost}}
- Cost per Operation: {{rides.carousel.green.cost_per_operation}}
- Capacity: {{rides.carousel.green.capacity}}
- Max Ticket Price: {{rides.carousel.green.max_ticket_price}}
- Excitement: {{rides.carousel.green.excitement}}
- Intensity: {{rides.carousel.green.intensity}}
- Breakdown Rate: {{rides.carousel.green.breakdown_rate}}

**Red**
- Building Cost: {{rides.carousel.red.building_cost}}
- Cost per Operation: {{rides.carousel.red.cost_per_operation}}
- Capacity: {{rides.carousel.red.capacity}}
- Max Ticket Price: {{rides.carousel.red.max_ticket_price}}
- Excitement: {{rides.carousel.red.excitement}}
- Intensity: {{rides.carousel.red.intensity}}
- Breakdown Rate: {{rides.carousel.red.breakdown_rate}}

### Ferris Wheels

**Yellow**
- Building Cost: {{rides.ferris_wheel.yellow.building_cost}}
- Cost per Operation: {{rides.ferris_wheel.yellow.cost_per_operation}}
- Capacity: {{rides.ferris_wheel.yellow.capacity}}
- Max Ticket Price: {{rides.ferris_wheel.yellow.max_ticket_price}}
- Excitement: {{rides.ferris_wheel.yellow.excitement}}
- Intensity: {{rides.ferris_wheel.yellow.intensity}}
- Breakdown Rate: {{rides.ferris_wheel.yellow.breakdown_rate}}

**Blue**
- Building Cost: {{rides.ferris_wheel.blue.building_cost}}
- Cost per Operation: {{rides.ferris_wheel.blue.cost_per_operation}}
- Capacity: {{rides.ferris_wheel.blue.capacity}}
- Max Ticket Price: {{rides.ferris_wheel.blue.max_ticket_price}}
- Excitement: {{rides.ferris_wheel.blue.excitement}}
- Intensity: {{rides.ferris_wheel.blue.intensity}}
- Breakdown Rate: {{rides.ferris_wheel.blue.breakdown_rate}}

**Green**
- Building Cost: {{rides.ferris_wheel.green.building_cost}}
- Cost per Operation: {{rides.ferris_wheel.green.cost_per_operation}}
- Capacity: {{rides.ferris_wheel.green.capacity}}
- Max Ticket Price: {{rides.ferris_wheel.green.max_ticket_price}}
- Excitement: {{rides.ferris_wheel.green.excitement}}
- Intensity: {{rides.ferris_wheel.green.intensity}}
- Breakdown Rate: {{rides.ferris_wheel.green.breakdown_rate}}

**Red**
- Building Cost: {{rides.ferris_wheel.red.building_cost}}
- Cost per Operation: {{rides.ferris_wheel.red.cost_per_operation}}
- Capacity: {{rides.ferris_wheel.red.capacity}}
- Max Ticket Price: {{rides.ferris_wheel.red.max_ticket_price}}
- Excitement: {{rides.ferris_wheel.red.excitement}}
- Intensity: {{rides.ferris_wheel.red.intensity}}
- Breakdown Rate: {{rides.ferris_wheel.red.breakdown_rate}}

### Roller Coasters

**Yellow**
- Building Cost: {{rides.roller_coaster.yellow.building_cost}}
- Cost per Operation: {{rides.roller_coaster.yellow.cost_per_operation}}
- Capacity: {{rides.roller_coaster.yellow.capacity}}
- Max Ticket Price: {{rides.roller_coaster.yellow.max_ticket_price}}
- Excitement: {{rides.roller_coaster.yellow.excitement}}
- Intensity: {{rides.roller_coaster.yellow.intensity}}
- Breakdown Rate: {{rides.roller_coaster.yellow.breakdown_rate}}

**Blue**
- Building Cost: {{rides.roller_coaster.blue.building_cost}}
- Cost per Operation: {{rides.roller_coaster.blue.cost_per_operation}}
- Capacity: {{rides.roller_coaster.blue.capacity}}
- Max Ticket Price: {{rides.roller_coaster.blue.max_ticket_price}}
- Excitement: {{rides.roller_coaster.blue.excitement}}
- Intensity: {{rides.roller_coaster.blue.intensity}}
- Breakdown Rate: {{rides.roller_coaster.blue.breakdown_rate}}

**Green**
- Building Cost: {{rides.roller_coaster.green.building_cost}}
- Cost per Operation: {{rides.roller_coaster.green.cost_per_operation}}
- Capacity: {{rides.roller_coaster.green.capacity}}
- Max Ticket Price: {{rides.roller_coaster.green.max_ticket_price}}
- Excitement: {{rides.roller_coaster.green.excitement}}
- Intensity: {{rides.roller_coaster.green.intensity}}
- Breakdown Rate: {{rides.roller_coaster.green.breakdown_rate}}

**Red**
- Building Cost: {{rides.roller_coaster.red.building_cost}}
- Cost per Operation: {{rides.roller_coaster.red.cost_per_operation}}
- Capacity: {{rides.roller_coaster.red.capacity}}
- Max Ticket Price: {{rides.roller_coaster.red.max_ticket_price}}
- Excitement: {{rides.roller_coaster.red.excitement}}
- Intensity: {{rides.roller_coaster.red.intensity}}
- Breakdown Rate: {{rides.roller_coaster.red.breakdown_rate}}

## All Shops

Note: Any existing shop can be sold for {{sell_percentage}}% of its building cost.

### Drink Shops

**Yellow**
- Building Cost: {{shops.drink.yellow.building_cost}}
- Item Cost: {{shops.drink.yellow.item_cost}}
- Max Item Price: {{shops.drink.yellow.max_item_price}}
- Thirst Reduction: {{shops.drink.yellow.thirst_reduction}}

**Blue**
- Building Cost: {{shops.drink.blue.building_cost}}
- Item Cost: {{shops.drink.blue.item_cost}}
- Max Item Price: {{shops.drink.blue.max_item_price}}
- Thirst Reduction: {{shops.drink.blue.thirst_reduction}}

**Green**
- Building Cost: {{shops.drink.green.building_cost}}
- Item Cost: {{shops.drink.green.item_cost}}
- Max Item Price: {{shops.drink.green.max_item_price}}
- Thirst Reduction: {{shops.drink.green.thirst_reduction}}
- Happiness Boost: {{shops.drink.green.happiness_boost}}

*In addition to quenching thirst, green drink shops additionally provide a boost to guest happiness.*

**Red**
- Building Cost: {{shops.drink.red.building_cost}}
- Item Cost: {{shops.drink.red.item_cost}}
- Max Item Price: {{shops.drink.red.max_item_price}}
- Thirst Reduction: {{shops.drink.red.thirst_reduction}}
- Energy Boost: {{shops.drink.red.energy_boost}}
- Caffeinated Steps: {{shops.drink.red.caffeinated_steps}}

*Red drinks caffeinate guests, which boosts a guest's energy and allows them to move twice as fast*

### Food Shops

**Yellow**
- Building Cost: {{shops.food.yellow.building_cost}}
- Item Cost: {{shops.food.yellow.item_cost}}
- Max Item Price: {{shops.food.yellow.max_item_price}}
- Hunger Reduction: {{shops.food.yellow.hunger_reduction}}

**Blue**
- Building Cost: {{shops.food.blue.building_cost}}
- Item Cost: {{shops.food.blue.item_cost}}
- Max Item Price: {{shops.food.blue.max_item_price}}
- Hunger Reduction: {{shops.food.blue.hunger_reduction}}

**Green**
- Building Cost: {{shops.food.green.building_cost}}
- Item Cost: {{shops.food.green.item_cost}}
- Max Item Price: {{shops.food.green.max_item_price}}
- Hunger Reduction: {{shops.food.green.hunger_reduction}}
- Thirst Reduction: {{shops.food.green.thirst_reduction}}

*Green food shops both satiate hunger and quench thirst.*

**Red**
- Building Cost: {{shops.food.red.building_cost}}
- Item Cost: {{shops.food.red.item_cost}}
- Max Item Price: {{shops.food.red.max_item_price}}
- Hunger Reduction: {{shops.food.red.hunger_reduction}}
- Happiness Boost: {{shops.food.red.happiness_boost}}

*Red food shops sell luxury food. This greatly satiates hunger and increases happiness*

### Specialty Shops

**TIP:** Guests will not target specialty shops, and will only visit specialty shops if the walk adjacent to one.

**Yellow (Souvenir Shop)**
- Building Cost: {{shops.specialty.yellow.building_cost}}
- Item Cost: {{shops.specialty.yellow.item_cost}}
- Max Item Price: {{shops.specialty.yellow.max_item_price}}
- Happiness Boost: {{shops.specialty.yellow.happiness_boost}}

*These provide a happiness boost to guests that buy them the first time, but this happiness boost diminishes with each subsequent souvenir purchased.*

**Blue (Information Booth)**
- Building Cost: {{shops.specialty.blue.building_cost}}
- Item Cost: {{shops.specialty.blue.item_cost}}
- Max Item Price: {{shops.specialty.blue.max_item_price}}

*These provide information to guests about the attractions in the park and ensures that guests only visit rides that fall within their budget and preferences.*

**Green (ATM)**
- Building Cost: {{shops.specialty.green.building_cost}}
- Item Cost: {{shops.specialty.green.item_cost}}
- Max Item Price: {{shops.specialty.green.max_item_price}}
- Money Withdrawal: {{shops.specialty.green.money_withdrawal}}

*ATMs allow guests to withdraw more money. The amount of money withdrawn decreases exponentially with every subsequent withdrawal, to a minimum of {{shops.specialty.green.min_withdrawal}}*

**Red (Billboard)**
- Building Cost: {{shops.specialty.red.building_cost}}
- Item Cost: {{shops.specialty.red.item_cost}}
- Max Item Price: {{shops.specialty.red.max_item_price}}
- Thirst Boost: {{shops.specialty.red.thirst_boost}}
- Hunger Boost: {{shops.specialty.red.hunger_boost}}

*Billboards make guests more hungry, thirsty, and happy. They will additionally reset the visit count of attractions (meaning that guests are more likely to revisit attractions), and, if the guest has less than ${{shops.specialty.red.money_threshold}}, will direct the guest to an ATM.*


## All Employees

Employees perform up to 500 actions per day. For example, moving to an adjacent tile costs a move action.

### Janitors

Janitors clean a tile up to their cleaning threshold before moving to the next tile to clean. In addition to their salary, janitors incur $1 per cleaning action in cleaning supplies. 

**Yellow**
- Daily Salary: {{staff.janitor.yellow.salary}}
- Clean Rate: {{staff.janitor.yellow.clean_rate}}
- Cleaning Threshold: {{staff.janitor.yellow.cleaning_threshold}}

**Blue**
- Daily Salary: {{staff.janitor.blue.salary}}
- Clean Rate: {{staff.janitor.blue.clean_rate}}
- Cleaning Threshold: {{staff.janitor.blue.cleaning_threshold}}

*Blue, green, and red janitors move at double speed.*

**Green**
- Daily Salary: {{staff.janitor.green.salary}}
- Clean Rate: {{staff.janitor.green.clean_rate}}
- Cleaning Threshold: {{staff.janitor.green.cleaning_threshold}}

**Red**
- Daily Salary: {{staff.janitor.red.salary}}
- Clean Rate: {{staff.janitor.red.clean_rate}}
- Cleaning Threshold: {{staff.janitor.red.cleaning_threshold}}

*Red janitors perform preventative cleaning, allowing them to clean a tile to {{staff.janitor.red.cleaning_threshold}}; normally tiles have a maximum cleanliness of 1.0*

### Mechanics

**Yellow**
- Daily Salary: {{staff.mechanic.yellow.salary}}
- Repair Rate: {{staff.mechanic.yellow.repair_rate}}

**Blue**
- Daily Salary: {{staff.mechanic.blue.salary}}
- Repair Rate: {{staff.mechanic.blue.repair_rate}}

*Blue, green, and red mechanics move at double speed.*

**Green**
- Daily Salary: {{staff.mechanic.green.salary}}
- Repair Rate: {{staff.mechanic.green.repair_rate}}

**Red**
- Daily Salary: {{staff.mechanic.red.salary}}
- Repair Rate: {{staff.mechanic.red.repair_rate}}

*Red mechanics also perform preventative maintenance -- this allows them to partially repair a ride before it breaks down, further reducing the time required for repairs.*

### Specialists

**Yellow (Clown)**
- Daily Salary: {{staff.specialist.yellow.salary}}
- Happiness Boost: {{staff.specialist.yellow.happiness_boost}}

*Clowns move between different rides, increasing the happiness of guests waiting in line.*

**Blue (Stocker)**
- Daily Salary: {{staff.specialist.blue.salary}}
- Stocking Rate: {{staff.specialist.blue.stocking_rate}}
- Max Inventory: {{staff.specialist.blue.max_inventory}}
- Idle Ticks: {{staff.specialist.blue.idle_ticks}}
- Restock Threshold: {{staff.specialist.blue.restock_threshold}}

*Stockers restock the inventory of shops when the proportion of the shop's remaining inventory drops below the Restock Threshold. When this happens a stocker will move to an entrance or exit, purchase {{staff.specialist.blue.stocking_rate}}% of the daily order quantity, and take it to the shop. Stockers can carry at most {{staff.specialist.blue.max_inventory}} units of inventory and will not order more than this quantity. Stockers will stop making new purchases in the last {{staff.specialist.blue.idle_ticks}} actions of the day to prevent them from restocking a shop immediately before closing.*

**Green (Crier)**
- Daily Salary: {{staff.specialist.green.salary}}

*Criers move between attractions, providing guests about information related to the cleanliness and operation (i.e., if an attraction is out of service) of attractions, as well as current line wait times. This prevents guests from visiting out of service attractions, and makes them more likely to visit cleaner attractions and those with shorter wait times.*

**Red (Vendor)**
- Daily Salary: {{staff.specialist.red.salary}}
- Hunger Reduction: {{staff.specialist.red.hunger_reduction}}
- Thirst Reduction: {{staff.specialist.red.thirst_reduction}}

*Vendors move between rides, providing food and drink to guests waiting in line. Vendors do not incur additional costs or make additional profits from their activities.*

## Action Space 

Actions must be written as python function calls with keyword arguments.
These action functions must be in the following format: 

```python
action_name(param_1=<param1_value>, param_2=<param1_value>, ... )
```

The full list of available actions, including the action names, parameters, and a description of what they do is below:  
  
---  
  
{{action_spec}}
    
