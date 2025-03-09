import React, { useRef, useEffect } from 'react';
import { TextField, Button } from '@mui/material';
import { 
  InputContainer,
  InputDecorations,
  textFieldStyles,
  sendButtonStyles
} from '../../styles/device/InputArea.styles';
import { STATUS_MESSAGES } from '../../utils/constants';

/**
 * Input area component with text field and send button
 * 
 * @param {string} input - Current input value
 * @param {Function} setInput - Function to update input value
 * @param {boolean} isConnected - Connection status with server
 * @param {Function} handleSubmit - Function to handle form submission
 * @param {boolean} isWaitingForResponse - Whether we're waiting for a response
 * @param {boolean} isReconnecting - Whether reconnection is in progress
 */
const InputArea = ({ 
  input, 
  setInput, 
  isConnected, 
  handleSubmit, 
  isWaitingForResponse,
  isReconnecting 
}) => {
  // Create a ref for the input field
  const inputRef = useRef(null);
  
  // Determine if input should be disabled
  const isDisabled = !isConnected || isWaitingForResponse || isReconnecting;
  
  // Focus the input field when it becomes enabled
  useEffect(() => {
    if (!isDisabled && inputRef.current) {
      // Small delay to ensure the DOM is ready
      setTimeout(() => {
        inputRef.current.focus();
      }, 100);
    }
  }, [isDisabled]);
  
  // Determine placeholder text based on connection status
  let placeholderText = STATUS_MESSAGES.READY;
  
  if (isReconnecting) {
    placeholderText = STATUS_MESSAGES.RECONNECTING;
  } else if (isWaitingForResponse) {
    placeholderText = STATUS_MESSAGES.WAITING;
  } else if (!isConnected) {
    placeholderText = STATUS_MESSAGES.DISCONNECTED;
  }
  
  // Handle key press events - send message on Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isDisabled) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  return (
    <InputContainer>
      <InputDecorations />
      
      <TextField
        fullWidth
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={placeholderText}
        disabled={isDisabled}
        variant="outlined"
        sx={textFieldStyles}
        onKeyDown={handleKeyPress}
        inputRef={inputRef}
      />
      
      <Button 
        type="submit" 
        variant="contained" 
        disabled={!isConnected || !input.trim() || isWaitingForResponse || isReconnecting}
        onClick={handleSubmit}
        sx={sendButtonStyles}
      >
        <span style={{ fontSize: '20px' }}>➤</span>
      </Button>
    </InputContainer>
  );
};

export default InputArea; 