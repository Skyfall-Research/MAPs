import copy
import json
from pathlib import Path
from map_py.observations_and_actions.shared_constants import MAP_CONFIG, ACTION_SPEC, SANDBOX_ACTION_SPEC


data = copy.deepcopy(MAP_CONFIG)
PARK_CONFIG_STR = f"## Park Config File\nThe following json contains the park's configuration including prices, properties, valid ranges and descriptions:\n\n```json\n{json.dumps(MAP_CONFIG)}```"

with open("documentation_base.md", "r") as f:
    md = f.read()

def recursive_replace(md, data, prefix="", silent_fail=False):
    for key, value in data.items():
        key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            md = recursive_replace(md, value, key, silent_fail=silent_fail)
            continue

        if f"{{{{{key}}}}}%" in md:  # Replace percentages correctly
            md = md.replace(f"{{{{{key}}}}}%", f'{value * 100}%')
        if f"{{{{{key}}}}}" in md:
            md = md.replace(f"{{{{{key}}}}}", str(value))
        elif not silent_fail and not key.endswith('.notes'):
            print(f"Key {key} not found in documentation_base.md")
    return md

md = recursive_replace(md, data)

action_spec = ""
for action in ACTION_SPEC:
    action_spec += f"**{action['action_name']}**  \n"
    action_spec += f"*Description*: {action['description']}  \n"
    action_spec += f"*Parameters*:  \n"
    for param in action['parameters']:
        action_spec += f"  - {param}: {action['parameters'][param]}  \n"
    if not action['parameters']:
        action_spec += f"  No parameters  \n"
    action_spec += "  \n---  \n"

md = md.replace("{{action_spec}}", action_spec)

# Save to README.md instead of printing
with open("shared/documentation.md", "w") as f:
    f.write(md)

print("documentation.md has been generated successfully!")

# Create action-space only documentation
action_md = md[md.rfind('## Action Space'):]
with open("shared/documentation_action_space.md", "w") as f:
    f.write(action_md + PARK_CONFIG_STR)
print("documentation_action_space.md has been generated successfully!")

# Begin generation of version of documentation with sandbox details
with open("documentation_sandbox_base.md", "r") as f:
    sandbox_md = f.read()

sandbox_md = recursive_replace(sandbox_md, data, silent_fail=True)

action_spec = ""
for action in SANDBOX_ACTION_SPEC:
    if action['action_name'] in ['set_sandbox_mode']:
        continue

    action_spec += f"**{action['action_name']}**  \n"
    action_spec += f"*Description*: {action['description']}  \n"
    action_spec += f"*Parameters*:  \n"
    for param in action['parameters']:
        action_spec += f"  - {param}: {action['parameters'][param]}  \n"
    if not action['parameters']:
        action_spec += f"  No parameters  \n"
    action_spec += "  \n---  \n"

sandbox_md = sandbox_md.replace("{{sandbox_action_spec}}", action_spec)


# Save to README.md instead of printing
full_sandbox_md = md + sandbox_md
with open("shared/documentation_sandbox.md", "w") as f:
    f.write(full_sandbox_md)

print("documentation_sandbox.md has been generated successfully!")


# Create action-space only documentation
action_md = full_sandbox_md[full_sandbox_md.rfind('## Action Space'):]
with open("shared/documentation_sandbox_action_space.md", "w") as f:
    f.write(action_md + PARK_CONFIG_STR)
print("documentation_sandbox_action_space.md has been generated successfully!")
