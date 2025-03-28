/**
 * Welcome messages to display when the chat starts
 */

export const WELCOME_MESSAGES = [
  "Hey there! I'm <USER_NAME>'s AI assistant. Ask me anything about his projects, skills, or experience—I'll do my best to help!",
  
  "Hey! <USER_NAME> set me up to chat with you. Need details on his work, GitHub projects, or anything else? Just ask!",
  
  "Hi! I'm here to make this easy—ask me anything about <USER_NAME>'s experience, code, or what he's been working on lately.",
  
  "Hey, welcome! I can walk you through <USER_NAME>'s projects, skills, and anything else you'd like to know. Where should we start?",
  
  "Hey, great to meet you! <USER_NAME>'s got some cool projects—let me know what you're curious about, and I’ll fill you in."
];


/**
 * Get a random welcome message from the collection
 * @returns {string} A random welcome message
 */
export const getRandomWelcomeMessage = () => {
  const randomIndex = Math.floor(Math.random() * WELCOME_MESSAGES.length);
  return WELCOME_MESSAGES[randomIndex];
}; 