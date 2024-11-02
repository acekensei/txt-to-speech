import asyncio
import edge_tts
import time
import os
from pydub import AudioSegment
from tkinter import Tk, filedialog

VOICES = ['en-PH-JamesNeural']
VOICE = VOICES[0]
OUTPUT_FILE = "final_output.mp3"
MAX_RETRIES = 5
RETRY_DELAY = 2
CHARACTER_LIMIT = 5000

# Function to split text into chunks within character limit
def split_text(text, limit):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 > limit:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# Convert text chunk to speech
async def amain(text: str, file_name: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(file_name)

# Retry logic for each chunk conversion
async def run_with_retries(text: str, file_name: str):
    for attempt in range(MAX_RETRIES):
        try:
            await amain(text, file_name)
            print(f"Chunk completed successfully, saved as {file_name}!")
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Max retries reached for this chunk.")

# Concatenate all chunks into one MP3
def concatenate_audio(files, output_file):
    combined = AudioSegment.empty()
    for file in files:
        audio = AudioSegment.from_file(file)
        combined += audio
    combined.export(output_file, format="mp3")
    print(f"All chunks combined into {output_file}")

# Delete temporary chunk files
def cleanup_files(files):
    for file in files:
        try:
            os.remove(file)
            print(f"Deleted temporary file {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

# Main function to handle file selection, text splitting, and combining audio
if __name__ == "__main__":
    # Open file dialog to select multiple text files
    root = Tk()
    root.withdraw()  # Hide the root window
    file_paths = filedialog.askopenfilenames(
        title="Select one or more text files",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if file_paths:
        audio_files = []
        
        for file_path in file_paths:
            with open(file_path, "r", encoding="utf-8") as file:
                user_text = file.read()
            
            chunks = split_text(user_text, CHARACTER_LIMIT)
            
            for idx, chunk in enumerate(chunks):
                file_name = f"{os.path.basename(file_path)}_chunk_{idx+1}.mp3"
                asyncio.run(run_with_retries(chunk, file_name))
                audio_files.append(file_name)

        # Combine all generated audio chunks into one file
        concatenate_audio(audio_files, OUTPUT_FILE)

        # Delete temporary chunk files
        cleanup_files(audio_files)
    else:
        print("No files selected.")
