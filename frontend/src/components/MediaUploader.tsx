import React, { useRef } from 'react';
import styled from 'styled-components';
import { COLORS } from '../theme';

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

const PreviewMedia = styled.div`
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  img, video { max-width: 100%; max-height: 240px; object-fit: contain; border-radius: 8px; }
`;

const ClearButton = styled.button`
  position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.6);
  color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px;
  cursor: pointer; z-index: 10; backdrop-filter: blur(4px);
  &:hover { background: ${COLORS.danger}; }
`;

interface MediaUploaderProps {
  previewUrl: string | null;
  type: 'image' | 'video';
  isUploading: boolean;
  onUpload: (file: File) => void;
  onClear: () => void;
  // Optional content to override default empty state (e.g. webcam button)
  emptyState?: React.ReactNode; 
  // Optional content to override preview (e.g. active webcam)
  customContent?: React.ReactNode;
}

export const MediaUploader: React.FC<MediaUploaderProps> = ({ 
  previewUrl, type, isUploading, onUpload, onClear, emptyState, customContent
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    if (!previewUrl && !customContent) {
      inputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      onUpload(e.target.files[0]);
    }
  };

  const hasContent = !!previewUrl || !!customContent;

  return (
    <>
      <DropzoneBox 
        $hasContent={hasContent} 
        onClick={handleClick}
      >
        {customContent ? (
          customContent
        ) : previewUrl ? (
          <>
            <ClearButton onClick={(e) => { e.stopPropagation(); onClear(); }}>Clear</ClearButton>
            <PreviewMedia>
              {type === 'image' ? (
                <img src={previewUrl} alt="Ref" />
              ) : (
                <video src={previewUrl} autoPlay loop muted playsInline />
              )}
            </PreviewMedia>
            {isUploading && (
              <div style={{position:'absolute', background: 'rgba(0,0,0,0.5)', color:'white', width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center'}}>
                Uploading...
              </div>
            )}
          </>
        ) : (
          emptyState || (
            <span style={{ color: COLORS.textMuted, fontSize: '13px' }}>Click to upload {type}</span>
          )
        )}
      </DropzoneBox>
      <input 
        type="file" 
        ref={inputRef} 
        hidden 
        accept={type === 'image' ? "image/*" : "video/*"} 
        onChange={handleFileChange} 
      />
    </>
  );
};
