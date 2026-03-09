import { useState, useRef, useCallback } from 'react';

const getSupportedMimeType = (): string | null => {
  const types = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4'];
  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return null;
};

export const useMediaCapture = (onCapture: (file: File) => void) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const webcamRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setIsWebcamActive(true);
      if (webcamRef.current) {
        webcamRef.current.srcObject = stream;
        webcamRef.current.play().catch(console.error);
      }
    } catch (error) {
      alert('Could not access webcam.');
    }
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
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType });
        stopWebcam();
        const file = new File([blob], 'motion.webm', { type: blob.type });
        onCapture(file);
      };
      
      mediaRecorder.start(100);
      setIsRecording(true);
      setTimeout(() => mediaRecorder.stop(), 5000); 
    }
  };

  return {
    isRecording,
    isWebcamActive,
    webcamRef,
    startWebcam,
    stopWebcam,
    toggleRecording
  };
};
