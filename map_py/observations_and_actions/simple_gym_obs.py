"""
Simple Gymnasium compatible observation space for the MAPs environment.

This is a simplified version that is lossy.
It only includes vector representations, no grid or detailed staff/survey data.
"""

import numpy as np
from typing import Dict
import yaml
import gymnasium as gym
from map_py.shared_constants import MAP_CONFIG as CONFIG

# Constants for observation space bounds
PARK_SIZE = CONFIG['park_size']
MAX_STEPS = 250
MAX_STAFF_PER_TYPE = 10
ATTRACTION_TYPES = list(CONFIG['rides'].keys()) + list(CONFIG['shops'].keys())
ATTRACTION_COLORS = list(CONFIG['rides'][ATTRACTION_TYPES[0]].keys())

# Staff enums for encoding string fields as integers
STAFF_SUBCLASS_MAP = {'yellow': 0, 'blue': 1, 'green': 2, 'red': 3}

# Normalization configuration for each numerical input
# Format: (use_log: bool, max_value: float)
NORMALIZATION_CONFIG = {
    # Rides Vector
    'num_rides': (False, 50),
    'min_uptime': (False, 1.0),
    'total_operating_cost': (True, 100000),
    'total_revenue_generated': (True, 1000000),
    'total_excitement': (True, 60.0),
    'avg_intensity': (False, 10.0),
    'total_capacity': (False, 100),
    'avg_wait_time': (False, 50.0),
    'avg_guests_per_operation': (False, 50.0),

    # Shops Vector
    'num_shops': (False, 50),
    'total_revenue_generated_shops': (True, 1000000),
    'total_operating_cost_shops': (True, 100000),

    # Staff Vector
    'num_staff': (False, 50),
    'total_salary_paid': (True, 15000),
    'total_operating_cost': (True, 50000),

    # Guest stats Vector
    'total_guests': (True, 2500),
    'avg_money_spent': (False, 250.0),
    'avg_time_in_park': (False, 250.0),
    'avg_rides_visited': (False, 250.0),
    'avg_food_shops_visited': (False, 250.0),
    'avg_drink_shops_visited': (False, 250.0),
    'avg_specialty_shops_visited': (False, 250.0),

    # Park Vector
    'step': (False, MAX_STEPS),
    'horizon': (False, MAX_STEPS),
    'money': (True, 10000000),
    'revenue': (True, 1000000),
    'expenses': (True, 1000000),
    'profit': (True, 1000000),
    'park_rating': (False, 100.0),
    'research_speed': (False, 4),
    'research_operating_cost': (True, 100000),
    'value': (True, 10000000),
    'fast_days_since_last_new_entity': (False, MAX_STEPS),
    'medium_days_since_last_new_entity': (False, MAX_STEPS),
    'slow_days_since_last_new_entity': (False, MAX_STEPS),
}


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


class MapsSimpleGymObservationSpace(gym.spaces.Dict):
    """
    Simplified Gymnasium compatible observation space for the MAP environment.

    Only includes vector representations, no grid or detailed staff/survey data.

    The observation consists of:
    - rides_vector: Counts by subtype/subclass + aggregate metrics (19 values)
    - shops_vector: Counts by subtype/subclass + aggregate metrics (15 values)
    - staff_vector: Counts by subtype/color + aggregate costs (14 values)
    - guests_vector: Summary statistics about guests (7 values)
    - park_vector: Overall park statistics (10 values)
    """

    def __init__(self):
        super().__init__({
            "rides_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(19,),
                dtype=np.float64
            ),
            "shops_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(15,),
                dtype=np.float64
            ),
            "staff_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(14,),
                dtype=np.float64
            ),
            "guests_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(7,),
                dtype=np.float64
            ),
            "park_vector": gym.spaces.Box(
                low=0.0,
                high=1.0,
                shape=(10,),
                dtype=np.float64
            )
        })


