import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';

// Physical TV-like device frame
export const Frame = styled.div`
  width: 850px;
  height: 750px;
  background: linear-gradient(to bottom, #D97E00, #CC6600, #B35900);
  border-radius: 25px;
  padding: 30px;
  position: relative;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  border: 2px solid #B35900;
  display: flex;
  justify-content: center;
  align-items: center;
`;

// TV Screen container
export const ScreenContainer = styled.div`
  width: calc(100% - 20px);
  height: calc(100% - 20px);
  background: #FFFFFF;
  border-radius: 15px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  border: 12px solid #4D3319;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.2);
`;

// Speaker grills
export const SpeakerGrills = styled.div`
  position: absolute;
  top: 16px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 20px;
  
  .speaker {
    width: 120px;
    height: 8px;
    background: #995200;
    border-radius: 4px;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
  }
`;

// App header bar
export const DeviceHeader = styled.div`
  height: 50px;
  background: linear-gradient(to right, #FF8000, #FF9933, #FF8000);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 15px;
  border-bottom: 2px solid #FF8000;
  position: relative;
  
  .title {
    font-family: 'Arial', sans-serif;
    font-size: 20px;
    font-weight: bold;
    color: #FFFFFF;
    letter-spacing: 0.5px;
    text-shadow: 1px 1px 0 rgba(0, 0, 0, 0.2);
  }
`;

// Add blinking animation for reconnecting state
const reconnectBlink = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
`;

// Power indicator light
export const PowerLight = styled.div`
  position: absolute;
  bottom: 15px;
  right: 15px;
  width: 12px;
  height: 12px;
  background: ${props => {
    if (props.isReconnecting) return '#FFAA33';
    return props.isConnected ? '#5FFF5F' : '#FF5F5F';
  }};
  border-radius: 50%;
  box-shadow: 0 0 8px ${props => {
    if (props.isReconnecting) return 'rgba(255, 170, 51, 0.7)';
    return props.isConnected ? 'rgba(95, 255, 95, 0.7)' : 'rgba(255, 95, 95, 0.7)';
  }};
  animation: ${props => props.isReconnecting ? reconnectBlink : 'blink'} ${props => props.isReconnecting ? '0.8s' : '4s'} infinite;
  z-index: 10;
  
  @keyframes blink {
    0%, 98%, 100% { opacity: 1; }
    99% { opacity: 0.5; }
  }
`;

// Model plate
export const DeviceDetails = styled.div`
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-family: 'Arial', sans-serif;
  font-size: 12px;
  font-weight: bold;
  color: #FFFFFF;
  background: #995200;
  padding: 3px 15px;
  border-radius: 0 0 8px 8px;
  border: 1px solid #4D3319;
  border-top: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
`; 