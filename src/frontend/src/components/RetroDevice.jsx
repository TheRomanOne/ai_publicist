import React, { useState } from 'react';
import DeviceFrame from './device/DeviceFrame';
import MessageDisplay from './device/MessageDisplay';
import InputArea from './device/InputArea';
import { DeviceContainer } from '../styles/RetroDevice.styles';

/**
 * Main component for the retro-styled chat device
 * 
 * @param {Array} messages - Array of message objects
 * @param {Function} onSendMessage - Function to handle sending messages
 * @param {boolean} isConnected - Connection status with server
 * @param {boolean} isWaitingForResponse - Whether we're waiting for a response
 * @param {boolean} isReconnecting - Whether a reconnection attempt is in progress
 */
const RetroDevice = ({ 
  messages, 
  onSendMessage, 
  isConnected, 
  isWaitingForResponse,
  isReconnecting 
}) => {
  const [input, setInput] = useState('');
  
  const handleSubmit = () => {
    if (input.trim() && onSendMessage) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <DeviceContainer>
      <DeviceFrame isConnected={isConnected} isReconnecting={isReconnecting}>
        <MessageDisplay 
          messages={messages} 
          isWaitingForResponse={isWaitingForResponse}
          isReconnecting={isReconnecting} 
        />
        <InputArea 
          input={input}
          setInput={setInput}
          isConnected={isConnected}
          handleSubmit={handleSubmit}
          isWaitingForResponse={isWaitingForResponse}
          isReconnecting={isReconnecting}
          // onKeyDown={handleKeyDown}
        />
      </DeviceFrame>
    </DeviceContainer>
  );
};

export default RetroDevice; 