"""Useful Constants"""
import importlib.resources
import map_py
import yaml 

# Path to the root of the package
MODULE_PATH = importlib.resources.files(map_py).parent

# MAP Gameplay Rules
with open(MODULE_PATH / 'shared' / 'documentation.md', 'r') as infile:
    GAMEPLAY_RULES = infile.read()

# MAP action space documentation
with open(MODULE_PATH / 'shared' / 'documentation_action_space.md', 'r') as infile:
    GAMEPLAY_RULES_ACTIONS_ONLY = infile.read()

# MAP Sandbox Gameplay Rules
with open(MODULE_PATH / 'shared' / 'documentation_sandbox.md', 'r') as infile:
    SANDBOX_GAMEPLAY_RULES = infile.read()

# MAP Sandbox action space documentation
with open(MODULE_PATH / 'shared' / 'documentation_sandbox_action_space.md', 'r') as infile:
    SANDBOX_GAMEPLAY_RULES_ACTIONS_ONLY = infile.read()

# MAP Sandbox Instructions
with open(MODULE_PATH / 'shared' / 'assets' / 'instructions_assets' / 'instructions.txt', 'r') as infile:
    SANDBOX_INSTR_WITH_DOC_REF = infile.read()

SANDBOX_INSTR_WITHOUT_DOC_REF = SANDBOX_INSTR_WITH_DOC_REF[:SANDBOX_INSTR_WITH_DOC_REF.index('Documentation:')].strip()

# MAP Layout directory
LAYOUTS_DIR = MODULE_PATH / 'shared' / 'layouts'

# MAP Config
MAP_CONFIG_PATH = MODULE_PATH / 'shared' / 'config.yaml'
with open(MAP_CONFIG_PATH, 'r') as infile:
    MAP_CONFIG = yaml.safe_load(infile)

HORIZON_BY_DIFFICULTY = {
    'easy': 50,
    'medium': 100,
    'hard': 250,
}