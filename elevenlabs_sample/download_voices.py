import os
import time
import subprocess
import requests

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY  = "sk_afc87c5d3a0f7e15259517a801b286e05fb86be2ed621263"        # ← paste your ElevenLabs API key here
MP3_DIR  = "elevenlabs_mp3"
WAV_DIR  = "elevenlabs_wav"

# ── Category folder mapping ───────────────────────────────────────────────────
CATEGORY_MAP = {
    "advertisement":           "1_Advertisement",
    "characters_animation":    "2_Characters_and_Animation",
    "conversational":          "3_Conversational",
    "entertainment_tv":        "4_Entertainment_and_TV",
    "informative_educational": "5_Informative_and_Educational",
    "narrative_story":         "6_Narrative_and_Story",
    "social_media":            "7_Social_Media",
}

# ── Create all folders upfront ────────────────────────────────────────────────
for folder in CATEGORY_MAP.values():
    os.makedirs(os.path.join(MP3_DIR, folder), exist_ok=True)
    os.makedirs(os.path.join(WAV_DIR, folder), exist_ok=True)
os.makedirs(os.path.join(MP3_DIR, "0_Uncategorized"), exist_ok=True)
os.makedirs(os.path.join(WAV_DIR, "0_Uncategorized"), exist_ok=True)

# ═════════════════════════════════════════════════════════════════════════════
# PHASE 1 — DOWNLOAD MP3s
# ═════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("PHASE 1 — DOWNLOADING VOICE PREVIEWS")
print("=" * 60)

headers    = {"xi-api-key": API_KEY}
all_voices = []
page       = 0
page_size  = 100

while True:
    resp = requests.get(
        "https://api.elevenlabs.io/v1/shared-voices",
        headers=headers,
        params={"page_size": page_size, "page": page}
    )

    if resp.status_code != 200:
        print(f"[ERROR] API returned {resp.status_code}: {resp.text}")
        break

    data   = resp.json()
    voices = data.get("voices", [])

    if not voices:
        print("[INFO] No more voices returned — done paginating.")
        break

    all_voices.extend(voices)
    print(f"[INFO] Page {page+1}: {len(voices)} voices (total so far: {len(all_voices)})")

    if len(voices) < page_size:
        break

    page += 1
    time.sleep(0.5)

print(f"[INFO] Total voices to process: {len(all_voices)}\n")

if len(all_voices) == 0:
    print("[FATAL] No voices fetched. Check your API key and internet connection.")
    exit(1)

downloaded = 0
skipped    = 0
errors     = 0

for i, voice in enumerate(all_voices):
    name        = voice.get("name", "unknown").replace(" ", "_").replace("/", "-")
    voice_id    = voice.get("voice_id", "unknown")
    preview_url = voice.get("preview_url", "")
    category    = voice.get("category", "").lower().replace(" ", "_")

    folder_name = CATEGORY_MAP.get(category, "0_Uncategorized")
    mp3_path    = os.path.join(MP3_DIR, folder_name, f"{name}__{voice_id}.mp3")

    if not preview_url:
        print(f"[SKIP] {name} — no preview URL")
        skipped += 1
        continue

    if os.path.exists(mp3_path):
        print(f"[EXISTS] {name}")
        skipped += 1
        continue

    try:
        audio = requests.get(preview_url, timeout=15)
        with open(mp3_path, "wb") as f:
            f.write(audio.content)
        print(f"[{i+1}/{len(all_voices)}] [OK] {folder_name} → {name}")
        downloaded += 1
        time.sleep(0.1)
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        errors += 1

print(f"""
[PHASE 1 DONE]
  Downloaded : {downloaded}
  Skipped    : {skipped}
  Errors     : {errors}
""")

print("[INFO] MP3s per category:")
for folder in sorted(os.listdir(MP3_DIR)):
    fp    = os.path.join(MP3_DIR, folder)
    count = len([f for f in os.listdir(fp) if f.endswith(".mp3")])
    print(f"  {folder}: {count} files")

# ═════════════════════════════════════════════════════════════════════════════
# PHASE 2 — CONVERT ALL MP3s TO WAV
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE 2 — CONVERTING TO WAV (22050 Hz mono)")
print("=" * 60 + "\n")

converted   = 0
wav_skipped = 0
wav_errors  = 0

for category_folder in os.listdir(MP3_DIR):
    mp3_cat = os.path.join(MP3_DIR, category_folder)
    wav_cat = os.path.join(WAV_DIR, category_folder)
    os.makedirs(wav_cat, exist_ok=True)

    mp3_files = [f for f in os.listdir(mp3_cat) if f.endswith(".mp3")]

    for mp3_file in mp3_files:
        wav_file     = mp3_file.replace(".mp3", ".wav")
        mp3_fullpath = os.path.join(mp3_cat, mp3_file)
        wav_fullpath = os.path.join(wav_cat, wav_file)

        if os.path.exists(wav_fullpath):
            print(f"[EXISTS] {category_folder} → {wav_file}")
            wav_skipped += 1
            continue

        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i",  mp3_fullpath,
                    "-ar", "22050",
                    "-ac", "1",
                    wav_fullpath
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                print(f"[OK] {category_folder} → {wav_file}")
                converted += 1
            else:
                print(f"[ERROR] ffmpeg failed: {mp3_file}")
                wav_errors += 1
        except FileNotFoundError:
            print("[FATAL] ffmpeg not found. Run: winget install --id Gyan.FFmpeg -e")
            exit(1)
        except Exception as e:
            print(f"[ERROR] {mp3_file}: {e}")
            wav_errors += 1

print(f"""
[PHASE 2 DONE]
  Converted  : {converted}
  Skipped    : {wav_skipped}
  Errors     : {wav_errors}
""")

print("[INFO] WAVs per category:")
for folder in sorted(os.listdir(WAV_DIR)):
    fp    = os.path.join(WAV_DIR, folder)
    count = len([f for f in os.listdir(fp) if f.endswith(".wav")])
    print(f"  {folder}: {count} files")

print("\n[ALL DONE]")
print(f"  MP3s → {os.path.abspath(MP3_DIR)}")
print(f"  WAVs → {os.path.abspath(WAV_DIR)}")