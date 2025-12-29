"""
Gymnasium compatible observation space for the MAPs environment.

This observation space supports all the data in the FullParkObs pydantic model and provides full expressiveness.
Data can be converted to and from the FullParkObs pydantic model.
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import yaml
from .pydantic_obs import FullParkObs, park_observability_context, ParkDataGranularity, ParkObservabilityMode
import gymnasium as gym
from map_py.shared_constants import MAP_CONFIG as CONFIG

# Load configuration and enums
import importlib.resources
MODULE_PATH = importlib.resources.files(__package__)
GUEST_ENUMS = yaml.safe_load(open(MODULE_PATH/'../../shared/guest_enums.yaml'))

# Constants for observation space bounds
PARK_SIZE = CONFIG['park_size']
MAX_STEPS = 250
MAX_STAFF_PER_TYPE = 10
ATTRACTION_TYPES = list(CONFIG['rides'].keys()) + list(CONFIG['shops'].keys())
ATTRACTION_COLORS = list(CONFIG['rides'][ATTRACTION_TYPES[0]].keys())
# Calculate max values from config
MAX_CAPACITY = max(
    max(ride_data['capacity'] for ride_data in ride_type.values())
    for ride_type in CONFIG['rides'].values()
)
MAX_SURVEY_RESULTS = CONFIG['max_guests_to_survey']

# Staff enums for encoding string fields as integers
STAFF_SUBCLASS_MAP = {'yellow': 0, 'blue': 1, 'green': 2, 'red': 3}
STAFF_SUBCLASS_REVERSE = {0: 'yellow', 1: 'blue', 2: 'green', 3: 'red'}
STAFF_SUCCESS_METRICS = {'amount_cleaned': 0, 'repair_steps_performed': 1, 'guests_entertained': 2, 'items_restocked': 3, 'guests_informed': 4, 'guests_served': 5}
STAFF_SUCCESS_METRICS_REVERSE = {0: 'amount_cleaned', 1: 'repair_steps_performed', 2: 'guests_entertained', 3: 'items_restocked', 4: 'guests_informed', 5: 'guests_served'}

# Normalization configuration for each numerical input
# Format: (use_log: bool, max_value: float)
# If use_log is True, then the value will be normalized using a log scale
NORMALIZATION_CONFIG = {
    # Grid numerical properties
    'price': (False, max(CONFIG['shops']['drink']['red']['max_item_price'], 
                         CONFIG['shops']['food']['red']['max_item_price'],
                         CONFIG['shops']['specialty']['red']['max_item_price'],
                         CONFIG['rides']['roller_coaster']['red']['max_ticket_price'])),
    'operating_cost': (True, 100000),  # Large operating costs
    'revenue_generated': (True, 1000000),  # Large revenue
    'guests_served': (True, 1000),  # Guest counts
    'cleanliness': (False, 1.0),  # Already [0,1]
    'excitement': (False, 10.0),
    'intensity': (False, 10.0),
    'capacity': (False, MAX_CAPACITY),
    'times_operated': (True, 500),  # Operational frequency
    'uptime': (False, 1.0),  # Already [0,1]
    
    # Rides Vector
    'total_rides': (False, MAX_STEPS),
    'min_uptime': (False, 1.0),  # Already [0,1]
    'total_operating_cost': (True, 100000),
    'total_revenue_generated': (True, 1000000),
    'total_excitement': (True, 60.0),
    'avg_intensity': (False, 10.0),
    'total_capacity': (False, 100),
    'avg_wait_time': (False, 50.0),
    'avg_guests_per_operation': (False, 50.0),
    
    # Shops Vector
    'total_shops': (False, MAX_STEPS),
    'total_revenue_generated_shops': (True, 1000000),
    'total_operating_cost_shops': (True, 100000),
    
    # Staff Vector
    'x': (False, PARK_SIZE),
    'y': (False, PARK_SIZE),
    'total_janitors': (False, MAX_STAFF_PER_TYPE),
    'total_mechanics': (False, MAX_STAFF_PER_TYPE),
    'total_specialists': (False, MAX_STAFF_PER_TYPE),
    'total_salary_paid': (True, 15000),
    
    # Staff performance metrics
    'amount_cleaned': (True, 175.0),  # Janitors can clean many tiles over time
    'repair_steps_performed': (True, 25000.0),  # Mechanics can perform many repair steps
    'guests_entertained': (True, 25000.0),  # Clowns can entertain many guests
    'items_restocked': (True, 1250.0),  # Stockers can perform many restocks
    'guests_informed': (True, 25000.0),  # Criers can inform many guests
    'guests_served': (True, 25000.0),  # Vendors can serve many guests
    
    # Guest stats Vector
    'total_guests': (True, 2500),
    'avg_money_spent': (False, 250.0),
    'avg_time_in_park': (False, 250.0),
    'avg_rides_visited': (False, 250.0),
    'avg_food_shops_visited': (False, 250.0),
    'avg_drink_shops_visited': (False, 250.0),
    'avg_specialty_shops_visited': (False, 250.0),

    # Guest survey Vector
    'survey_age': (False, MAX_STEPS),
    'happiness_at_exit': (False, 1.0),  # Already [0,1]
    'hunger_at_exit': (False, 1.0),  # Already [0,1]
    'thirst_at_exit': (False, 1.0),  # Already [0,1]
    'remaining_energy': (False, 250),
    'remaining_money': (False, 250),
    'percent_of_money_spent': (False, 1.0),  # Already [0,1]
    'reason_for_exit_id': (False, len(GUEST_ENUMS['exit_reasons'])-1),
    'preference_id': (False, len(GUEST_ENUMS['preferences'])-1),
    
    # Park Vector
    'step': (False, MAX_STEPS),
    'horizon': (False, MAX_STEPS),
    'money': (True, 10000000),  # Park wealth
    'revenue': (True, 1000000),  # Daily revenue
    'expenses': (True, 1000000),  # Daily expenses
    'profit': (True, 1000000),  # Daily profit
    'park_rating': (False, 100.0),
    'research_speed': (False, 4),  # 0-4 range
    'new_entity_available': (False, 1.0),  # Boolean
    'fast_days_since_last_new_entity': (False, MAX_STEPS),
    'medium_days_since_last_new_entity': (False, MAX_STEPS),
    'slow_days_since_last_new_entity': (False, MAX_STEPS),

    # New fields to match pydantic_obs
    'value': (True, 10000000),  # Park value
    'research_operating_cost': (True, 100000),
    'item_cost': (False, max(CONFIG['shops']['drink']['red']['item_cost'],
                             CONFIG['shops']['food']['red']['item_cost'],
                             CONFIG['shops']['specialty']['red']['item_cost'])),
    'number_of_restocks': (False, 100),
    'order_quantity': (False, 100),
    'inventory': (False, 500),
    'cost_per_operation': (True, 10000),
    'breakdown_rate': (False, 1.0),
    'shop_uptime': (False, 1.0),
    'min_uptime_shops': (False, 1.0),
    'salary': (True, 5000),
    'employee_operating_cost': (True, 5000),
    'tiles_traversed': (True, 1000),
    'success_metric_id': (False, len(STAFF_SUCCESS_METRICS)),
    'subclass_id': (False, len(STAFF_SUBCLASS_MAP)),
    'staff_total_operating_cost': (True, 50000),
}

# Unified grid channels - all as floats
GRID_CHANNELS = [
    # Boolean indicators (0.0 or 1.0)
    'is_entrance', 'is_exit', 'is_path', 'is_water',
    'is_roller_coaster', 'is_ferris_wheel', 'is_carousel',
    'is_drink', 'is_food', 'is_specialty',
    'is_yellow', 'is_blue', 'is_green', 'is_red', 'out_of_service',
    # Numerical properties (normalized to [0, 1])
    'price', 'operating_cost', 'revenue_generated', 'guests_served',
    'cleanliness', 'excitement', 'intensity', 'capacity', 'times_operated',
    'uptime', 'avg_wait_time', 'avg_guests_per_operation',
    # Ride-specific fields (set to 0 for non-rides)
    'cost_per_operation', 'breakdown_rate',
    # Shop-specific fields (set to 0 for non-shops)
    'item_cost', 'number_of_restocks', 'order_quantity', 'inventory', 'shop_uptime'
]

# Create a channel index mapping for O(1) lookups
GRID_CHANNEL_INDICES = {channel: idx for idx, channel in enumerate(GRID_CHANNELS)}

def normalize_with_config(value: float, config_key: str) -> float:
    """
    Normalize a value using the configuration for that field.
    
    Args:
        value: The value to normalize
        config_key: The key in NORMALIZATION_CONFIG
    """
    use_log, max_value = NORMALIZATION_CONFIG[config_key]
    value = np.round(value, 2)
    if max_value == 1.0:
        raise ValueError(f"Normalize value for {config_key} is 1.0")
    if use_log:
        if value <= -1.0:
            raise ValueError(f"Normalize value {value} for {config_key} is less than or equal to -1.0")
        value, max_value = np.log1p(value), np.log1p(max_value)
    return value / max_value

def denormalize_with_config(value: float, config_key: str) -> float:
    """
    Denormalize a value from [0, 1] range back to original scale.
    """
    use_log, max_value = NORMALIZATION_CONFIG[config_key]    
    if max_value == 1.0:
        raise ValueError(f"Denormalize value for {config_key} is 1.0")
    if use_log:
        # For log normalization, we need to use log1p(max_value) as the scaling factor
        log_max_value = np.log1p(max_value)
        denorm_value = value * log_max_value
        denorm_value = np.expm1(denorm_value)
    else:
        # For linear normalization, just multiply by max_value
        denorm_value = value * max_value
    
    if isinstance(max_value, int):
        denorm_value = round(denorm_value.item())
    else:
        denorm_value = round(denorm_value.item(), 2)
    return denorm_value

# Update the conversion function to use the configuration
def obs_pydantic_to_array(obs: FullParkObs) -> Dict[str, np.ndarray]:
    """
    Convert a FullParkObs pydantic object to gym-compatible numpy arrays.
    Uses configuration-based normalization for all values.
    """
    # Initialize unified grid
    grid = np.zeros((PARK_SIZE, PARK_SIZE, len(GRID_CHANNELS)), dtype=np.float64)
    
    # Fill entrance and exit
    grid[obs.entrance[0], obs.entrance[1], GRID_CHANNEL_INDICES['is_entrance']] = 1.0
    grid[obs.exit[0], obs.exit[1], GRID_CHANNEL_INDICES['is_exit']] = 1.0
    
    # Fill paths
    for path in obs.paths:
        grid[path.x, path.y, GRID_CHANNEL_INDICES['is_path']] = 1.0
        grid[path.x, path.y, GRID_CHANNEL_INDICES['cleanliness']] = path.cleanliness
    
    # Fill waters
    for water in obs.waters:
        grid[water.x, water.y, GRID_CHANNEL_INDICES['is_water']] = 1.0
    
    attraction_list = [('ride', attraction) for attraction in obs.rides.ride_list] + [('shop', attraction) for attraction in obs.shops.shop_list]
    # Fill rides
    for type, attraction in attraction_list:
        # Set specific ride type
        if attraction.subtype == 'roller_coaster':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_roller_coaster']] = 1.0
        elif attraction.subtype == 'ferris_wheel':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_ferris_wheel']] = 1.0
        elif attraction.subtype == 'carousel':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_carousel']] = 1.0
        # Set specific shop type
        elif attraction.subtype == 'drink':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_drink']] = 1.0
        elif attraction.subtype == 'food':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_food']] = 1.0
        elif attraction.subtype == 'specialty':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_specialty']] = 1.0
        
        # Set color
        if attraction.subclass == 'yellow':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_yellow']] = 1.0
        elif attraction.subclass == 'blue':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_blue']] = 1.0
        elif attraction.subclass == 'green':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_green']] = 1.0
        elif attraction.subclass == 'red':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['is_red']] = 1.0
        
        # Set out of service
        if attraction.out_of_service:
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['out_of_service']] = 1.0
        
        # Shared numerical properties
        grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['cleanliness']] = np.round(attraction.cleanliness, 2)
        grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['operating_cost']] = normalize_with_config(attraction.operating_cost, 'operating_cost')
        grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['revenue_generated']] = normalize_with_config(attraction.revenue_generated, 'revenue_generated')

        # Shared, but differently named numerical properties
        price = attraction.ticket_price if type == 'ride' else attraction.item_price
        grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['price']] = normalize_with_config(price, 'price')
        num_guests = attraction.guests_entertained if type == 'ride' else attraction.guests_served
        grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['guests_served']] = normalize_with_config(num_guests, 'guests_served')

        # Ride-specific numerical properties
        if type == 'ride':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['excitement']] = normalize_with_config(attraction.excitement, 'excitement')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['intensity']] = normalize_with_config(attraction.intensity, 'intensity')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['capacity']] = normalize_with_config(attraction.capacity, 'capacity')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['uptime']] = np.round(attraction.uptime, 2)
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['times_operated']] = normalize_with_config(attraction.times_operated, 'times_operated')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['avg_wait_time']] = normalize_with_config(attraction.avg_wait_time, 'avg_wait_time')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['avg_guests_per_operation']] = normalize_with_config(attraction.avg_guests_per_operation, 'avg_guests_per_operation')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['cost_per_operation']] = normalize_with_config(attraction.cost_per_operation, 'cost_per_operation')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['breakdown_rate']] = np.round(attraction.breakdown_rate, 3)

        # Shop-specific numerical properties
        elif type == 'shop':
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['item_cost']] = normalize_with_config(attraction.item_cost, 'item_cost')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['number_of_restocks']] = normalize_with_config(attraction.number_of_restocks, 'number_of_restocks')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['order_quantity']] = normalize_with_config(attraction.order_quantity, 'order_quantity')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['inventory']] = normalize_with_config(attraction.inventory, 'inventory')
            grid[attraction.x, attraction.y, GRID_CHANNEL_INDICES['shop_uptime']] = np.round(attraction.uptime, 2)

    # Create vectors with configuration-based normalization
    rides_vector = np.array([
        normalize_with_config(obs.rides.total_rides, 'total_rides'),
        np.round(obs.rides.min_uptime, 2),
        normalize_with_config(obs.rides.total_operating_cost, 'total_operating_cost'),
        normalize_with_config(obs.rides.total_revenue_generated, 'total_revenue_generated'),
        normalize_with_config(obs.rides.total_excitement, 'total_excitement'),
        normalize_with_config(obs.rides.avg_intensity, 'avg_intensity'),
        normalize_with_config(obs.rides.total_capacity, 'total_capacity'),
    ], dtype=np.float64)
    
    shops_vector = np.array([
        normalize_with_config(obs.shops.total_shops, 'total_shops'),
        normalize_with_config(obs.shops.total_revenue_generated, 'total_revenue_generated_shops'),
        normalize_with_config(obs.shops.total_operating_cost, 'total_operating_cost_shops'),
        np.round(obs.shops.min_uptime, 2)
    ], dtype=np.float64)
    
    # Staff vector with color-coded counts (14 elements total)
    # total_janitors, total_mechanics, total_specialists are Lists of 4 ints each
    staff_vector = np.array([
        # Janitors by color (4 values)
        normalize_with_config(obs.staff.total_janitors[0], 'total_janitors'),
        normalize_with_config(obs.staff.total_janitors[1], 'total_janitors'),
        normalize_with_config(obs.staff.total_janitors[2], 'total_janitors'),
        normalize_with_config(obs.staff.total_janitors[3], 'total_janitors'),
        # Mechanics by color (4 values)
        normalize_with_config(obs.staff.total_mechanics[0], 'total_mechanics'),
        normalize_with_config(obs.staff.total_mechanics[1], 'total_mechanics'),
        normalize_with_config(obs.staff.total_mechanics[2], 'total_mechanics'),
        normalize_with_config(obs.staff.total_mechanics[3], 'total_mechanics'),
        # Specialists by color (4 values)
        normalize_with_config(obs.staff.total_specialists[0], 'total_specialists'),
        normalize_with_config(obs.staff.total_specialists[1], 'total_specialists'),
        normalize_with_config(obs.staff.total_specialists[2], 'total_specialists'),
        normalize_with_config(obs.staff.total_specialists[3], 'total_specialists'),
        # Aggregate staff costs (2 values)
        normalize_with_config(obs.staff.total_salary_paid, 'total_salary_paid'),
        normalize_with_config(obs.staff.total_operating_cost, 'staff_total_operating_cost')
    ], dtype=np.float64)
    
    # Create janitor vector with all Employee fields including x,y (50, 8)
    # Fields: [x, y, subclass_id, salary, operating_cost, success_metric_id, success_metric_value, tiles_traversed]
    # Sort janitors by (x, y) coordinates to match extraction order
    sorted_janitors = sorted(obs.staff.staff_list, key=lambda s: (s.x, s.y) if s.subtype == 'janitor' else (999, 999))
    sorted_janitors = [s for s in sorted_janitors if s.subtype == 'janitor'][:MAX_STAFF_PER_TYPE]
    janitor_vector = np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64)
    for i, janitor in enumerate(sorted_janitors):
        janitor_vector[i] = [
            normalize_with_config(janitor.x, 'x'),
            normalize_with_config(janitor.y, 'y'),
            normalize_with_config(STAFF_SUBCLASS_MAP[janitor.subclass], 'subclass_id'),
            normalize_with_config(janitor.salary or 0, 'salary'),
            normalize_with_config(janitor.operating_cost or 0, 'employee_operating_cost'),
            normalize_with_config(STAFF_SUCCESS_METRICS[janitor.success_metric], 'success_metric_id'),
            normalize_with_config(janitor.success_metric_value or 0.0, janitor.success_metric),
            normalize_with_config(janitor.tiles_traversed or 0, 'tiles_traversed')
        ]

    # Create mechanic vector with all Employee fields including x,y (50, 8)
    # Fields: [x, y, subclass_id, salary, operating_cost, success_metric_id, success_metric_value, tiles_traversed]
    # Sort mechanics by (x, y) coordinates to match extraction order
    sorted_mechanics = sorted(obs.staff.staff_list, key=lambda s: (s.x, s.y) if s.subtype == 'mechanic' else (999, 999))
    sorted_mechanics = [s for s in sorted_mechanics if s.subtype == 'mechanic'][:MAX_STAFF_PER_TYPE]
    mechanic_vector = np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64)
    for i, mechanic in enumerate(sorted_mechanics):
        mechanic_vector[i] = [
            normalize_with_config(mechanic.x, 'x'),
            normalize_with_config(mechanic.y, 'y'),
            normalize_with_config(STAFF_SUBCLASS_MAP[mechanic.subclass], 'subclass_id'),
            normalize_with_config(mechanic.salary or 0, 'salary'),
            normalize_with_config(mechanic.operating_cost or 0, 'employee_operating_cost'),
            normalize_with_config(STAFF_SUCCESS_METRICS[mechanic.success_metric], 'success_metric_id'),
            normalize_with_config(mechanic.success_metric_value or 0.0, mechanic.success_metric),
            normalize_with_config(mechanic.tiles_traversed or 0, 'tiles_traversed')
        ]

    # Create specialist vector with all Employee fields including x,y (50, 8)
    # Specialists aren't on grid so we store x,y in the vector
    # Sort specialists by (x, y) coordinates to match extraction order
    sorted_specialists = sorted(obs.staff.staff_list, key=lambda s: (s.x, s.y) if s.subtype == 'specialist' else (999, 999))
    sorted_specialists = [s for s in sorted_specialists if s.subtype == 'specialist'][:MAX_STAFF_PER_TYPE]
    specialist_vector = np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64)
    for i, specialist in enumerate(sorted_specialists):
        success_metric_id = STAFF_SUCCESS_METRICS[specialist.success_metric]
        specialist_vector[i] = [
            normalize_with_config(specialist.x, 'x'),
            normalize_with_config(specialist.y, 'y'),
            normalize_with_config(STAFF_SUBCLASS_MAP[specialist.subclass], 'subclass_id'),
            normalize_with_config(specialist.salary or 0, 'salary'),
            normalize_with_config(specialist.operating_cost or 0, 'employee_operating_cost'),
            normalize_with_config(success_metric_id, 'success_metric_id'),
            normalize_with_config(specialist.success_metric_value or 0.0, specialist.success_metric),
            normalize_with_config(specialist.tiles_traversed or 0, 'tiles_traversed')
        ]
    
    guests_vector = np.array([
        normalize_with_config(obs.guests.total_guests, 'total_guests'),
        normalize_with_config(obs.guests.avg_money_spent, 'avg_money_spent'),
        normalize_with_config(obs.guests.avg_time_in_park, 'avg_time_in_park'),
        normalize_with_config(obs.guests.avg_rides_visited, 'avg_rides_visited'),
        normalize_with_config(obs.guests.avg_food_shops_visited, 'avg_food_shops_visited'),
        normalize_with_config(obs.guests.avg_drink_shops_visited, 'avg_drink_shops_visited'),
        normalize_with_config(obs.guests.avg_specialty_shops_visited, 'avg_specialty_shops_visited')
    ], dtype=np.float64)
    
    # Survey results
    survey_age = np.array([
        normalize_with_config(obs.guest_survey_results.age_of_results, 'survey_age')
    ], dtype=np.float64)
    
    survey_results = np.zeros((MAX_SURVEY_RESULTS, 8), dtype=np.float64)
    for i, result in enumerate(obs.guest_survey_results.list_of_results[:MAX_SURVEY_RESULTS]):
        reason_for_exit_id = GUEST_ENUMS['exit_reason_description_to_id'][result.reason_for_exit]
        preference_id = GUEST_ENUMS['preference_description_to_id'][result.preference]
        if result:
            survey_results[i] = [
                np.round(result.happiness_at_exit, 2),
                np.round(result.hunger_at_exit, 2),
                np.round(result.thirst_at_exit, 2),
                normalize_with_config(result.remaining_energy, 'remaining_energy'),
                normalize_with_config(result.remaining_money, 'remaining_money'),
                np.round(result.percent_of_money_spent, 2),
                normalize_with_config(reason_for_exit_id, 'reason_for_exit_id'),  # Would need to parse from string
                normalize_with_config(preference_id, 'preference_id')  # Would need to parse from string
            ]
    
    # Park vector with configuration-based normalization
    research_speed_map = {'none': 0, 'slow': 1, 'medium': 2, 'fast': 4}
    research_speed = research_speed_map.get(obs.research_speed, 0)

    in_research = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    # Research topic mapping (includes staff types)
    research_topic_map = {
        "carousel": 0, "ferris_wheel": 1, "roller_coaster": 2,
        "drink": 3, "food": 4, "specialty": 5,
        "janitor": 6, "mechanic": 7, "specialist": 8
    }

    in_research = [0.0] * 9
    for research_topic in obs.research_topics:
        if research_topic in research_topic_map:
            in_research[research_topic_map[research_topic]] = 1.0

    # Include all entity types (attractions + staff)
    all_entity_types = ATTRACTION_TYPES + ['janitor', 'mechanic', 'specialist']
    available_entities = np.zeros(len(all_entity_types) * len(ATTRACTION_COLORS), dtype=np.float64)
    i = 0
    for entity_type in all_entity_types:
        for entity_color in ATTRACTION_COLORS:
            if entity_type in obs.available_entities and entity_color in obs.available_entities[entity_type]:
                available_entities[i] = 1.0
            i += 1
    
    park_vector = np.array([
        normalize_with_config(obs.step, 'step'),
        normalize_with_config(obs.horizon, 'horizon'),
        normalize_with_config(obs.value, 'value'),
        normalize_with_config(obs.money, 'money'),
        normalize_with_config(obs.revenue, 'revenue'),
        normalize_with_config(obs.expenses, 'expenses'),
        1.0 if obs.profit > 0 else 0.0, # profit sign
        normalize_with_config(abs(obs.profit), 'profit'),
        normalize_with_config(obs.park_rating, 'park_rating'),
        normalize_with_config(research_speed, 'research_speed'),
        *in_research,
        normalize_with_config(obs.research_operating_cost, 'research_operating_cost'),
        *available_entities,
        1.0 if obs.new_entity_available else 0.0, # new_entity_available
        normalize_with_config(obs.fast_days_since_last_new_entity, 'fast_days_since_last_new_entity'),
        normalize_with_config(obs.medium_days_since_last_new_entity, 'medium_days_since_last_new_entity'),
        normalize_with_config(obs.slow_days_since_last_new_entity, 'slow_days_since_last_new_entity'),
        round(obs.min_cleanliness, 2),
    ], dtype=np.float64)

    return {
        'grid': grid,
        'rides_vector': rides_vector,
        'shops_vector': shops_vector,
        'staff_vector': staff_vector,
        'janitor_vector': janitor_vector,
        'mechanic_vector': mechanic_vector,
        'specialist_vector': specialist_vector,
        'guests_vector': guests_vector,
        'survey_age': survey_age,
        'survey_results': survey_results,
        'park_vector': park_vector
    }

def obs_array_to_pydantic(obs_dict: Dict[str, np.ndarray], data_level: ParkDataGranularity, observability_mode: ParkObservabilityMode, as_dict: bool=False, raw_state: Optional[dict] = None) -> FullParkObs:
    """
    Convert gym-compatible numpy arrays to a FullParkObs pydantic object.

    Args:
        obs_dict: Dictionary of numpy arrays from gym observation
        data_level: Park data granularity level
        observability_mode: Park observability mode
        as_dict: Whether to return as dictionary instead of pydantic object
    """
    grid = obs_dict['grid']
    rides_vector = obs_dict['rides_vector']
    shops_vector = obs_dict['shops_vector']
    staff_vector = obs_dict['staff_vector']
    janitor_vector = obs_dict.get('janitor_vector', np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64))
    mechanic_vector = obs_dict.get('mechanic_vector', np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64))
    specialist_vector = obs_dict.get('specialist_vector', np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64))
    guests_vector = obs_dict['guests_vector']
    survey_age = obs_dict['survey_age']
    survey_results = obs_dict['survey_results']
    park_vector = obs_dict['park_vector']
    
    # Extract grid data
    entrance_coords = None
    exit_coords = None
    paths = []
    waters = []
    rides = []
    shops = []
    janitors = []
    mechanics = []
    specialists = []
    for x in range(PARK_SIZE):
        for y in range(PARK_SIZE):
            if grid[x, y, GRID_CHANNEL_INDICES['is_entrance']] > 0.5:
                entrance_coords = (x, y)
            elif grid[x, y, GRID_CHANNEL_INDICES['is_exit']] > 0.5:
                exit_coords = (x, y)
    
            elif grid[x, y, GRID_CHANNEL_INDICES['is_path']] > 0.5:
                cleanliness = round(grid[x, y, GRID_CHANNEL_INDICES['cleanliness']].item(), 2)
                paths.append({
                    'x': x,
                    'y': y,
                    'cleanliness': cleanliness
                })
            elif grid[x, y, GRID_CHANNEL_INDICES['is_water']] > 0.5:
                waters.append({
                    'x': x,
                    'y': y
                })
    
            elif grid[x, y, GRID_CHANNEL_INDICES['is_roller_coaster']] > 0.5:
                rides.append(_extract_ride_data(grid, x, y, 'roller_coaster'))
            elif grid[x, y, GRID_CHANNEL_INDICES['is_ferris_wheel']] > 0.5:
                rides.append(_extract_ride_data(grid, x, y, 'ferris_wheel'))
            elif grid[x, y, GRID_CHANNEL_INDICES['is_carousel']] > 0.5:
                rides.append(_extract_ride_data(grid, x, y, 'carousel'))
            elif grid[x, y, GRID_CHANNEL_INDICES['is_drink']] > 0.5:
                shops.append(_extract_shop_data(grid, x, y, 'drink'))
            elif grid[x, y, GRID_CHANNEL_INDICES['is_food']] > 0.5:
                shops.append(_extract_shop_data(grid, x, y, 'food'))
            elif grid[x, y, GRID_CHANNEL_INDICES['is_specialty']] > 0.5:
                shops.append(_extract_shop_data(grid, x, y, 'specialty'))

    # Reconstruct janitors from janitor_vector
    for i in range(MAX_STAFF_PER_TYPE):
        if np.any(janitor_vector[i] != 0):  # Check if janitor exists
            success_metric = STAFF_SUCCESS_METRICS_REVERSE[int(denormalize_with_config(janitor_vector[i, 5], 'success_metric_id'))]
            janitors.append({
                'x': int(denormalize_with_config(janitor_vector[i, 0], 'x')),
                'y': int(denormalize_with_config(janitor_vector[i, 1], 'y')),
                'subtype': 'janitor',
                'subclass': STAFF_SUBCLASS_REVERSE[int(denormalize_with_config(janitor_vector[i, 2], 'subclass_id'))],
                'salary': int(denormalize_with_config(janitor_vector[i, 3], 'salary')),
                'operating_cost': int(denormalize_with_config(janitor_vector[i, 4], 'employee_operating_cost')),
                'success_metric': success_metric,
                'success_metric_value': denormalize_with_config(janitor_vector[i, 6], success_metric),
                'tiles_traversed': int(denormalize_with_config(janitor_vector[i, 7], 'tiles_traversed'))
            })

    # Reconstruct mechanics from mechanic_vector
    for i in range(MAX_STAFF_PER_TYPE):
        if np.any(mechanic_vector[i] != 0):  # Check if mechanic exists
            success_metric = STAFF_SUCCESS_METRICS_REVERSE[int(denormalize_with_config(mechanic_vector[i, 5], 'success_metric_id'))]
            mechanics.append({
                'x': int(denormalize_with_config(mechanic_vector[i, 0], 'x')),
                'y': int(denormalize_with_config(mechanic_vector[i, 1], 'y')),
                'subtype': 'mechanic',
                'subclass': STAFF_SUBCLASS_REVERSE[int(denormalize_with_config(mechanic_vector[i, 2], 'subclass_id'))],
                'salary': int(denormalize_with_config(mechanic_vector[i, 3], 'salary')),
                'operating_cost': int(denormalize_with_config(mechanic_vector[i, 4], 'employee_operating_cost')),
                'success_metric': success_metric,
                'success_metric_value': denormalize_with_config(mechanic_vector[i, 6], success_metric),
                'tiles_traversed': int(denormalize_with_config(mechanic_vector[i, 7], 'tiles_traversed'))
            })

    # Reconstruct specialists from specialist_vector
    for i in range(MAX_STAFF_PER_TYPE):
        if np.any(specialist_vector[i] != 0):  # Check if specialist exists
            success_metric = STAFF_SUCCESS_METRICS_REVERSE[int(denormalize_with_config(specialist_vector[i, 5], 'success_metric_id'))]
            specialists.append({
                'x': int(denormalize_with_config(specialist_vector[i, 0], 'x')),
                'y': int(denormalize_with_config(specialist_vector[i, 1], 'y')),
                'subtype': 'specialist',
                'subclass': STAFF_SUBCLASS_REVERSE[int(denormalize_with_config(specialist_vector[i, 2], 'subclass_id'))],
                'salary': int(denormalize_with_config(specialist_vector[i, 3], 'salary')),
                'operating_cost': int(denormalize_with_config(specialist_vector[i, 4], 'employee_operating_cost')),
                'success_metric': success_metric,
                'success_metric_value': denormalize_with_config(specialist_vector[i, 6], success_metric),
                'tiles_traversed': int(denormalize_with_config(specialist_vector[i, 7], 'tiles_traversed'))
            })

    # Parse vectors
    rides_data = {
        'total_rides': int(denormalize_with_config(rides_vector[0], 'total_rides')),
        'min_uptime': round(rides_vector[1].item(), 2),
        'total_operating_cost': int(denormalize_with_config(rides_vector[2], 'total_operating_cost')),
        'total_revenue_generated': int(denormalize_with_config(rides_vector[3], 'total_revenue_generated')),
        'total_excitement': denormalize_with_config(rides_vector[4], 'total_excitement'),
        'avg_intensity': denormalize_with_config(rides_vector[5], 'avg_intensity'),
        'total_capacity': int(denormalize_with_config(rides_vector[6], 'total_capacity')),
        'ride_list': rides
    }
    
    shops_data = {
        'total_shops': int(denormalize_with_config(shops_vector[0], 'total_shops')),
        'total_revenue_generated': int(denormalize_with_config(shops_vector[1], 'total_revenue_generated_shops')),
        'total_operating_cost': int(denormalize_with_config(shops_vector[2], 'total_operating_cost_shops')),
        'min_uptime': round(shops_vector[3].item(), 2),
        'shop_list': shops
    }
    
    staff_data = {
        'total_janitors': [
            int(denormalize_with_config(staff_vector[0], 'total_janitors')),
            int(denormalize_with_config(staff_vector[1], 'total_janitors')),
            int(denormalize_with_config(staff_vector[2], 'total_janitors')),
            int(denormalize_with_config(staff_vector[3], 'total_janitors'))
        ],
        'total_mechanics': [
            int(denormalize_with_config(staff_vector[4], 'total_mechanics')),
            int(denormalize_with_config(staff_vector[5], 'total_mechanics')),
            int(denormalize_with_config(staff_vector[6], 'total_mechanics')),
            int(denormalize_with_config(staff_vector[7], 'total_mechanics'))
        ],
        'total_specialists': [
            int(denormalize_with_config(staff_vector[8], 'total_specialists')),
            int(denormalize_with_config(staff_vector[9], 'total_specialists')),
            int(denormalize_with_config(staff_vector[10], 'total_specialists')),
            int(denormalize_with_config(staff_vector[11], 'total_specialists'))
        ],
        'total_salary_paid': int(denormalize_with_config(staff_vector[12], 'total_salary_paid')),
        'total_operating_cost': int(denormalize_with_config(staff_vector[13], 'staff_total_operating_cost')),
        'staff_list': janitors + mechanics + specialists
    }
    
    guests_data = {
        'total_guests': denormalize_with_config(guests_vector[0], 'total_guests'),
        'avg_money_spent': denormalize_with_config(guests_vector[1], 'avg_money_spent'),
        'avg_time_in_park': denormalize_with_config(guests_vector[2], 'avg_time_in_park'),
        'avg_rides_visited': denormalize_with_config(guests_vector[3], 'avg_rides_visited'),
        'avg_food_shops_visited': denormalize_with_config(guests_vector[4], 'avg_food_shops_visited'),
        'avg_drink_shops_visited': denormalize_with_config(guests_vector[5], 'avg_drink_shops_visited'),
        'avg_specialty_shops_visited': denormalize_with_config(guests_vector[6], 'avg_specialty_shops_visited')
    }

    # Parse survey results
    survey_results_list = []
    for i in range(survey_results.shape[0]):

        if np.any(survey_results[i] != 0):  # Check if row has any non-zero values
            result = {
                'happiness_at_exit': round(survey_results[i, 0].item(), 2),
                'hunger_at_exit': round(survey_results[i, 1].item(), 2),
                'thirst_at_exit': round(survey_results[i, 2].item(), 2),
                'remaining_energy': denormalize_with_config(survey_results[i, 3], 'remaining_energy'),
                'remaining_money': denormalize_with_config(survey_results[i, 4], 'remaining_money'),
                'percent_of_money_spent': round(survey_results[i, 5].item(), 2),
                'reason_for_exit': GUEST_ENUMS['exit_reasons'][int(denormalize_with_config(survey_results[i, 6], 'reason_for_exit_id'))]['description'],
                'preference': GUEST_ENUMS['preferences'][int(denormalize_with_config(survey_results[i, 7], 'preference_id'))]['description']
            }
            survey_results_list.append(result)
    
    survey_data = {
        'age_of_results': int(denormalize_with_config(survey_age[0], 'survey_age')),
        'list_of_results': survey_results_list
    }
    
    # Parse park vector
    research_speed_map = {0: 'none', 1: 'slow', 2: 'medium', 4: 'fast'}
    research_speed = research_speed_map.get(int(denormalize_with_config(park_vector[9], 'research_speed')), 'none')

    # Parse research topics (now includes staff types)
    # Preserve original order, don't sort
    research_topics = []
    research_topic_map = {0: "carousel", 1: "ferris_wheel", 2: "roller_coaster", 3: "drink", 4: "food", 5: "specialty",
                          6: "janitor", 7: "mechanic", 8: "specialist"}
    for i in range(9):
        if park_vector[10 + i] > 0.5:  # Research topics start at index 10
            research_topics.append(research_topic_map[i])

    # Parse available entities (start after research_operating_cost at index 19)
    # Includes attractions + staff types
    all_entity_types = ATTRACTION_TYPES + ['janitor', 'mechanic', 'specialist']
    available_entities = {k: [] for k in all_entity_types}
    i = 0
    for entity_type in all_entity_types:
        for entity_color in ATTRACTION_COLORS:
            if park_vector[20 + i] > 0.5:
                available_entities[entity_type].append(entity_color)
            i += 1

    profit_sign = 1 if park_vector[6] > 0.5 else -1

    with park_observability_context(data_level, observability_mode):
        # Create FullParkObs object
        full_park_obs = FullParkObs(
            step=int(denormalize_with_config(park_vector[0], 'step')),
            horizon=int(denormalize_with_config(park_vector[1], 'horizon')),
            value=int(denormalize_with_config(park_vector[2], 'value')),
            money=int(denormalize_with_config(park_vector[3], 'money')),
            revenue=int(denormalize_with_config(park_vector[4], 'revenue')),
            expenses=int(denormalize_with_config(park_vector[5], 'expenses')),
            profit=int(denormalize_with_config(park_vector[7], 'profit')) * profit_sign,
            park_rating=denormalize_with_config(park_vector[8], 'park_rating'),
            guests=guests_data,
            guest_survey_results=survey_data,
            rides=rides_data,
            shops=shops_data,
            staff=staff_data,
            research_speed=research_speed,
            research_topics=research_topics,
            research_operating_cost=int(denormalize_with_config(park_vector[19], 'research_operating_cost')),
            available_entities=available_entities,
            new_entity_available=park_vector[56] > 0.5,
            fast_days_since_last_new_entity=int(denormalize_with_config(park_vector[57], 'fast_days_since_last_new_entity')),
            medium_days_since_last_new_entity=int(denormalize_with_config(park_vector[58], 'medium_days_since_last_new_entity')),
            slow_days_since_last_new_entity=int(denormalize_with_config(park_vector[59], 'slow_days_since_last_new_entity')),
            entrance=entrance_coords,
            exit=exit_coords,
            paths=paths,
            waters=waters,
            min_cleanliness=round(park_vector[60].item(), 2)
        )
    if as_dict:
        return full_park_obs.model_dump(exclude_none=True)

    return full_park_obs


def _extract_ride_data(grid: np.ndarray, x: int, y: int, subtype: str) -> dict:
    """Helper function to extract ride data from grid."""
    # Determine subclass (color)
    subclass = None
    if grid[x, y, GRID_CHANNEL_INDICES['is_yellow']] > 0.5:
        subclass = 'yellow'
    elif grid[x, y, GRID_CHANNEL_INDICES['is_blue']] > 0.5:
        subclass = 'blue'
    elif grid[x, y, GRID_CHANNEL_INDICES['is_green']] > 0.5:
        subclass = 'green'
    elif grid[x, y, GRID_CHANNEL_INDICES['is_red']] > 0.5:
        subclass = 'red'

    return {
        'subtype': subtype,
        'subclass': subclass,
        'x': x,
        'y': y,
        'out_of_service': grid[x, y, GRID_CHANNEL_INDICES['out_of_service']] > 0.5,
        'uptime': round(grid[x, y, GRID_CHANNEL_INDICES['uptime']].item(), 2),
        'cleanliness': round(grid[x, y, GRID_CHANNEL_INDICES['cleanliness']].item(), 2),
        'ticket_price': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['price']], 'price')),
        'operating_cost': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['operating_cost']], 'operating_cost')),
        'revenue_generated': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['revenue_generated']], 'revenue_generated')),
        'capacity': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['capacity']], 'capacity')),
        'intensity': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['intensity']], 'intensity')),
        'excitement': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['excitement']], 'excitement')),
        'guests_entertained': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['guests_served']], 'guests_served')),
        'times_operated': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['times_operated']], 'times_operated')),
        'cost_per_operation': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['cost_per_operation']], 'cost_per_operation')),
        'avg_wait_time': denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['avg_wait_time']], 'avg_wait_time'),
        'avg_guests_per_operation': denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['avg_guests_per_operation']], 'avg_guests_per_operation'),
        'breakdown_rate': round(grid[x, y, GRID_CHANNEL_INDICES['breakdown_rate']].item(), 3)
    }

def _extract_shop_data(grid: np.ndarray, x: int, y: int, subtype: str) -> dict:
    """Helper function to extract shop data from grid."""
    # Determine subclass (color)
    subclass = None
    if grid[x, y, GRID_CHANNEL_INDICES['is_yellow']] > 0.5:
        subclass = 'yellow'
    elif grid[x, y, GRID_CHANNEL_INDICES['is_blue']] > 0.5:
        subclass = 'blue'
    elif grid[x, y, GRID_CHANNEL_INDICES['is_green']] > 0.5:
        subclass = 'green'
    elif grid[x, y, GRID_CHANNEL_INDICES['is_red']] > 0.5:
        subclass = 'red'
    
    return {
        'subtype': subtype,
        'subclass': subclass,
        'x': x,
        'y': y,
        'item_price': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['price']], 'price')),
        'item_cost': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['item_cost']], 'item_cost')),
        'operating_cost': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['operating_cost']], 'operating_cost')),
        'uptime': round(grid[x, y, GRID_CHANNEL_INDICES['shop_uptime']].item(), 2),
        'number_of_restocks': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['number_of_restocks']], 'number_of_restocks')),
        'order_quantity': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['order_quantity']], 'order_quantity')),
        'inventory': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['inventory']], 'inventory')),
        'revenue_generated': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['revenue_generated']], 'revenue_generated')),
        'cleanliness': round(grid[x, y, GRID_CHANNEL_INDICES['cleanliness']].item(), 2),
        'guests_served': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['guests_served']], 'guests_served')),
        'out_of_service': grid[x, y, GRID_CHANNEL_INDICES['out_of_service']] > 0.5
    }

class MapsGymObservationSpace(gym.spaces.Dict):
    """
    Gymnasium compatible observation space for the MAP environment.

    This observation space provides a structured representation of the park state
    that can be used with reinforcement learning algorithms.

    The observation consists of:
    - grid: Park layout and properties (size determined by GRID_CHANNELS)
    - rides_vector: Summary statistics about all rides
    - shops_vector: Summary statistics about all shops
    - staff_vector: Summary statistics about staff
    - janitor_vector: Individual janitor details (including x,y positions)
    - mechanic_vector: Individual mechanic details (including x,y positions)
    - specialist_vector: Individual specialist details (including x,y positions)
    - guests_vector: Summary statistics about guests
    - survey_age: Age of survey results
    - survey_results: Individual guest survey results
    - park_vector: Overall park statistics
    """
    
    def __init__(self):
        # Constants from the existing gym_obs.py
        PARK_SIZE = 20
        MAX_SURVEY_RESULTS = 25  # From config

        super().__init__({
            # Grid representation (channels: boolean indicators + numerical properties)
            "grid": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(PARK_SIZE, PARK_SIZE, len(GRID_CHANNELS)),
                dtype=np.float64
            ),

            # # Rides summary vector (7 values)
            "rides_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(7,),
                dtype=np.float64
            ),

            # # Shops summary vector (4 values)
            "shops_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(4,),
                dtype=np.float64
            ),

            # # Staff summary vector (14 values: 4 janitors + 4 mechanics + 4 specialists + 2 costs)
            "staff_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(14,),
                dtype=np.float64
            ),

            # # Janitor vector (MAX_STAFF_PER_TYPE x 8 fields per janitor, includes x,y)
            "janitor_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(MAX_STAFF_PER_TYPE, 8),
                dtype=np.float64
            ),

            # # Mechanic vector (MAX_STAFF_PER_TYPE x 8 fields per mechanic, includes x,y)
            "mechanic_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(MAX_STAFF_PER_TYPE, 8),
                dtype=np.float64
            ),

            # # Specialist vector (MAX_STAFF_PER_TYPE x 8 fields per specialist, includes x,y)
            "specialist_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(MAX_STAFF_PER_TYPE, 8),
                dtype=np.float64
            ),

            # # Guests summary vector (7 values)
            "guests_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(7,),
                dtype=np.float64
            ),

            # # Survey age (1 value)
            "survey_age": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(1,),
                dtype=np.float64
            ),

            # # Survey results: MAX_SURVEY_RESULTS x 8 array
            "survey_results": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(MAX_SURVEY_RESULTS, 8),
                dtype=np.float64
            ),

            # Park summary vector (61 values: includes 9 research topics + 36 available entities for attractions+staff)
            "park_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(61,),
                dtype=np.float64
            )
        })
        
        # Store constants for reference
        self.PARK_SIZE = PARK_SIZE
        self.MAX_SURVEY_RESULTS = MAX_SURVEY_RESULTS
        self.GRID_CHANNELS = GRID_CHANNELS
        
        # Create channel index mapping for O(1) lookups
        self.GRID_CHANNEL_INDICES = GRID_CHANNEL_INDICES
    
    def sample(self) -> Dict[str, np.ndarray]:
        """Sample a random observation from the observation space."""
        return super().sample()
    
    def contains(self, x: Dict[str, np.ndarray]) -> bool:
        """Check if the observation is within the observation space."""
        return super().contains(x)
    
    def to_pydantic(self, obs_dict: Dict[str, np.ndarray]) -> 'FullParkObs':
        """
        Convert gym-compatible observation to FullParkObs pydantic object.
        Uses the existing obs_array_to_pydantic function.
        """
        return obs_array_to_pydantic(obs_dict)
    
    def from_pydantic(self, obs: 'FullParkObs') -> Dict[str, np.ndarray]:
        """
        Convert FullParkObs pydantic object to gym-compatible observation.
        Uses the existing obs_pydantic_to_array function.
        """
        return obs_pydantic_to_array(obs)

def format_gym_observation(state: dict) -> MapsGymObservationSpace:
    """
    Convert a raw state dictionary directly to gym-compatible observation arrays.
    
    This function bypasses the pydantic conversion and directly constructs
    the gym observation from the raw state data.
    
    Args:
        state: Raw state dictionary from the game server
        
    Returns:
        ParkObservationSpace containing gym-compatible numpy arrays
    """
    # Initialize unified grid
    grid = np.zeros((PARK_SIZE, PARK_SIZE, len(GRID_CHANNELS)), dtype=np.float64)
    
    # Fill entrance and exit
    entrance = (state['entrance']['x'], state['entrance']['y'])
    exit_coords = (state['exit']['x'], state['exit']['y'])
    grid[entrance[0], entrance[1], GRID_CHANNEL_INDICES['is_entrance']] = 1.0
    grid[exit_coords[0], exit_coords[1], GRID_CHANNEL_INDICES['is_exit']] = 1.0

    ride_uptime, ride_operating_cost, ride_revenue_generated, ride_excitement, ride_intensity, ride_capacity = [], 0, 0, state['state']['park_excitement'], 0, 0
    shop_operating_cost, shop_revenue_generated, shop_uptime = 0, 0, []
    cleanliness = []

    
    # Fill paths and waters from terrain
    for terrain in state['terrain']:
        x, y = terrain['x'], terrain['y']
        if terrain['type'] == 'path':
            grid[x, y, GRID_CHANNEL_INDICES['is_path']] = 1.0
            grid[x, y, GRID_CHANNEL_INDICES['cleanliness']] = np.round(terrain['cleanliness'], 2)
            cleanliness.append(terrain['cleanliness'])
        elif terrain['type'] == 'water':
            grid[x, y, GRID_CHANNEL_INDICES['is_water']] = 1.0
    
    # Fill rides
    for attraction in state['rides'] + state['shops']:
        x, y = attraction['x'], attraction['y']
        if attraction['type'] == 'ride':
            ride_uptime.append(attraction['uptime'])
            ride_operating_cost += attraction['operating_cost']
            ride_revenue_generated += attraction['revenue_generated']
            ride_intensity += attraction['intensity']
            ride_capacity += attraction['capacity']
        elif attraction['type'] == 'shop':
            shop_operating_cost += attraction['operating_cost']
            shop_revenue_generated += attraction['revenue_generated']
            shop_uptime.append(attraction['uptime'])
        cleanliness.append(attraction['cleanliness'])

        # Set ride type indicators
        if attraction['subtype'] == 'roller_coaster':
            grid[x, y, GRID_CHANNEL_INDICES['is_roller_coaster']] = 1.0
        elif attraction['subtype'] == 'ferris_wheel':
            grid[x, y, GRID_CHANNEL_INDICES['is_ferris_wheel']] = 1.0
        elif attraction['subtype'] == 'carousel':
            grid[x, y, GRID_CHANNEL_INDICES['is_carousel']] = 1.0
        elif attraction['subtype'] == 'drink':
            grid[x, y, GRID_CHANNEL_INDICES['is_drink']] = 1.0
        elif attraction['subtype'] == 'food':
            grid[x, y, GRID_CHANNEL_INDICES['is_food']] = 1.0
        elif attraction['subtype'] == 'specialty':
            grid[x, y, GRID_CHANNEL_INDICES['is_specialty']] = 1.0
        
        # Set color indicators
        if attraction['subclass'] == 'yellow':
            grid[x, y, GRID_CHANNEL_INDICES['is_yellow']] = 1.0
        elif attraction['subclass'] == 'blue':
            grid[x, y, GRID_CHANNEL_INDICES['is_blue']] = 1.0
        elif attraction['subclass'] == 'green':
            grid[x, y, GRID_CHANNEL_INDICES['is_green']] = 1.0
        elif attraction['subclass'] == 'red':
            grid[x, y, GRID_CHANNEL_INDICES['is_red']] = 1.0
        
        # Set status
        if attraction['out_of_service']:
            grid[x, y, GRID_CHANNEL_INDICES['out_of_service']] = 1.0
        
        # Set numerical properties
        price_key = 'ticket_price' if attraction['type'] == 'ride' else 'item_price'
        grid[x, y, GRID_CHANNEL_INDICES['price']] = normalize_with_config(attraction[price_key], 'price')
        grid[x, y, GRID_CHANNEL_INDICES['operating_cost']] = normalize_with_config(attraction['operating_cost'], 'operating_cost')
        grid[x, y, GRID_CHANNEL_INDICES['revenue_generated']] = normalize_with_config(attraction['revenue_generated'], 'revenue_generated')
        guests_served_key = 'guests_entertained' if attraction['type'] == 'ride' else 'guests_served'
        grid[x, y, GRID_CHANNEL_INDICES['guests_served']] = normalize_with_config(attraction[guests_served_key], 'guests_served')
        grid[x, y, GRID_CHANNEL_INDICES['cleanliness']] = np.round(attraction['cleanliness'], 2)
        if attraction['type'] == 'ride':
            grid[x, y, GRID_CHANNEL_INDICES['excitement']] = normalize_with_config(attraction['excitement'], 'excitement')
            grid[x, y, GRID_CHANNEL_INDICES['intensity']] = normalize_with_config(attraction['intensity'], 'intensity')
            grid[x, y, GRID_CHANNEL_INDICES['capacity']] = normalize_with_config(attraction['capacity'], 'capacity')
            grid[x, y, GRID_CHANNEL_INDICES['times_operated']] = normalize_with_config(attraction['times_operated'], 'times_operated')
            grid[x, y, GRID_CHANNEL_INDICES['uptime']] = np.round(attraction['uptime'], 2)
            grid[x, y, GRID_CHANNEL_INDICES['avg_wait_time']] = normalize_with_config(attraction['avg_wait_time'], 'avg_wait_time')
            grid[x, y, GRID_CHANNEL_INDICES['avg_guests_per_operation']] = normalize_with_config(attraction['avg_guests_per_operation'], 'avg_guests_per_operation')
            grid[x, y, GRID_CHANNEL_INDICES['cost_per_operation']] = normalize_with_config(attraction['cost_per_operation'], 'cost_per_operation')
            grid[x, y, GRID_CHANNEL_INDICES['breakdown_rate']] = np.round(attraction['breakdown_rate'], 3)
        elif attraction['type'] == 'shop':
            grid[x, y, GRID_CHANNEL_INDICES['item_cost']] = normalize_with_config(attraction['item_cost'], 'item_cost')
            grid[x, y, GRID_CHANNEL_INDICES['number_of_restocks']] = normalize_with_config(attraction['number_of_restocks'], 'number_of_restocks')
            grid[x, y, GRID_CHANNEL_INDICES['order_quantity']] = normalize_with_config(attraction['order_quantity'], 'order_quantity')
            grid[x, y, GRID_CHANNEL_INDICES['inventory']] = normalize_with_config(attraction['inventory'], 'inventory')
            grid[x, y, GRID_CHANNEL_INDICES['shop_uptime']] = np.round(attraction['uptime'], 2)

    # Calculate total staff operating cost
    total_staff_operating_cost = sum(staff_member['operating_cost'] for staff_member in state['staff'])

    # Create rides vector
    rides_vector = np.array([
        normalize_with_config(len(state['rides']), 'total_rides'),
        round(min(ride_uptime), 2) if len(ride_uptime) > 0 else 1.0,
        normalize_with_config(ride_operating_cost, 'total_operating_cost'),
        normalize_with_config(ride_revenue_generated, 'total_revenue_generated'),
        normalize_with_config(state['state']['park_excitement'], 'total_excitement'),
        normalize_with_config(ride_intensity / max(len(state['rides']), 1), 'avg_intensity'),
        normalize_with_config(ride_capacity, 'total_capacity'),
    ], dtype=np.float64)
    
    # Create shops vector
    shops_vector = np.array([
        normalize_with_config(len(state['shops']), 'total_shops'),
        normalize_with_config(shop_revenue_generated, 'total_revenue_generated_shops'),
        normalize_with_config(shop_operating_cost, 'total_operating_cost_shops'),
        round(min(shop_uptime), 2) if len(shop_uptime) > 0 else 1.0
    ], dtype=np.float64)
    
    # Create staff vector with color-coded counts
    janitors = [s for s in state['staff'] if s['subtype'] == 'janitor']
    mechanics = [s for s in state['staff'] if s['subtype'] == 'mechanic']
    specialists = [s for s in state['staff'] if s['subtype'] == 'specialist']

    # Count by color for each staff type
    janitor_colors = [0, 0, 0, 0]  # yellow, blue, green, red
    mechanic_colors = [0, 0, 0, 0]
    specialist_colors = [0, 0, 0, 0]

    for j in janitors:
        if j['subclass'] == 'yellow': janitor_colors[0] += 1
        elif j['subclass'] == 'blue': janitor_colors[1] += 1
        elif j['subclass'] == 'green': janitor_colors[2] += 1
        elif j['subclass'] == 'red': janitor_colors[3] += 1

    for m in mechanics:
        if m['subclass'] == 'yellow': mechanic_colors[0] += 1
        elif m['subclass'] == 'blue': mechanic_colors[1] += 1
        elif m['subclass'] == 'green': mechanic_colors[2] += 1
        elif m['subclass'] == 'red': mechanic_colors[3] += 1

    for s in specialists:
        if s['subclass'] == 'yellow': specialist_colors[0] += 1
        elif s['subclass'] == 'blue': specialist_colors[1] += 1
        elif s['subclass'] == 'green': specialist_colors[2] += 1
        elif s['subclass'] == 'red': specialist_colors[3] += 1

    staff_vector = np.array([
        # Janitors by color
        normalize_with_config(janitor_colors[0], 'total_janitors'),
        normalize_with_config(janitor_colors[1], 'total_janitors'),
        normalize_with_config(janitor_colors[2], 'total_janitors'),
        normalize_with_config(janitor_colors[3], 'total_janitors'),
        # Mechanics by color
        normalize_with_config(mechanic_colors[0], 'total_mechanics'),
        normalize_with_config(mechanic_colors[1], 'total_mechanics'),
        normalize_with_config(mechanic_colors[2], 'total_mechanics'),
        normalize_with_config(mechanic_colors[3], 'total_mechanics'),
        # Specialists by color
        normalize_with_config(specialist_colors[0], 'total_specialists'),
        normalize_with_config(specialist_colors[1], 'total_specialists'),
        normalize_with_config(specialist_colors[2], 'total_specialists'),
        normalize_with_config(specialist_colors[3], 'total_specialists'),
        # Aggregate costs
        normalize_with_config(state['state']['total_salary_paid'], 'total_salary_paid'),
        normalize_with_config(total_staff_operating_cost, 'staff_total_operating_cost')
    ], dtype=np.float64)
    
    # Create janitor vector with all Employee fields including x,y (50, 8)
    # Sort janitors by (x, y) coordinates to match extraction order
    sorted_janitors = sorted(janitors, key=lambda j: (j['x'], j['y']))[:MAX_STAFF_PER_TYPE]
    janitor_vector = np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64)
    for i, janitor in enumerate(sorted_janitors):
        success_metric = janitor.get('success_metric', 'amount_cleaned')
        janitor_vector[i] = [
            normalize_with_config(janitor['x'], 'x'),
            normalize_with_config(janitor['y'], 'y'),
            normalize_with_config(STAFF_SUBCLASS_MAP[janitor['subclass']], 'subclass_id'),
            normalize_with_config(janitor.get('salary', 0), 'salary'),
            normalize_with_config(janitor.get('operating_cost', 0), 'employee_operating_cost'),
            normalize_with_config(STAFF_SUCCESS_METRICS.get(success_metric, 0), 'success_metric_id'),
            normalize_with_config(janitor.get('success_metric_value', janitor.get('amount_cleaned', 0.0)), success_metric),
            normalize_with_config(janitor.get('tiles_traversed', 0), 'tiles_traversed')
        ]

    # Create mechanic vector with all Employee fields including x,y (50, 8)
    # Sort mechanics by (x, y) coordinates to match extraction order
    sorted_mechanics = sorted(mechanics, key=lambda m: (m['x'], m['y']))[:MAX_STAFF_PER_TYPE]
    mechanic_vector = np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64)
    for i, mechanic in enumerate(sorted_mechanics):
        success_metric = mechanic.get('success_metric', 'repair_steps_performed')
        mechanic_vector[i] = [
            normalize_with_config(mechanic['x'], 'x'),
            normalize_with_config(mechanic['y'], 'y'), 
            normalize_with_config(STAFF_SUBCLASS_MAP[mechanic['subclass']], 'subclass_id'),
            normalize_with_config(mechanic.get('salary', 0), 'salary'),
            normalize_with_config(mechanic.get('operating_cost', 0), 'employee_operating_cost'),
            normalize_with_config(STAFF_SUCCESS_METRICS.get(success_metric, 1), 'success_metric_id'),
            normalize_with_config(mechanic.get('success_metric_value', mechanic.get('repair_steps_performed', 0.0)), success_metric),
            normalize_with_config(mechanic.get('tiles_traversed', 0), 'tiles_traversed')
        ]

    # Create specialist vector with all Employee fields including x,y (50, 8)
    # Sort specialists by (x, y) coordinates to match extraction order
    sorted_specialists = sorted(specialists, key=lambda s: (s['x'], s['y']))[:MAX_STAFF_PER_TYPE]
    specialist_vector = np.zeros((MAX_STAFF_PER_TYPE, 8), dtype=np.float64)
    for i, specialist in enumerate(sorted_specialists):
        success_metric_id = STAFF_SUCCESS_METRICS[specialist['success_metric']]
        specialist_vector[i] = [
            normalize_with_config(specialist['x'], 'x'),
            normalize_with_config(specialist['y'], 'y'),
            normalize_with_config(STAFF_SUBCLASS_MAP[specialist['subclass']], 'subclass_id'),
            normalize_with_config(specialist.get('salary', 0), 'salary'),
            normalize_with_config(specialist.get('operating_cost', 0), 'employee_operating_cost'),
            normalize_with_config(success_metric_id, 'success_metric_id'),
            normalize_with_config(specialist.get('success_metric_value', 0.0), specialist['success_metric']),
            normalize_with_config(specialist.get('tiles_traversed', 0), 'tiles_traversed')
        ]
    
    # Create guests vector (avg_steps_taken maps to avg_time_in_park in pydantic)
    guests_vector = np.array([
        normalize_with_config(state['guestStats']['total_guests'], 'total_guests'),
        normalize_with_config(state['guestStats']['avg_money_spent'], 'avg_money_spent'),
        normalize_with_config(state['guestStats']['avg_steps_taken'], 'avg_time_in_park'),
        normalize_with_config(state['guestStats']['avg_rides_visited'], 'avg_rides_visited'),
        normalize_with_config(state['guestStats']['avg_food_shops_visited'], 'avg_food_shops_visited'),
        normalize_with_config(state['guestStats']['avg_drink_shops_visited'], 'avg_drink_shops_visited'),
        normalize_with_config(state['guestStats']['avg_specialty_shops_visited'], 'avg_specialty_shops_visited')
    ], dtype=np.float64)
    
    # Create survey data
    survey_age = np.array([normalize_with_config(state['guest_survey_results']['age_of_results'], 'survey_age')], dtype=np.float64)
    
    survey_results = np.zeros((MAX_SURVEY_RESULTS, 8), dtype=np.float64)
    for i, result in enumerate(state['guest_survey_results']['list_of_results'][:MAX_SURVEY_RESULTS]):
        if result:
            survey_results[i] = [
                round(result['happiness_at_exit'], 2),
                round(result['hunger_at_exit'], 2),
                round(result['thirst_at_exit'], 2),
                normalize_with_config(result['remaining_energy'], 'remaining_energy'),
                normalize_with_config(result['remaining_money'], 'remaining_money'),
                round(result['percent_of_money_spent'], 2),
                normalize_with_config(result['reason_for_exit_id'], 'reason_for_exit_id'),
                normalize_with_config(result['preference_id'], 'preference_id')
            ]
    
    # Create park vector
    research_speed_map = {'none': 0, 'slow': 1, 'medium': 2, 'fast': 4}
    research_speed = research_speed_map.get(state['state']['research_speed'], 0)
    
    # Research topics mapping (includes staff types)
    research_topic_map = {
        "carousel": 0, "ferris_wheel": 1, "roller_coaster": 2,
        "drink": 3, "food": 4, "specialty": 5,
        "janitor": 6, "mechanic": 7, "specialist": 8
    }

    in_research = [0.0] * 9
    for research_topic in state['state']['research_topics']:
        if research_topic in research_topic_map:
            in_research[research_topic_map[research_topic]] = 1.0

    # Include all entity types (attractions + staff)
    all_entity_types = ATTRACTION_TYPES + ['janitor', 'mechanic', 'specialist']
    available_entities = []
    for entity_type in all_entity_types:
        for entity_color in ATTRACTION_COLORS:
            if entity_type in state['state']['available_entities'] and entity_color in state['state']['available_entities'][entity_type]:
                available_entities.append(1.0)
            else:
                available_entities.append(0.0)

    profit = state['state']['revenue'] - state['state']['expenses']
    
    park_vector = np.array([
        normalize_with_config(state['state']['step'], 'step'),
        normalize_with_config(state['state']['horizon'], 'horizon'),
        normalize_with_config(state['state']['value'], 'value'),
        normalize_with_config(state['state']['money'], 'money'),
        normalize_with_config(state['state']['revenue'], 'revenue'),
        normalize_with_config(state['state']['expenses'], 'expenses'),
        1.0 if profit > 0 else 0.0, # profit sign
        normalize_with_config(abs(profit), 'profit'),
        normalize_with_config(state['state']['park_rating'], 'park_rating'),
        normalize_with_config(research_speed, 'research_speed'),
        *in_research,  # 6 research topic indicators
        normalize_with_config(state['state'].get('research_operating_cost', 0), 'research_operating_cost'),
        *available_entities,  # 24 (6 attraction types * 4 colors) attraction type indicators
        1.0 if state['state']['new_entity_available'] else 0.0,  # new_entity_available
        normalize_with_config(state['state'].get('fast_days_since_last_new_entity', 0), 'fast_days_since_last_new_entity'),
        normalize_with_config(state['state'].get('medium_days_since_last_new_entity', 0), 'medium_days_since_last_new_entity'),
        normalize_with_config(state['state'].get('slow_days_since_last_new_entity', 0), 'slow_days_since_last_new_entity'),
        round(min(cleanliness), 2),
    ], dtype=np.float64)
    
    return {
        'grid': grid,
        'rides_vector': rides_vector,
        'shops_vector': shops_vector,
        'staff_vector': staff_vector,
        'janitor_vector': janitor_vector,
        'mechanic_vector': mechanic_vector,
        'specialist_vector': specialist_vector,
        'guests_vector': guests_vector,
        'survey_age': survey_age,
        'survey_results': survey_results,
        'park_vector': park_vector
    }
