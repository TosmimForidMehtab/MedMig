import os
import litert_lm
from app.config import settings

class AIService:
    def __init__(self):
        self.engine = None
        self.model_path = settings.MODEL_PATH

    def initialize(self):
        if not os.path.exists(self.model_path):
            raise RuntimeError(f"Model not found at {self.model_path}")
        
        self.engine = litert_lm.Engine(
            self.model_path,
            backend=litert_lm.Backend.CPU,
            vision_backend=litert_lm.Backend.CPU,
            audio_backend=litert_lm.Backend.CPU,
        )

    async def generate_response(self, prompt: str, conversation_history: list = None) -> str:
        if not self.engine:
            self.initialize()
            
        content_array = [{"type": "text", "text": prompt}]
        message = {"role": "user", "content": content_array}
        
        with self.engine.create_conversation() as conversation:
            # Note: conversation context management would go here
            response = conversation.send_message(message)
            return response["content"][0]["text"]

    async def infer_document_metadata(self, text_content: str) -> dict:
        """
        Uses Gemma to infer title, type, description and tags from medical text.
        """
        prompt = f"""
Analyze the following medical record text and provide metadata in JSON format.
Fields:
- title: A concise name for the document.
- type: One of [prescription, lab_report, discharge_summary, imaging, medical_certificate, insurance, other].
- description: A 1-sentence summary of the key finding or purpose.
- tags: A list of 3-5 keywords (e.g., "diabetes", "blood test", "cardiology").

Medical Text:
{text_content[:2000]}

Return ONLY valid JSON.
"""
        response_text = await self.generate_response(prompt)
        
        import json
        import re
        try:
            # Try to find JSON block in case model adds prose
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response_text)
        except Exception:
            # Fallback if AI fails to return valid JSON
            return {
                "title": "Inferred Medical Record",
                "type": "other",
                "description": "Metadata extraction failed.",
                "tags": []
            }

    async def extract_health_metrics(self, text_content: str) -> list:
        """
        Uses Gemma to extract all health metrics (vitals, lab results) from medical text.
        """
        prompt = f"""
Analyze the following medical record and extract any health metrics (e.g., blood pressure, glucose, hemoglobin, WBC, RBC, cholesterol, etc.).
Return ONLY a valid JSON array of objects. Each object must have:
- metric_type: A normalized string name (e.g., "hemoglobin", "wbc_count", "systolic_bp").
- value: The numeric value (float).
- unit: The unit of measurement (string).

Medical Text:
{text_content[:2000]}

Return ONLY valid JSON array.
"""
        response_text = await self.generate_response(prompt)
        import json
        import re
        try:
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response_text)
        except Exception:
            return []

ai_service = AIService()
