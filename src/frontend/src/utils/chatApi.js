/**
 * Chat API client for interacting with the backend
 */

// Default configuration
const DEFAULT_CONFIG = {
  apiHost: 'http://localhost:5000',
  endpoints: {
    chat: '/api/chat',
    health: '/api/health'
  }
};

/**
 * Create a chat client to interact with the API
 * @param {Object} config - Configuration object
 * @returns {Object} - Chat client methods
 */
export const createChatClient = (config = DEFAULT_CONFIG) => {
  // Store session ID for continuous conversation
  let sessionId = localStorage.getItem('chat_session_id') || null;
  
  /**
   * Send a chat message to the API
   * @param {string} message - User message
   * @returns {Promise<Object>} - API response
   */
  const sendMessage = async (message) => {
    try {
      const response = await fetch(`${config.apiHost}${config.endpoints.chat}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error (${response.status}): ${errorText}`);
      }
      
      const data = await response.json();
      
      // Store the session ID for future requests
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem('chat_session_id', sessionId);
      }
      
      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      return {
        content: "Error connecting to the chat service. Please try again.",
        session_id: sessionId,
        request_time: 0
      };
    }
  };
  
  /**
   * Check API health status
   * @returns {Promise<Object>} - Health status
   */
  const checkHealth = async () => {
    try {
      const response = await fetch(`${config.apiHost}${config.endpoints.health}`);
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