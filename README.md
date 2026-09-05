# Vox-Clone — Modular AI Story & Voice Pipeline

Vox-Clone is a high-fidelity voice cloning and AI story generation tool built on **Chatterbox TTS** and **NVIDIA Nemotron**. It clones voices from short audio references and synthesises natural-sounding narration from AI-generated horror/mystery scripts.

> **v2 — Modular rewrite.** Story generation and TTS are now independent modes. The Perth watermarker patch is applied automatically. CUDA memory handling has been overhauled for low-VRAM GPUs (4–6 GB).

---

## Modes

| Mode | What it does |
|------|-------------|
| `story` | Generates a script via Nemotron and saves it as `story.txt`. No TTS. |
| `tts` | Reads an existing `story.txt` and narrates it. No API call to Nemotron. |
| `auto` | Full pipeline — story generation followed immediately by TTS. |

---

## Hardware Requirements

| Component | Minimum |
|-----------|---------|
| GPU VRAM | 4 GB (NVIDIA, CUDA 12.1+) |
| RAM | 8 GB |
| Disk | ~4 GB (model weights, cached after first run) |
| CPU fallback | Supported — slow but functional |

> Tested on RTX 3050 Ti (4 GB VRAM) with chunk size 120 chars, `torch.no_grad()`, and `empty_cache()` per chunk. OOM chunks automatically retry on CPU.

---

## Prerequisites

### 1. Python 3.11

