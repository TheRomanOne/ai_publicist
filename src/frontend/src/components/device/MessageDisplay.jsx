import React, { useState, useEffect, useRef } from 'react';
import { 
  ChatArea,
  MessageContainer,
  Message, 
  TypingIndicator,
  CodeBlockContainer,
  ExpandButton
} from '../../styles/device/MessageDisplay.styles';
import { ERROR_MESSAGES } from '../../utils/constants';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
  const [expandedBlocks, setExpandedBlocks] = useState({});
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
  
  // Toggle code block expansion
  const toggleCodeBlock = (blockId) => {
    setExpandedBlocks(prev => ({
      ...prev,
      [blockId]: !prev[blockId]
    }));
    
    // Small delay to ensure smooth scroll after animation
    setTimeout(() => {
      if (chatAreaRef.current) {
        const element = document.getElementById(`code-block-${blockId}`);
        if (element) {
          const rect = element.getBoundingClientRect();
          const isPartiallyVisible = 
            rect.top < 0 && 
            rect.bottom > 0 && 
            rect.bottom < chatAreaRef.current.clientHeight;
          
          if (isPartiallyVisible) {
            element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        }
      }
    }, 50);
  };
  
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
  
  // Replace the formatMessage function with this enhanced version
  const formatMessage = (content, messageIndex) => {
    if (!content) return '';
    
    // Check if the content contains code blocks
    if (content.includes('```')) {
      // Parse and render code blocks with syntax highlighting
      const segments = [];
      let lastIndex = 0;
      const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
      
      let match;
      let blockCount = 0;
      while ((match = codeBlockRegex.exec(content)) !== null) {
        // Add text before the code block
        if (match.index > lastIndex) {
          const textSegment = content.substring(lastIndex, match.index);
          const formattedText = textSegment
            .replace(/\n/g, "<br>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
          
          segments.push(
            <span 
              key={`text-${lastIndex}`} 
              dangerouslySetInnerHTML={{ __html: formattedText }}
            />
          );
        }
        
        // Add the code block with syntax highlighting
        const language = match[1] || 'text';
        const code = match[2];
        const codeLines = code.split('\n');
        const blockId = `${messageIndex}-${blockCount}`;
        const isExpanded = expandedBlocks[blockId] || false;
        const isTooLong = codeLines.length > 10;
        
        segments.push(
          <CodeBlockContainer 
            key={`code-${match.index}`} 
            id={`code-block-${blockId}`}
            expanded={isExpanded}
          >
            <SyntaxHighlighter
              language={language}
              style={atomDark}
              customStyle={{
                borderRadius: '6px',
                fontSize: '1rem',
                margin: '0',
                maxHeight: isExpanded ? 'none' : (isTooLong ? '200px' : 'none'),
                transition: 'max-height 0.3s ease-in-out'
              }}
              showLineNumbers={true}
              wrapLines={true}
            >
              {code}
            </SyntaxHighlighter>
            
            {isTooLong && (
              <ExpandButton 
                onClick={() => toggleCodeBlock(blockId)}
                role="button"
                tabIndex={0}
              >
                {isExpanded ? 'Show less' : 'Show more'}
              </ExpandButton>
            )}
          </CodeBlockContainer>
        );
        
        blockCount++;
        lastIndex = match.index + match[0].length;
      }
      
      // Add any remaining text after the last code block
      if (lastIndex < content.length) {
        const textSegment = content.substring(lastIndex);
        const formattedText = textSegment
          .replace(/\n/g, "<br>")
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        
        segments.push(
          <span 
            key={`text-${lastIndex}`} 
            dangerouslySetInnerHTML={{ __html: formattedText }}
          />
        );
      }
      
      return segments;
    } else {
      // No code blocks, just format text with bold and line breaks
      let c = content.replace(/\n/g, "<br>");
      c = c.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      return <span dangerouslySetInnerHTML={{ __html: c }} />;
    }
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
              <Message isUser={msg.type === 'user'}>
                {formatMessage(msg.content, index)}
              </Message>
            </MessageContainer>
          );
        })
      )}
    </ChatArea>
  );
};

export default MessageDisplay; 