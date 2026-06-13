import os
import sys
import shutil
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import structlog

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.join(current_dir, "workspace")
os.makedirs(workspace_dir, exist_ok=True)

# Import our consolidated backend modules
from backend.audio import ffmpeg_codec_type, ffmpeg_extract_audio, demucs_split_file
from backend.asr_parameters import WhisperParameters

# Load inference wrappers gracefully
from backend.inference_faster_whisper import FasterWhisperInference
try:
    from backend.inference_whisper import WhisperInference
except ImportError:
    WhisperInference = None

try:
    from backend.inference_whisper_timestamped import WhisperTimestampedInference
except ImportError:
    WhisperTimestampedInference = None

try:
    from backend.inference_whisperx import WhisperXInference
except ImportError:
    WhisperXInference = None

logger = structlog.get_logger()

app = FastAPI(title="Standalone Whisper Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(current_dir, "frontend")
os.makedirs(frontend_path, exist_ok=True)

def get_whisper_inf(engine_name: str):
    switch_dict = {
        'faster-whisper': lambda: FasterWhisperInference(),
        'whisper': lambda: WhisperInference() if WhisperInference else FasterWhisperInference(),
        'whisper-timestamped': lambda: WhisperTimestampedInference() if WhisperTimestampedInference else FasterWhisperInference(),
        'whisperX': lambda: WhisperXInference() if WhisperXInference else FasterWhisperInference()
    }
    return switch_dict.get(engine_name, lambda: FasterWhisperInference())()

def path_change_ext(filepath, new_ext):
    base, _ = os.path.splitext(filepath)
    return base + new_ext

@app.get("/api/config")
async def get_config():
    allowed_models = ["large-v3", "large-v3-turbo"]
    
    inf = FasterWhisperInference()
    try:
        languages = inf.available_langs()
    except Exception:
        languages = ["english", "korean", "japanese", "chinese"]
    
    engines = ['faster-whisper', 'whisper', 'whisper-timestamped', 'whisperX']
    
    try:
        compute_types = FasterWhisperInference.available_compute_types()
    except Exception:
        compute_types = ["default", "float16", "float32", "int8"]

    return {
        "models": allowed_models,
        "engines": engines,
        "languages": languages,
        "compute_types": compute_types
    }

@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    engine: str = Form("faster-whisper"),
    model: str = Form("large-v3"),
    language: str = Form("english"),
    compute_type: str = Form("default"),
    highlight_words: str = Form("false"),
    denoise_level: int = Form(0),
    convert_to_traditional: str = Form("false")
):
    try:
        is_highlight = highlight_words.lower() == "true"
        is_s2t = convert_to_traditional.lower() == "true"
        
        # Save file to workspace
        safe_name = f"{int(time.time())}_{file.filename}"
        source_file_path = os.path.join(workspace_dir, safe_name)
        
        with open(source_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        logger.info(f"File saved to {source_file_path}")
        
        has_audio, has_video = ffmpeg_codec_type(source_file_path)
        if not has_audio and not source_file_path.lower().endswith(('.wav', '.mp3', '.flac', '.ogg')):
            # Fallback if ffprobe fails but it is an audio file
            if not has_video and not has_audio:
                has_audio = True

        if not has_audio:
            raise HTTPException(status_code=400, detail="The uploaded file has no audio track.")
            
        audio_format = "flac"
        input_audio_file = path_change_ext(source_file_path, f'.{audio_format}')
        ffmpeg_extract_audio(source_file_path, input_audio_file, audio_format)
        
        # Denoising
        input_path = input_audio_file
        if denoise_level > 0:
            demucs_model = 'htdemucs' if denoise_level == 1 else 'htdemucs_ft'
            output_dir = os.path.dirname(input_audio_file)
            inst_audio, vocal_audio = demucs_split_file(input_audio_file, output_dir, demucs_model, audio_format)
            input_path = vocal_audio if os.path.exists(vocal_audio) else input_audio_file
            
        # Inference
        params = WhisperParameters(model_size=model, lang=language.lower(), compute_type=compute_type, convert_to_traditional=is_s2t)
        whisper_inf = get_whisper_inf(engine)
        
        # Using progress=None to bypass Gradio
        subtitles = whisper_inf.transcribe_file(input_path, params, is_highlight, None)
        
        srt_file = None
        for s in subtitles:
            if s.endswith('.srt'):
                srt_file = s
                break
                
        srt_content = ""
        if srt_file and os.path.exists(srt_file):
            with open(srt_file, 'r', encoding='utf-8') as f:
                srt_content = f.read()
                
        return JSONResponse(content={
            "success": True,
            "srt_content": srt_content,
            "message": "Transcription successful"
        })
        
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/open-workspace")
async def open_workspace():
    import subprocess
    try:
        if sys.platform == "win32":
            os.startfile(workspace_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", workspace_dir])
        else:
            subprocess.Popen(["xdg-open", workspace_dir])
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to open workspace: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
