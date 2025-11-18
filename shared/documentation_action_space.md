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

    
## Park Config File
The following json contains the park's configuration including prices, properties, valid ranges and descriptions:

```json
{"rides": {"carousel": {"yellow": {"building_cost": 250, "cost_per_operation": 1, "capacity": 6, "max_ticket_price": 4, "ticket_price": -1, "excitement": 1, "intensity": 1, "breakdown_rate": 0.001}, "blue": {"building_cost": 1500, "cost_per_operation": 2, "capacity": 14, "max_ticket_price": 6, "ticket_price": -1, "excitement": 4, "intensity": 3, "breakdown_rate": 0.002}, "green": {"building_cost": 11500, "cost_per_operation": 30, "capacity": 26, "max_ticket_price": 14, "ticket_price": -1, "excitement": 3, "intensity": 4, "breakdown_rate": 0.003}, "red": {"building_cost": 24000, "cost_per_operation": 12, "capacity": 24, "max_ticket_price": 24, "ticket_price": -1, "excitement": 8, "intensity": 5, "breakdown_rate": 0.005}}, "ferris_wheel": {"yellow": {"building_cost": 600, "cost_per_operation": 10, "capacity": 10, "max_ticket_price": 5, "ticket_price": -1, "excitement": 2, "intensity": 2, "breakdown_rate": 0.006}, "blue": {"building_cost": 7500, "cost_per_operation": 20, "capacity": 20, "max_ticket_price": 7, "ticket_price": -1, "excitement": 5, "intensity": 3, "breakdown_rate": 0.009}, "green": {"building_cost": 50000, "cost_per_operation": 55, "capacity": 40, "max_ticket_price": 15, "ticket_price": -1, "excitement": 4, "intensity": 6, "breakdown_rate": 0.024}, "red": {"building_cost": 75000, "cost_per_operation": 75, "capacity": 30, "max_ticket_price": 28, "ticket_price": -1, "excitement": 9, "intensity": 8, "breakdown_rate": 0.032}}, "roller_coaster": {"yellow": {"building_cost": 1000, "cost_per_operation": 8, "capacity": 4, "max_ticket_price": 10, "ticket_price": -1, "excitement": 3, "intensity": 4, "breakdown_rate": 0.01}, "blue": {"building_cost": 18000, "cost_per_operation": 25, "capacity": 12, "max_ticket_price": 20, "ticket_price": -1, "excitement": 7, "intensity": 7, "breakdown_rate": 0.02}, "green": {"building_cost": 60000, "cost_per_operation": 45, "capacity": 28, "max_ticket_price": 34, "ticket_price": -1, "excitement": 6, "intensity": 9, "breakdown_rate": 0.025}, "red": {"building_cost": 100000, "cost_per_operation": 100, "capacity": 22, "max_ticket_price": 50, "ticket_price": -1, "excitement": 10, "intensity": 10, "breakdown_rate": 0.04}}}, "ride_rejection_happiness_penalty": 0.2, "shops": {"drink": {"yellow": {"building_cost": 100, "thirst_reduction": 0.24, "max_item_price": 3, "item_price": -1, "item_cost": 0, "order_quantity": -1, "notes": "\u2193 thirst."}, "blue": {"building_cost": 2250, "thirst_reduction": 0.6, "max_item_price": 6, "item_price": -1, "item_cost": 1, "order_quantity": -1, "notes": "\u2193 thirst."}, "green": {"building_cost": 17500, "thirst_reduction": 0.96, "happiness_boost": 0.4, "max_item_price": 17, "item_price": -1, "item_cost": 3, "order_quantity": -1, "notes": "\u2193 thirst and \u2191 happiness."}, "red": {"building_cost": 48000, "max_item_price": 25, "thirst_reduction": 0.72, "energy_boost": 20, "caffeinated_steps": 50, "item_price": -1, "item_cost": 5, "order_quantity": -1, "notes": "\u2193 thirst and \u2191 energy and walking speed."}}, "food": {"yellow": {"building_cost": 200, "hunger_reduction": 0.2, "max_item_price": 5, "item_price": -1, "item_cost": 1, "order_quantity": -1, "notes": "\u2193 hunger."}, "blue": {"building_cost": 3600, "hunger_reduction": 0.5, "max_item_price": 9, "item_price": -1, "item_cost": 2, "order_quantity": -1, "notes": "\u2193 hunger."}, "green": {"building_cost": 28000, "hunger_reduction": 0.8, "thirst_reduction": 0.4, "max_item_price": 18, "item_price": -1, "item_cost": 4, "order_quantity": -1, "notes": "\u2193 hunger and thirst."}, "red": {"building_cost": 60000, "hunger_reduction": 1.0, "happiness_boost": 0.6, "max_item_price": 34, "item_price": -1, "item_cost": 8, "order_quantity": -1, "notes": "\u2193 hunger and \u2191 happiness."}}, "specialty": {"yellow": {"building_cost": 250, "happiness_boost": 0.5, "max_item_price": 15, "item_price": -1, "item_cost": 4, "order_quantity": -1, "notes": "\u2191 guest happiness."}, "blue": {"building_cost": 10000, "max_item_price": 5, "item_price": -1, "item_cost": 2, "order_quantity": -1, "notes": "Informs guests about attractions."}, "green": {"building_cost": 50000, "money_withdrawal": 64, "min_withdrawal": 16, "max_item_price": 5, "item_price": -1, "item_cost": 3, "order_quantity": -1, "notes": "Allows guests to withdraw money."}, "red": {"building_cost": 10000, "thirst_boost": 0.25, "hunger_boost": 0.25, "happiness_boost": 0.25, "max_item_price": 0, "item_price": -1, "item_cost": 0, "order_quantity": -1, "money_threshold": 25, "notes": "\u2191 thirst, hunger, and happiness."}}}, "specialty_decay_rate": 2, "staff": {"janitor": {"yellow": {"salary": 25, "clean_rate": 0.028, "cleaning_threshold": 0.85, "notes": "Cleans tiles."}, "blue": {"salary": 100, "clean_rate": 0.075, "cleaning_threshold": 0.95, "notes": "Cleans tiles fast, walks fast."}, "green": {"salary": 500, "clean_rate": 0.2, "cleaning_threshold": 1.0, "notes": "Cleans tiles faster, walks fast."}, "red": {"salary": 2000, "clean_rate": 0.35, "cleaning_threshold": 1.2, "notes": "Cleans tiles fastest, walks fast.\nProvides preventative cleaning."}}, "mechanic": {"yellow": {"salary": 15, "repair_rate": 2, "notes": "Repairs rides."}, "blue": {"salary": 100, "repair_rate": 8, "notes": "Repairs rides fast, walks fast."}, "green": {"salary": 250, "repair_rate": 20, "notes": "Repairs rides faster, walks fast."}, "red": {"salary": 1000, "repair_rate": 50, "notes": "Repairs rides fastest, walks fast.\nProvides preventative maintenance."}}, "specialist": {"yellow": {"salary": 60, "happiness_boost": 0.25, "notes": "Entertains guest in ride lines."}, "blue": {"salary": 350, "notes": "Restocks shops.", "stocking_rate": 0.1, "max_inventory": 100, "restock_threshold": 0.25, "idle_ticks": 30}, "green": {"salary": 250, "notes": "Informs guests about dirty\nor out of service attractions."}, "red": {"salary": 300, "happiness_boost": 0.2, "hunger_reduction": 0.3, "thirst_reduction": 0.4, "notes": "Provides fun food and drink to\nguests waiting in line."}}}, "guest_initial_money": [150, 25], "guest_initial_energy": [100, 20], "hunger_build_rate": 0.012, "thirst_build_rate": 0.018, "happiness_decay_rate": 0.04, "soft_target_threshold": 0.6, "hard_target_threshold": 0.82, "happiness_decay_rate_low_cleanliness": 0.03, "happiness_attraction_rejection_penalty": 0.2, "per_guest_survey_cost": 500, "max_guests_to_survey": 25, "littering_penalty": 0.005, "ride_repair_cost_percentage": 0.045, "sell_percentage": 0.66, "research_value_per_point": 60, "park_size": 20, "ticks_per_day": 500, "vis_update_rate": 1, "path_addition_cost": 1000, "path_removal_cost": 2500, "water_addition_cost": 5000, "water_removal_cost": 10000, "path_nodes_range": [3, 16], "min_node_distance_range": [2, 6], "node_densification_range": [0, 1], "vertical_pathing_prob_range": [0, 1], "research": {"speed_progress": {"none": 0, "slow": 25, "medium": 50, "fast": 100}, "speed_cost": {"none": 0, "slow": 2000, "medium": 8000, "fast": 32000}, "points_required": {"blue": 100, "green": 200, "red": 400}}, "horizon_by_difficulty": {"easy": 50, "medium": 100, "hard": 250}, "sandbox_mode_steps": 100, "test_layouts": ["zig_zag", "the_islands", "ribs"], "train_layouts": ["diagonal_squares", "the_ladder", "two_paths", "the_line", "the_fork"], "train_seed": 663, "test_seed": 286}```