Download from [python.org](https://www.python.org/downloads/release/python-3119/).  
During install, check **"Add Python to PATH"**.

### 2. uv

```powershell
pip install uv
```

### 3. FFmpeg

```powershell
winget install --id Gyan.FFmpeg -e
```

Close and reopen your terminal after install. Verify with:

```powershell
ffmpeg -version
```

---

## Project Setup

### 4. Navigate to project folder

```powershell
cd "C:\Users\evion\OneDrive\to_local_download\Documents\Antigravity\vox-clone"
```

### 5. Create virtual environment (Python 3.11)

```powershell
uv venv --python 3.11 venv
.\venv\Scripts\activate
```

Your prompt should now show `(venv)`.

### 6. Install dependencies

```powershell
uv pip install chatterbox-tts
uv pip install "huggingface_hub[hf_xet]" peft
uv pip install --reinstall resemble-perth
uv pip install openai python-dotenv requests
```

### 7. Freeze requirements

```powershell
uv pip freeze > requirements.txt
```

> **No manual Perth patch needed.** The `AudioEngine` automatically detects and patches the Perth watermarker bug on Windows at startup. If it fails for any reason, the warning message will tell you.

---

## Environment Variables

Create a `.env` file in the project root:

```env
NVIDIA_API_KEY=your_nvidia_nim_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key   # optional — only needed for voice sync
```

Get your NVIDIA NIM key from [integrate.api.nvidia.com](https://integrate.api.nvidia.com).  
Get your ElevenLabs key from [elevenlabs.io](https://elevenlabs.io).

---

## Prepare Reference Audio

Place your source audio in the project folder and convert it:

```powershell
ffmpeg -i sample_1.m4a -ar 22050 -ac 1 reference.wav
```

Reference audio requirements:
- 5–15 seconds of clean speech
- No background music or noise
- The specific voice you want to clone

---

## Running

Always activate the venv first:

```powershell
cd "C:\Users\evion\OneDrive\to_local_download\Documents\Antigravity\vox-clone"
.\venv\Scripts\activate
python main.py
```

You will be prompted to select a mode:

```
=== VOX-CLONE — MODE SELECT ===
1. Story only     (generate script, save story.txt)
2. TTS only       (narrate an existing story.txt)
3. Auto           (story → TTS, full pipeline)
Select (1/2/3):
```

### Mode 1 — Story only

Generates and saves your story. Use this when you want to review or edit the script before narrating.

```
[1] Story only selected
Story idea / gist: an abandoned hospital with a locked basement
Duration: 1. 30 min  2. 45 min  3. 60 min  4. Custom
→ story saved to outputs/session_YYYYMMDD_HHMMSS_<topic>/story.txt
```

### Mode 2 — TTS only

Narrates an existing `story.txt` without making any Nemotron API calls. Useful for re-narrating with a different voice or after editing the script.

```
[2] TTS only selected
Path to existing story.txt: outputs/session_.../story.txt
→ narration.wav saved to the same session folder
```

### Mode 3 — Auto

Full pipeline, no interruptions. Story generation → voice selection → narration.

---

## GPU Acceleration

The script auto-detects CUDA. To explicitly install the CUDA-enabled PyTorch build:

```powershell
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### VRAM behaviour on 4 GB GPUs

| Setting | Value | Reason |
|---------|-------|--------|
| Chunk size | 120 chars | Prevents OOM on generation |
| `torch.no_grad()` | Always on | Cuts ~30% activation memory |
| `empty_cache()` | After every chunk | Releases fragmented VRAM |
| OOM fallback | CPU retry | Skipped chunk re-runs on CPU instead of crashing |

VRAM usage is printed every chunk so you can monitor headroom in real time.

---

## Project Structure

```
vox-clone/
├── venv/                          ← Virtual environment
├── modules/
│   ├── audio_engine.py            ← ChatterboxTTS + Perth auto-patch + CUDA safety
│   ├── story_engine.py            ← Nemotron story generation with partial save
│   ├── voice_engine.py            ← ElevenLabs voice sync (optional)
│   └── utils.py                   ← Folder creation, FFmpeg helpers
├── main.py                        ← Mode selector entry point
├── .env                           ← API keys (gitignored)
├── reference.wav                  ← Your converted voice reference
├── sample_1.m4a                   ← Original source audio (gitignored)
└── outputs/
    └── session_YYYYMMDD_HHMMSS_topic/
        ├── story.txt              ← Generated script
        └── narration.wav          ← Final audio output
```

---

## Known Issues & Fixes Applied

### Perth watermarker crash (Windows)

**Symptom:** `TypeError` or `AttributeError` immediately on model load.  
**Cause:** `resemble-perth` native extension fails silently on Windows.  
**Fix:** `AudioEngine._patch_perth()` automatically rewrites the relevant lines in `chatterbox/tts.py` on startup. No manual editing required.

### CUDA OOM mid-generation

**Symptom:** Script crashes partway through a long story with `torch.cuda.OutOfMemoryError`.  
**Cause:** Chunk size of 200 chars + no memory management = spikes over 4 GB.  
**Fix:** Chunk size reduced to 120 chars. `torch.no_grad()` wraps every generation call. `torch.cuda.empty_cache()` runs after every chunk. OOM chunks are retried on CPU automatically.

### ElevenLabs voice sync failing

**Symptom:** 401 or empty voice list when syncing samples.  
**Cause:** `/v1/shared-voices` requires library access; the correct endpoint is `/v1/voices`.  
**Fix:** `voice_engine.py` now calls `/v1/voices`.

### Nemotron model name

If story generation fails with a 404 or model-not-found error, verify your model string in `story_engine.py` against your NVIDIA NIM dashboard at [integrate.api.nvidia.com](https://integrate.api.nvidia.com). NVIDIA renames models without notice. Common working names as of early 2025:

- `nvidia/llama-3.1-nemotron-ultra-253b-v1`
- `nvidia/nemotron-4-340b-instruct`

Update `self.client.chat.completions.create(model="...")` accordingly.

### Story lost on Nemotron crash

**Fix:** `story_engine.py` now saves partial output every ~500 characters to `story_partial_<topic>.txt`. If generation crashes, your partial script is not lost.

---

## ElevenLabs Voice Sync (Optional)

If you want to browse pre-downloaded ElevenLabs voices as references instead of recording your own:

```powershell
python main.py
# → Select any mode → choose option 1 for voice → sync when prompted
```

Voices are downloaded as MP3, converted to 22050 Hz mono WAV, and organised into category folders under `elevenlabs_wav/`. This is a one-time operation; existing files are skipped on future syncs.

---

## .gitignore

The project includes a pre-configured `.gitignore` that excludes large binary files, credentials, and transient session data while ensuring core code and configuration are tracked.

```gitignore
# --- Credentials & Local Config ---
.env

# --- Output folders (generated content) ---
outputs/
story_partial_*.txt
temp_reference.wav

# --- Media & Voice Data ---
*.wav
*.m4a
*.mp3
elevenlabs_mp3/
elevenlabs_wav/
voice_samples/

# --- Virtual Environments & Python Cache ---
venv/
.venv/
__pycache__/
*.py[cod]

# --- Model Weights & Large Binary Files ---
*.pt
*.pth
*.safe_tensors
checkpoint/

# --- IDEs & System Files ---
.vscode/
.idea/
```

---

## Senior Engineering Polish

The codebase has been updated with:
- **Comprehensive Docstrings**: Every class and method now includes detailed explanations of its purpose, parameters, and return values.
- **Thought-Process Comments**: Internal comments provide a "behind-the-scenes" look at architectural decisions, such as why specific audio formats or memory management strategies were chosen.
- **Standardized Error Handling**: Improved robustness in the audio and story engines to handle API failures and hardware constraints gracefully.

---

## Roadmap

- [ ] `--mode` CLI flag to skip interactive prompts (`python main.py --mode tts --story outputs/.../story.txt`)
- [ ] Progress bar for chunk narration (tqdm)
- [ ] Background music mixer (ambient layer under narration)
- [ ] Web UI via Gradio

## Repository Standardization

This repository was standardized on 2026-09-05 under the ownership of [TheClairvoyantBeing](https://github.com/TheClairvoyantBeing).

### Changes applied

- Added a consistent `.gitignore` hygiene section covering IDE metadata (`.idea/`, `.vscode/`), Python caches, Node dependencies, build output, virtual environments, coverage output, `.env` files, and `reviews.md`.
- Ensured `requirements.txt` exists. Existing dependency declarations were preserved; repositories without detected Python dependencies contain a clearly marked placeholder.
- Standardized the repository license to the GNU Affero General Public License v3 (AGPLv3), with TheClairvoyantBeing as the copyright holder. AGPLv3 requires corresponding source to remain available when covered software is distributed or provided as a network service.
- This section records the repository-level maintenance changes; existing project-specific setup, usage, architecture, and development documentation remains above.
