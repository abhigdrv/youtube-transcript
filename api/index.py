from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

# Utility function to extract video ID from URL
def extract_video_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.|m\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.match(pattern, url)
    return match.group(1) if match else None

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

if __name__ == '__main__':
    app.run(debug=True)