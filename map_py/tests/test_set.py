"""Test that set correctly sets the environment state.
"""
import unittest
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.tests.utils import test_state_equality_after_set
from map_py.tests.states import EMPTY_ENV4_STATE, COMPLEX_ENV4_STATE, TEST_PROFIT_NO_RIDES
import copy 
import json 

GRID_SIZE = 20  # Hard-coded in MiniAmusementPark
HOST = 'localhost'
PORT = '3000'

class TestThemeParkSemanticErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        map = MiniAmusementPark(HOST, PORT) 
        cls.ENV_ID = map.park_id
        #map.shutdown()  # No, can't shutdown park as this'd kill the park_id. I think.

    def test_grid_simple(self) -> None:
        map_game = MiniAmusementPark(host=HOST, port=PORT, park_id=self.ENV_ID)

        map_game.set(EMPTY_ENV4_STATE) 
        _, state = map_game.get_observation_and_raw_state()

        """
        expected =  [
        [1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,2,2,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,0,0,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,0,0,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,0,0,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,2,0,2,2,2,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,3]
        ]
        """
        expected_state = copy.deepcopy(EMPTY_ENV4_STATE)
        test_state_equality_after_set(expected_state, state)

    def test_grid_complex(self) -> None:
        map_game = MiniAmusementPark(host=HOST, port=PORT, park_id=self.ENV_ID)

        map_game.set(COMPLEX_ENV4_STATE) 
        _, state = map_game.get_observation_and_raw_state()
        assert isinstance(state, dict), state

        """
        expected =  [
        [1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [2,2,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,5,5,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,2,2,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,0,0,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,0,0,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,0,0,2,0,0,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,2,0,2,2,2,2,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,3]
        ]
        """
        
        expected_state = copy.deepcopy(COMPLEX_ENV4_STATE)
        test_state_equality_after_set(expected_state, state)

def test_grid_complex2(self) -> None:
        map_game = MiniAmusementPark(host=HOST, port=PORT, park_id=self.ENV_ID)

        map_game.set(TEST_PROFIT_NO_RIDES) 
        _, state = map_game.get_observation_and_raw_state()
        assert isinstance(state, dict), state
        
        expected_state = copy.deepcopy(TEST_PROFIT_NO_RIDES)
        test_state_equality_after_set(expected_state, state) 
    
if __name__ == "__main__":
       #input("Once the server is running at port 3000, then press any key.\nie., from the map root directory run: \nnode server.js\n")
       unittest.main()

