from flask import Flask, request, jsonify, render_template_string
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import requests
import re
import os



app = Flask(__name__)

# Styled HTML content
html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Transcript Downloader</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/axios/0.21.1/axios.min.js"></script>
    <style>
        body {
            font-family: 'Comic Sans MS', cursive, sans-serif;
            background: linear-gradient(to bottom, #ffe4e1, #ffebcd);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            color: #555;
            text-align: center;
        }

        h1 {
            font-size: 2.5em;
            font-weight: bold;
            color: #fa8072;
            margin-bottom: 20px;
        }

        .input-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 90%;
            max-width: 600px;
            margin-top: 20px;
        }

        input, select, button {
            width: 100%;
            padding: 12px;
            margin: 5px 0;
            border: 2px dashed #fa8072;
            border-radius: 10px;
            font-size: 1em;
            background-color: #fff;
        }

        button {
            background-color: #fa8072;
            color: #fff;
            cursor: pointer;
            border: none;
            transition: background-color 0.3s, transform 0.3s;
            font-family: 'Comic Sans MS', cursive, sans-serif;
        }

        button:hover {
            background-color: #ff6347;
            transform: scale(1.05);
        }

        #webhookResponse {
            white-space: pre-wrap;
            background-color: #fffaf0;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            width: 90%;
            max-width: 600px;
            text-align: center;
            border: 2px solid #fa8072;
        }

        /* Cute cooking easter egg */
        .cooking-easter-egg {
            font-size: 1.2em;
            margin-top: 20px;
            color: #ff4500;
        }
    </style>
</head>
<body>
    <h1>Welcome to Your Cute Kitchen</h1>
    <div class="input-container">
        <input type="text" id="youtubeInput" placeholder="Paste a YouTube Link Here" aria-label="YouTube Link" />
        <select id="categorySelect" aria-label="Category">
            <option value="Cooking">Cooking</option>
            <option value="Podcasts">Podcasts</option>
        </select>
        <button onclick="processInput()">Let's Cook Up a Recipe!</button>
    </div>
    <div id="webhookResponse"></div>
    <div class="cooking-easter-egg">
        🍰 Did you know? Great cookies are made with a dash of love and a hint of creativity! 🍪
    </div>
    <script>
        async function processInput() {
            const youtubeInput = document.getElementById('youtubeInput').value;
            const category = document.getElementById('categorySelect').value;

            document.getElementById('webhookResponse').textContent = 'Whipping up something delightful...';

            try {
                const response = await axios.post('/get_transcript', {
                    youtube_url: youtubeInput,
                    category: category
                });

                document.getElementById('webhookResponse').textContent = `Received: ${response.data.response}`;
            } catch (error) {
                document.getElementById('webhookResponse').textContent = `Oh no, an error occurred! ${error.response ? error.response.data.message : error.message}`;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(html_content)

def get_video_id(youtube_url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, youtube_url)
    return match.group(1) if match else None

def get_video_title(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = re.findall(r'<title>(.*?) - YouTube</title>', response.text)
        return matches[0] if matches else "Unknown"
    except requests.RequestException as e:
        print(f"Error fetching video title: {e}")
        return "Unknown"

def download_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(['en'])
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript.fetch())
        transcript_text = re.sub(r'\[.*?\]', '', transcript_text)
        return transcript_text
    except Exception as e:
        print(f"Error downloading transcript: {e}")
        return ""

@app.route('/get_transcript', methods=['POST'])
def get_transcript():
    data = request.get_json()
    youtube_url = data.get('youtube_url')
    category = data.get('category')
    webhook_url = 'https://hook.eu2.make.com/2k4rkl600pe8ivnib9c8lrfrl2denpmx'
    video_id = get_video_id(youtube_url)
    if video_id:
        transcript_text = download_transcript(video_id)
        if transcript_text:
            video_title = get_video_title(video_id)
            try:
                response = requests.post(webhook_url, json={
                    'transcript': transcript_text,
                    'youtube_url': youtube_url,
                    'video_title': video_title,
                    'category': category
                }, headers={'Content-Type': 'application/json'})
                return jsonify({'status': 'success', 'response': response.text}), 200
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        else:
            return jsonify({'status': 'error', 'message': 'Unable to download transcript.'}), 500
    else:
        return jsonify({'status': 'error', 'message': 'Invalid YouTube URL.'}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
