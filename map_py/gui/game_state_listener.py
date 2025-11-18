import socketio
import threading
from map_py.observations_and_actions.pydantic_obs import format_pydantic_observation
import map_py.gui.visualizer as visualizer
from collections import defaultdict

from collections import deque

class Queue:
    def __init__(self):
        self._items = deque()

    def enqueue(self, item):
        """Add an item to the back of the queue."""
        self._items.append(item)

    def dequeue(self):
        """Remove and return the item at the front of the queue."""
        if self.is_empty():
            raise IndexError("dequeue from an empty queue")
        return self._items.popleft()

    def peek(self):
        """Return the item at the front without removing it."""
        if self.is_empty():
            return {}
        return self._items[0]

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self._items) == 0

    def size(self):
        """Return the number of items in the queue."""
        return len(self._items)
    
    def clear(self):
        """Remove all items from the queue."""
        self._items = deque()

    def __repr__(self):
        return f"Queue({list(self._items)})"


class GameStateListener:
    def __init__(self, buffer: Queue, accept_midday_updates: bool = False):
        self.sio = socketio.Client()
        self.accept_midday_updates = accept_midday_updates
        
        # Step and buffer management
        self.buffer = buffer
        self.num_updates = 0

    def start_socketio_listener(self, server="http://localhost:3000"):
        def run():
            try:
                self.sio.connect(server)
                self.sio.wait()
            except Exception as e:
                print(f"[SocketIO] Connection failed: {e}")

        @self.sio.event
        def connect():
            print("[SocketIO] Connected to server")

        @self.sio.event
        def disconnect():
            print("[SocketIO] Disconnected from server")

        @self.sio.on("action")
        def on_action(data):
            print(data)

        @self.sio.on("game_update")
        def on_update(data):
            if data["state_type"] in ["full_state", "day_start", "day_end"]:
                staff_list = data["data"]["staff"]
                state = format_pydantic_observation(data["data"], as_dict=True)
                # Add id information back into staff
                state["staff"]["staff_list"] = staff_list
                self.buffer.enqueue({data["state_type"]: state})
            elif data["state_type"] == "mid_day" and self.accept_midday_updates:
                self.num_updates += 1 
                data["data"]["staff"] = {"staff_list": data["data"]["staff"]}
                self.buffer.enqueue({'mid_day': data["data"]})
            elif data["state_type"] == "exit_time" and self.accept_midday_updates:
                self.buffer.enqueue({'exit_time': data["data"]})

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def set_accept_midday_updates(self, accept: bool):
        """Enable/disable midday updates"""
        self.accept_midday_updates = accept

    def get_num_updates(self):
        """Get the number of updates received"""
        return self.num_updates

    def disconnect(self):
        """Disconnect from the server"""
        if self.sio:
            self.sio.disconnect()

    def is_connected(self):
        """Check if connected to server"""
        return self.sio and self.sio.connected

    def emit_action(self, action):
        """Emit an action to the server"""
        if self.sio and self.sio.connected:
            self.sio.emit('action', action)
        else:
            print("[SocketIO] Not connected to server, cannot emit action")


def create_game_state_listener():
    """Factory function to create a GameStateListener with a new queue"""
    buffer = Queue()
    return GameStateListener(buffer)
