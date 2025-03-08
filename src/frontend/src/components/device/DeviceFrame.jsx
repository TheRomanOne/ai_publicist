import React from 'react';
import {
  Frame,
  ScreenContainer,
  SpeakerGrills,
  DeviceHeader,
  PowerLight,
  DeviceDetails
} from '../../styles/device/DeviceFrame.styles';

/**
 * Frame component for the retro device UI
 * 
 * @param {React.ReactNode} children - Child components
 * @param {boolean} isConnected - Connection status with server
 * @param {boolean} isReconnecting - Whether reconnection is in progress
 */
const DeviceFrame = ({ children, isConnected = true, isReconnecting }) => {
  // Create speaker grill elements
  const speakerHoles = [];
  for (let i = 0; i < 3; i++) {
    const holes = [];
    for (let j = 0; j < 3; j++) {
      holes.push(<div key={`${i}-${j}`} className="hole"></div>);
    }
    speakerHoles.push(
      <div key={i} className="speaker">
        {holes}
      </div>
    );
  }

  return (
    <Frame>
      <SpeakerGrills>
        {speakerHoles}
      </SpeakerGrills>
      
      <ScreenContainer>
        <DeviceHeader>
          <div className="title">Mr Agent</div>
        </DeviceHeader>
        {children}
      </ScreenContainer>
      
      <PowerLight isConnected={isConnected} isReconnecting={isReconnecting} />
      <DeviceDetails>By Roman.V</DeviceDetails>
    </Frame>
  );
};

export default DeviceFrame; 