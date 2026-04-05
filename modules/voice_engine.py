import os
import time
import requests
import subprocess
from dotenv import load_dotenv

load_dotenv()

class VoiceEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.mp3_dir = "elevenlabs_mp3"
        self.wav_dir = "elevenlabs_wav"
        self.category_map = {
            "advertisement":           "1_Advertisement",
            "characters_animation":    "2_Characters_and_Animation",
            "conversational":          "3_Conversational",
            "entertainment_tv":        "4_Entertainment_and_TV",
            "informative_educational": "5_Informative_and_Educational",
            "narrative_story":         "6_Narrative_and_Story",
            "social_media":            "7_Social_Media",
        }

    def download_voice_samples(self):
        """
        Fetches shared voice samples from the ElevenLabs API, downloads the 
        previews, and converts them to 22050Hz Mono WAV format for compatibility
        with the Chatterbox TTS model.
        """
        if not self.api_key:
            print("[ERROR] No ElevenLabs API Key. Add it to your .env file.")
            return

        headers = {"xi-api-key": self.api_key}
        print("\n[INFO] Fetching voices from ElevenLabs...")
        
        try:
            # Fetch public/shared voices
            resp = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, params={"page_size": 100})
            if resp.status_code != 200:
                print(f"[ERROR] ElevenLabs API failed: {resp.status_code}")
                return
            
            voices = resp.json().get("voices", [])
            print(f"[INFO] Found {len(voices)} shared voices.")

            # Ensure all category directories exist
            for cat in self.category_map.values():
                os.makedirs(os.path.join(self.mp3_dir, cat), exist_ok=True)
                os.makedirs(os.path.join(self.wav_dir, cat), exist_ok=True)

            for i, voice in enumerate(voices):
                name = voice.get("name", "unknown").replace(" ", "_").replace("/", "-")
                vid = voice.get("voice_id", "unknown")
                url = voice.get("preview_url", "")
                cat = voice.get("category", "").lower().replace(" ", "_")
                
                # Default to 0_Uncategorized if the category is unknown
                folder = self.category_map.get(cat, "0_Uncategorized")
                mp3_path = os.path.join(self.mp3_dir, folder, f"{name}__{vid}.mp3")
                wav_path = os.path.join(self.wav_dir, folder, f"{name}__{vid}.wav")

                # Ensure path exists for uncategorized or new folders
                os.makedirs(os.path.join(self.mp3_dir, folder), exist_ok=True)
                os.makedirs(os.path.join(self.wav_dir, folder), exist_ok=True)

                if not url or os.path.exists(wav_path):
                    continue

                # Download & Convert
                print(f"[{i+1}/{len(voices)}] Downloading {name}...")
                r = requests.get(url)
                with open(mp3_path, "wb") as f:
                    f.write(r.content)
                
                # Convert to 22050 mono wav via ffmpeg (Chatterbox requirement)
                subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ar", "22050", "-ac", "1", wav_path], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            print("[INFO] ElevenLabs voices updated.")

        except Exception as e:
            print(f"[ERROR] Voice sync failed: {e}")
