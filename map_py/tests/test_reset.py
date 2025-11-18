"""Misc tests for MiniAmusementPark, currently regression tests that don't
have a better home yet.
"""
import unittest
from map_py.mini_amusement_park import MiniAmusementPark, FullParkObs
from map_py.tests.states import EMPTY_ENV4_STATE, COMPLEX_ENV4_STATE
from map_py.tests.utils import test_state_equality_after_reset
import copy 

GRID_SIZE = 20  # Hard-coded in MiniAmusementPark
HOST = 'localhost'
PORT = '3000'
class TestThemeParkSemanticErrors(unittest.TestCase):
    def test_reset_raw_after_action(self) -> None:
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info
    
        _, ori_state = map.get_observation_and_raw_state()
        _,_,_,_,info = map.step('place(type="staff", subtype="janitor", subclass="red", x=1,y=1)')
        assert 'error' not in info
        _, new_state = map.get_observation_and_raw_state()
        assert ori_state != new_state # f'{ori_state}\n\n{new_state}'
        response, info = map.reset()
        assert 'error' not in info
        _, reset_state = map.get_observation_and_raw_state()

        #assert ori_state == reset_state
        test_state_equality_after_reset(ori_state, reset_state)

    def test_reset_after_action(self) -> None:
        map = MiniAmusementPark(host=HOST, port=PORT, layout='old_layout', return_detailed_guest_info=True)
        _, info = map.reset()
        assert 'error' not in info

        ori_state = map.observe()
        _,_,_,_,info = map.step('place(type="staff", subtype="janitor", subclass="red", x=1,y=1)')
        assert 'error' not in info
        new_state = map.observe()
        assert ori_state != new_state # f'{ori_state}\n\n{new_state}'
        response, info = map.reset()
        assert 'error' not in info
        reset_state = map.observe()

        assert isinstance(ori_state, FullParkObs)
        assert isinstance(reset_state, FullParkObs)

        test_state_equality_after_reset(ori_state.model_dump(), reset_state.model_dump())


    # ====================================================
    

if __name__ == "__main__":
       #input("Once the server is running at port 3000, then press any key.\nie., from the map root directory run: \nnode server.js\n")
       unittest.main()

