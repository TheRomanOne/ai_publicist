// Application configuration

// Default configuration for API connections
export const DEFAULT_CONFIG = {
  api: {
    host: 'http://localhost',
    port: 5000,
    endpoints: {
      chat: '/api/chat',
      health: '/api/health'
    }
  }
};

// Build full API host URL
export const getApiConfig = () => {
  const { api } = DEFAULT_CONFIG;
  return {
    apiHost: `${api.host}:${api.port}`,
    endpoints: api.endpoints
  };
};

// Backend service configuration
export const backend = {
  baseUrl: 'http://localhost:5000',
  apiPath: '/api'
};

// Theme configuration options
export const themeConfig = {
  darkMode: false,
  animations: true
}; 