import os
import sys
from modules.utils import create_output_folder, convert_to_wav
from modules.story_engine import StoryEngine
from modules.audio_engine import AudioEngine
from modules.voice_engine import VoiceEngine

def cleanup_empty_folders(root):
    # Walk bottom-up to ensure nested empty folders are caught
    for dir_path, dir_names, file_names in os.walk(root, topdown=False):
        if not dir_names and not file_names:
            try:
                os.rmdir(dir_path)
                print(f"[CLEANUP] Removed empty folder: {dir_path}")
            except OSError:
                pass

def main():
    print("=" * 60)
    print("      VOX-CLONE — MODULAR AI STORY PIPELINE")
    print("=" * 60)

    # 1. OPTIONAL: SYNC ELEVENLABS
    voice_engine = VoiceEngine()
    print("\n[V] Check ElevenLabs samples?")
    sync_choice = input("Would you like to sync/download new ElevenLabs samples first? (y/n): ").strip().lower()
    if sync_choice == 'y':
        voice_engine.download_voice_samples()

    # 2. VOICE SELECTION
    print("\n--- VOICE SELECTION ---")
    print("1. Use ElevenLabs pre-downloaded samples")
    print("2. Use your own voice sample (MP4, MP3, WAV)")
    voice_choice = input("Select an option (1/2): ").strip()

    reference_path = ""
    if voice_choice == "1":
        wav_dir = voice_engine.wav_dir
        if not os.path.exists(wav_dir) or not os.listdir(wav_dir):
            print(f"[ERROR] {wav_dir} not found or empty. Syncing first...")
            voice_engine.download_voice_samples()
        
        # Filter out empty categories
        categories = sorted([d for d in os.listdir(wav_dir) if os.path.isdir(os.path.join(wav_dir, d)) and os.listdir(os.path.join(wav_dir, d))])
        
        if not categories:
            print("[ERROR] No voice categories found. Check your API key and sync again.")
            sys.exit(1)

        print("\nCategories available:")
        for idx, cat in enumerate(categories, 1):
            print(f"  {idx}. {cat}")
        
        cat_idx = int(input("\nSelect category number: ").strip()) - 1
        selected_cat = categories[cat_idx]
        cat_path = os.path.join(wav_dir, selected_cat)
        
        voices = sorted([f for f in os.listdir(cat_path) if f.endswith(".wav")])
        print(f"\nVoices in {selected_cat}:")
        for idx, voice in enumerate(voices, 1):
            name = voice.split("__")[0]
            print(f"  {idx}. {name}")
        
        voice_idx = int(input("\nSelect voice number: ").strip()) - 1
        reference_path = os.path.join(cat_path, voices[voice_idx])
        print(f"[INFO] Selected: {voices[voice_idx]}")

    else:
        sample_path = input("\nPath to your voice sample: ").strip().replace('"', '')
        if not os.path.exists(sample_path):
            print(f"[ERROR] Path not found: {sample_path}")
            sys.exit(1)
        
        ext = os.path.splitext(sample_path)[1].lower()
        if ext in [".mp4", ".mp3", ".m4a"]:
            print(f"[INFO] Converting {ext} to WAV (22050Hz mono)...")
            temp_wav = "temp_reference.wav"
            if convert_to_wav(sample_path, temp_wav):
                reference_path = temp_wav
            else:
                sys.exit(1)
        else:
            reference_path = sample_path

    # 3. STORY GENERATION
    print("\n--- STORY GENERATION ---")
    topic = input("Basic gist / idea for your story: ").strip()
    
    print("\nDesired Duration:")
    print("1. 30 Minutes")
    print("2. 45 Minutes")
    print("3. 1 Hour (60 Minutes)")
    print("4. Custom (Enter custom minutes)")
    dur_choice = input("Select an option (1/2/3/4): ").strip()
    
    duration_map = {"1": "30", "2": "45", "3": "60"}
    if dur_choice == "4":
        duration_str = input("Enter minutes: ").strip()
    else:
        duration_str = duration_map.get(dur_choice, "30")

    # 4. INITIALIZE ENGINES & FOLDERS
    try:
        story_engine = StoryEngine()
        audio_engine = AudioEngine()
    except ValueError as e:
        print(e)
        sys.exit(1)

    session_root = create_output_folder(topic)
    print(f"\n[INFO] Folder created: {session_root}")

    # PHASES
    story_text = story_engine.generate_story(topic, duration_str)
    if not story_text:
        print("[ERROR] Story generation failed.")
        sys.exit(1)
    
    story_file = os.path.join(session_root, "story.txt")
    with open(story_file, "w", encoding="utf-8") as f:
        f.write(story_text)
    print(f"\n[INFO] Story saved → {story_file}")

    output_audio = os.path.join(session_root, "narration.wav")
    success = audio_engine.generate_narration(story_text, reference_path, output_audio)

    if success:
        print("\n" + "=" * 60)
        print("COMPLETED SUCCESSFULLY!")
        print(f"  Folder: {os.path.abspath(session_root)}")
        print("=" * 60)
    else:
        print("[ERROR] Narration failed.")

    # FINAL CLEANUP
    if os.path.exists("temp_reference.wav"):
        os.remove("temp_reference.wav")
    
    print("\n[INFO] Running maintenance...")
    cleanup_empty_folders(".")

if __name__ == "__main__":
    main()
