from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import csv
import time
import urllib.parse


load_dotenv()

def collect_clip_urls(username, num_clips=10):
    print(f"Starting to collect {num_clips} clips for {username}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the clips page
        page.goto(f"https://www.twitchtracker.com/{username}/clips")
        page.wait_for_timeout(2000)
        
        # Click the period button and select "All time"
        page.click('div#clips-period button.btn-success')
        page.wait_for_timeout(1000)
        page.click('text=All time')
        page.wait_for_timeout(2000)
        
        # Create CSV file
        os.makedirs('outputs', exist_ok=True)
        csv_filename = f'outputs/{username}_clips.csv'
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Clip URL'])
            
            # Find and process clips
            clip_containers = page.query_selector_all('div.clip-entity')
            total_clips_found = len(clip_containers)
            print(f"Found {total_clips_found} clips on the page")
            
            processed_count = 0
            target_clips = min(num_clips, total_clips_found)
            
            for clip in clip_containers[:target_clips]:
                try:
                    # Click the clip
                    clip.click()
                    page.wait_for_timeout(2000)
                    
                    # Wait for the modal with the iframe to appear
                    page.wait_for_selector('div.lity-iframe iframe', timeout=5000)
                    iframe_elem = page.query_selector('div.lity-iframe iframe')
                    if iframe_elem:
                        iframe_src = iframe_elem.get_attribute('src')
                        # The src is like //clips.twitch.tv/embed?parent=twitchtracker.com&autoplay=true&clip=SuperEasyTrianglePJSalt-J0IgXQHTA0_ws9Lk
                        # Extract the clip slug from the src
                        parsed = urllib.parse.urlparse(iframe_src)
                        query = urllib.parse.parse_qs(parsed.query)
                        clip_id = query.get('clip', [None])[0]
                        if clip_id:
                            clip_url = f'https://clips.twitch.tv/{clip_id}'
                            writer.writerow([clip_url])
                            processed_count += 1
                            print(f"Processed clip {processed_count}/{target_clips}: {clip_url}")
                        else:
                            print("Could not extract clip ID from iframe src.")
                    else:
                        print("Could not find iframe in modal.")
                    
                    # Close the modal
                    close_button = page.query_selector('button[aria-label="Close"]')
                    if close_button:
                        close_button.click()
                        page.wait_for_timeout(500)
                    else:
                        # Try pressing Escape if close button is not found
                        page.keyboard.press('Escape')
                        page.wait_for_timeout(500)
                except Exception as e:
                    print(f"Error processing clip: {str(e)}")
                    continue
        
        browser.close()
        print(f"Successfully collected {processed_count} clip URLs. Saved to {csv_filename}")
        return processed_count

if __name__ == "__main__":
    username = input("Enter the username of the streamer: ")
    num_clips = int(input("Enter number of clips to collect: "))
    collect_clip_urls(username, num_clips)
