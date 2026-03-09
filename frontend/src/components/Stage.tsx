import React from 'react';
import styled, { keyframes } from 'styled-components';
import { COLORS } from '../theme';

const spin = keyframes`to { transform: rotate(360deg); }`;

const StageContainer = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: radial-gradient(circle at center, #151226 0%, ${COLORS.bgBase} 100%);
`;

const LoadingOverlay = styled.div`
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(9, 8, 16, 0.85); backdrop-filter: blur(8px);
  display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000;
`;

const Spinner = styled.div`
  width: 50px; height: 50px; border: 4px solid ${COLORS.bgCard};
  border-top-color: ${COLORS.primary}; border-radius: 50%; animation: ${spin} 1s linear infinite; margin-bottom: 20px;
`;

interface StageProps {
  finalVideoUrl: string | null;
  isSubmitting: boolean;
  statusMessage: string;
}

export const Stage: React.FC<StageProps> = ({ finalVideoUrl, isSubmitting, statusMessage }) => {
  return (
    <StageContainer>
      {!finalVideoUrl && !isSubmitting && (
        <div style={{ textAlign: 'center', color: COLORS.textMuted }}>
          <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.2 }}>✨</div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: COLORS.textMain, margin: '0 0 8px 0' }}>Ready to Animate</h2>
          <p style={{ fontSize: '14px', maxWidth: '300px', margin: 0, lineHeight: 1.5 }}>
            Upload a character image and an action template in the sidebar to generate your video.
          </p>
        </div>
      )}

      {finalVideoUrl && (
        <video 
          src={finalVideoUrl} 
          controls autoPlay loop 
          style={{ maxWidth: '80%', maxHeight: '80%', borderRadius: '12px', boxShadow: '0 24px 80px rgba(0,0,0,0.6)', border: `1px solid ${COLORS.border}` }}
        />
      )}

      {isSubmitting && (
        <LoadingOverlay>
          <Spinner />
          <h2 style={{ fontSize: '18px', margin: '0 0 8px 0' }}>Synthesizing Video</h2>
          <p style={{ color: COLORS.primary, fontSize: '14px', fontWeight: 600 }}>{statusMessage}</p>
        </LoadingOverlay>
      )}
    </StageContainer>
  );
};
