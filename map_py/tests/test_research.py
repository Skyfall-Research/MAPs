"""Misc tests for MiniAmusementPark, currently regression tests that don't
have a better home yet.
"""
import unittest
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.tests.states import COMPLEX_ENV4_STATE, EMPTY_ENV4_STATE, TEST_PROFIT_NO_RIDES
from map_py.tests.utils import test_state_equality_after_set, CONFIG
import copy 
import json
from itertools import chain, combinations

def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

GRID_SIZE = CONFIG['park_size']  

HOST = 'localhost'
PORT = '3000'

# Note: order matters.; rides, shops, staff
RESEARCH_TOPICS = ['carousel', 'ferris_wheel', 'roller_coaster', 'drink', 'food', 'specialty', 'janitor', 'mechanic', 'specialist']

class TestThemeParkResearch(unittest.TestCase):
    def test_full_queue_unlimited_money(self):
        map = MiniAmusementPark(host=HOST, port=PORT)

        start_state = copy.deepcopy(COMPLEX_ENV4_STATE)
        start_state['state']['money'] = 999999999

        yellow_available = {'carousel': ['yellow'], 'ferris_wheel': ['yellow'], 'roller_coaster': ['yellow'], 
                            'drink': ['yellow'], 'food': ['yellow'], 'specialty': ['yellow'],
                            'janitor': ['yellow'], 'mechanic': ['yellow'], 'specialist': ['yellow'],}

        queues = [list(x) for x in powerset(RESEARCH_TOPICS) if len(x) > 0]
        for queue in queues:
            for level, speed in CONFIG['research']['speed_progress'].items():
                if speed == 0:
                    continue 

                _, info = map.set(start_state) 
                assert 'error' not in info, info 

                expected_start = copy.deepcopy(yellow_available)
                if speed >= CONFIG['research']['points_required']['blue']:
                    expected_start[queue[0]].append('blue')
        
                action = f"set_research(research_speed={repr(level)}, research_topics={repr(queue)})"
                obs, reward, terminated, truncated, info = map.step(action)
                assert 'error' not in info, (info, action)
                assert obs.research_speed == level, f'After {action} Expected {level}, got {obs.research_speed}\n{info}\n{json.dumps(map.get_raw_state())}'
                assert obs.research_topics == queue, f'Expected: {queue}\nActual: {obs.research_topics}'
                assert obs.available_entities == expected_start, obs.available_entities
                # Check nothing new is available, or the correct counter is 0
                assert not obs.new_entity_available or \
                        (level == 'fast' and obs.fast_days_since_last_new_entity == 0) or \
                        (level == 'medium' and obs.fast_days_since_last_new_entity == 0 and obs.new_entity_available) or \
                        (level == 'slow' and obs.fast_days_since_last_new_entity == 0 and obs.new_entity_available)
                assert obs.new_entity_available == (speed >= CONFIG['research']['points_required']['blue']), obs.new_entity_available


    def test_full_queue_unlimited_money2(self):
        """Same test, but loading the state from a config file."""
        for diff in ['hard', 'medium']:
            map = MiniAmusementPark(host=HOST, port=PORT)
            map.update_settings(layout='old_layout', difficulty=diff, starting_money=99999999, horizon=1000)
            map.reset()

            yellow_available = {'carousel': ['yellow'], 
                                'ferris_wheel': ['yellow'], 
                                'roller_coaster': ['yellow'], 
                                'janitor': ['yellow'],
                                'mechanic': ['yellow'],
                                'specialist': ['yellow'],
                                'drink': ['yellow'], 
                                'food': ['yellow'], 
                                'specialty': ['yellow']}

            queues = [list(x) for x in powerset(RESEARCH_TOPICS) if len(x) > 0]
            for queue in queues:
                for level, speed in CONFIG['research']['speed_progress'].items():
                    if speed == 0:
                        continue 

                    map.reset()

                    expected_start = copy.deepcopy(yellow_available)
                    if speed >= CONFIG['research']['points_required']['blue']:
                        expected_start[queue[0]].append('blue')
            
                    action = f"set_research(research_speed={repr(level)}, research_topics={repr(queue)})"
                    obs, reward, terminated, truncated, info = map.step(action)
                    assert 'error' not in info, (info, action)
                    assert obs.research_speed == level, f'Expected {level}, got {obs.research_speed}. Difficulty {diff}'
                    assert sorted(obs.research_topics) == sorted(queue), f'Expected: {queue} Actual: {obs.research_topics}'
                    assert obs.available_entities == expected_start, f'Expected: {expected_start} Actual: {obs.available_entities}'
                    assert not obs.new_entity_available or \
                        (level == 'fast' and obs.fast_days_since_last_new_entity == 0) or \
                        (level == 'medium' and obs.fast_days_since_last_new_entity == 0 and obs.new_entity_available) or \
                        (level == 'slow' and obs.fast_days_since_last_new_entity == 0 and obs.new_entity_available)
                    assert obs.new_entity_available == (speed >= CONFIG['research']['points_required']['blue']), obs.new_entity_available


if __name__ == "__main__":
       #input("Once the server is running at port 3000, then press any key.\nie., from the map root directory run: \nnode server.js\n")
       unittest.main()





