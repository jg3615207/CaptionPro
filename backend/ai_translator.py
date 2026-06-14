import json
import logging
import time
from typing import List, Dict, Optional
import pysubs2
from openai import OpenAI
import structlog

logger = structlog.get_logger()

class AITranslator:
    def __init__(self, api_base="http://localhost:1234/v1", model_name="local-model"):
        self.api_base = api_base
        self.model_name = model_name
        self.client = OpenAI(base_url=self.api_base, api_key="lm-studio")
        self.chunk_size = 40  # Number of subtitles per chunk
        
    def _create_prompt(self, target_lang: str) -> str:
        return f"""You are a professional subtitle translator.
Translate the following subtitle text into {target_lang}.
You will receive a JSON array of objects. Each object has an 'id' and 'text'.
Your task is to translate the 'text' field while keeping the 'id' exactly the same.
Return ONLY a valid JSON array of objects, with NO markdown formatting, NO backticks, and NO additional text.
Example input:
[
  {{"id": 0, "text": "Hello, how are you?"}},
  {{"id": 1, "text": "I am fine, thank you."}}
]
Example output:
[
  {{"id": 0, "text": "你好，你好嗎？"}},
  {{"id": 1, "text": "我很好，謝謝。"}}
]"""

    def translate_srt(self, file_path: str, target_lang: str, output_path: str = None) -> str:
        logger.info(f"Starting AI translation for {file_path} to {target_lang}")
        
        subs = pysubs2.load(file_path, encoding="utf-8")
        total_subs = len(subs)
        
        # Split into chunks
        chunks = []
        for i in range(0, total_subs, self.chunk_size):
            chunk_subs = subs[i:i + self.chunk_size]
            chunk_data = [{"id": j, "text": sub.text} for j, sub in enumerate(chunk_subs)]
            chunks.append({
                "start_idx": i,
                "data": chunk_data
            })
            
        logger.info(f"Split {total_subs} subtitles into {len(chunks)} chunks.")
        
        # Translate each chunk
        for chunk_idx, chunk in enumerate(chunks):
            logger.info(f"Translating chunk {chunk_idx + 1}/{len(chunks)}...")
            translated_data = self._translate_chunk_with_retry(chunk["data"], target_lang)
            
            # Map translated text back to original subs
            start_idx = chunk["start_idx"]
            for item in translated_data:
                idx = item.get("id")
                new_text = item.get("text", "")
                if idx is not None and 0 <= idx < len(chunk["data"]):
                    subs[start_idx + idx].text = new_text
                    
        # Save translated SRT
        if not output_path:
            output_path = file_path.replace(".srt", f"_{target_lang}.srt")
            
        subs.save(output_path, encoding="utf-8")
        logger.info(f"Translation complete. Saved to {output_path}")
        return output_path

    def _translate_chunk_with_retry(self, chunk_data: List[Dict], target_lang: str, max_retries: int = 3) -> List[Dict]:
        system_prompt = self._create_prompt(target_lang)
        user_content = json.dumps(chunk_data, ensure_ascii=False)
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.3,
                )
                
                content = response.choices[0].message.content.strip()
                
                # Cleanup potential markdown formatting from LLM
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                    
                content = content.strip()
                
                translated_data = json.loads(content)
                
                # Basic validation
                if len(translated_data) != len(chunk_data):
                    logger.warning(f"Length mismatch in chunk (expected {len(chunk_data)}, got {len(translated_data)}). Retrying...")
                    continue
                    
                return translated_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.error(f"Error during API call on attempt {attempt + 1}: {e}")
                
            time.sleep(2)
            
        logger.error("Max retries reached for chunk. Returning original text as fallback.")
        return chunk_data

