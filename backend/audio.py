import os
import subprocess
import json
import shutil
import structlog

logger = structlog.get_logger()

def ffmpeg_codec_type(input_path: str):
    has_video = False
    has_audio = False
    
    if not os.path.exists(input_path):
        return has_audio, has_video
        
    command = [
        'ffprobe',
        '-loglevel', 'error',
        '-show_entries', 'stream=codec_type',
        '-of', 'json',
        input_path
    ]
    
    try:       
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        if "streams" in data:
            for stream in data["streams"]:
                if stream["codec_type"] == "video":
                    has_video = True
                elif stream["codec_type"] == "audio":
                    has_audio = True
    except Exception as e:
        logger.error(f'ffprobe execution failed: {str(e)}')
    
    return has_audio, has_video


def ffmpeg_extract_audio(input_path: str, output_path: str, audio_format: str = "wav"):  
    encoding_options = "-acodec pcm_s16le -ar 48000 -b:a 320k -ac 2"
    if audio_format == "flac":
        encoding_options = "-acodec flac -ar 48000 -compression_level 0 -ac 2"
    elif audio_format == "mp3":
        encoding_options = "-f mp3 -qscale:a 0 -ar 48000 -ac 2"
    elif audio_format == "ogg":
        encoding_options = "-acodec libvorbis -ar 48000 -b:a 320k -ac 2"
      
    command = f'ffmpeg -y -i "{input_path}" -vn {encoding_options} "{output_path}" -nostdin'    
    os.system(command)  
    return output_path    


def ffmpeg_convert_audio(input_path: str, output_path: str, audio_format: str):
    encoding_options = "-c:a pcm_s16le -ar 48000 -b:a 320k -ac 2"
    if audio_format == "flac":
        encoding_options = "-c:a flac -ar 48000 -compression_level 0 -ac 2"
    elif audio_format == "mp3":
        encoding_options = "-c:a libmp3lame -qscale:a 0 -ar 48000 -ac 2"
    elif audio_format == "ogg":
        encoding_options = "-c:a libvorbis -ar 48000 -b:a 320k -ac 2"
        
    command = f'ffmpeg -y -i "{input_path}" {encoding_options} "{output_path}" -nostdin'             
    os.system(command)


def demucs_split_file(input_path: str, output_dir: str, demucs_model: str, audio_format: str):
    temp_directory = os.path.join(output_dir, "demucs_temp")
    os.makedirs(temp_directory, exist_ok=True)
        
    file_name = os.path.splitext(os.path.basename(input_path))[0]  
    demucs_inst_file = os.path.join(temp_directory, demucs_model, file_name, "no_vocals.wav")
    demucs_vocal_file = os.path.join(temp_directory, demucs_model, file_name, "vocals.wav")

    command = f'python -m demucs.separate -n {demucs_model} --two-stems=vocals "{input_path}" -o "{temp_directory}" --float32'
    os.system(command)
            
    inst_audio_file = os.path.join(output_dir, f"{file_name}_{demucs_model}_inst.{audio_format}")
    vocal_audio_file = os.path.join(output_dir, f"{file_name}_{demucs_model}_vocal.{audio_format}")
    
    if os.path.exists(demucs_inst_file):
        ffmpeg_convert_audio(demucs_inst_file, inst_audio_file, audio_format)
    if os.path.exists(demucs_vocal_file):
        ffmpeg_convert_audio(demucs_vocal_file, vocal_audio_file, audio_format)

    # Cleanup temp
    shutil.rmtree(temp_directory, ignore_errors=True)

    return inst_audio_file, vocal_audio_file
