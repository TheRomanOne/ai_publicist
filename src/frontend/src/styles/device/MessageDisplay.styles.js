import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';

// Define colors for different message types
export const userColor = {
  bg: '#5c80aa',           // Blue for user messages
  accent: '#3A6BC5',       // Darker blue accent
  text: '#FFFFFF',         // White text
  shadow: 'rgba(74, 122, 219, 0.3)'
};

export const systemColor = {
  // bg: '#a2bd8c',           // Green for assistant messages
  bg: '#869e72',           // Green for assistant messages
  accent: '#689F38',       // Darker green accent
  text: '#FFFFFF',         // White text
  shadow: 'rgba(124, 179, 66, 0.3)'
};

// Fade-in animation for messages
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

// Message slide-in animation (right for user, left for assistant)
const slideInRight = keyframes`
  from { transform: translateX(20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
`;

const slideInLeft = keyframes`
  from { transform: translateX(-20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
`;

// Pulse animation for hover
const subtlePulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.03); }
  100% { transform: scale(1); }
`;

// Main chat area container
export const ChatArea = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  scroll-behavior: smooth;
  background-color: rgba(255, 237, 144, 0.66);
  background-image: linear-gradient(to bottom, rgba(250, 248, 242, 0.8), rgba(242, 240, 230, 0.8));
`;

// Container for individual message with positioning
export const MessageContainer = styled.div`
  display: flex;
  justify-content: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  margin: 12px 0;
  position: relative;
  animation: ${props => props.isUser ? slideInRight : slideInLeft} 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
`;

// Message bubble with styling
export const Message = styled.div`
  position: relative;
  max-width: 80%;
  padding: 14px 18px;
  background-color: ${props => props.isUser ? userColor.bg : systemColor.bg};
  color: ${props => props.isUser ? userColor.text : systemColor.text};
  border-radius: 18px;
  border-bottom-${props => props.isUser ? 'right' : 'left'}-radius: 4px;
  box-shadow: 0 3px 12px ${props => props.isUser ? userColor.shadow : systemColor.shadow};
  overflow-wrap: break-word;
  font-size: 1.3rem;
  line-height: 1.5;
  transition: all 0.3s ease;
  
  &:hover {
    filter: brightness(1.05);
    box-shadow: 0 5px 15px ${props => props.isUser ? userColor.shadow : systemColor.shadow};
  }
`;

// Accent bar for visual appeal - MAKING INVISIBLE
export const MessageAccent = styled.div`
  display: none; /* Hide the accent line */
`;

// Improved typing indicator that's more visible and properly positioned
export const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 18px;
  border-radius: 18px;
  background-color: ${systemColor.bg};
  width: auto;
  min-width: 60px;
  align-self: flex-start;
  margin: 4px 60px 4px 16px;
  box-shadow: 0 3px 12px ${systemColor.shadow};
  animation: ${fadeIn} 0.5s ease, ${subtlePulse} 2s ease infinite;
  
  span {
    width: 8px;
    height: 8px;
    margin: 0 3px;
    background-color: rgba(255, 255, 255, 0.9);
    border-radius: 50%;
    display: inline-block;
    
    &:nth-child(1) {
      animation: mediumPulse 1.4s infinite 0.0s;
    }
    &:nth-child(2) {
      animation: mediumPulse 1.4s infinite 0.2s;
    }
    &:nth-child(3) {
      animation: mediumPulse 1.4s infinite 0.4s;
    }
  }
  
  @keyframes mediumPulse {
    0% { opacity: 0.4; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.3); }
    100% { opacity: 0.4; transform: scale(1); }
  }
`; 