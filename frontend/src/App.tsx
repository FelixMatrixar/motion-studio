import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { StorageClient } from './services/storageClient';
import { useMediaCapture } from './hooks/useMediaCapture';
import { useJobOrchestrator } from './hooks/useJobOrchestrator';
import { WelcomeModal } from './components/WelcomeModal';
import { MediaUploader } from './components/MediaUploader';
import { WebcamRecorder } from './components/WebcamRecorder';
import { Stage } from './components/Stage';
import { COLORS } from './theme';

const pulseGlow = keyframes`
  0%, 100% { box-shadow: 0 0 15px rgba(97, 75, 255, 0.4); }
  50% { box-shadow: 0 0 25px rgba(97, 75, 255, 0.7); }
`;

const AppContainer = styled.div`
  height: 100svh;
  display: flex;
  background: ${COLORS.bgBase};
  color: ${COLORS.textMain};
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  overflow: hidden;
`;

const Sidebar = styled.div`
  width: 380px;
  background: ${COLORS.bgPanel};
  border-right: 1px solid ${COLORS.border};
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 10;
  box-shadow: 4px 0 24px rgba(0,0,0,0.2);
`;

const Header = styled.div`
  padding: 24px;
  border-bottom: 1px solid ${COLORS.border};
`;

const Title = styled.h1`
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  letter-spacing: -0.5px;
  background: url('/MotionStudio-CompleteLogo.svg') no-repeat center left / contain;
  text-indent: -9999px; 
  width: 600px; 
  height: 100px;  
  &::before { display: none; }
`;

const Subtitle = styled.p`
  font-size: 12px;
  color: ${COLORS.textMuted};
  margin: 0;
`;

const ScrollableInputs = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const InputSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const SectionLabel = styled.h2`
  font-size: 13px;
  font-weight: 600;
  margin: 0;
  color: ${COLORS.textMain};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ExecuteButton = styled.button`
  margin: 24px;
  padding: 16px;
  border-radius: 8px;
  border: none;
  background: ${COLORS.primary};
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 1px;

  &:hover:not(:disabled) {
    background: ${COLORS.primaryHover};
    animation: ${pulseGlow} 2s infinite;
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background: ${COLORS.bgCard};
    color: ${COLORS.textMuted};
  }
`;

const App: React.FC = () => {
  const [showModal, setShowModal] = useState(() => {
    return localStorage.getItem('hideWelcomeModal') !== 'true';
  });

  const dismissModal = () => {
    setShowModal(false);
    localStorage.setItem('hideWelcomeModal', 'true');
  };

  const [referenceImage, setReferenceImage] = useState<string | null>(null);
  const [motionVideo, setMotionVideo] = useState<string | null>(null);
  const [localImageUrl, setLocalImageUrl] = useState<string | null>(null);
  const [localVideoUrl, setLocalVideoUrl] = useState<string | null>(null);

  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);

  const { 
    isRecording, isWebcamActive, webcamRef, 
    startWebcam, toggleRecording 
  } = useMediaCapture(async (file) => {
    // Handle webcam file capture
    await handleVideoUpload(file);
  });

  const { isSubmitting, statusMessage, finalVideoUrl, startJob } = useJobOrchestrator();

  const handleImageUpload = async (file: File) => {
    const localUrl = URL.createObjectURL(file);
    setLocalImageUrl(localUrl);
    setIsUploadingImage(true);
    try {
      const url = await StorageClient.uploadFile(file);
      if (url) setReferenceImage(url);
    } finally {
      setIsUploadingImage(false);
    }
  };

  const handleVideoUpload = async (file: File) => {
    const localUrl = URL.createObjectURL(file);
    setLocalVideoUrl(localUrl);
    setIsUploadingVideo(true);
    try {
      const url = await StorageClient.uploadFile(file);
      if (url) setMotionVideo(url);
    } finally {
      setIsUploadingVideo(false);
    }
  };

  const handleSubmit = () => {
    if (referenceImage && motionVideo) {
      startJob(referenceImage, motionVideo);
    }
  };

  const canSubmit = referenceImage && motionVideo && !isSubmitting;

  return (
    <AppContainer>
      {showModal && <WelcomeModal onDismiss={dismissModal} />}

      <Sidebar>
        <Header>
          <Title>Animate Studio</Title>
          <Subtitle>Powered by Qwen AnimateAnyone</Subtitle>
        </Header>

        <ScrollableInputs>
          <InputSection>
            <SectionHeader>
              <SectionLabel>1. Character Image</SectionLabel>
            </SectionHeader>
            <MediaUploader
              type="image"
              previewUrl={localImageUrl || referenceImage}
              isUploading={isUploadingImage}
              onUpload={handleImageUpload}
              onClear={() => { setReferenceImage(null); setLocalImageUrl(null); }}
            />
          </InputSection>

          <InputSection>
            <SectionHeader>
              <SectionLabel>2. Action Template</SectionLabel>
            </SectionHeader>
            <MediaUploader
              type="video"
              previewUrl={localVideoUrl || motionVideo}
              isUploading={isUploadingVideo}
              onUpload={handleVideoUpload}
              onClear={() => { setMotionVideo(null); setLocalVideoUrl(null); }}
              customContent={isWebcamActive ? (
                <WebcamRecorder 
                  webcamRef={webcamRef} 
                  isRecording={isRecording} 
                  onToggleRecording={toggleRecording} 
                />
              ) : undefined}
              emptyState={
                <div style={{display:'flex', flexDirection:'column', alignItems:'center', gap: '8px'}}>
                  <span style={{ color: COLORS.textMuted, fontSize: '13px' }}>Click to upload video</span>
                  <span style={{ color: COLORS.border, fontSize: '11px' }}>— OR —</span>
                  <button onClick={(e) => { e.stopPropagation(); startWebcam(); }} style={{background: COLORS.border, border: 'none', color: 'white', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px'}}>
                    Use Webcam
                  </button>
                </div>
              }
            />
          </InputSection>
        </ScrollableInputs>

        <ExecuteButton disabled={!canSubmit} onClick={handleSubmit}>
          Generate Animation
        </ExecuteButton>
      </Sidebar>

      <Stage 
        finalVideoUrl={finalVideoUrl} 
        isSubmitting={isSubmitting} 
        statusMessage={statusMessage} 
      />
    </AppContainer>
  );
};

export default App;
