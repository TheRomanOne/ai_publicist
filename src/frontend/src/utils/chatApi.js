/**
 * Chat API client for interacting with the backend
 */

// Default configuration
const DEFAULT_CONFIG = {
  apiHost: 'http://localhost:5000',
  endpoints: {
    chat: '/api/chat',
    health: '/api/health'
  },
  timeout: 60000  // Increase timeout to 60 seconds (was likely defaulting to 10-30 seconds)
};

/**
 * Create a chat API client
 * 
 * @param {Object} config - Configuration object
 * @returns {Object} - Chat client interface
 */
export const createChatClient = (config = {}) => {
  // Merge default config with provided config
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  
  // Store session ID for continuous conversation
  let sessionId = localStorage.getItem('chat_session_id') || null;
  
  /**
   * Send a message to the chat API
   * 
   * @param {string} message - Message to send
   * @returns {Promise<Object>} - Response from the API
   */
  const sendMessage = async (message) => {
    const url = `${mergedConfig.apiHost}${mergedConfig.endpoints.chat}`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId
        }),
        signal: AbortSignal.timeout(mergedConfig.timeout)  // Set explicit timeout
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Store session ID
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem('chat_session_id', sessionId);
      }
      
      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  };
  
  /**
   * Check API health status
   * @returns {Promise<Object>} - Health status
   */
  const checkHealth = async () => {
    try {
      const response = await fetch(`${mergedConfig.apiHost}${mergedConfig.endpoints.health}`);
      if (!response.ok) {
        throw new Error(`Health check failed with status ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'error', message: error.message };
    }
  };
  
  /**
   * Reset the chat session
   */
  const resetSession = () => {
    sessionId = null;
    localStorage.removeItem('chat_session_id');
  };
  
  return {
    sendMessage,
    checkHealth,
    resetSession,
    getCurrentSessionId: () => sessionId
  };
}; 