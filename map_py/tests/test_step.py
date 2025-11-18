

"""Misc tests for MiniAmusementPark, currently regression tests that don't
have a better home yet.
"""
import unittest
from map_py.mini_amusement_park import MiniAmusementPark, FullParkObs 
from map_py.tests.states import COMPLEX_ENV4_STATE, EMPTY_ENV4_STATE
from map_py.tests.test_pathing import is_occupied
import copy 
from map_py.tests.utils import test_pydantic_state_equality_after_set, CONFIG
import random 

GRID_SIZE = 20  # Hard-coded in MiniAmusementPark

HOST = 'localhost'
PORT = '3000'

def is_occupied_by(raw, x, y, target_type) -> bool:
    if 'ride' in target_type:
        return len([r for r in raw['rides'] if (r['x'] == x and r['y'] == y)]) != 0
    else:
        assert 'shop' in target_type
        return len([s for s in raw['shops'] if (s['x'] == x and s['y'] == y)]) != 0

class TestThemeParkSemanticErrors(unittest.TestCase):
    def test_step_missing_args(self) -> None:
        """Check action fails if missing arguments"""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        # Check this spot is free, this isn't a correctness check, just making sure the test itself is OK
        assert not is_occupied(map.get_raw_state(), 0, 2)

        CMD = "place_ride(x=0, y=2, subtype='carousel', excitement=3, capacity=5, ticketPrice=3)"
        step_obs, reward, done, trunc, info = map.step(CMD)

        assert 'error' in info, info 
        

    def test_step_excess_args(self) -> None:
        """Check action fails if missing arguments"""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        # Check this spot is free, this isn't a correctness check, just making sure the test itself is OK
        assert not is_occupied(map.get_raw_state(), 0, 2)

        CMD = "place(type='staff', subtype='janitor', subclass='yellow', x=0, y=2, exceess='exceess should not be!')"
        step_obs, reward, done, trunc, info = map.step(CMD)

        assert 'error' in info, info 


    def test_valid_move(self):
        """Check store can be moved to a valid location."""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info
        
        REACHABLE_LOCS = [(2,0), (8,4)]
        food_price = random.randint(1, CONFIG['shops']['food']['yellow']['max_item_price'])
        spec_price = random.randint(1, CONFIG['shops']['specialty']['yellow']['max_item_price'])
        drink_price = random.randint(1, CONFIG['shops']['drink']['yellow']['max_item_price'])
        car_price = random.randint(1, CONFIG['rides']['carousel']['yellow']['max_ticket_price'])

        variants = ["place(x={}, y={}, type='shop', subtype='food', order_quantity=100,  subclass='yellow', price="+str(food_price)+")",
                    "place(x={}, y={}, type='shop', subtype='specialty', order_quantity=300, subclass='yellow', price="+str(spec_price)+")",
                    "place(x={}, y={}, type='shop', subtype='drink', order_quantity=150, subclass='yellow', price="+ str(drink_price)+")",
                    "place(x={}, y={}, type='ride', subtype='carousel', subclass='yellow', price="+str(car_price)+")"]

        for i, variant in enumerate(variants):
            target_type = 'shop' if i != 3 else 'ride'
            ori_x, ori_y = 0, 2
            for x,y in REACHABLE_LOCS:
                # Set to empty park
                map.set(EMPTY_ENV4_STATE) 
                
                # Place building at valid location
                obs,_,_,_,info = map.step(variant.format(ori_x, ori_y))
                assert 'error' not in info, info 

                # Get building attributes for move command
                obs = map.observe()
                if target_type == 'ride':
                    assert obs.rides is not None and obs.rides.ride_list is not None
                    building = next((r for r in obs.rides.ride_list if r.x == ori_x and r.y == ori_y), None)
                else:
                    assert obs.shops is not None and obs.shops.shop_list is not None
                    building = next((s for s in obs.shops.shop_list if s.x == ori_x and s.y == ori_y), None)
                
                assert building is not None, f"Building not found at ({ori_x}, {ori_y})"
                
                # Move to valid location
                _,_,_,_,info = map.step(f"move(type='{target_type}', subtype='{building.subtype}', subclass='{building.subclass}', x={ori_x}, y={ori_y}, new_x={x}, new_y={y})")
                assert 'error' not in info, info 


                # Observe raw & check grid and store location
                _, raw = map.get_observation_and_raw_state()
                # Check grid
                assert isinstance(raw, dict)
                assert not is_occupied(raw, ori_x, ori_y)
                assert is_occupied_by(raw, x, y, target_type)

                # Check raw location
                matches = [tar for tar in raw[target_type+"s"] if tar['x'] == x and tar['y'] == y]
                assert len(matches) == 1

                matches = [tar for tar in raw[target_type+"s"] if tar['x'] == ori_x and tar['y'] == ori_y]
                assert len(matches) == 0

                # Check pydantic location
                obs = map.observe()
                assert isinstance(obs, FullParkObs)
                targets = getattr(obs, target_type+"s")
                targets = getattr(targets, f"{target_type}_list")
                matches = [tar for tar in targets if tar.x == x and tar.y == y]
                assert len(matches) == 1
                matches = [tar for tar in targets if tar.x == ori_x and tar.y == ori_y]
                assert len(matches) == 0


    def test_valid_sell(self):
        """Check store can be moved to a valid location."""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        REACHABLE_LOCS = [(2,0), (8,4)]
        food_price = random.randint(1, CONFIG['shops']['food']['yellow']['max_item_price'])
        spec_price = random.randint(1, CONFIG['shops']['specialty']['yellow']['max_item_price'])
        drink_price = random.randint(1, CONFIG['shops']['drink']['yellow']['max_item_price'])
        car_price = random.randint(1, CONFIG['rides']['carousel']['yellow']['max_ticket_price'])

        variants = [("place(x={}, y={}, type='shop', subtype='food', order_quantity=100,  subclass='yellow', price="+str(food_price)+")", "subtype='food', subclass='yellow'"),
                    ("place(x={}, y={}, type='shop', subtype='specialty', order_quantity=300, subclass='yellow', price="+str(spec_price)+")", "subtype='specialty', subclass='yellow'"),
                    ("place(x={}, y={}, type='shop', subtype='drink', order_quantity=150, subclass='yellow', price="+ str(drink_price)+")", "subtype='drink', subclass='yellow'"),
                    ("place(x={}, y={}, type='ride', subtype='carousel', subclass='yellow', price="+str(car_price)+")", "subtype='carousel', subclass='yellow'")]

        for i, (variant, var_args) in enumerate(variants):
            target_type = 'shop' if i != 3 else 'ride'
            ori_x, ori_y = 0, 2
            for x,y in REACHABLE_LOCS:
                # Set to empty park
                map.set(raw_state=EMPTY_ENV4_STATE) 
                
                # Place building at valid location
                obs,_,_,_,info = map.step(variant.format(ori_x, ori_y))
                assert 'error' not in info, info 

                # Sell
                _,_,_,_,info = map.step(f"remove(x={ori_x}, y={ori_y}, {var_args}, type='{target_type}')")
                assert 'error' not in info, info 


                # Observe raw & check grid and store location
                _, raw = map.get_observation_and_raw_state()
                # Check grid
                assert isinstance(raw, dict)
                assert not is_occupied(raw, ori_x, ori_y)

                # Check raw location
                matches = [tar for tar in raw[target_type+"s"] if tar['x'] == ori_x and tar[y] == ori_y]
                assert len(matches) == 0, matches 

                # Check pydantic location
                obs = map.observe()
                assert isinstance(obs, FullParkObs)
                targets = getattr(obs, target_type+"s")
                targets = getattr(targets, f"{target_type}_list")
                matches = [tar for tar in targets if tar.x == ori_x and tar.y == ori_y]
                assert len(matches) == 0, matches 
    
    def test_valid_sell_serial(self):
        """Check store can sold without impacting other stores."""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        REACHABLE_LOCS = [(2,0), (8,4)]

        food_price = random.randint(1, CONFIG['shops']['food']['yellow']['max_item_price'])
        spec_price = random.randint(1, CONFIG['shops']['specialty']['yellow']['max_item_price'])
        drink_price = random.randint(1, CONFIG['shops']['drink']['yellow']['max_item_price'])
        car_price = random.randint(1, CONFIG['rides']['carousel']['yellow']['max_ticket_price'])

        variants = [("place(x={}, y={}, type='shop', subtype='food', order_quantity=100,  subclass='yellow', price="+str(food_price)+")", "subtype='food', subclass='yellow'"),
                    ("place(x={}, y={}, type='shop', subtype='specialty', order_quantity=300, subclass='yellow', price="+str(spec_price)+")", "subtype='specialty', subclass='yellow'"),
                    ("place(x={}, y={}, type='shop', subtype='drink', order_quantity=150, subclass='yellow', price="+ str(drink_price)+")", "subtype='drink', subclass='yellow'"),
                    ("place(x={}, y={}, type='ride', subtype='carousel', subclass='yellow', price="+str(car_price)+")", "subtype='carousel', subclass='yellow'")]

        for i, (variant, var_args) in enumerate(variants):
            # Set to empty park
            start_state = copy.deepcopy(EMPTY_ENV4_STATE)
            start_state['state']['money'] = 9999
            map.set(raw_state=start_state) 
                
            target_type = 'shop' if i != 3 else 'ride'
            # Place building at valid location
            ori_x, ori_y = 0, 2
            obs,_,_,_,info = map.step(variant.format(ori_x, ori_y))
            assert 'error' not in info, info 
            for x,y in REACHABLE_LOCS:
                obs,_,_,_,info = map.step(variant.format(x, y))
                assert 'error' not in info, info

                _, obs_dir = map.get_observation_and_raw_state()
                assert len(obs_dir[target_type+"s"]) == 2

                # Sell
                _,_,_,_,info = map.step(f"remove(x={x}, y={y}, type='{target_type}', {var_args})")
                assert 'error' not in info, info 

                # Observe raw & check grid and store location
                _, raw = map.get_observation_and_raw_state()
                # Check grid
                assert isinstance(raw, dict)
                assert not is_occupied(raw, x, y)
                assert is_occupied(raw, ori_x, ori_y)
                assert is_occupied_by(raw, ori_x, ori_y, target_type)

                # Check raw location
                matches = [tar for tar in raw[target_type+"s"] if tar['x'] == x and tar['y'] == y]
                assert len(matches) == 0, matches 
                assert len(raw[target_type+"s"]) == 1

                # Check pydantic location
                obs = map.observe()
                assert isinstance(obs, FullParkObs)
                targets = getattr(obs, target_type+"s")
                targets = getattr(targets, f"{target_type}_list")
                assert len(targets) == 1 
                matches = [tar for tar in targets if tar.x == x and tar.y == y]
                assert len(matches) == 0, matches 

    def test_move_staff(self):
        """Test moving staff to a valid location"""
        variants = ["place(x={}, y={}, type='staff', subtype='janitor', subclass='yellow')",
                    "place(x={}, y={}, type='staff', subtype='mechanic', subclass='yellow')"]

        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        REACHABLE_LOCS = [(19, 19), (0,1), (8, 5)]

        for i, variant in enumerate(variants):
            for x,y in REACHABLE_LOCS:
                ori_x, ori_y = 0, 0
                staff_type = 'janitor' if i == 0 else 'mechanic'

                # Set to empty park
                map.set(raw_state=EMPTY_ENV4_STATE) 
                # Place staff at valid location
                obs,_,_,_,info = map.step(variant.format(ori_x, ori_y))
                assert 'error' not in info, info 

                assert isinstance(obs, FullParkObs)
                assert obs.staff is not None
                assert obs.staff.staff_list is not None
                matching_staff = [s for s in obs.staff.staff_list if s.subtype == staff_type]
                assert len(matching_staff) == 1
                staff_member = matching_staff[0]

                # Move to valid location
                _,_,_,_,info = map.step(f"move(type='staff', subtype='{staff_type}', subclass='{staff_member.subclass}', x={staff_member.x}, y={staff_member.y}, new_x={x}, new_y={y})")
                assert 'error' not in info, info 

                # Observe raw & normal obs
                _, raw = map.get_observation_and_raw_state()
                assert isinstance(raw, dict)
                matches = [s for s in raw['staff'] if s['x'] == ori_x and s['y'] == ori_y]
                assert len(matches) == 0
                matches = [s for s in raw['staff'] if s['x'] == x and s['y'] == y]
                assert len(matches) == 1

                obs = map.observe()
                assert isinstance(obs, FullParkObs)
                matches = [s for s in obs.staff.staff_list if s.x == x and s.y == y and s.subtype == staff_type]
                assert len(matches) == 1
                matches = [s for s in obs.staff.staff_list if s.x == ori_x and s.y == ori_y and s.subtype == staff_type]
                assert len(matches) == 0


    def test_fire_staff(self):
        """Test firing staff"""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        variants = ["place(x={}, y={}, type='staff', subtype='janitor', subclass='yellow')",
                    "place(x={}, y={}, type='staff', subtype='mechanic', subclass='yellow')"]

        REACHABLE_LOCS = [(19, 19), (0,1), (8, 5)]

        for i, variant in enumerate(variants):
            for x,y in REACHABLE_LOCS:
                ori_x, ori_y = 0, 0
                staff_type = 'janitor' if i == 0 else 'mechanic'

                # Set to empty park
                _, info = map.set(raw_state=EMPTY_ENV4_STATE) 
                assert 'error' not in info 

                # Place staff at valid location
                obs,_,_,_,info = map.step(variant.format(ori_x, ori_y))
                assert 'error' not in info, info 

                assert isinstance(obs, FullParkObs)
                matching_staff = [s for s in obs.staff.staff_list if s.subtype == staff_type]
                assert len(matching_staff) == 1
                staff_member = matching_staff[0]

                # Fire
                _,_,_,_,info = map.step(f"remove(type='staff', subtype='{staff_type}', subclass='{staff_member.subclass}', x={staff_member.x}, y={staff_member.y})")
                assert 'error' not in info, info 

                # Observe raw & normal obs
                _, raw = map.get_observation_and_raw_state()
                assert isinstance(raw, dict)
                matches = [s for s in raw['staff'] if s['x'] == x and s['y'] == y]
                assert len(matches) == 0

                obs = map.observe()
                assert isinstance(obs, FullParkObs)
                matches = [s for s in obs.staff.staff_list if s.x == x and s.y == y and s.subtype == staff_type]
                assert len(matches) == 0

    # TODO: Attempt to construct on top of the entrance or exit.

if __name__ == "__main__":
       #input("Once the server is running at port 3000, then press any key.\nie., from the map root directory run: \nnode server.js\n")
       unittest.main()


