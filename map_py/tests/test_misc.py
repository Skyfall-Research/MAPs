"""Misc tests for MiniAmusementPark, currently regression tests that don't
have a better home yet.
"""
import unittest
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.tests.states import COMPLEX_ENV4_STATE, EMPTY_ENV4_STATE, TEST_PROFIT_NO_RIDES
from map_py.tests.utils import test_state_equality_after_set, CONFIG
from map_py.shared_constants import LAYOUTS_DIR
import copy 
import random 

import yaml 

with open(LAYOUTS_DIR/'old_layout.yaml', 'r') as f:
    OLD_LAYOUT = yaml.safe_load(f)

GRID_SIZE = 20  # Hard-coded in MiniAmusementPark
HOST = 'localhost'
PORT = '3000'

class TestStocker(unittest.TestCase):
    def test_non_negative_inventory(self):
        map = MiniAmusementPark(host=HOST, 
                              port=PORT, 
                              layout='old_layout',
                              difficulty="easy")
        _, info = map.reset()
        assert 'error' not in info 
        start_state = copy.deepcopy(COMPLEX_ENV4_STATE)
        start_state['state']['money'] = 9999999
        start_state['shops'][0]['order_quantity'] = 1
        start_state['shops'][1]['order_quantity'] = 1
        start_state['difficulty'] = "easy"
        for topic in start_state['state']['available_entities']:
            start_state['state']['available_entities'][topic].extend(['blue', 'green', 'red'])

        for _ in range(20):
            _, info = map.set(start_state)
            assert 'error' not in info, info


            for action in ['place(type="ride",x=0,y=2,subtype="roller_coaster", subclass="red",price=40)', 
                        'place(type="staff", x=0,y=2,subtype="specialist",subclass="blue")']:
                _, _, _, _, info = map.step(action)
                assert 'error' not in info, info

            for _ in range(40):
                obs, _, _, _, info = map.step("wait()")
                assert 'error' not in info 

                raw = map.get_raw_state()
                assert all(s['inventory'] >= 0 for s in raw['shops']), raw['shop']

class TestMisc(unittest.TestCase):
    def test_observation(self):
        map = MiniAmusementPark(host=HOST, 
                              port=PORT, 
                              layout='old_layout', 
                              return_detailed_guest_info=True)
        _, info = map.reset()
        obs, raw = map.get_observation_and_raw_state() 
        # Shouldn't get oracle info
        assert not hasattr(obs.guests, "avg_hunger"), obs.guests #or obs.guests.avg_hunger is None
        assert not hasattr(obs.guests, "avg_thirst") #or obs.guests.avg_thirst is None

        obs, _, _, _, info = map.step("wait()")
        assert 'error' not in info 

        # Shouldn't get oracle info
        assert not hasattr(obs.guests, "avg_hunger") #or obs.guests.avg_hunger is None
        assert not hasattr(obs.guests, "avg_thirst") #or obs.guests.avg_thirst is None

    def test_observation2(self):
        map = MiniAmusementPark(host=HOST, 
                              port=PORT, 
                              layout='old_layout', 
                              return_detailed_guest_info=False)
        _, info = map.reset()
        obs, raw = map.get_observation_and_raw_state() 
        # Shouldn't get oracle info
        assert not hasattr(obs.guests, "avg_hunger"), obs.guests #or obs.guests.avg_hunger is None
        assert not hasattr(obs.guests, "avg_thirst") #or obs.guests.avg_thirst is None

        obs, _, _, _, info = map.step("wait()")
        assert 'error' not in info 

        # Shouldn't get oracle info
        assert not hasattr(obs.guests, "avg_hunger") #or obs.guests.avg_hunger is None
        assert not hasattr(obs.guests, "avg_thirst") #or obs.guests.avg_thirst is None



    def test_reset(self):
        #print("TESTING RESET")
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        #print(info)
        map.get_observation_and_raw_state()
        #print("RESET DONE")

    def test_set(self):
        map_game = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout')
        map_game.reset()
        state = map_game.get_raw_state()
        #print(state)
        map_game2 = MiniAmusementPark(host=HOST, port=PORT)
        map_game2.set(state) 
        _, state = map_game2.get_observation_and_raw_state()

        #print("SET DONE")
        
    def test_survey_goes_through(self):
        map_game = MiniAmusementPark(host=HOST, port=PORT)
        START = copy.deepcopy(COMPLEX_ENV4_STATE)
        START['rides'] = []
        assert len(START['shops']) > 0  # Not part of the test, just a check
        START['state']['money'] = 3001  # We'll incur operating expense from
        
        # Check we have expenses if we wait
        map_game.set(START)
        obs, reward, _, _, info = map_game.step("wait()")
        assert 'error' not in info, info 
        assert reward < 0
        assert obs.money < 3001

        # Check we have expenses if we survey
        map_game.set(START)
        obs, reward, _, _, info = map_game.step('survey_guests(num_guests=3)')
        assert 'error' not in info, info 
        assert obs.money < 3001
        assert reward <= 3 * CONFIG['per_guest_survey_cost'], reward
        assert len(obs.guest_survey_results.list_of_results) == 0, obs.guest_survey_results.list_of_results

        # Check we get the right number of guests if there are guests
        START = copy.deepcopy(COMPLEX_ENV4_STATE)
        assert len(START['rides']) > 0  # Not part of the test, just a check
        START['state']['money'] = 3001
        map_game.set(START)
        obs, reward, _, _, info = map_game.step('survey_guests(num_guests=3)')
        assert 'error' not in info, info 
        assert len(obs.guest_survey_results.list_of_results) == 3, obs.guest_survey_results.list_of_results



