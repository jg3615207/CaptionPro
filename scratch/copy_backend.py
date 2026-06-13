import os
import re

source_dir = r"C:\Ai\Vide_coding\CaptionFlow\voice-pro-repo\app"
dest_dir = r"C:\Ai\Vide_coding\CaptionFlow\WhisperWebUI\backend"

os.makedirs(dest_dir, exist_ok=True)

files_to_process = {
    "abus_asr_parameters.py": "asr_parameters.py",
    "abus_asr_faster_whisper.py": "inference_faster_whisper.py",
    "abus_asr_whisper.py": "inference_whisper.py",
    "abus_asr_whisper_timestamped.py": "inference_whisper_timestamped.py",
    "abus_asr_whisperx.py": "inference_whisperx.py"
}

for src_name, dest_name in files_to_process.items():
    src_path = os.path.join(source_dir, src_name)
    dest_path = os.path.join(dest_dir, dest_name)
    
    if not os.path.exists(src_path):
        print(f"Not found: {src_path}")
        continue
        
    with open(src_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace imports
    # from app.abus_subtitle import ... -> from .subtitles import ...
    content = re.sub(r'from app\.abus_subtitle import .*', 'from .subtitles import get_srt, get_vtt, write_file', content)
    # Remove app.abus_path
    content = re.sub(r'from app\.abus_path import .*', '', content)
    # from app.abus_asr_parameters import ... -> from .asr_parameters import ...
    content = re.sub(r'from app\.abus_asr_parameters import .*', 'from .asr_parameters import WhisperParameters', content)
    # Remove gradio
    content = re.sub(r'import gradio as gr', '', content)
    content = re.sub(r'gr\.Progress\(\)', 'None', content)
    content = re.sub(r'gr\.Progress', 'object', content) # Mock typing
    
    # Provide a simple path_change_ext
    path_func = """
def path_change_ext(filepath, new_ext):
    import os
    base, _ = os.path.splitext(filepath)
    return base + new_ext
"""
    # Insert path_change_ext near top
    if 'class ' in content:
        content = content.replace('class ', path_func + '\nclass ', 1)
        
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Backend files copied and refactored successfully.")
