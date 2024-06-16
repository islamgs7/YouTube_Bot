import os
import random
import requests
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, CompositeAudioClip, clips_array, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# Facts data
facts = [
    "the Facts"
]

# Paths to output directories
audio_dir = "audio_clips"
merged_output_dir = "output_merged_videos"
os.makedirs(audio_dir, exist_ok=True)
os.makedirs(merged_output_dir, exist_ok=True)

def generate_audio(text, filename):
    tts = gTTS(text)
    tts.save(filename)
    return filename

def get_random_video_from_pexels(api_key, min_duration=7):
    queries = ["history", "nature", "geography", "culture"]
    query = random.choice(queries)
    
    url = "https://api.pexels.com/videos/search"
    headers = {
        'Authorization': api_key
    }
    params = {
        'query': query,
        'per_page': 1,
        'orientation': 'landscape',
        'min_duration': min_duration,
        'page': random.randint(1, 100)
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    videos = response.json()['videos']
    highest_res_video = max(videos, key=lambda video: max(file['height'] for file in video['video_files']))
    video_file = max(highest_res_video['video_files'], key=lambda file: file['height'])
    video_url = video_file['link']
    video_path = f"random_video_{random.randint(1, 10000)}.mp4"
    video_data = requests.get(video_url).content
    with open(video_path, 'wb') as f:
        f.write(video_data)
    return video_path

def create_text_image(text, img_path="text.png"):
    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))  # Use landscape dimensions
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 35)  # Adjusted font size for better readability

    # Text wrapping every 5 words
    words = text.split()
    lines = [" ".join(words[i:i + 5]) for i in range(0, len(words), 5)]
    
    y_text = (img.height - len(lines) * draw.textbbox((0, 0), lines[0], font=font)[3]) // 2
    for line in lines:
        width, height = draw.textbbox((0, 0), line, font=font)[2:]
        # Draw text border (black)
        draw.text(((img.width - width) // 2 - 2, y_text - 2), line, font=font, fill="black")
        draw.text(((img.width - width) // 2 + 2, y_text - 2), line, font=font, fill="black")
        draw.text(((img.width - width) // 2 - 2, y_text + 2), line, font=font, fill="black")
        draw.text(((img.width - width) // 2 + 2, y_text + 2), line, font=font, fill="black")
        # Draw text (white)
        draw.text(((img.width - width) // 2, y_text), line, font=font, fill="white")
        y_text += height

    img.save(img_path)
    return img_path

def get_random_music_file(music_folder):
    music_files = [os.path.join(music_folder, f) for f in os.listdir(music_folder) if f.endswith('.mp3')]
    return random.choice(music_files) if music_files else None

def merge_videos_with_text(top_video_path, bottom_video_path, facts, fact_audio_files, music_file, target_width=1080):
    try:
        if not os.path.exists(top_video_path):
            print(f"Top video file not found: {top_video_path}")
            return None

        top_clip = VideoFileClip(top_video_path).without_audio()  # Mute the first video
        bottom_clip = VideoFileClip(bottom_video_path)

        min_width = min(top_clip.w, bottom_clip.w)
        top_clip = top_clip.resize(width=min_width)
        bottom_clip = bottom_clip.resize(width=min_width)

        top_clip = top_clip.resize(width=target_width)
        bottom_clip = bottom_clip.resize(width=target_width)

        total_duration = sum(AudioFileClip(f).duration for f in fact_audio_files)
        
        # Ensure the bottom clip is long enough by looping it if necessary
        if bottom_clip.duration < total_duration:
            loop_count = int(total_duration // bottom_clip.duration) + 1
            bottom_clip = concatenate_videoclips([bottom_clip] * loop_count).set_duration(total_duration)
        else:
            bottom_clip = bottom_clip.subclip(0, total_duration)

        # Loop top clip if necessary
        if top_clip.duration < total_duration:
            loop_count = int(total_duration // top_clip.duration) + 1
            top_clip = concatenate_videoclips([top_clip] * loop_count).set_duration(total_duration)
        else:
            top_clip = top_clip.subclip(0, total_duration)

        final_clip = clips_array([[top_clip], [bottom_clip]])

        final_clip = final_clip.set_duration(total_duration)

        final_height = final_clip.h
        final_width = int(final_height * 9 / 16)
        x_center = final_clip.w / 2
        x1 = x_center - final_width / 2
        x2 = x_center + final_width / 2

        final_clip = final_clip.crop(x1=x1, x2=x2)

        fact_clips = []
        start_time = 0
        for fact, fact_audio_file in zip(facts, fact_audio_files):
            fact_audio = AudioFileClip(fact_audio_file)
            fact_audio_duration = fact_audio.duration

            text_image_path = create_text_image(fact)
            text_clip = ImageClip(text_image_path).set_duration(fact_audio_duration).set_position('center')
            fact_clip = CompositeVideoClip([final_clip.subclip(start_time, start_time + fact_audio_duration), text_clip])
            fact_clip = fact_clip.set_audio(fact_audio)
            fact_clips.append(fact_clip)

            start_time += fact_audio_duration

        final_fact_video = concatenate_videoclips(fact_clips)

        background_music = AudioFileClip(music_file).subclip(0, total_duration) if music_file else None
        if background_music:
            final_audio = CompositeAudioClip([final_fact_video.audio, background_music.volumex(0.1)])
            final_fact_video = final_fact_video.set_audio(final_audio)

        return final_fact_video

    except Exception as e:
        print(f"An error occurred while merging videos: {e}")
        return None

# Pexels API key
pexels_api_key = "pexels_api_key"
music_folder = "the path to your music_folder"
top_video_dir = "the path to your top_video_dir"
bottom_video_dir = "the path to your bottom_video_dir"

batch_size = 3
for batch_index in range(0, len(facts), batch_size):
    batch_facts = facts[batch_index:batch_index + batch_size]

    fact_audio_files = []
    for i, fact in enumerate(batch_facts):
        audio_path = os.path.join(audio_dir, f"fact_{batch_index + i}.mp3")
        generate_audio(fact, audio_path)
        fact_audio_files.append(audio_path)

    total_fact_duration = sum(AudioFileClip(f).duration for f in fact_audio_files)

    background_video_path = get_random_video_from_pexels(pexels_api_key, min_duration=total_fact_duration)
    
    top_video_path = os.path.join(top_video_dir, f"split_{batch_index // batch_size}.mp4")
    music_file = get_random_music_file(music_folder)

    final_video = merge_videos_with_text(top_video_path, background_video_path, batch_facts, fact_audio_files, music_file)

    if final_video:
        final_video_path = os.path.join(merged_output_dir, f"Fun_fact_{batch_index // batch_size}.mp4")
        final_video.write_videofile(final_video_path, codec='libx264', audio_codec='aac')
        print(f"Created final video: {final_video_path}")
