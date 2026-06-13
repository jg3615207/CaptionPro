import re
import time

def timeformat_srt(time_val):
    hours = time_val // 3600
    minutes = (time_val - hours * 3600) // 60
    seconds = time_val - hours * 3600 - minutes * 60
    milliseconds = (time_val - int(time_val)) * 1000
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{int(milliseconds):03d}"

def timeformat_vtt(time_val):
    hours = time_val // 3600
    minutes = (time_val - hours * 3600) // 60
    seconds = time_val - hours * 3600 - minutes * 60
    milliseconds = (time_val - int(time_val)) * 1000
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{int(milliseconds):03d}"

def write_file(subtitle, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(subtitle)

def get_srt(segments):
    output = ""
    for i, segment in enumerate(segments):
        output += f"{i + 1}\n"
        output += f"{timeformat_srt(segment['start'])} --> {timeformat_srt(segment['end'])}\n"
        if segment['text'].startswith(' '):
            segment['text'] = segment['text'][1:]
        output += f"{segment['text']}\n\n"
    return output

def get_vtt(segments):
    output = "WebVTT\n\n"
    for i, segment in enumerate(segments):
        output += f"{i + 1}\n"
        output += f"{timeformat_vtt(segment['start'])} --> {timeformat_vtt(segment['end'])}\n"
        if segment['text'].startswith(' '):
            segment['text'] = segment['text'][1:]
        output += f"{segment['text']}\n\n"
    return output

def get_txt(segments):
    output = ""
    for i, segment in enumerate(segments):
        if segment['text'].startswith(' '):
            segment['text'] = segment['text'][1:]
        output += f"{segment['text']}\n"
    return output

def get_srt_wordlevel(segments):
    output = ""
    i = 0
    for segment in segments:
        for word in segment.get('words', []):
            i += 1
            output += f"{i}\n"
            output += f"{timeformat_srt(word.start)} --> {timeformat_srt(word.end)}\n"
            
            striped = word.word.strip()
            highlighted = f'<font color=\"#0e556a\"><b><u>{striped}</u></b></font>'
            line = segment['text'].replace(striped, highlighted)

            output += f"{line}\n\n"    
    return output

def apply_post_processing(segments, params):
    if getattr(params, 'convert_to_traditional', False):
        try:
            import opencc
            # Using s2hk for Simplified to Traditional (Hong Kong standard) as requested
            converter = opencc.OpenCC('s2hk.json')
            for segment in segments:
                if 'text' in segment and segment['text']:
                    segment['text'] = converter.convert(segment['text'])
                if 'words' in segment and segment['words']:
                    # faster-whisper returns objects with .word, whisperx returns dicts with 'word'
                    for w in segment['words']:
                        if isinstance(w, dict) and 'word' in w:
                            w['word'] = converter.convert(w['word'])
                        elif hasattr(w, 'word'):
                            w.word = converter.convert(w.word)
        except Exception as e:
            print(f"Failed to convert to traditional Chinese: {e}")
    return segments

def safe_filename(name):
    return f'{name}-{int(time.time())}'
