"""MiniAmusementPark Tests focussed on pathing.
"""
import unittest
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.observations_and_actions.pydantic_obs import FullParkObs, ParkObservabilityMode
from map_py.tests.states import COMPLEX_ENV4_STATE, EMPTY_ENV4_STATE
from map_py.tests.utils import CONFIG
import copy 
import random 

REACHABLE_LOCS = [(0,2)]
UNREACHABLE_LOCS = [(0,10), (10, 18), (3,0)]  # Guests cannot travel on diagonals
ALMOST_REACHABLE_LOCS = [((0,2), (0,3))]
RIDE_LOC = (17, 19)
OTHER_LOC = (2, 0)
EXIT = (19, 19)

END_OF_DAY_CODE=1  # Enum for guest leaving due to end of day.

# Shortest path to exit
STEPS_TO_EXIT = 38

HOST = 'localhost'
PORT = '3000'

def at_exit(guest: dict) -> bool:
    return (guest['x'], guest['y']) == EXIT

def assert_unoccupied(raw: dict, x:int, y: int):
    assert isinstance(raw, dict)
    assert not is_occupied(raw, x, y)

def is_occupied(raw: dict, x: int, y: int) -> bool:
    return len([r for r in raw['rides'] if (r['x'] == x and r['y'] == y)]) != 0 or \
        len([s for s in raw['shops'] if (s['x'] == x and s['y'] == y)]) != 0

