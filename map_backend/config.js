// config.mjs
import fs from 'fs';
import YAML from 'yaml';


export const TRAJECTORY_SAVE_BUCKET = "skyfall-maps-leaderboard-saved-trajectories"
export const LEADERBOARD_TABLE = "maps_leaderboard"
export const REGION = "us-east-2"

const file = fs.readFileSync('./shared/config.yaml', 'utf8');
const config = YAML.parse(file);

// Load shared action specification
const actionSpecData = JSON.parse(fs.readFileSync('./shared/action_spec.json', 'utf8'));

// Generate ACTION_PARAMS from shared spec
export const ACTION_PARAMS = {}
for (const action of actionSpecData.actions) {
  const params = new Set(Object.keys(action.parameters))
  params.add('parkId') // Always include parkId
  ACTION_PARAMS[action.action_name] = params
}

// Generate ACTION_PARAM_TYPES from shared spec
const typeMap = {
  'string': String,
  'number': Number,
  'boolean': Boolean,
  'object': Object,
  'array': Array
}

export const ACTION_PARAM_TYPES = {}
for (const [param, typeName] of Object.entries(actionSpecData.param_types)) {
  ACTION_PARAM_TYPES[param] = typeMap[typeName] || String
}

// Default settings
export const DEFAULT_SETTINGS = {
  starting_money: {
    easy: 500,
    medium: 500,
    hard: 500
  },
  horizon: {
    easy: 50,
    medium: 100,
    hard: 250
  }
}

export default config;
