from flask import Flask, request, jsonify, render_template
import os
import csv
import time
import urllib.parse
import pandas as pd
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('collect-clips.html')

@app.route('/collect-clips', methods=['POST'])
def collect_clips():
    try:
        username = request.form.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        # Step 1: Collect clip URLs from TwitchTracker
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"https://www.twitchtracker.com/{username}/clips")
            page.wait_for_timeout(2000)
            page.click('div#clips-period button.btn-success')
            page.wait_for_timeout(1000)
            page.click('text=All time')
            page.wait_for_timeout(2000)
            csv_filename = f'outputs/{username}_clips.csv'
            with open(csv_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Clip URL'])
                clip_containers = page.query_selector_all('div.clip-entity')
                processed_count = 0
                for clip in clip_containers[:20]:
                    try:
                        clip.click()
                        page.wait_for_timeout(2000)
                        page.wait_for_selector('div.lity-iframe iframe', timeout=5000)
                        iframe_elem = page.query_selector('div.lity-iframe iframe')
                        if iframe_elem:
                            iframe_src = iframe_elem.get_attribute('src')
                            parsed = urllib.parse.urlparse(iframe_src)
                            query = urllib.parse.parse_qs(parsed.query)
                            clip_id = query.get('clip', [None])[0]
                            if clip_id:
                                clip_url = f'https://clips.twitch.tv/{clip_id}'
                                writer.writerow([clip_url])
                                processed_count += 1
                        close_button = page.query_selector('button[aria-label="Close"]')
                        if close_button:
                            close_button.click()
                            page.wait_for_timeout(500)
                        else:
                            page.keyboard.press('Escape')
                            page.wait_for_timeout(500)
                    except Exception as e:
                        continue
            browser.close()

        # Step 2: Download each clip from clipsey.com
        df = pd.read_csv(csv_filename)
        clip_urls = df['Clip URL'].tolist()
        output_dir = f'outputs/{username}_clips'
        os.makedirs(output_dir, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://clipsey.com/")
            for clip_url in clip_urls:
                page.fill('input.clip-url-input', clip_url)
                page.click('button.get-download-link-button')
                page.wait_for_selector('a.download-clip-button[data-resolution="1080p"]', timeout=10000)
                # Get the download link href
                download_link = page.get_attribute('a.download-clip-button[data-resolution="1080p"]', 'href')
                if download_link:
                    # Download the file manually
                    file_name = clip_url.split('/')[-1] + '.mp4'
                    file_path = os.path.join(output_dir, file_name)
                    # Use requests to download the file
                    import requests
                    r = requests.get(download_link, stream=True)
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    time.sleep(2)
            browser.close()

        return jsonify({
            'message': f'Successfully collected and downloaded clips for {username}',
            'download_dir': output_dir
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
