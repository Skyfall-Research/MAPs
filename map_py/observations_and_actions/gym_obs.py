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
MAX_STAFF_PER_TYPE = 50
ATTRACTION_TYPES = list(CONFIG['rides'].keys()) + list(CONFIG['shops'].keys())
ATTRACTION_COLORS = list(CONFIG['rides'][ATTRACTION_TYPES[0]].keys())
# Calculate max values from config
MAX_CAPACITY = max(
    max(ride_data['capacity'] for ride_data in ride_type.values())
    for ride_type in CONFIG['rides'].values()
)
MAX_SURVEY_RESULTS = CONFIG['max_guests_to_survey']

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
    'excitement': (False, 10),
    'intensity': (False, 10),
    'capacity': (False, MAX_CAPACITY),
    'times_operated': (True, 500),  # Operational frequency
    'num_mechanics': (False, MAX_STAFF_PER_TYPE // 2),
    'num_janitors': (False, MAX_STAFF_PER_TYPE // 2),
    'uptime': (False, 1.0),  # Already [0,1]
    
    # Rides Vector
    'total_rides': (False, MAX_STEPS),
    'min_uptime': (False, 1.0),  # Already [0,1]
    'total_operating_cost': (True, 100000),
    'total_revenue_generated': (True, 1000000),
    'total_excitement': (True, 60),
    'avg_intensity': (False, 10.0),
    'total_capacity': (False, 100),
    'avg_wait_time': (False, 50.0),
    'avg_guests_per_operation': (False, 50.0),
    
    # Shops Vector
    'total_shops': (False, MAX_STEPS),
    'total_revenue_generated_shops': (True, 1000000),
    'total_operating_cost_shops': (True, 100000),
    
    # Staff Vector
    'total_janitors': (False, MAX_STAFF_PER_TYPE),
    'total_mechanics': (False, MAX_STAFF_PER_TYPE),
    'total_salary_paid': (True, 15000),
    
    # Staff performance metrics
    'amount_cleaned': (True, 500),  # Janitors can clean many tiles over time
    'repair_steps_performed': (True, 500),  # Mechanics can perform many repair steps
    
    # Guest stats Vector
    'total_guests': (True, 2500),
    'avg_money_spent': (False, 250.0),
    'avg_happiness': (False, 1.0),
    'avg_hunger': (False, 1.0),
    'avg_thirst': (False, 1.0),
    'avg_steps_taken': (False, 250.0),
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
    'avg_path_cleanliness': (False, 1.0),  # Already [0,1]
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
    'num_mechanics', 'num_janitors', 'uptime', 'avg_wait_time', 'avg_guests_per_operation'
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

    # Count mechanics and janitors per tile
    for mechanic in obs.staff.mechanics:
        grid[mechanic.x, mechanic.y, GRID_CHANNEL_INDICES['num_mechanics']] += 1.0
    
    for janitor in obs.staff.janitors:
        grid[janitor.x, janitor.y, GRID_CHANNEL_INDICES['num_janitors']] += 1.0
        
    # Normalize staff counts more efficiently
    mechanics_channel = GRID_CHANNEL_INDICES['num_mechanics']
    janitors_channel = GRID_CHANNEL_INDICES['num_janitors']
    
    grid[:, :, mechanics_channel] = normalize_with_config(grid[:, :, mechanics_channel], 'num_mechanics')
    grid[:, :, janitors_channel] = normalize_with_config(grid[:, :, janitors_channel], 'num_janitors')
    
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
        normalize_with_config(obs.shops.total_operating_cost, 'total_operating_cost_shops')
    ], dtype=np.float64)
    
    staff_vector = np.array([
        normalize_with_config(obs.staff.total_janitors, 'total_janitors'),
        normalize_with_config(obs.staff.total_mechanics, 'total_mechanics'),
        normalize_with_config(obs.staff.total_salary_paid, 'total_salary_paid')
    ], dtype=np.float64)
    
    # Create janitor vector with amount_cleaned values
    # Sort janitors by (x, y) coordinates to match extraction order
    sorted_janitors = sorted(obs.staff.janitors, key=lambda j: (j.x, j.y))[:MAX_STAFF_PER_TYPE]
    janitor_vector = np.zeros(MAX_STAFF_PER_TYPE, dtype=np.float64)
    for i, janitor in enumerate(sorted_janitors):
        janitor_vector[i] = normalize_with_config(janitor.amount_cleaned or 0.0, 'amount_cleaned')
    
    # Create mechanic vector with repair_steps_performed values
    # Sort mechanics by (x, y) coordinates to match extraction order
    sorted_mechanics = sorted(obs.staff.mechanics, key=lambda m: (m.x, m.y))[:MAX_STAFF_PER_TYPE]
    mechanic_vector = np.zeros(MAX_STAFF_PER_TYPE, dtype=np.float64)
    for i, mechanic in enumerate(sorted_mechanics):
        mechanic_vector[i] = normalize_with_config(mechanic.repair_steps_performed or 0.0, 'repair_steps_performed')
    
    guests_vector = np.array([
        normalize_with_config(obs.guests.total_guests, 'total_guests'),
        normalize_with_config(obs.guests.avg_money_spent, 'avg_money_spent'),
        np.round(obs.guests.avg_happiness, 2),
        np.round(obs.guests.avg_hunger, 2),
        np.round(obs.guests.avg_thirst, 2),
        normalize_with_config(obs.guests.avg_steps_taken, 'avg_steps_taken'),
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

    # More efficient research topic mapping
    research_topic_map = {
        "carousel": 0, "ferris_wheel": 1, "roller_coaster": 2,
        "drink": 3, "food": 4, "specialty": 5
    }
    
    in_research = [0.0] * 6
    for research_topic in obs.research_topics:
        in_research[research_topic_map[research_topic]] = 1.0

    available_entities = np.zeros(len(ATTRACTION_TYPES) * len(ATTRACTION_COLORS), dtype=np.float64)
    i = 0
    for attraction_type in ATTRACTION_TYPES:
        for attraction_color in ATTRACTION_COLORS:
            if attraction_color in obs.available_entities[attraction_type]:
                available_entities[i] = 1.0
            i += 1
    
    park_vector = np.array([
        obs.parkId,
        normalize_with_config(obs.step, 'step'),
        normalize_with_config(obs.horizon, 'horizon'),
        normalize_with_config(obs.money, 'money'),
        normalize_with_config(obs.revenue, 'revenue'),
        normalize_with_config(obs.expenses, 'expenses'),
        1.0 if obs.profit > 0 else 0.0, # profit sign
        normalize_with_config(abs(obs.profit), 'profit'),
        normalize_with_config(obs.park_rating, 'park_rating'),
        normalize_with_config(research_speed, 'research_speed'),
        *in_research,
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
        'guests_vector': guests_vector,
        'survey_age': survey_age,
        'survey_results': survey_results,
        'park_vector': park_vector
    }

def obs_array_to_pydantic(obs_dict: Dict[str, np.ndarray], data_level: ParkDataGranularity, observability_mode: ParkObservabilityMode, as_dict: bool=False) -> FullParkObs:
    """
    Convert gym-compatible numpy arrays to a FullParkObs pydantic object.
    """
    grid = obs_dict['grid']
    rides_vector = obs_dict['rides_vector']
    shops_vector = obs_dict['shops_vector']
    staff_vector = obs_dict['staff_vector']
    janitor_vector = obs_dict.get('janitor_vector', np.zeros(MAX_STAFF_PER_TYPE, dtype=np.float64))
    mechanic_vector = obs_dict.get('mechanic_vector', np.zeros(MAX_STAFF_PER_TYPE, dtype=np.float64))
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
    
            num_mechanics = denormalize_with_config(
                grid[x, y, GRID_CHANNEL_INDICES['num_mechanics']], 'num_mechanics'
            )
            num_janitors = denormalize_with_config(
                grid[x, y, GRID_CHANNEL_INDICES['num_janitors']], 'num_janitors'
            )
            
            for i in range(int(num_mechanics)):
                if len(mechanics) < MAX_STAFF_PER_TYPE:
                    mechanics.append({
                        'x': x,
                        'y': y,
                        'repair_steps_performed': denormalize_with_config(mechanic_vector[len(mechanics)], 'repair_steps_performed')
                    })
            
            for i in range(int(num_janitors)):
                if len(janitors) < MAX_STAFF_PER_TYPE:
                    janitors.append({
                        'x': x,
                        'y': y,
                        'amount_cleaned': denormalize_with_config(janitor_vector[len(janitors)], 'amount_cleaned')
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
        'shop_list': shops
    }
    
    staff_data = {
        'total_janitors': int(denormalize_with_config(staff_vector[0], 'total_janitors')),
        'total_mechanics': int(denormalize_with_config(staff_vector[1], 'total_mechanics')),
        'total_salary_paid': int(denormalize_with_config(staff_vector[2], 'total_salary_paid')),
        'janitors': janitors,
        'mechanics': mechanics
    }
    
    guests_data = {
        'total_guests': denormalize_with_config(guests_vector[0], 'total_guests'),
        'avg_money_spent': denormalize_with_config(guests_vector[1], 'avg_money_spent'),
        'avg_happiness': round(guests_vector[2].item(), 2),
        'avg_hunger': round(guests_vector[3].item(), 2),
        'avg_thirst': round(guests_vector[4].item(), 2),
        'avg_steps_taken': denormalize_with_config(guests_vector[5], 'avg_steps_taken'),
        'avg_rides_visited': denormalize_with_config(guests_vector[6], 'avg_rides_visited'),
        'avg_food_shops_visited': denormalize_with_config(guests_vector[7], 'avg_food_shops_visited'),
        'avg_drink_shops_visited': denormalize_with_config(guests_vector[8], 'avg_drink_shops_visited'),
        'avg_specialty_shops_visited': denormalize_with_config(guests_vector[9], 'avg_specialty_shops_visited')
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
    
    # Parse research topics
    research_topics = []
    research_topic_map = {0: "carousel", 1: "ferris_wheel", 2: "roller_coaster", 3: "drink", 4: "food", 5: "specialty"}
    for i in range(6):
        if park_vector[10 + i] > 0.5:  # Research topics start at index 7
            research_topics.append(research_topic_map[i])
    research_topics.sort()

    # Parse available attractions
    available_entities = {k: [] for k in ATTRACTION_TYPES}
    i = 0
    for attraction_type in ATTRACTION_TYPES:
        for attraction_color in ATTRACTION_COLORS:
            if park_vector[16 + i] > 0.5:
                available_entities[attraction_type].append(attraction_color)
            i += 1

    profit_sign = 1 if park_vector[6] > 0.5 else -1

    with park_observability_context(data_level, observability_mode): 
        # Create FullParkObs object
        full_park_obs = FullParkObs(
            parkId=int(park_vector[0]),  # Not in array
            step=int(denormalize_with_config(park_vector[1], 'step')),
            horizon=int(denormalize_with_config(park_vector[2], 'horizon')),
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
            available_entities=available_entities,
            new_entity_available=park_vector[40] > 0.5, 
            fast_days_since_last_new_entity=int(denormalize_with_config(park_vector[41], 'fast_days_since_last_new_entity')),
            medium_days_since_last_new_entity=int(denormalize_with_config(park_vector[42], 'medium_days_since_last_new_entity')),
            slow_days_since_last_new_entity=int(denormalize_with_config(park_vector[43], 'slow_days_since_last_new_entity')),
            entrance=entrance_coords,
            exit=exit_coords,
            paths=paths,
            waters=waters,
            min_cleanliness=round(park_vector[44].item(), 2)
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
        'avg_wait_time': denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['avg_wait_time']], 'avg_wait_time'),
        'avg_guests_per_operation': denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['avg_guests_per_operation']], 'avg_guests_per_operation')
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
        'operating_cost': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['operating_cost']], 'operating_cost')),
        'revenue_generated': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['revenue_generated']], 'revenue_generated')),
        'cleanliness': round(grid[x, y, GRID_CHANNEL_INDICES['cleanliness']].item(), 2),
        'out_of_service': grid[x, y, GRID_CHANNEL_INDICES['out_of_service']] > 0.5,
        'guests_served': int(denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['guests_served']], 'guests_served')),
        'avg_wait_time': denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['avg_wait_time']], 'avg_wait_time'),
        'avg_guests_per_operation': denormalize_with_config(grid[x, y, GRID_CHANNEL_INDICES['avg_guests_per_operation']], 'avg_guests_per_operation')
    }

