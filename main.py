from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import csv
import time
import urllib.parse
import pandas as pd
from playwright.sync_api import sync_playwright
from clips_collector import collect_clip_urls
from clips_downloader import download_clip
import subprocess

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the root directory of the project
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template('collect-clips.html')

@app.route('/collect-clips', methods=['POST'])
def collect_clips():
    try:
        username = request.form.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        # Step 1: Collect clip URLs using clips_collector
        collect_clip_urls(username)
        
        # Step 2: Read the CSV and download clips
        csv_filename = os.path.join(ROOT_DIR, f'outputs/{username}_clips.csv')
        output_dir = os.path.join(ROOT_DIR, f'downloaded_clips/{username}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Read the CSV file
        df = pd.read_csv(csv_filename)
        clip_urls = df['Clip URL'].tolist()
        
        # Download each clip
        for index, clip_url in enumerate(clip_urls, 1):
            try:
                # Create a numbered filename
                clip_id = clip_url.split('/')[-1]
                numbered_filename = f"{index:02d}_{clip_id}.mp4"
                output_path = os.path.join(output_dir, numbered_filename)
                
                # Download the clip with the numbered filename
                subprocess.run([
                    os.getenv("TWITCH_CLI_PATH"),
                    "clipdownload",
                    "--id", clip_id,
                    "--output", output_path
                ], check=True)
                
                # Add a small delay between downloads
                time.sleep(1)
            except Exception as e:
                print(f"Error downloading clip {clip_url}: {str(e)}")
                continue

        return jsonify({
            'message': f'Successfully collected and downloaded clips for {username}',
            'download_dir': output_dir
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
