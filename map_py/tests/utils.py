import copy 
import json 
from map_py.mini_amusement_park import FullParkObs 
from map_py.shared_constants import MAP_CONFIG
import yaml
import importlib.resources
MODULE_PATH = importlib.resources.files(__package__)

CONFIG = copy.deepcopy(MAP_CONFIG)

def _clean_state(state: dict) -> dict:
    """Remove any state information that shouldn't be preserved after set is called.

    Currently only purges the ParkId (as that is directly sent to map.set)
    """
    clean = copy.deepcopy(state)
    # Park Id can change
    if 'parkId' in clean:
        del clean['parkId']
    if 'parkId' in clean['state']:
        del clean['state']['parkId']

    # Guest info isn't loaded
    if 'guests' in clean:
        del clean['guests']

    return clean 

def test_state_equality_after_set(set_state, observed_state):
    set_state = _clean_state(set_state)
    observed_state = _clean_state(observed_state)
    assert set(set_state.keys()) == set(observed_state.keys()), (list(sorted(set_state.keys())), list(sorted(observed_state.keys())))
    for key in set_state.keys():
        if key == 'guestStats':
            continue  # Skip, shouldn't matter for simulation.

        if key == 'grid':
            for row, new_row in zip(set_state['grid'], observed_state['grid']):
                for col, new_col in zip(row, new_row):
                    assert col == new_col, (col, new_col)

        # System will set unset seeds on a set. Sigh.
        if key == 'state' and set_state[key]['seed'] is None:  # Setting with unknown seed will create a seed.
            observed_state[key]['seed'] = None

        if set_state[key] != observed_state[key]:
            if not isinstance(set_state[key], list) or len(set_state[key]) <= 10 or len(set_state[key]) != len(observed_state[key]):
                error = f'{key}\n\nExpected: {json.dumps(set_state[key], sort_keys=True)}\n\nActual:   {json.dumps(observed_state[key], sort_keys=True)}'
            else:
                mismaches = []
                for a,b in zip(set_state[key], observed_state[key]):
                    if a != b:
                        mismaches.append(f'Expected: {a}\nObserved: {b}')
                error = f'"{key}" Mismatches:\n{"\n".join(mismaches)}'
            assert set_state[key] == observed_state[key], error 

def test_pydantic_state_equality_after_set(py_set_state: FullParkObs, py_observed_state: FullParkObs):
    set_state = py_set_state.model_dump()
    observed_state = py_observed_state.model_dump()
    assert set(set_state.keys()) == set(observed_state.keys()), (list(sorted(set_state.keys())), list(sorted(observed_state.keys())))
    for key in set_state.keys():
        if key == 'grid':
            for row, new_row in zip(set_state['grid'], observed_state['grid']):
                for col, new_col in zip(row, new_row):
                    assert col == new_col, (col, new_col)

        if set_state[key] != observed_state[key]:
            if not isinstance(set_state[key], list) or len(set_state[key]) <= 10 or len(set_state[key]) != len(observed_state[key]):
                error = f'{key}\n\n{json.dumps(set_state[key], sort_keys=True)}\n\n{json.dumps(observed_state[key], sort_keys=True)}'
            else:
                mismaches = []
                for a,b in zip(set_state[key], observed_state[key]):
                    if a != b:
                        mismaches.append(f'Expected: {a}\nObserved: {b}')
                error = f'"{key}" Mismatches:\n{"\n".join(mismaches)}'
            assert set_state[key] == observed_state[key], error 

def map_ids_raw(set_state, observed_state, allow_empty=False):
    id_map = dict()
    observed_state = copy.deepcopy(observed_state)
    set_state = copy.deepcopy(set_state)
    if 'guests' in observed_state:
        del observed_state['guests']
    if 'guests' in set_state:
        del set_state['guests']

    # Figure out mapping of ids
    for x in range(len(set_state['grid'])):
        for y in range(len(observed_state['grid'])):
            if allow_empty and \
                set_state['grid'][x][y] == observed_state['grid'][x][y] and \
                    set_state['grid'][x][y] == '':
                continue

            set_name = set_state['grid'][x][y].split('-')
            assert len(set_name) == 2

            obs_name = observed_state['grid'][x][y].split('-')
            assert len(obs_name) == 2

            assert set_name[0] == obs_name[0]

            id_map[observed_state['grid'][x][y]] = set_state['grid'][x][y]

            # Change ID
            observed_state['grid'][x][y] = set_state['grid'][x][y]

    # Change observed state to use the original state's ids
    for path in observed_state['paths']:
        path['id'] = id_map[path['id']]

    # TODO: Update ride & shop ids according to the map as well.
    
    return set_state, observed_state

def test_state_equality_after_reset(set_state, observed_state):
    #set_state, observed_state = map_ids_raw(set_state, observed_state, allow_empty=True)
    set_state = copy.deepcopy(set_state)
    observed_state = copy.deepcopy(observed_state)

    assert set(set_state.keys()) == set(observed_state.keys()), (list(sorted(set_state.keys())), list(sorted(observed_state.keys())))
    for key in set_state.keys():
        if key == 'grid':
            for row, new_row in zip(set_state['grid'], observed_state['grid']):
                for col, new_col in zip(row, new_row):
                    assert col == new_col, (col, new_col)

        if set_state[key] != observed_state[key]:
            if not isinstance(set_state[key], list) or len(set_state[key]) <= 10 or len(set_state[key]) != len(observed_state[key]):
                error = f'{key}\n\n{json.dumps(set_state[key], sort_keys=True)}\n\n{json.dumps(observed_state[key], sort_keys=True)}'
            else:
                mismaches = []
                for a,b in zip(set_state[key], observed_state[key]):
                    if a != b:
                        mismaches.append(f'Expected: {a}\nObserved: {b}')
                error = f'"{key}" Mismatches:\n{"\n".join(mismaches)}'

            if key == 'state' and set_state[key]['seed'] is None:  # Setting with unknown seed will create a seed.
                observed_state[key]['seed'] = None
            assert set_state[key] == observed_state[key], error 