class ParkObservationSpace(gym.spaces.Dict):
    """
    Gymnasium compatible observation space for the MAP environment.
    
    This observation space provides a structured representation of the park state
    that can be used with reinforcement learning algorithms.
    
    The observation consists of:
    - grid: 20x20x25 array representing the park layout and properties
    - rides_vector: Summary statistics about all rides
    - shops_vector: Summary statistics about all shops  
    - staff_vector: Summary statistics about staff
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
            # Grid representation: 20x20x25 array
            # Channels: boolean indicators + numerical properties
            "grid": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(PARK_SIZE, PARK_SIZE, 25), 
                dtype=np.float64
            ),
            
            # Rides summary vector (8 values)
            "rides_vector": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(10,), 
                dtype=np.float64
            ),
            
            # Shops summary vector (4 values) 
            "shops_vector": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(4,), 
                dtype=np.float64
            ),
            
            # Staff summary vector (3 values)
            "staff_vector": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(3,), 
                dtype=np.float64
            ),

            # Janitor vector (MAX_STAFF_PER_TYPE values)
            "janitor_vector": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(MAX_STAFF_PER_TYPE,), 
                dtype=np.float64
            ),

            # Mechanic vector (MAX_STAFF_PER_TYPE values)
            "mechanic_vector": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(MAX_STAFF_PER_TYPE,), 
                dtype=np.float64
            ),
            
            # Guests summary vector (2 values)
            "guests_vector": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(2,), 
                dtype=np.float64
            ),
            
            # Survey age (1 value)
            "survey_age": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(1,), 
                dtype=np.float64
            ),
            
            # Survey results: MAX_SURVEY_RESULTS x 8 array
            "survey_results": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(MAX_SURVEY_RESULTS, 8), 
                dtype=np.float64
            ),
            
            # Park summary vector (17 values)
            "park_vector": gym.spaces.Box(
                low=0.0, 
                high=1.0, 
                shape=(45,), 
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

def format_gym_observation(state: dict) -> ParkObservationSpace:
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
    shop_operating_cost, shop_revenue_generated = 0, 0
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
    
    # Fill staff positions
    for staff_member in state['staff']:
        x, y = staff_member['x'], staff_member['y']
        if staff_member['type'] == 'janitor':
            grid[x, y, GRID_CHANNEL_INDICES['num_janitors']] += 1.0
        elif staff_member['type'] == 'mechanic':
            grid[x, y, GRID_CHANNEL_INDICES['num_mechanics']] += 1.0

    grid[:, :, GRID_CHANNEL_INDICES['num_mechanics']] = normalize_with_config(grid[:, :, GRID_CHANNEL_INDICES['num_mechanics']], 'num_mechanics')
    grid[:, :, GRID_CHANNEL_INDICES['num_janitors']] = normalize_with_config(grid[:, :, GRID_CHANNEL_INDICES['num_janitors']], 'num_janitors')
    
    # Create rides vector
    rides_vector = np.array([
        normalize_with_config(len(state['rides']), 'total_rides'),
        round(min(ride_uptime), 2) if len(ride_uptime) > 0 else 0.0,
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
        normalize_with_config(shop_operating_cost, 'total_operating_cost_shops')
    ], dtype=np.float64)
    
    # Create staff vector
    janitors = [s for s in state['staff'] if s['type'] == 'janitor']
    mechanics = [s for s in state['staff'] if s['type'] == 'mechanic']
    staff_vector = np.array([
        normalize_with_config(len(janitors), 'total_janitors'),
        normalize_with_config(len(mechanics), 'total_mechanics'),
        normalize_with_config(state['state']['total_salary_paid'], 'total_salary_paid')
    ], dtype=np.float64)
    
    # Create janitor vector with amount_cleaned values
    # Sort janitors by (x, y) coordinates to match extraction order
    sorted_janitors = sorted(janitors, key=lambda j: (j['x'], j['y']))[:MAX_STAFF_PER_TYPE]
    janitor_vector = np.zeros(MAX_STAFF_PER_TYPE, dtype=np.float64)
    for i, janitor in enumerate(sorted_janitors):
        janitor_vector[i] = normalize_with_config(janitor.get('amount_cleaned', 0.0), 'amount_cleaned')
    
    # Create mechanic vector with repair_steps_performed values
    # Sort mechanics by (x, y) coordinates to match extraction order
    sorted_mechanics = sorted(mechanics, key=lambda m: (m['x'], m['y']))[:MAX_STAFF_PER_TYPE]
    mechanic_vector = np.zeros(MAX_STAFF_PER_TYPE, dtype=np.float64)
    for i, mechanic in enumerate(sorted_mechanics):
        mechanic_vector[i] = normalize_with_config(mechanic.get('repair_steps_performed', 0.0), 'repair_steps_performed')
    
    # Create guests vector
    guests_vector = np.array([
        normalize_with_config(state['guestStats']['total_guests'], 'total_guests'),
        normalize_with_config(state['guestStats']['avg_money_spent'], 'avg_money_spent'),
        np.round(state['guestStats']['avg_happiness'], 2),
        np.round(state['guestStats']['avg_hunger'], 2),
        np.round(state['guestStats']['avg_thirst'], 2),
        normalize_with_config(state['guestStats']['avg_steps_taken'], 'avg_steps_taken'),
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
    
    # Research topics mapping
    research_topic_map = {
        "carousel": 0, "ferris_wheel": 1, "roller_coaster": 2,
        "drink": 3, "food": 4, "specialty": 5
    }
    
    in_research = [0.0] * 6
    for research_topic in state['state']['research_topics']:
        if research_topic in research_topic_map:
            in_research[research_topic_map[research_topic]] = 1.0

    available_entities = []
    for attraction_type in ATTRACTION_TYPES:
        for attraction_color in ATTRACTION_COLORS:
            if attraction_color in state['state']['available_entities'][attraction_type]:
                available_entities.append(1.0)
            else:
                available_entities.append(0.0)

    profit = state['state']['revenue'] - state['state']['expenses']
    
    park_vector = np.array([
        state['state']['parkId'],
        normalize_with_config(state['state']['step'], 'step'),
        normalize_with_config(state['state']['horizon'], 'horizon'),
        normalize_with_config(state['state']['money'], 'money'),
        normalize_with_config(state['state']['revenue'], 'revenue'),
        normalize_with_config(state['state']['expenses'], 'expenses'),
        1.0 if profit > 0 else 0.0, # profit sign
        normalize_with_config(abs(profit), 'profit'),
        normalize_with_config(state['state']['park_rating'], 'park_rating'),
        normalize_with_config(research_speed, 'research_speed'),
        *in_research,  # 6 research topic indicators
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
        'guests_vector': guests_vector,
        'survey_age': survey_age,
        'survey_results': survey_results,
        'park_vector': park_vector
    }
