"""Test that an error is raised if syntactically correct
but semantically invalid commands are run in the environment
"""

import unittest
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.tests.states import COMPLEX_ENV4_STATE


# List of sequences of syntactically valid commands.
# The inner lists are of sequences are such that the last command is semantically invalid.
SIMPLE_INVALID = [
    ['place(type="ride",x=0,y=2,subtype="rocket",subclass="yellow",price=1)'],  # Ride type doesn't exist
    ['place(type="ride",x=0,y=20,subtype="ferris_wheel", subclass="yellow",price=1)',], # Bad position
    ['place(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow",price=-1)',], # Bad price
    ['place(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow",price=99)',], # Bad price

    ['place(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow",price=1)',
      'place(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow",price=1)',],  # Space occupied
    ['place(type="ride",x=-1,y=4,subtype="ferris_wheel", subclass="yellow",price=1)',], # Bad position

    ['place(type="shop",x=0,y=2,subtype="rocket",subclass="yellow",price=1)'],  # shop type doesn't exist
    ['place(type="shop",x=0,y=20,subtype="food",subclass="yellow",price=1,order_quantity=200)',], # Bad position
    ['place(type="shop",x=0,y=2,subtype="food",subclass="yellow",price=1,order_quantity=200)',
      'place(type="shop",x=0,y=2,subtype="food",subclass="yellow",price=1,order_quantity=200)',],  # Space occupied

    ['move(type="ride",subtype="ferris_wheel",subclass="yellow",x=3,y=0,new_x=0,new_y=2)'], # Bad ID
    ['move(type="ride",subtype="ferris_wheel",subclass="yellow",x=1,y=2,new_x=0,new_y=2)',
     'move(type="ride",subtype="ferris_wheel",subclass="yellow",x=1,y=2,new_x=40,new_y=4)'], # Bad position
    ['place(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow",price=1)',
     'move(type="ride",subtype="ferris_wheel",subclass="yellow",x=1,y=2,new_x=0,new_y=2)',], # Occupied position

    ['move(type="shop",subtype="food",subclass="yellow",x=1,y=2,new_x=0,new_y=2)'], # Ride not shop
    ['move(type="shop",subtype="food",subclass="yellow",x=4,y=3,new_x=0,new_y=2)'], # Bad position

    ['place(type="staff",subtype="NoSuchJob",subclass="yellow",x=0,y=2)'], # Bad job type
    ['place(type="staff",subtype="janitor",subclass="yellow",x=1,y=2)',
     'place(type="staff",subtype="janitor",subclass="blue",x=40,y=4)'], # Bad position

    ['remove(type="staff", subtype="janitor", subclass="yellow", x=2, y=7)'],  # Bad ID
    ['remove(type="staff", subtype="janitor", subclass="blue", x=2, y=2)',
    'remove(type="staff", subtype="janitor", subclass="yellow", x=7, y=2)'],  # Bad ID
    ['remove(type="staff", subtype="janitor", subclass="blue", x=2, y=2)',
    'remove(type="staff", subtype="janitor", subclass="blue", x=2, y=2)',],  # Fire an already fired employee

    ['move(type="staff", subtype="janitor", subclass="red", x=7,y=7,new_x=16,new_y=11)'],  # Bad ID
    ['move(type="staff", subtype="janitor", subclass="blue", x=2,y=2,new_x=16,new_y=11)',
    'move(type="staff", subtype="janitor", subclass="blue", x=16,y=11,new_x=4,new_y=99)'],  # Bad position
    
    ['place(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow",price=1)',
      'remove(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow")',
      'remove(type="ride",x=0,y=2,subtype="ferris_wheel", subclass="yellow")',], 

    ['remove(type="ride",x=19,y=19,subtype="ferris_wheel", subclass="yellow")',],

    ['remove(type="ride",x=18,y=18,subtype="ferris_wheel", subclass="yellow")',],

    ['remove(type="ride",x=21,y=18,subtype="ferris_wheel", subclass="yellow")',],
]

HOST = 'localhost'
PORT = '3000'

