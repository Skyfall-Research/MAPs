import os
import subprocess
import sys
import time
from pathlib import Path
env = os.environ.copy()

project_root = Path(__file__).parent.resolve()

server_script = project_root / "map_backend" / "server.js"
python_game_script = project_root / "map_py" / "gui" / "gui.py"
python_path = project_root / "map_py" 

GAME_PORT = 3223
env["MAP_PORT"] = str(GAME_PORT)
print("starting node.js server")
server_process = subprocess.Popen(["node", str(server_script)] + (['--vis']), cwd=project_root, env=env.copy())

time.sleep(1)

env["PYTHONPATH"] = f"{env.get('PYTHONPATH', '')}{os.pathsep}{python_path}"

print("starting python game")
# Forward all original command-line arguments except the script name
game_process = subprocess.Popen([sys.executable, str(python_game_script), '--port', str(GAME_PORT)] + sys.argv[1:], env=env)

try:
    game_process.wait()
finally:
    print("stopping node.js server")
    server_process.terminate()
