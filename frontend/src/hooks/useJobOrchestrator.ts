import { useState } from 'react';
import { ApiClient } from '../services/apiClient';

export const useJobOrchestrator = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>("Initializing...");
  const [finalVideoUrl, setFinalVideoUrl] = useState<string | null>(null);

  const startJob = async (referenceImage: string, motionVideo: string) => {
    setIsSubmitting(true);
    setStatusMessage("Starting DAG Execution...");
    setFinalVideoUrl(null);

    try {
      const dagPayload = {
        graph_id: "motion-control-pipeline-v2",
        state: { reference_image: referenceImage, motion_video: motionVideo },
        nodes: [
          { 
            id: "node_ffmpeg_1", 
            type: "ffmpeg_processor", 
            inputs: { video_url: "{{motion_video}}", action: "trim_and_resize" } 
          },
          {
            id: "node_template_1",
            type: "alibaba_template_generator",
            inputs: { video_url: "{{node_ffmpeg_1.output_path}}" }
          },
          {
            id: "node_image_1",
            type: "alibaba_image_detector",
            inputs: { image_url: "{{reference_image}}" }
          },
          { 
            id: "node_qwen_1", 
            type: "qwen_video_generator", 
            inputs: { 
              validated_image_url: "{{node_image_1.validated_image_url}}", 
              template_id: "{{node_template_1.template_id}}",
              prompt: "apply the motion to the reference image" 
            } 
          }
        ],
        edges: [
          { source: "node_ffmpeg_1", target: "node_template_1" },
          { source: "node_template_1", target: "node_qwen_1" },
          { source: "node_image_1", target: "node_qwen_1" }
        ]
      };

      const { job_id } = await ApiClient.executeGraph(dagPayload);

      const poll = setInterval(async () => {
        try {
          const statData = await ApiClient.getJobStatus(job_id);
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
        } catch (e) {
            console.error(e);
        }
      }, 5000);

    } catch (e) {
      setIsSubmitting(false);
      alert("Server error. Is FastAPI running?");
    }
  };

  return {
    isSubmitting,
    statusMessage,
    finalVideoUrl,
    startJob
  };
};