def format_simple_gym_observation(state: dict) -> Dict[str, np.ndarray]:
    """
    Convert a raw state dictionary to simplified gym-compatible observation arrays.

    This is a lossy conversion that only includes vector representations,
    no grid or detailed staff/survey data.

    Args:
        state: Raw state dictionary from the game server

    Returns:
        Dictionary containing 5 vectors: rides_vector, shops_vector, staff_vector,
        guests_vector, park_vector
    """

    # ===== RIDES VECTOR (19 values) =====
    # Format: [carousel: 4 colors, ferris_wheel: 4 colors, roller_coaster: 4 colors,
    #          min_uptime, total_operating_cost, total_revenue_generated,
    #          total_excitement, avg_intensity, total_capacity, avg_wait_time]
    ride_subtypes = ['carousel', 'ferris_wheel', 'roller_coaster']
    colors = ['yellow', 'blue', 'green', 'red']

    ride_counts = {}
    for subtype in ride_subtypes:
        for color in colors:
            ride_counts[f"{subtype}_{color}"] = 0

    # Count rides by subtype and color
    for ride in state['rides']:
        key = f"{ride['subtype']}_{ride['subclass']}"
        if key in ride_counts:
            ride_counts[key] += 1

    rides_vector = np.array([
        normalize_with_config(ride_counts[f'{subtype}_{color}'], 'num_rides')
        for subtype in ride_subtypes
        for color in colors
    ] + [
        # Aggregate metrics
        round(min(r['uptime'] for r in state['rides']), 2) if state['rides'] else 1.0,
        normalize_with_config(sum(r['operating_cost'] for r in state['rides']), 'total_operating_cost'),
        normalize_with_config(sum(r['revenue_generated'] for r in state['rides']), 'total_revenue_generated'),
        normalize_with_config(state['state']['park_excitement'], 'total_excitement'),
        normalize_with_config(sum(r['intensity'] for r in state['rides']) / max(len(state['rides']), 1), 'avg_intensity'),
        normalize_with_config(sum(r['capacity'] for r in state['rides']), 'total_capacity'),
        normalize_with_config(sum(r['avg_wait_time'] for r in state['rides']) / max(len(state['rides']), 1), 'avg_wait_time'),
    ], dtype=np.float64)

    # ===== SHOPS VECTOR (15 values) =====
    # Format: [drink: 4 colors, food: 4 colors, specialty: 4 colors,
    #          total_revenue_generated, total_operating_cost, min_uptime]
    shop_subtypes = ['drink', 'food', 'specialty']

    shop_counts = {}
    for subtype in shop_subtypes:
        for color in colors:
            shop_counts[f"{subtype}_{color}"] = 0

    # Count shops by subtype and color
    for shop in state['shops']:
        key = f"{shop['subtype']}_{shop['subclass']}"
        if key in shop_counts:
            shop_counts[key] += 1

    shops_vector = np.array([
        normalize_with_config(shop_counts[f'{subtype}_{color}'], 'num_shops')
        for subtype in shop_subtypes
        for color in colors
    ] + [
        # Aggregate metrics
        normalize_with_config(sum(s['revenue_generated'] for s in state['shops']), 'total_revenue_generated_shops'),
        normalize_with_config(sum(s['operating_cost'] for s in state['shops']), 'total_operating_cost_shops'),
        round(min(s['uptime'] for s in state['shops']), 2) if state['shops'] else 1.0,
    ], dtype=np.float64)

    # ===== STAFF VECTOR (14 values) =====
    # Format: [janitor: 4 colors, mechanic: 4 colors, specialist: 4 colors,
    #          total_salary_paid, total_operating_cost]
    staff_subtypes = ['janitor', 'mechanic', 'specialist']

    staff_counts = {}
    for subtype in staff_subtypes:
        for color in colors:
            staff_counts[f"{subtype}_{color}"] = 0

    # Count staff by subtype and color
    for staff_member in state['staff']:
        key = f"{staff_member['subtype']}_{staff_member['subclass']}"
        if key in staff_counts:
            staff_counts[key] += 1

    # Calculate total staff operating cost
    total_staff_operating_cost = sum(staff_member['operating_cost'] for staff_member in state['staff'])

    staff_vector = np.array([
        normalize_with_config(staff_counts[f'{subtype}_{color}'], 'num_staff')
        for subtype in staff_subtypes
        for color in colors
    ] + [
        normalize_with_config(state['state']['total_salary_paid'], 'total_salary_paid'),
        normalize_with_config(total_staff_operating_cost, 'total_operating_cost')
    ], dtype=np.float64)

    # ===== GUESTS VECTOR (7 values) =====
    guests_vector = np.array([
        normalize_with_config(state['guestStats']['total_guests'], 'total_guests'),
        normalize_with_config(state['guestStats']['avg_money_spent'], 'avg_money_spent'),
        normalize_with_config(state['guestStats']['avg_steps_taken'], 'avg_time_in_park'),
        normalize_with_config(state['guestStats']['avg_rides_visited'], 'avg_rides_visited'),
        normalize_with_config(state['guestStats']['avg_food_shops_visited'], 'avg_food_shops_visited'),
        normalize_with_config(state['guestStats']['avg_drink_shops_visited'], 'avg_drink_shops_visited'),
        normalize_with_config(state['guestStats']['avg_specialty_shops_visited'], 'avg_specialty_shops_visited')
    ], dtype=np.float64)

    # ===== PARK VECTOR (10 values) =====
    profit = state['state']['revenue'] - state['state']['expenses']

    # Calculate min cleanliness
    cleanliness = []
    for terrain in state['terrain']:
        if terrain['type'] == 'path':
            cleanliness.append(terrain['cleanliness'])
    for attraction in state['rides'] + state['shops']:
        cleanliness.append(attraction['cleanliness'])
    min_cleanliness = min(cleanliness) if cleanliness else 1.0

    # Research speed mapping
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

    # Available entities (9 entity types × 4 colors = 36 values)
    all_entity_types = ATTRACTION_TYPES + ['janitor', 'mechanic', 'specialist']
    available_entities = []
    for entity_type in all_entity_types:
        for entity_color in ATTRACTION_COLORS:
            if entity_type in state['state']['available_entities'] and entity_color in state['state']['available_entities'][entity_type]:
                available_entities.append(1.0)
            else:
                available_entities.append(0.0)

    park_vector = np.array([
        normalize_with_config(state['state']['step'], 'step'),
        normalize_with_config(state['state']['horizon'], 'horizon'),
        normalize_with_config(state['state']['value'], 'value'),
        normalize_with_config(state['state']['money'], 'money'),
        normalize_with_config(state['state']['revenue'], 'revenue'),
        normalize_with_config(state['state']['expenses'], 'expenses'),
        1.0 if profit > 0 else 0.0,  # profit sign
        normalize_with_config(abs(profit), 'profit'),
        normalize_with_config(state['state']['park_rating'], 'park_rating'),
        round(min_cleanliness, 2),
    ], dtype=np.float64)

    return {
        'rides_vector': rides_vector,
        'shops_vector': shops_vector,
        'staff_vector': staff_vector,
        'guests_vector': guests_vector,
        'park_vector': park_vector
    }
