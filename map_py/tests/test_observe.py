"""Misc tests for MiniAmusementPark, currently regression tests that don't
have a better home yet.
"""
import unittest
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.observations_and_actions.pydantic_obs import FullParkObs
from map_py.tests.states import COMPLEX_ENV4_STATE, EMPTY_ENV4_STATE
import copy 

GRID_SIZE = 20  # Hard-coded in MiniAmusementPark
HOST = 'localhost'
PORT = '3000'

class TestThemeParkSemanticErrors(unittest.TestCase):
    def test_raw_obs_is_dict(self) -> None:
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout')
        _, info = map.reset()
        assert 'error' not in info

        _, ori_state = map.get_observation_and_raw_state()
        assert isinstance(ori_state, dict)

    def test_non_raw_obs_is_park(self) -> None:
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout')
        _, info = map.reset()
        assert 'error' not in info

        ori_state = map.observe()
        assert isinstance(ori_state, FullParkObs)

    def test_park_rating_observed(self) -> None:
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout')
        _, info = map.reset()
        assert 'error' not in info

        _, ori_state = map.get_observation_and_raw_state()
        map.step('place(type="staff", subtype="janitor", subclass="blue", x=1,y=1)')
        _, new_state = map.get_observation_and_raw_state()

        assert 'park_rating' in new_state['state']

    # TODO: Add meaningful tests of observation.


if __name__ == "__main__":
       #input("Once the server is running at port 3000, then press any key.\nie., from the map root directory run: \nnode server.js\n")
       unittest.main()

