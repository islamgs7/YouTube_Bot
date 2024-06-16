import os
from moviepy.editor import AudioFileClip

def split_audio(file_path, segment_length=2 * 60):
    """
    Splits the audio file into segments of the specified length.
    
    :param file_path: Path to the input audio file.
    :param segment_length: Length of each segment in seconds (default is 2 minutes).
    """
    audio = AudioFileClip(file_path)
    total_length = int(audio.duration)
    
    # Create output directory
    output_dir = os.path.splitext(file_path)[0] + "_segments"
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(0, total_length, segment_length):
        segment_start = i
        segment_end = min(i + segment_length, total_length)
        segment = audio.subclip(segment_start, segment_end)
        segment_name = os.path.join(output_dir, f"segment_{i // segment_length + 1}.mp3")
        segment.write_audiofile(segment_name, codec='mp3')
        print(f"Exported {segment_name}")

# Example usage
input_file = r"the path to your mp3 file"
split_audio(input_file)
