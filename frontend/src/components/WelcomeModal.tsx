import React from 'react';
import styled from 'styled-components';
import { COLORS } from '../theme';

const ModalOverlay = styled.div`
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(9, 8, 16, 0.85); backdrop-filter: blur(12px);
  display: flex; align-items: center; justify-content: center; z-index: 2000;
`;

const ModalCard = styled.div`
  background: ${COLORS.bgPanel};
  border: 1px solid ${COLORS.border};
  border-radius: 16px;
  padding: 40px;
  max-width: 760px;
  width: 90%;
  box-shadow: 0 32px 120px rgba(0,0,0,0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
`;

const ModalTitle = styled.h2`
  font-size: 24px; font-weight: 700; color: ${COLORS.textMain}; margin: 0;
`;

const ModalText = styled.p`
  font-size: 15px; color: ${COLORS.textMuted}; margin: 0; text-align: center; line-height: 1.5;
`;

const ExampleRow = styled.div`
  display: flex; align-items: center; gap: 16px; width: 100%; justify-content: center;
  margin: 16px 0;
`;

const ExampleBox = styled.div`
  background: ${COLORS.bgCard}; border: 1px solid ${COLORS.border};
  border-radius: 12px; padding: 12px; display: flex; flex-direction: column;
  align-items: center; gap: 12px; width: 180px;
  
  span { font-size: 12px; font-weight: 600; color: ${COLORS.textMuted}; text-transform: uppercase; }
  img, video { width: 100%; height: 200px; object-fit: cover; border-radius: 8px; }
`;

const PlusMath = styled.div`
  font-size: 24px; color: ${COLORS.textMuted}; font-weight: bold;
`;

const StartButton = styled.button`
  padding: 14px 32px; border-radius: 8px; border: none;
  background: ${COLORS.primary}; color: white; font-size: 15px; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease; margin-top: 8px;
  &:hover { background: ${COLORS.primaryHover}; transform: translateY(-2px); }
`;

interface WelcomeModalProps {
  onDismiss: () => void;
}

export const WelcomeModal: React.FC<WelcomeModalProps> = ({ onDismiss }) => {
  return (
    <ModalOverlay onClick={onDismiss}>
      <ModalCard onClick={(e) => e.stopPropagation()}>
        <ModalTitle>Welcome to Animate Studio</ModalTitle>
        <ModalText>
          Bring any character to life. Just upload a clear, full-body character image and a motion template video to generate your AI animation.
        </ModalText>
        
        <ExampleRow>
          <ExampleBox>
            <span>1. Character</span>
            <img src="https://bbgljtsebzqqlspagmfs.supabase.co/storage/v1/object/public/motion-studio-media/intro/black-bear.jpg" alt="Example Bear" />
          </ExampleBox>
          
          <PlusMath>+</PlusMath>
          
          <ExampleBox>
            <span>2. Motion</span>
            <video src="https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/en-US/20250704/xwikan/2.mp4" autoPlay loop muted playsInline />
          </ExampleBox>
          
          <PlusMath>=</PlusMath>
          
          <ExampleBox style={{ borderColor: COLORS.primary, boxShadow: `0 0 20px rgba(97, 75, 255, 0.2)` }}>
            <span style={{ color: COLORS.primary }}>Result</span>
            <video 
              src="https://bbgljtsebzqqlspagmfs.supabase.co/storage/v1/object/public/motion-studio-media/intro/black-bear-dancing.mp4" 
              autoPlay 
              loop 
              muted 
              playsInline 
              style={{ width: '100%', height: '200px', objectFit: 'cover', borderRadius: '8px', border: `1px solid ${COLORS.primary}` }}
            />
          </ExampleBox>
        </ExampleRow>

        <StartButton onClick={onDismiss}>
          Got it, let's animate
        </StartButton>
      </ModalCard>
    </ModalOverlay>
  );
};
