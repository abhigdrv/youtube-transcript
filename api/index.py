from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
import yt_dlp
import cv2
import os
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image
import io
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

# Utility function to extract video ID from URL
def extract_video_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.|m\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.match(pattern, url)
    return match.group(1) if match else None

def get_video_screenshots(video_url, timestamps):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': f'{temp_dir}/video.mp4',
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            
        # Open the video file
        video_path = f'{temp_dir}/video.mp4'
        cap = cv2.VideoCapture(video_path)
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        screenshots = []
        
        for timestamp in timestamps:
            # Convert timestamp to frame number
            frame_number = int(timestamp * fps)
            
            # Set the frame position
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read the frame
            ret, frame = cap.read()
            
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)
                
                # Save to bytes
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr.seek(0)
                
                # Convert to base64
                base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                
                screenshots.append({
                    'timestamp': timestamp,
                    'image_base64': f'data:image/jpeg;base64,{base64_image}'
                })
        
        cap.release()
        return screenshots

@app.route('/api/transcript', methods=['POST'])
def get_transcript():
    try:
        # Get the request data
        data = request.get_json()
        video_url = data.get('url')

        if not video_url:
            return jsonify({"error": "You must provide a YouTube video URL."}), 400

        # Extract video ID
        video_id = extract_video_id(video_url)

        if not video_id:
            return jsonify({"error": "Invalid YouTube video URL."}), 400

        # Fetch transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return jsonify({"transcript": transcript}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/screenshots', methods=['POST'])
def get_screenshots():
    try:
        data = request.get_json()
        video_url = data.get('url')
        timestamps = data.get('timestamps', [])

        if not video_url:
            return jsonify({"error": "You must provide a YouTube video URL."}), 400

        if not timestamps:
            return jsonify({"error": "You must provide timestamps."}), 400

        if not isinstance(timestamps, list):
            return jsonify({"error": "Timestamps must be provided as a list."}), 400

        # Extract video ID
        video_id = extract_video_id(video_url)

        if not video_id:
            return jsonify({"error": "Invalid YouTube video URL."}), 400

        # Get screenshots with base64 encoding
        screenshots = get_video_screenshots(video_url, timestamps)

        return jsonify({"screenshots": screenshots}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
