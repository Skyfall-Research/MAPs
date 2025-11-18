// Check if we're running tests
const isNode = typeof process !== 'undefined' && process.versions && process.versions.node;

let config = null;
let actionSpec = null;
let ACTION_PARAMS = null;
let ACTION_PARAM_TYPES = null;
let DEFAULT_SETTINGS = null;

// Load config from shared files
async function loadConfig() {
  if (isNode) {
    // Node.js environment - use fs
    try {
      const fs = (await import('fs')).default;
      const { fileURLToPath } = await import('url');
      const { dirname, join } = await import('path');
      const __filename = fileURLToPath(import.meta.url);
      const __dirname = dirname(__filename);
      const configPath = join(__dirname, '../shared/config.yaml');
      const yaml = (await import('yaml')).default;
      const configData = yaml.parse(fs.readFileSync(configPath, 'utf8'));
      config = configData;
      return configData;
    } catch (error) {
      console.error(`Error loading config.json: ${error.message}`);
      return {};
    }
  } else {
    // Browser environment - use fetch
    const configPath = '/config.yaml';
    try {
      const response = await fetch(configPath);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const yaml = (await import('yaml')).default;
      const configData = yaml.parse(await response.text());
      config = configData;
      return configData;
    } catch (error) {
      console.error(`Error loading ${configPath}: ${error.message}`);
      return {};
    }
  }
}

// Load action spec from shared files
async function loadActionSpec() {
  if (actionSpec) return actionSpec; // Return cached spec if already loaded
  
  if (isNode) {
    // Node.js environment - use fs
    try {
      const fs = (await import('fs')).default;
      const { fileURLToPath } = await import('url');
      const { dirname, join } = await import('path');
      const __filename = fileURLToPath(import.meta.url);
      const __dirname = dirname(__filename);
      const actionSpecPath = join(__dirname, '../shared/action_spec.json');
      actionSpec = JSON.parse(fs.readFileSync(actionSpecPath, 'utf8'));
    } catch (error) {
      console.error('Failed to load action_spec.json:', error);
      return null;
    }
  } else {
    // Browser environment - use fetch
    try {
      const actionSpecResponse = await fetch('/action_spec.json');
      actionSpec = await actionSpecResponse.json();
    } catch (error) {
      console.error('Failed to load action_spec.json:', error);
      return null;
    }
  }
  
  if (actionSpec) {
    // Generate ACTION_PARAMS from shared spec
    ACTION_PARAMS = {};
    for (const action of actionSpec.actions) {
      const params = new Set(Object.keys(action.parameters));
      params.add('parkId'); // Always include parkId
      ACTION_PARAMS[action.action_name] = params;
    }
    
    // Generate ACTION_PARAM_TYPES from shared spec
    const typeMap = {
      'string': String,
      'number': Number,
      'boolean': Boolean,
      'object': Object,
      'array': Array
    };
    
    ACTION_PARAM_TYPES = {};
    for (const [param, typeName] of Object.entries(actionSpec.param_types)) {
      ACTION_PARAM_TYPES[param] = typeMap[typeName] || String;
    }
  }
  
  return actionSpec;
}

// Default settings
DEFAULT_SETTINGS = {
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
};

// Initialize config on module load
loadConfig();
loadActionSpec();

// Export functions and getters
export { loadConfig, loadActionSpec };

// Export getters that will return the loaded values
export function getConfig() {
  return config;
}

export function getActionSpec() {
  return actionSpec;
}

export function getActionParams() {
  return ACTION_PARAMS;
}

export function getActionParamTypes() {
  return ACTION_PARAM_TYPES;
}

export function getDefaultSettings() {
  return DEFAULT_SETTINGS;
}

// For backward compatibility, export the values directly
export { config, actionSpec, ACTION_PARAMS, ACTION_PARAM_TYPES, DEFAULT_SETTINGS };

export default config;
