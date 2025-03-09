import React, { useState, useEffect, useRef } from 'react';
import { ThemeProvider } from '@emotion/react';
import RetroDevice from './components/RetroDevice';
import { theme } from './theme';
import { createChatClient } from './utils/chatApi';
import { ERROR_MESSAGES } from './utils/constants';
import { getRandomWelcomeMessage } from './utils/welcomeMessages';

function App() {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  
  // Create chat client reference
  const chatClientRef = useRef(null);
  
  // Initialize chat client and show welcome message on component mount
  useEffect(() => {
    const initializeClient = async () => {
      console.log('Initializing chat client...');
      setIsReconnecting(true);
      
      if (!chatClientRef.current) {
        chatClientRef.current = createChatClient();
      }
      
      try {
        // Check API health
        const healthStatus = await chatClientRef.current.checkHealth();
        
        if (healthStatus.status === 'ok') {
          console.log('✅ API connection successful');
          setIsConnected(true);
          setConnectionError(null);
          
          // Only add welcome message if there are no messages yet
          // This prevents adding it again if app rerenders
          if (messages.length === 0) {
            const welcomeMessage = getRandomWelcomeMessage();
            setMessages([{
              type: 'assistant',
              content: welcomeMessage
            }]);
          }
        } else {
          console.error('⚠️ API health check failed:', healthStatus);
          setIsConnected(false);
          setConnectionError('error');
        }
      } catch (error) {
        console.error('⛔ Error connecting to API:', error);
        setIsConnected(false);
        setConnectionError('error');
      } finally {
        setIsReconnecting(false);
      }
    };
    
    initializeClient();
    
    // Set up health check interval
    const healthCheckInterval = setInterval(async () => {
      if (chatClientRef.current && !isReconnecting) {
        try {
          const healthStatus = await chatClientRef.current.checkHealth();
          if (healthStatus.status !== 'ok' && isConnected) {
            setIsConnected(false);
            setConnectionError('disconnected');
          } else if (healthStatus.status === 'ok' && !isConnected) {
            setIsConnected(true);
            setConnectionError(null);
          }
        } catch (error) {
          if (isConnected) {
            setIsConnected(false);
            setConnectionError('error');
          }
        }
      }
    }, 30000);
    
    return () => {
      clearInterval(healthCheckInterval);
    };
  }, [isConnected, isReconnecting]);
  
  // Function to send a message using the chat client
  const sendMessage = async (content) => {
    if (!chatClientRef.current || !isConnected) {
      setConnectionError('disconnected');
      return;
    }
    
    // Add user message to UI
    setMessages(prev => [...prev, { type: 'user', content }]);
    setIsWaitingForResponse(true);
    
    try {
      // Send message to API
      const response = await chatClientRef.current.sendMessage(content);
      
      setIsWaitingForResponse(false);
      
      if (response.content) {
        // Add response to messages
        setMessages(prev => [...prev, { type: 'assistant', content: response.content }]);
      } else {
        // Handle error
        setConnectionError('error');
        setMessages(prev => [...prev, { 
          type: 'assistant', 
          content: ERROR_MESSAGES.GENERAL 
        }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setIsWaitingForResponse(false);
      setConnectionError('error');
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: ERROR_MESSAGES.GENERAL 
      }]);
    }
  };
  
  return (
    <ThemeProvider theme={theme}>
      <RetroDevice 
        messages={messages}
        onSendMessage={sendMessage}
        isConnected={isConnected}
        isWaitingForResponse={isWaitingForResponse}
        isReconnecting={isReconnecting}
        className={"App"}
      />
    </ThemeProvider>
  );
}

export default App; 