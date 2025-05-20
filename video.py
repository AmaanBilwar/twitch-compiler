import ffmpeg
import os
import glob

def concatenate_user_clips(username):
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the user's clips directory
    clips_dir = os.path.join(root_dir, 'downloaded_clips', username)
    
    # Check if directory exists
    if not os.path.exists(clips_dir):
        print(f"Directory {clips_dir} does not exist")
        return False
    
    # Get all video files in the directory
    video_files = glob.glob(os.path.join(clips_dir, '*.mp4'))
    
    if not video_files:
        print(f"No video clips found in {clips_dir}")
        return False
    
    # Create a temporary file list for ffmpeg
    temp_list = os.path.join(root_dir, 'temp_file_list.txt')
    try:
        with open(temp_list, 'w', encoding='utf-8') as f:
            for video in video_files:
                # Use absolute paths and proper escaping
                abs_path = os.path.abspath(video)
                f.write(f"file '{abs_path}'\n")
        
        # Concatenate all videos
        output_file = os.path.join(clips_dir, f'{username}_compilation.mp4')
        ffmpeg.input(temp_list, format='concat', safe=0).output(output_file, c='copy').run()
        print(f"Successfully created compilation at {output_file}")
        return True
    except ffmpeg.Error as e:
        print(f"Error concatenating videos: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"Error during concatenation: {str(e)}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_list):
            try:
                os.remove(temp_list)
            except Exception as e:
                print(f"Error removing temporary file: {str(e)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python video.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    concatenate_user_clips(username)

