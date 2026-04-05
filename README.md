# 🎙️ Vox-Clone — Premium AI Story Narration Pipeline

Vox-Clone is a high-fidelity, modular AI pipeline designed for generating and narrating long-form horror and mystery stories. Built on the **Chatterbox TTS** model and powered by **NVIDIA's Nemotron**, it transforms a simple story idea into a fully synthesized, immersive audio experience.

---

## ✨ Key Features

- **🎭 Modular Engine**: Separated logic for Story Generation, Audio Synthesis, and Voice Management.
- **🧠 NVIDIA Nemotron Integration**: Generates deep, complex horror narratives with paralinguistic cues.
- **🎙️ Advanced Voice Cloning**: Clone any voice from a 10-second WAV sample with high emotional range.
- **🔊 RMS Normalization**: Automatically balances volume across all audio chunks for consistent loudness.
- **🧹 Intelligent Text Cleaning**: Automatically strips paralinguistic tags (e.g., `[gasped]`) and `[EDIT]` headers before narration.
- **🛡️ Automated Windows Patching**: Integrated runtime monkey-patching for the `perth` watermarker, ensuring a smooth experience on Windows OS.

---

## 🚀 Quick Start Guide (Windows)

### 1. Prerequisites
- **Python 3.11**: [Download here](https://www.python.org/downloads/release/python-3119/)
- **uv**: `pip install uv`
- **FFmpeg**: `winget install --id Gyan.FFmpeg -e` (Restart terminal after install)

### 2. Installation
```powershell
# Clone the repository and enter the directory
cd vox-clone

# Create and activate virtual environment
uv venv --python 3.11 venv
.\venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```
NVIDIA_API_KEY=your_nvidia_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

---

## 🛠️ Usage

Run the main entry point:
```powershell
python main.py
```

### Execution Modes:
1. **Story Only**: Generate the script and save it to `story.txt`.
2. **TTS Only**: Narrate an existing `story.txt` using a voice clone.
3. **Auto**: End-to-end pipeline from story idea to final audio.

---

## 📁 Project Architecture

```
vox-clone/
├── main.py                # Main entry point & CLI
├── modules/
│   ├── audio_engine.py    # TTS synthesis, RMS normalization, & cleaning
│   ├── story_engine.py    # LLM story generation & token stripping
│   ├── voice_engine.py    # ElevenLabs sample management & conversion
│   └── utils.py           # File system & path utilities
├── outputs/               # Session-based results (story.txt + narration.wav)
├── elevenlabs_wav/        # Synced voice samples for cloning
└── reference.wav          # Your default voice clone reference
```

---

## 🔧 Maintenance & Fixes

- **Perth Watermarker**: The project automatically detects Windows environments and patches the `resemble-perth` extension at runtime. No manual file editing is required.
- **Nemotron Leaks**: The `story_engine` aggressively strips `<think>` reasoning blocks to ensure clean output.
- **Audio Consistency**: RMS normalization is set to a target of `0.08` by default in `audio_engine.py`.

---

## 📜 License
MIT License. See [LICENSE](LICENSE) for details.