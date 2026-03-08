import React, { useState, useRef, useEffect, useCallback } from 'react';
import styled, { keyframes } from 'styled-components';
import { uploadFile, useTemplateVariables } from './bridge';

const getSupportedMimeType = (): string | null => {
  const types = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4'];
  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return null;
};

const spin = keyframes`to { transform: rotate(360deg); }`;
const pulseGlow = keyframes`
  0%, 100% { box-shadow: 0 0 15px rgba(97, 75, 255, 0.4); }
  50% { box-shadow: 0 0 25px rgba(97, 75, 255, 0.7); }
`;

// --- NEW QWEN COLOR PALETTE ---
const COLORS = {
  bgBase: '#090810',      // Deepest purple/black
  bgPanel: '#131120',     // Slightly lighter for the sidebar
  bgCard: '#1C1930',      // Card backgrounds
  primary: '#614BFF',     // Qwen Logo Purple
  primaryHover: '#7662FF',
  textMain: '#FFFFFF',
  textMuted: '#9E97C1',
  border: '#2A2545',
  danger: '#FF4455'
};

const AppContainer = styled.div`
  height: 100svh;
  display: flex;
  background: ${COLORS.bgBase};
  color: ${COLORS.textMain};
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  overflow: hidden;
`;

// --- SIDEBAR (Left Panel) ---
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
    
  /* 1. We replace the old Qwen logo url with your new PUBLIC WORDMARK URL */
  /* (Make sure you screenshot the horizontal wordmark from the image I sent) */
  background: url('/MotionStudio-CompleteLogo.svg') no-repeat center left / contain;
  
  /* 2. Make sure the HTML text disappears (the logo has the text built-in) */
  text-indent: -9999px; /* Hide the HTML text, but keep it accessible */
  width: 600px; /* Set an appropriate width to display the logo */
  height: 100px;  /* Set an appropriate height to display the logo */
  
  /* 3. Turn off the pseudo-element we used before */
  &::before {
    display: none; 
  }
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