class TestPathing(unittest.TestCase):
    # TODO: Once implemented, test guest pathing will not reach unreachable buildings
    # Currently just raises an exception
    def test_unreachable_build_impossible(self):
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        food_price = random.randint(1, CONFIG['shops']['food']['yellow']['max_item_price'])
        spec_price = random.randint(1, CONFIG['shops']['specialty']['yellow']['max_item_price'])
        drink_price = random.randint(1, CONFIG['shops']['drink']['yellow']['max_item_price'])
        car_price = random.randint(1, CONFIG['rides']['carousel']['yellow']['max_ticket_price'])

        variants = ["place(x={}, y={}, type='shop', subtype='food', subclass='yellow', price="+str(food_price)+", order_quantity=200)",
                    "place(x={}, y={}, type='shop', subtype='specialty', subclass='yellow', price="+str(spec_price)+", order_quantity=300)",
                    "place(x={}, y={}, type='shop', subtype='drink', subclass='yellow', price="+ str(drink_price)+", order_quantity=150)",
                    "place(x={}, y={}, type='ride', subtype='carousel', subclass='yellow', price="+str(car_price)+")"]

        for variant in variants:
            for x,y in UNREACHABLE_LOCS:
                # Set to empty park
                map.set(raw_state=EMPTY_ENV4_STATE) 
                _,_,_,_,info = map.step(variant.format(x,y))

                assert 'Invalid placement' in info['error']['message'], info 

                # Observe raw & normal obs
                _, raw = map.get_observation_and_raw_state()
                assert_unoccupied(raw, x, y)


    def test_unreachable_build_impossible2(self):
        """Make sure can't build a chain of shops with the last being unreachable."""

        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        food_price = random.randint(1, CONFIG['shops']['food']['yellow']['max_item_price'])
        spec_price = random.randint(1, CONFIG['shops']['specialty']['yellow']['max_item_price'])

        steps = ["place(x=0, y=2, type='shop', subtype='food', subclass='yellow',  price="+str(food_price)+", order_quantity=200)",
                 "place(x=0, y=3, type='shop', subtype='specialty', subclass='yellow', price="+str(spec_price)+", order_quantity=300)",]

        for i, step in enumerate(steps):
            # Set to empty park
            map.set(raw_state=EMPTY_ENV4_STATE) 
            _,_,_,_,info = map.step(step)

            if i < len(steps) - 1:
                assert 'error' not in info, info  
            else:
                assert 'Invalid placement' in info['error']['message'], info

                # Observe raw & normal obs
                _, raw = map.get_observation_and_raw_state()
                assert isinstance(raw, dict)
                assert_unoccupied(raw, 0, 3)

    # TODO: When implemented, test staff pathing to unreachable objects
    # TODO: Test that moving an attraction to a reachable location will result in traffic
    # TODO: Test that moving an attraction to an unreachable location will stop traffic, and won't freeze guests.

    def test_unreachable_move_impossible(self):
        """Test that it is impossible to move an attraction to an unreachable location"""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        food_price = random.randint(1, CONFIG['shops']['food']['yellow']['max_item_price'])
        spec_price = random.randint(1, CONFIG['shops']['specialty']['yellow']['max_item_price'])
        drink_price = random.randint(1, CONFIG['shops']['drink']['yellow']['max_item_price'])
        car_price = random.randint(1, CONFIG['rides']['carousel']['yellow']['max_ticket_price'])

        variants = [("place(x={}, y={}, type='shop', subtype='food', subclass='yellow', price="+str(food_price)+", order_quantity=200)", 'shop'),
                    ("place(x={}, y={}, type='shop', subtype='specialty', subclass='yellow', price="+str(spec_price)+", order_quantity=300)", 'shop'),
                    ("place(x={}, y={}, type='shop', subtype='drink', subclass='yellow', price="+ str(drink_price)+", order_quantity=150)", 'shop'),
                    ("place(x={}, y={}, type='ride', subtype='carousel', subclass='yellow', price="+str(car_price)+")", 'ride')]

        for variant, attr_type in variants:
            for x,y in UNREACHABLE_LOCS:
                # Set to empty park
                map.set(raw_state=EMPTY_ENV4_STATE) 
                # Place building at valid location
                obs,_,_,_,info = map.step(variant.format(*REACHABLE_LOCS[0]))
                assert 'error' not in info, info 

                # Get building attributes for move command
                obs = map.observe()
                if attr_type == 'ride':
                    assert obs.rides is not None and obs.rides.ride_list is not None
                    building = next((r for r in obs.rides.ride_list if r.x == REACHABLE_LOCS[0][0] and r.y == REACHABLE_LOCS[0][1]), None)
                else:
                    assert obs.shops is not None and obs.shops.shop_list is not None
                    building = next((s for s in obs.shops.shop_list if s.x == REACHABLE_LOCS[0][0] and s.y == REACHABLE_LOCS[0][1]), None)
                
                assert building is not None, f"Building not found at ({REACHABLE_LOCS[0][0]}, {REACHABLE_LOCS[0][1]})"
                
                # Move to invalid location
                _,_,_,_,info = map.step(f"move(type='{attr_type}', subtype='{building.subtype}', subclass='{building.subclass}', x={REACHABLE_LOCS[0][0]}, y={REACHABLE_LOCS[0][1]}, new_x={x}, new_y={y})")
                assert 'error' in info, info
                # TODO: Improve this error message
                assert 'Invalid placement' in info['error']['message'], info 

                # Observe raw & normal obs
                _, raw = map.get_observation_and_raw_state()
                assert isinstance(raw, dict)
                assert_unoccupied(raw, x, y)
                #assert not raw['grid'][REACHABLE_LOCS[0][0]][REACHABLE_LOCS[0][1]].startswith('empty-'), raw['grid'][x][y]
                assert is_occupied(raw, REACHABLE_LOCS[0][0], REACHABLE_LOCS[0][1])

    # TODO: When implemented, test staff hiring and movement to non-pathable locations
    # TODO: Test staff get "stuck" if off-path
    # TODO: Test staff get "unstuck" once put back on the path
    # TODO: Test deleting path doesn't break things
    """
    def test_path_creation(self):
        for path_pos, ride_pos in ALMOST_REACHABLE_LOCS:
            # Confirm intended position is not reachable
            # Set to empty park
            map.set(env_id=self.ENV_ID, state=EMPTY_ENV4_STATE) 
            # Create a ride, otherwise no guests will show up
            _,_,_,_,info = map.step(f"place(x={ride_pos[0]}, y={ride_pos[1]}, type='ride', subtype='carousel', subclass='yellow', price=2)", env_id=self.ENV_ID)
            assert 'error' in info

            # Make sure it becomes reachable with a path
            # Set to empty park
            map.set(env_id=self.ENV_ID, state=EMPTY_ENV4_STATE) 
            # Place path
            _,_,_,_,info = map.step(f"place_path_tile(x={path_pos[0]}, y={path_pos[1]})", env_id=self.ENV_ID)
            assert 'error' not in info
            # Create a ride, otherwise no guests will show up
            _,_,_,_,info = map.step(f"place(x={ride_pos[0]}, y={ride_pos[1]}, type='ride', subtype='carousel', subclass='yellow', price=2)", env_id=self.ENV_ID)
            assert 'error' not in info

            # Observe raw & normal obs
            obs = map.observe(self.ENV_ID)
            assert isinstance(obs, Park)
            _, raw = map.get_observation_and_raw_state(self.ENV_ID)
            assert isinstance(raw, dict)

            # Check raw state is consistent with guest just leaving
            assert len(raw['guests']) > 0
            for guest in raw['guests']:
                assert guest["steps_at_exit"] >= STEPS_TO_EXIT  # Takes at least this long to leave
                assert at_exit(guest)

                ZERO_KEYS = ['drink_shops_visited', 'food_shops_visited', 'specialty_shops_visited']

                if guest['money_spent'] > 0:
                    assert guest['rides_visited'] > 0
                else:
                    ZERO_KEYS += ['money_spent', 'rides_visited']

                for key in ZERO_KEYS:
                    assert guest[key] == 0

            # Double check guest count stats match
            assert obs.guests.total_guests == len(raw['guests'])

            # Check non-raw state is consistent with guest just leaving
            assert obs.guests.avg_steps_taken >= STEPS_TO_EXIT
            zero_keys = ['avg_drink_shops_visited', 'avg_food_shops_visited', 'avg_specialty_shops_visited']
            if obs.guests.avg_money_spent > 0:
                assert obs.guests.avg_rides_visited > 0
            else:
                zero_keys += ['avg_money_spent', 'avg_rides_visited', ]

            for attr in zero_keys:
                assert getattr(obs.guests, attr) == 0

            assert obs.guests.avg_rides_visited > 0, "If this fails, there's probably (thought not certainly) something wrong"
    """
            
    # TODO: Test that selling an attraction doesn't cause problems (might not be possible to tell with the current API)

    # TODO: Test pathing doesn't break after reset, or set to same state (steps at exit > 0)

    # TODO: Test pathing doesn't break after reset, or set to same state (steps at exit > 0)


if __name__ == '__main__':
    unittest.main()