import React, { useState, useEffect, useRef } from 'react';
import { 
  ChatArea,
  MessageContainer,
  Message, 
  TypingIndicator
} from '../../styles/device/MessageDisplay.styles';
import { ERROR_MESSAGES } from '../../utils/constants';

/**
 * Component to display chat messages with styling
 * 
 * @param {Array} messages - Array of message objects
 * @param {boolean} isWaitingForResponse - Whether we're waiting for a response
 * @param {string} connectionStatus - Current connection status
 * @param {boolean} isReconnecting - Whether the connection is in the process of reconnecting
 */
const MessageDisplay = ({ messages, isWaitingForResponse, connectionStatus, isReconnecting }) => {
  const [errorMessage, setErrorMessage] = useState(null);
  const chatAreaRef = useRef(null);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages, isWaitingForResponse]);
  
  // Update error message based on connection status
  useEffect(() => {
    if (connectionStatus === 'error') {
      setErrorMessage(ERROR_MESSAGES.GENERAL);
    } else if (connectionStatus === 'disconnected') {
      setErrorMessage(ERROR_MESSAGES.DISCONNECTED);
    } else if (connectionStatus === 'timeout') {
      setErrorMessage(ERROR_MESSAGES.TIMEOUT);
    } else {
      setErrorMessage(null);
    }
  }, [connectionStatus]);
  
  // Create display messages (copies existing messages, adds waiting indicator)
  const displayMessages = [...messages];
  
  // Add typing indicator when waiting for response
  if (isWaitingForResponse && !isReconnecting) {
    displayMessages.push({
      type: 'typing',
      id: 'typing-indicator'
    });
  }
  
  // Add error message if needed
  if (errorMessage && !displayMessages.some(m => 
    m.type === 'assistant' && m.content === errorMessage)) {
    displayMessages.push({
      type: 'assistant',
      content: errorMessage
    });
  }
  
  // Create a helper function at the top of your file
  const formatMessage = (content) => {
    if (!content) return '';
    return content.replace(/\n/g, "<br>");
  };
  
  return (
    <ChatArea ref={chatAreaRef}>
      {(
        displayMessages.map((msg, index) => {
          if (msg.type === 'typing') {
            return (
              <TypingIndicator key="typing">
                <span></span><span></span><span></span>
              </TypingIndicator>
            );
          }
          
          return (
            <MessageContainer key={index} isUser={msg.type === 'user'} className="hover-container">
              <Message 
                isUser={msg.type === 'user'} 
                dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
              />
            </MessageContainer>
          );
        })
      )}
    </ChatArea>
  );
};

export default MessageDisplay; 