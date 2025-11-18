"""A simple demonstration of map interface.
"""
from map_py.mini_amusement_park import MiniAmusementPark
from map_py.observations_and_actions.pydantic_obs import FullParkObs
import json 
import time


RUN_CMDS = True  # Set to False to manually type commands instead
CMDS = [
    "set_research(research_speed='fast', research_topics=['carousel', 'ferris_wheel', 'roller_coaster', 'drink', 'food', 'specialty'])",
    "place(x=1, y=2, type='ride', subtype='carousel', subclass='yellow', price=2)",
    "place(x=3, y=4, type='shop', order_quantity=100, subtype='food', subclass='yellow', price=5)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=2, y=2)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=2, y=2)",
    "place(x=1, y=3, type='shop', order_quantity=100, subtype='drink', subclass='yellow', price=2)",
    "place(x=3, y=3, type='shop', order_quantity=100, subtype='specialty', subclass='yellow', price=12)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=3, y=6, type='ride', subtype='ferris_wheel', subclass='yellow', price=3)",
    "place(x=1, y=5, type='ride', subtype='ferris_wheel', subclass='blue', price=3)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=4, y=4, type='ride', subtype='roller_coaster', subclass='blue', price=4)",
    "place(x=4, y=6, type='ride', subtype='roller_coaster', subclass='blue', price=4)",
    "wait()",
    "place(x=5, y=4, type='shop', order_quantity=100, subtype='drink', subclass='blue', price=4)",
    "place(x=6, y=4, type='ride', subtype='ferris_wheel', subclass='blue', price=4)",
    "wait()",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=1, y=4, type='shop', order_quantity=100, subtype='food', subclass='blue', price=4)",
    "set_research(research_speed='fast', research_topics=['ferris_wheel', 'specialty'])",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=5, y=6, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=6, y=6, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=7, y=6, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=7, y=7, type='ride', subtype='roller_coaster', subclass='blue', price=4)",
    "place(x=8, y=7, type='shop', order_quantity=100, subtype='specialty', subclass='green', price=1)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "set_research(research_speed='fast', research_topics=['roller_coaster'])",
    "place(x=8, y=6, type='ride', subtype='ferris_wheel', subclass='red', price=4)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=9, y=4, type='ride', subtype='roller_coaster', subclass='green', price=4)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=7, y=4, type='shop', order_quantity=100, subtype='specialty', subclass='green', price=1)",
    "place(x=8, y=4, type='shop', order_quantity=100, subtype='specialty', subclass='green', price=1)",
    "place(x=10, y=4, type='ride', subtype='roller_coaster', subclass='red', price=4)",
    "place(x=11, y=4, type='ride', subtype='roller_coaster', subclass='red', price=4)",
    "place(x=12, y=4, type='ride', subtype='roller_coaster', subclass='red', price=4)",
    "place(x=13, y=5, type='ride', subtype='roller_coaster', subclass='red', price=4)",
    "place(x=10, y=6, type='shop', order_quantity=100, subtype='drink', subclass='blue', price=4)",
    "place(x=11, y=6, type='shop', order_quantity=100, subtype='food', subclass='blue', price=4)",
    "place(x=10, y=10, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "wait()",
    "place(x=11, y=10, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=10, y=12, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=11, y=12, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=12, y=12, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=15, y=9, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=15, y=10, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "wait()",
    "wait()",
    "wait()",
    "place(x=15, y=11, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=15, y=12, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=15, y=13, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=15, y=14, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=15, y=15, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(type='staff', subclass='yellow', subtype='mechanic', x=10, y=11)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(type='staff', subclass='yellow', subtype='janitor', x=1, y=2)",
    "place(x=17, y=10, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=17, y=11, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=17, y=12, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "wait()",
    "wait()",
    "wait()",
    "wait()",
    "wait()",
    "wait()",
    "place(x=17, y=13, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=17, y=14, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=17, y=8, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=17, y=9, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "place(x=16, y=7, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
    "wait()",
    "wait()",
    "wait()",
    "place(x=17, y=8, type='ride', subtype='ferris_wheel', subclass='green', price=4)",
]

tile_to_char = {
    '': ' ',
    'ride': 'R',
    'shop': 'S',
    'path': 'P',
    'entrance': 'E',
    'exit': 'X',
}

def terminal_grid_print(state: FullParkObs, xlim=20, ylim=20):
    occupied = {state.entrance: 'E', state.exit: 'X'}
    for shop in state.shops.shop_list:
        occupied[(shop.x, shop.y)] = 'S'
    for ride in state.rides.ride_list:
        occupied[(ride.x, ride.y)] = 'R'
    for path in state.paths:
        occupied[(path.x, path.y)] = 'P'

    for row in range(xlim):
        for col in range(ylim):
            if (row, col) in occupied:
                char = occupied[(row, col)]
            else:
                char = ' '
            print(char, end='')
        print()

def print_state(state):
    print(f"Step: {state.step}, Guest Count: {state.guests.total_guests} Money: {state.money}, Park Rating: {state.park_rating}")
    # print(f"Available Rides: {state.available_entities}")
    terminal_grid_print(state)

def main():
    map = MiniAmusementPark(host='localhost', port='3000', layout='old_layout') 
    map.update_settings(difficulty='medium', starting_money=9999999)
    state, _ = map.reset()

    done = False

    start_time = time.time()

    while not done:
        obs = map.observe() #['state']

        if RUN_CMDS:
            if len(CMDS) == 0:
                exit(-1)
            action = CMDS.pop(0)
            # print(f"Performing Action: {action}")
            # input("Press Enter to Continue")
        else:
            action = input("Enter Action to Perform: ").strip()
            if action == 'exit':
                exit(0)

        try:
            st = time.time()
            new_obs, reward, done,_,  info = map.step(action)
            et = time.time()
            print(f"guests {new_obs.guests.total_guests:>4}, time: {et-st:.2f}")
            if 'error' in info:
                print(f"----")
                print(f"Error on step {new_obs.step}: {info['error']}")
                print(f"Action performed: {action}")
                print_state(obs)
                #print(json.dumps(map.get_raw_state(), indent=2, sort_keys=True))
                print(f"----")
            if done:
                print_state(obs)
                print(f"TOTAL TIME:{time.time() - start_time:.2f}")
                print(f"---DONE---")

            if new_obs.guest_survey_results.age_of_results == 0:
                print(json.dumps(new_obs.guest_survey_results.list_of_results, indent=2, sort_keys=True))
                pass

        except RuntimeError as e:
            print(e)


if __name__ == '__main__':
    main()