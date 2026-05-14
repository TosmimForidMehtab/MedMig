import os
import uuid
import edge_tts
from app.config import settings

class TTSService:
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def text_to_speech(self, text: str, voice: str = "hi-IN-MadhurNeural") -> str:
        """
        Generates speech from text using edge-tts.
        Returns the path to the generated audio file.
        """
        filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(self.output_dir, filename)
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        
        return output_path

tts_service = TTSService()
