/**
 * Application-wide constants
 */

// Error messages
export const ERROR_MESSAGES = {
  GENERAL: "I encountered an error while generating the response. Please try again.",
  DISCONNECTED: "The connection to the server was lost. Please try again when reconnected.",
  TIMEOUT: "The request took too long to process. Please try a simpler query."
};

// Status messages
export const STATUS_MESSAGES = {
  RECONNECTING: "Reconnecting to server...",
  WAITING: "Waiting for response...",
  DISCONNECTED: "Disconnected from server",
  READY: "Type a message..."
}; 