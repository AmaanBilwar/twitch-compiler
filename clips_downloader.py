import subprocess
import re
import os
from dotenv import load_dotenv

load_dotenv()
CLI_PATH = os.getenv("TWITCH_CLI_PATH")  # Path to TwitchDownloaderCLI

def extract_twitch_links(text):
    return re.findall(r'(https?://(?:www\.)?(?:clips\.)?twitch\.tv/\S+)', text)

def download_clip(link: str):
    print(f"[INFO] Downloading: {link}")
    try:
        subprocess.run([
            CLI_PATH,
            "clipdownload",
            "--id", link.split("/")[-1],
            "--output", f"{link.split('/')[-1]}.mp4"
        ], check=True)
        print("✅ Download complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download: {e}")

def handle_prompt(prompt):
    links = extract_twitch_links(prompt)
    if not links:
        print("❌ No links found.")
        return
    for link in links:
        download_clip(link)

if __name__ == "__main__":
    print("🌐 Cross-Platform Twitch CLI Downloader")
    while True:
        prompt = input("Paste Twitch clip/VOD links (or type 'exit'):\n> ")
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        handle_prompt(prompt)