class TestCreation(unittest.TestCase):

    def test_easy_disables_preferences(self):
        for i in range(3):
            map = MiniAmusementPark(host=HOST, port=PORT, 
                                  layout='old_layout')
            map.reset()
            raw = map.get_raw_state()
            assert raw['difficulty'] == 'easy'
            assert raw['guest_preferences'] == ["no preferences"]

    def test_non_easy_disables_preferences(self):
        for diff in ['easy', 'medium']:
            for i in range(3):
                map = MiniAmusementPark(host=HOST, port=PORT, 
                                      layout='old_layout')
                map.update_settings(difficulty=diff)
                map.reset()
                raw = map.get_raw_state()
                assert raw['difficulty'] == diff, raw['difficulty']
                expected_prefs = OLD_LAYOUT['preferences'][i] if diff == 'hard' else ['no preferences']
                assert raw['guest_preferences'] == expected_prefs, (diff, expected_prefs, raw['guest_preferences'])
 

class TestThemeParkSemanticErrors(unittest.TestCase):

    def test_action_sequence(self):
        """Check a simple action sequence can run without crashing."""
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout')
        _, info = map.reset()
        assert 'error' not in info

        CMDS = [
            "set_research(research_speed='fast', research_topics=['carousel'])",
            "wait()",
            "wait()",
            "wait()",
            "wait()",
            "wait()",
            "wait()",
            "wait()",
            "wait()",
            "wait()",
            "wait()",
            "place(x=1, y=2, type='ride', subtype='carousel', subclass='blue', price=2)",
            "place(x=3, y=4, type='shop', subtype='food', subclass='yellow', price=6, order_quantity=200)",
            "place(type='staff', subtype='janitor', subclass='blue', x=2, y=2)",
            "place(x=3, y=3, type='shop', subtype='specialty', subclass='yellow', price=15, order_quantity=300)",
            "wait()",
            "wait()",
            "wait()",
            "place(x=3, y=3, type='ride', subtype='ferris_wheel', subclass='yellow', price=3)",
        ]

        while CMDS:
             action = CMDS.pop(0)
             map.observe()
             map.step(action)       

    def test_increase_ticket_price(self) -> None:
        # reset park to a known non-random state
        # TODO: Update when randomization is possible
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout')
        _, info = map.reset()
        assert 'error' not in info

        _, info = map.set(COMPLEX_ENV4_STATE) 
        assert 'error' not in info 
        obs, state = map.get_observation_and_raw_state()

        expected = copy.deepcopy(COMPLEX_ENV4_STATE)
        # NOTE: we aren't meant to be loading guests
        expected['guests'] = []
        
        test_state_equality_after_set(expected, state)

        # Take an action
        ride_at_pos = [r for r in obs.rides.ride_list if r.x == 1 and r.y == 2]
        assert len(ride_at_pos) == 1
        r = ride_at_pos[0]
        _,_,_,_,info = map.step(f'modify(type="ride", x=1, y=2, price=3)')
        assert 'error' not in info, info

        # Observe updated state
        _, state = map.get_observation_and_raw_state()
        target_ride = [x for x in state['rides'] if x['x'] == 1 and x['y'] == 2]
        assert len(target_ride) == 1
        target_ride = target_ride[0]
        assert target_ride['ticket_price'] == 3, f'Expected ticket price 3 but got {target_ride['ticket_price']}'

        _,_,_,_,info = map.step('modify(type="ride", x=7, y=7, price=3)')
        assert 'error' in info, info

    def test_no_guests_in_raw(self):
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=False)
        _, info = map.reset()
        assert 'error' not in info

        state, info = map.reset()
        assert 'error' not in info
        _, info = map.set(COMPLEX_ENV4_STATE) 
        assert 'error' not in info 
        map.step('wait()')
        obs, raw = map.get_observation_and_raw_state()
        assert 'guests' not in raw, raw['guests']
    
    def test_no_profit_without_rides(self):
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout')
        _, info = map.reset()
        assert 'error' not in info

        _, info = map.set(TEST_PROFIT_NO_RIDES) 
        assert 'error' not in info 
        obs, reward, terminated, truncated, info = map.step('place(x=18,y=3,type=\"shop\",subtype=\"drink\",subclass=\"blue\",price=5,order_quantity=150)')
        assert reward == 0
        assert 'error' in info


if __name__ == "__main__":
       #input("Once the server is running at port 3000, then press any key.\nie., from the map root directory run: \nnode server.js\n")
       unittest.main()