// --- STAGE (Right Panel) ---
const Stage = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: radial-gradient(circle at center, #151226 0%, ${COLORS.bgBase} 100%);
`;

// --- SHARED UI COMPONENTS ---
const DropzoneBox = styled.div<{ $isDragging?: boolean; $hasContent?: boolean }>`
  width: 100%;
  aspect-ratio: ${props => props.$hasContent ? 'auto' : '16/9'};
  min-height: 160px;
  background: ${COLORS.bgCard};
  border: 2px dashed ${props => props.$isDragging ? COLORS.primary : COLORS.border};
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  position: relative;

  &:hover {
    border-color: ${COLORS.primaryHover};
    background: #221d3b;
  }
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

// (Re-using standard styled elements for recording/loading internally)
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

const ClearButton = styled.button`
  position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.6);
  color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px;
  cursor: pointer; z-index: 10; backdrop-filter: blur(4px);
  &:hover { background: ${COLORS.danger}; }
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

const PreviewMedia = styled.div`
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  img, video { max-width: 100%; max-height: 240px; object-fit: contain; border-radius: 8px; }
`;


const App: React.FC = () => {
  const initialVariables = useTemplateVariables();
  const [referenceImage, setReferenceImage] = useState<string | null>(initialVariables.reference_image || null);
  const [motionVideo, setMotionVideo] = useState<string | null>(initialVariables.motion_video || null);
  const [finalVideoUrl, setFinalVideoUrl] = useState<string | null>(null);

  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>("Initializing...");

  const [localImageUrl, setLocalImageUrl] = useState<string | null>(null);
  const [localVideoUrl, setLocalVideoUrl] = useState<string | null>(null);

  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const webcamRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (isWebcamActive && webcamRef.current && streamRef.current) {
      webcamRef.current.srcObject = streamRef.current;
      webcamRef.current.play().catch(console.error);
    }
  }, [isWebcamActive]);

  const handleImageUpload = async (file: File) => {
    const localUrl = URL.createObjectURL(file);
    setLocalImageUrl(localUrl);
    setIsUploadingImage(true);
    try {
      const url = await uploadFile(file);
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
      const url = await uploadFile(file);
      if (url) setMotionVideo(url);
    } finally {
      setIsUploadingVideo(false);
    }
  };

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setIsWebcamActive(true);
    } catch (error) { alert('Could not access webcam.'); }
  };

  const stopWebcam = useCallback(() => {
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    setIsWebcamActive(false);
    setIsRecording(false);
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
    } else {
      if (!streamRef.current) return;
      const mediaRecorder = new MediaRecorder(streamRef.current, { mimeType: getSupportedMimeType() || '' });
      mediaRecorderRef.current = mediaRecorder;
      const chunks: Blob[] = [];
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType });
        stopWebcam();
        await handleVideoUpload(new File([blob], 'motion.webm', { type: blob.type }));
      };
      mediaRecorder.start(100);
      setIsRecording(true);
      setTimeout(() => mediaRecorder.stop(), 5000); // Auto stop after 5s
    }
  };

  // The Exact Async Execution Logic we built
  const handleSubmit = async () => {
    if (referenceImage && motionVideo) {
      setIsSubmitting(true);
      setStatusMessage("Starting DAG Execution...");
      try {
        const dagPayload = {
          graph_id: "motion-control-pipeline-v1",
          state: { reference_image: referenceImage, motion_video: motionVideo },
          nodes: [
            { id: "node_ffmpeg_1", type: "ffmpeg_processor", inputs: { video_url: "{{motion_video}}", action: "trim_and_resize" } },
            { id: "node_qwen_1", type: "qwen_video_generator", inputs: { reference_image: "{{reference_image}}", motion_video: "{{node_ffmpeg_1.output_path}}" } }
          ],
          edges: [{ source: "node_ffmpeg_1", target: "node_qwen_1" }]
        };

        const initRes = await fetch('http://localhost:8000/execute-graph', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dagPayload)
        });
        if (!initRes.ok) throw new Error('Failed to start');
        
        const { job_id } = await initRes.json();
        const poll = setInterval(async () => {
          const statRes = await fetch(`http://localhost:8000/job-status/${job_id}`);
          const statData = await statRes.json();
          setStatusMessage(statData.message || "Processing...");
          
          if (statData.status === 'completed') {
            clearInterval(poll);
            setFinalVideoUrl(statData.final_state["node_qwen_1.video_url"]);
            setIsSubmitting(false);
          } else if (statData.status === 'failed') {
            clearInterval(poll);
            alert(`Failed: ${statData.error}`);
            setIsSubmitting(false);
          }
        }, 5000);
      } catch (e) {
        setIsSubmitting(false);
        alert("Server error. Is FastAPI running?");
      }
    }
  };

  const canSubmit = referenceImage && motionVideo && !isSubmitting;

  return (
    <AppContainer>
      {/* LEFT SIDEBAR - INPUTS */}
      <Sidebar>
        <Header>
          <Title>Animate Studio</Title>
          <Subtitle>Powered by Qwen AnimateAnyone</Subtitle>
        </Header>

        <ScrollableInputs>
          {/* IMAGE UPLOAD */}
          <InputSection>
            <SectionHeader>
              <SectionLabel>1. Character Image</SectionLabel>
            </SectionHeader>
            <DropzoneBox 
              $hasContent={!!referenceImage || !!localImageUrl} 
              onClick={() => !isUploadingImage && imageInputRef.current?.click()}
            >
              {(referenceImage || localImageUrl) ? (
                <>
                  <ClearButton onClick={(e) => { e.stopPropagation(); setReferenceImage(null); setLocalImageUrl(null); }}>Clear</ClearButton>
                  <PreviewMedia><img src={localImageUrl || referenceImage || ''} alt="Ref" /></PreviewMedia>
                  {isUploadingImage && <div style={{position:'absolute', background: 'rgba(0,0,0,0.5)', color:'white', width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center'}}>Uploading...</div>}
                </>
              ) : (
                <span style={{ color: COLORS.textMuted, fontSize: '13px' }}>Click to upload image</span>
              )}
            </DropzoneBox>
            <input type="file" ref={imageInputRef} hidden accept="image/*" onChange={(e) => e.target.files?.[0] && handleImageUpload(e.target.files[0])} />
          </InputSection>

          {/* MOTION UPLOAD / RECORD */}
          <InputSection>
            <SectionHeader>
              <SectionLabel>2. Action Template</SectionLabel>
            </SectionHeader>
            <DropzoneBox 
              $hasContent={!!motionVideo || !!localVideoUrl || isWebcamActive}
              onClick={() => { if(!motionVideo && !isWebcamActive) videoInputRef.current?.click() }}
            >
              {isWebcamActive ? (
                <>
                  <PreviewMedia><video ref={webcamRef} autoPlay muted playsInline style={{transform: 'scaleX(-1)'}} /></PreviewMedia>
                  <RecordButton $isRecording={isRecording} onClick={(e) => { e.stopPropagation(); toggleRecording(); }} />
                </>
              ) : (motionVideo || localVideoUrl) ? (
                <>
                  <ClearButton onClick={(e) => { e.stopPropagation(); setMotionVideo(null); setLocalVideoUrl(null); }}>Clear</ClearButton>
                  <PreviewMedia><video src={localVideoUrl || motionVideo || ''} autoPlay loop muted playsInline /></PreviewMedia>
                  {isUploadingVideo && <div style={{position:'absolute', background: 'rgba(0,0,0,0.5)', color:'white', width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center'}}>Uploading...</div>}
                </>
              ) : (
                <div style={{display:'flex', flexDirection:'column', alignItems:'center', gap: '8px'}}>
                  <span style={{ color: COLORS.textMuted, fontSize: '13px' }}>Click to upload video</span>
                  <span style={{ color: COLORS.border, fontSize: '11px' }}>— OR —</span>
                  <button onClick={(e) => { e.stopPropagation(); startWebcam(); }} style={{background: COLORS.border, border: 'none', color: 'white', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px'}}>
                    Use Webcam
                  </button>
                </div>
              )}
            </DropzoneBox>
            <input type="file" ref={videoInputRef} hidden accept="video/*" onChange={(e) => e.target.files?.[0] && handleVideoUpload(e.target.files[0])} />
          </InputSection>
        </ScrollableInputs>

        <ExecuteButton disabled={!canSubmit} onClick={handleSubmit}>
          Generate Animation
        </ExecuteButton>
      </Sidebar>

      {/* RIGHT STAGE - OUTPUT */}
      <Stage>
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
      </Stage>

      {/* LOADING OVERLAY */}
      {isSubmitting && (
        <LoadingOverlay>
          <Spinner />
          <h2 style={{ fontSize: '18px', margin: '0 0 8px 0' }}>Synthesizing Video</h2>
          <p style={{ color: COLORS.primary, fontSize: '14px', fontWeight: 600 }}>{statusMessage}</p>
        </LoadingOverlay>
      )}

    </AppContainer>
  );
};

export default App;