import React from 'react';
import styled from 'styled-components';
import { COLORS } from '../theme';

const RecordButton = styled.button<{ $isRecording: boolean }>`
  width: 48px; height: 48px; border-radius: 50%;
  border: 2px solid ${COLORS.danger};
  background: ${props => props.$isRecording ? COLORS.danger : 'transparent'};
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s ease; position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); z-index: 10;
  &::after {
    content: ''; width: ${props => props.$isRecording ? '16px' : '24px'};
    height: ${props => props.$isRecording ? '16px' : '24px'};
    background: ${props => props.$isRecording ? '#fff' : COLORS.danger};
    border-radius: ${props => props.$isRecording ? '4px' : '50%'};
    transition: all 0.2s ease;
  }
`;

const PreviewMedia = styled.div`
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  img, video { max-width: 100%; max-height: 240px; object-fit: contain; border-radius: 8px; }
`;

interface WebcamRecorderProps {
  webcamRef: React.RefObject<HTMLVideoElement | null>;
  isRecording: boolean;
  onToggleRecording: () => void;
}

export const WebcamRecorder: React.FC<WebcamRecorderProps> = ({ webcamRef, isRecording, onToggleRecording }) => {
  return (
    <>
      <PreviewMedia>
        <video ref={webcamRef} autoPlay muted playsInline style={{transform: 'scaleX(-1)'}} />
      </PreviewMedia>
      <RecordButton 
        $isRecording={isRecording} 
        onClick={(e) => { e.stopPropagation(); onToggleRecording(); }} 
      />
    </>
  );
};
