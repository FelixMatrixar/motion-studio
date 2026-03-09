import os
import tempfile
import urllib.request
import asyncio
import ffmpeg
import uuid
from core.interfaces import IMediaProcessor

class FFmpegVideoProcessor(IMediaProcessor):
    def _process_ffmpeg_sync(self, input_url: str, action: str) -> str:
        """Synchronous core for FFmpeg to be run in a separate thread."""
        if input_url.startswith("http://") or input_url.startswith("https://"):
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            urllib.request.urlretrieve(input_url, temp_input)
            target_input = temp_input
            is_temp = True
        else:
            target_input = input_url
            is_temp = False

        output_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_processed.mp4")
        
        try:
            if action == "trim_and_resize":
                (
                    ffmpeg
                    .input(target_input, t=5) 
                    # Scale width to 720, automatically calculate height to preserve aspect ratio. 
                    # The -2 ensures the height is an even number (required by libx264).
                    .filter('scale', 720, -2)
                    .filter('fps', fps=24)
                    .output(output_filename, vcodec='libx264', crf=23, acodec='aac')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            else:
                raise ValueError(f"Unsupported FFmpeg action: {action}")
                
        except ffmpeg.Error as e:
            print(f"FFmpeg stderr: {e.stderr.decode('utf8')}")
            raise RuntimeError("FFmpeg processing failed")
        finally:
            if is_temp and os.path.exists(target_input):
                os.remove(target_input)

        return output_filename

    async def trim_and_resize(self, input_path: str, output_path: str = None) -> str:
        """
        Processes the video. output_path is ignored here as it generates a temp file.
        Returns the path to the processed file.
        """
        print(f"[FFmpeg] Processing video: {input_path}")
        # We ignore output_path because _process_ffmpeg_sync generates a temp file.
        # But the interface requires it, so we can just return the temp file path.
        return await asyncio.to_thread(self._process_ffmpeg_sync, input_path, "trim_and_resize")
