/**
 * Application-wide constants
 */

// Error messages
export const ERROR_MESSAGES = {
  GENERAL: "I encountered an error while generating the response. Please try again.",
  DISCONNECTED: "The connection to the server was lost. Please try again when reconnected.",
  TIMEOUT: "The request is taking longer than usual. The system may be indexing data. Please wait or try a simpler query.",
  LOADING_FIRST: "The first request may take a bit longer as the system indexes your code. Please be patient."
};

// Status messages
export const STATUS_MESSAGES = {
  CONNECTING: "Connecting to server...",
  INDEXING: "Indexing code for better responses...",
  PROCESSING: "Processing your request..."
}; 