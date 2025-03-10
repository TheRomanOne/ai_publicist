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
  padding: 0px 16px;
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
  padding: 14px; 18px;
  background-color: ${props => props.isUser ? userColor.bg : systemColor.bg};
  color: ${props => props.isUser ? userColor.text : systemColor.text};
  border-radius: 18px;
  border-bottom-${props => props.isUser ? 'right' : 'left'}-radius: 4px;
  box-shadow: 0 3px 12px ${props => props.isUser ? userColor.shadow : systemColor.shadow};
  overflow-wrap: break-word;
  font-size: 1.3rem;
  line-height: 1.3;
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

// Code block container with expand/collapse functionality
export const CodeBlockContainer = styled.div`
  position: relative;
  margin: 12px 0;
  overflow: hidden;
  border-radius: 8px;
  background-color: #282c34;
  
  /* Refined styling with subtle details */
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  
  /* Smoother height transition */
  transition: all 0.45s cubic-bezier(0.3, 0, 0.2, 1);
  max-height: ${props => props.expanded ? '9000px' : '220px'};
  
  /* Space for the button */
  padding-bottom: ${props => !props.expanded ? '40px' : '0'};
  
  /* Refined gradient overlay for collapsed state */
  &:after {
    content: '';
    display: ${props => props.expanded ? 'none' : 'block'};
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 80px;
    background: linear-gradient(
      to bottom,
      rgba(40, 44, 52, 0),
      rgba(40, 44, 52, 0.95) 65%
    );
    pointer-events: none;
  }
  
  /* Clean code styling */
  pre {
    margin: 0 !important;
    padding: 16px !important;
    border-radius: 8px !important;
    background-color: transparent !important;
  }
  
  code {
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace !important;
    font-size: 0.9rem !important;
    line-height: 1.5 !important;
  }
`;

// Button to expand/collapse code blocks - completely redesigned
export const ExpandButton = styled.button`
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  
  /* Pill-shaped button with gradient */
  background:rgb(23, 51, 1);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 11px;
  font-weight: 500;
  
  /* Remove default button styling */
  cursor: pointer;
  transition: all 0.25s ease;
  
  /* Add subtle shadow and border */
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.15);
  
  /* Center text and icon */
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  
  /* Hover animation */
  &:hover {
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 5px 12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.1);
    background: linear-gradient(90deg, #5a7fbf, #6e6ed8);
  }
  
  &:active {
    transform: translateX(-50%) translateY(-1px);
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.2);
  }
  
  /* Icon styling - using a simple arrow */
  &:before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    border: solid white;
    border-width: 0 2px 2px 0;
    transform: ${props => props.children && props.children.includes('less') ? 'rotate(-135deg)' : 'rotate(45deg)'};
    margin-right: 2px;
    position: relative;
    top: ${props => props.children && props.children.includes('less') ? '1px' : '-1px'};
    transition: transform 0.2s ease;
  }
  
  /* Clean, simple text */
  span {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    letter-spacing: 0.5px;
  }
  
  /* Entrance animation */
  animation: buttonFadeIn 0.4s ease-out;
  
  @keyframes buttonFadeIn {
    from { 
      opacity: 0;
      transform: translateX(-50%) translateY(5px);
    }
    to { 
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }
`; 