class TestThemeParkSemanticErrors(unittest.TestCase):

    def test_simple_invalid(self):
        """Run every sequence of commands in SIMPLE_INVALID. Each sequence is a 
        separate subtest. 

        Each sequence should produce a RuntimeError with the last command.
        """
        map = MiniAmusementPark(host=HOST, port=PORT)
        map.set(COMPLEX_ENV4_STATE)

        for cmd_seq in SIMPLE_INVALID:
            with self.subTest(cmd_seq):
                for cmd in cmd_seq[:-1]:
                    _, _, _, _, info = map.step(cmd)
                    assert 'error' not in info, (cmd, info)

                # Last command in sequence is semantically invalid
                _, _, _, _, info = map.step(cmd_seq[-1])
                assert 'error' in info, (cmd_seq[-1], info)
                     
            _, info = map.set(COMPLEX_ENV4_STATE)
            assert 'error' not in info
    
    def test_move_attraction_out_of_bounds(self):
        """Test that a shop moved out of bounds produces a runtime error
        """
        map = MiniAmusementPark(host=HOST, port=PORT)
        _, info = map.set(COMPLEX_ENV4_STATE)
        assert 'error' not in info
        X=8
        Y=4
        _,_,_,_,info = map.step(f'place(type="shop",x={X},y={Y},subtype="food", subclass="yellow", price=2, order_quantity=200)')
        assert 'error' not in info, info

        _,_,_,_,info = map.step(f'move(type="shop",subtype="food",subclass="yellow",x={X}, y={Y},new_x=0,new_y=2)')
        assert 'error' not in info 
        
        _,_,_,_,info = map.step(f'move(type="shop",subtype="food",subclass="yellow",x=0,y=2,new_x=40,new_y=4)')
        assert 'error' in info  

    def test_malformed_strings(self):
        """Test malformed command.
        """
        map = MiniAmusementPark(host=HOST, port=PORT)
        _, info = map.set(COMPLEX_ENV4_STATE)
        assert 'error' not in info

        # Malformed
        _,_,_,_,info = map.step('place(type="shop",x={X},y={Y},subtype="food", subclass="yellow", price=2, order_quantity=200)')
        assert 'error' in info, info

        # OK but invalid
        X=8
        Y=4
        _,_,_,_,info = map.step(f'move(type="shop",subtype="food",subclass="yellow",x={X}, y={Y},new_x=0,new_y=2)')
        assert 'error' in info 

        # OK but invalid
        _,_,_,_,info = map.step(f'move(type="shop",subtype="food",subclass="yellow",x=0,y=2,new_x=40,new_y=4)')
        assert 'error' in info 

        # Malformed
        _,_,_,_,info = map.step('place(type="shop",x=None,y=0,subtype="food", subclass="yellow", price=2, order_quantity=200)')
        assert 'error' in info, info

        # Malformed
        _,_,_,_,info = map.step('place(type="shop",x="0",y=0,subtype="food", subclass="yellow", price=2, order_quantity=200)')
        assert 'error' in info, info
              
    def test_move_attraction_occupied(self):
        """Test that a shop moved into a space with a shop produces a runtime error
        """
        map = MiniAmusementPark(host=HOST, port=PORT)
        _, info = map.set(COMPLEX_ENV4_STATE)
        assert 'error' not in info

        _,_,_,_,info = map.step('place(type="shop",x=0,y=2,subtype="food", subclass="yellow", price=4, order_quantity=200)')
        assert 'error' not in info 

        _,_,_,_,info = map.step(f'move(type="shop",subtype="food",subclass="yellow",x=3,y=3,new_x=0,new_y=2)')
        assert 'error' in info 

    def test_move_occupied2(self):
        """Test that a shop moved into a space with a ride produces a runtime error
        """
        map = MiniAmusementPark(host=HOST, port=PORT)
        _, info = map.set(COMPLEX_ENV4_STATE)
        assert 'error' not in info

        _,_,_,_,info = map.step('place(type="shop",x=0,y=2,subtype="food", subclass="yellow", price=1, order_quantity=2)')
        assert 'error' not in info

        _,_,_,_,info = map.step('place(type="shop",x=8,y=4,subtype="food", subclass="yellow", price=3, order_quantity=2)')
        assert 'error' not in info, info

        _,_,_,_,info = map.step(f'move(type="shop",subtype="food",subclass="yellow",x=0,y=2, new_x=1, new_y=2)')
        assert 'error' in info 

    # TODO: Check available funds
    def test_move_occupied3(self):
        """Test that a shop moved into a space with a ride produces a runtime error
        """
        map = MiniAmusementPark(host=HOST, port=PORT)
        _, info = map.set(COMPLEX_ENV4_STATE)
        assert 'error' not in info

        _,_,_,_,info = map.step('place(type="shop",x=0,y=2,subtype="food", subclass="yellow", price=1, order_quantity=200)')
        assert 'error' not in info

        _,_,_,_,info = map.step('place(type="shop",x=8,y=4,subtype="food", subclass="yellow", price=3, order_quantity=200)')
        assert 'error' not in info, info

        _,_,_,_,info = map.step(f'move(type="shop",subtype="food",subclass="yellow",x=0,y=2, new_x=1, new_y=2)')
        assert 'error' in info 


    
if __name__ == "__main__":
       #input("Once the server is running at port 3000, then press any key.\nie., from the map root directory run: \nnode server.js\n")
       unittest.main()

