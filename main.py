from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright
from clips_collector import collect_clip_urls
from clips_downloader import download_clip
import subprocess
import ffmpeg

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the root directory of the project
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def concatenate_clips(username):
    try:
        clips_dir = os.path.join(ROOT_DIR, f'downloaded_clips/{username}')
        if not os.path.exists(clips_dir):
            return False, "Clips directory not found"

        # Get all video files in the directory
        video_files = sorted([f for f in os.listdir(clips_dir) if f.endswith('.mp4') and not f.endswith('_compilation.mp4')])
        if not video_files:
            return False, "No video clips found"

        # Create a temporary file list for ffmpeg
        temp_list = os.path.join(ROOT_DIR, 'temp_file_list.txt')
        try:
            with open(temp_list, 'w', encoding='utf-8') as f:
                for video in video_files:
                    abs_path = os.path.abspath(os.path.join(clips_dir, video))
                    f.write(f"file '{abs_path}'\n")

            # Concatenate all videos with better handling of audio/video sync
            output_file = os.path.join(clips_dir, f'{username}_compilation.mp4')
            
            # Use ffmpeg-python to handle the concatenation with better options
            stream = ffmpeg.input(temp_list, format='concat', safe=0)
            stream = ffmpeg.output(
                stream,
                output_file,
                c='copy',
                vsync='vfr',  # Variable frame rate
                acodec='copy',
                vcodec='copy',
                loglevel='error'  # Reduce noise in output
            )
            ffmpeg.run(stream, overwrite_output=True)
            
            return True, f"Successfully created compilation at {output_file}"
        except ffmpeg.Error as e:
            return False, f"FFmpeg error: {e.stderr.decode()}"
        except Exception as e:
            return False, f"Error during concatenation: {str(e)}"
        finally:
            if os.path.exists(temp_list):
                try:
                    os.remove(temp_list)
                except Exception as e:
                    print(f"Error removing temporary file: {str(e)}")
    except Exception as e:
        return False, f"Error in concatenation process: {str(e)}"

@app.route('/')
def index():
    return render_template('collect-clips.html')

@app.route('/collect-clips', methods=['POST'])
def collect_clips():
    try:
        username = request.form.get('username')
        clip_count = int(request.form.get('clipCount', 10))  # Default to 10 if not provided
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        # Step 1: Collect clip URLs using clips_collector
        collected_count = collect_clip_urls(username, clip_count)
        if collected_count == 0:
            return jsonify({'error': 'No clips were collected'}), 400
        
        # Step 2: Read the CSV and download clips
        csv_filename = os.path.join(ROOT_DIR, f'outputs/{username}_clips.csv')
        output_dir = os.path.join(ROOT_DIR, f'downloaded_clips/{username}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Read the CSV file
        df = pd.read_csv(csv_filename)
        clip_urls = df['Clip URL'].tolist()
        
        # Download each clip
        successful_downloads = 0
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
                
                successful_downloads += 1
                # Add a small delay between downloads
                time.sleep(1)
            except Exception as e:
                print(f"Error downloading clip {clip_url}: {str(e)}")
                continue

        if successful_downloads == 0:
            return jsonify({'error': 'No clips were successfully downloaded'}), 500

        # Step 3: Concatenate the clips
        success, message = concatenate_clips(username)
        if not success:
            return jsonify({
                'message': f'Clips downloaded but concatenation failed: {message}',
                'download_dir': output_dir,
                'collected_count': collected_count,
                'downloaded_count': successful_downloads
            })

        return jsonify({
            'message': f'Successfully collected, downloaded, and concatenated {successful_downloads} clips for {username}',
            'download_dir': output_dir,
            'collected_count': collected_count,
            'downloaded_count': successful_downloads
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/concatenate-clips', methods=['POST'])
def handle_concatenate():
    try:
        username = request.form.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        success, message = concatenate_clips(username)
        if success:
            return jsonify({
                'message': message,
                'download_dir': os.path.join(ROOT_DIR, f'downloaded_clips/{username}')
            })
        else:
            return jsonify({'error': message}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
