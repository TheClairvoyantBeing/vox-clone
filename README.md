# Vox-Clone — Chatterbox TTS Voice Cloning Project

Vox-Clone is a high-fidelity voice cloning tool built using the **Chatterbox TTS** model. This project allows you to clone voices from short audio references and synthesize natural-sounding speech with expressive paralinguistic tags.

---

## Complete Build Guide — Windows (Chatterbox TTS)

### Prerequisites

**1. Install Python 3.11**
Download from: [python.org/downloads/release/python-3119/](https://www.python.org/downloads/release/python-3119/)
*During install, ensure "Add Python to PATH" is checked.*

**2. Install uv**
```powershell
pip install uv
```

**3. Install FFmpeg**
```powershell
winget install --id Gyan.FFmpeg -e
```
*Note: Close and reopen your terminal after installing FFmpeg to update your PATH. Verify with `ffmpeg -version`.*

---

### Project Setup

**4. Create or navigate to your project folder**
```powershell
cd "C:\Users\evion\OneDrive\to_local_download\Documents\Antigravity\vox-clone"
```

**5. Create and activate the virtual environment (`venv`) using Python 3.11**
```powershell
uv venv --python 3.11 venv
.\venv\Scripts\activate
```
*Your prompt should now show `(venv)`.*

**6. Install all dependencies**
```powershell
uv pip install chatterbox-tts
uv pip install "huggingface_hub[hf_xet]" peft
uv pip install --reinstall resemble-perth
```

**7. Freeze requirements**
```powershell
uv pip freeze > requirements.txt
```

---

### Patch Chatterbox (Required — Perth Watermarker Bug on Windows)

This is a known Windows issue where `resemble-perth` native extension silently fails. We patch it out as the watermarker is non-critical.

**8. Open the patch target**
```powershell
code .\venv\Lib\site-packages\chatterbox\tts.py
```

**9. Apply Patch A — around line 126**
Find:
```python
self.watermarker = perth.PerthImplicitWatermarker()
```
Replace with:
```python
try:
    self.watermarker = perth.PerthImplicitWatermarker()
except (TypeError, AttributeError):
    self.watermarker = None
    print("[WARN] Perth watermarker unavailable — skipping watermarking.")
```

**10. Apply Patch B — find watermarker usage — The Missing Fix (~line 265)**
Find this block near the very end of the file:
```python
            wav = wav.squeeze(0).detach().cpu().numpy()
            watermarked_wav = self.watermarker.apply_watermark(wav, sample_rate=self.sr)
        return torch.from_numpy(watermarked_wav).unsqueeze(0)
```
Replace it with:
```python
            wav = wav.squeeze(0).detach().cpu().numpy()
            if self.watermarker is not None:
                wav = self.watermarker.apply_watermark(wav, sample_rate=self.sr)
        return torch.from_numpy(wav).unsqueeze(0)
```

---

### Prepare Your Reference Audio

**11. Convert your voice reference clip to WAV**
Place your source audio (e.g., `sample_1.m4a`) in the project folder, then run:
```powershell
ffmpeg -i sample_1.m4a -ar 22050 -ac 1 reference.wav
```
*Wait, ensure your reference audio meets these requirements:*
- *5–15 seconds of clean speech*
- *No background music or noise*
- *The specific voice you want to clone*

---

### Running the Script

**12. Execute the generator**
Always activate the venv first:
```powershell
cd "C:\Users\evion\OneDrive\to_local_download\Documents\Antigravity\vox-clone"
.\venv\Scripts\activate
python vox-clone.py
```

*The **first run** will download approximately 3GB of model weights. This only happens once and is cached for future use.*

---

### Final Project Structure

```
vox-clone/
├── venv/                    ← Virtual environment
├── vox-clone.py              ← Main generation script
├── requirements.txt         ← Dependency lock-file
├── sample_1.m4a             ← Original reference audio
├── reference.wav            ← Converted reference (via ffmpeg)
└── test-output.wav          ← Generated output
```

---

### GPU Acceleration (Optional — For NVIDIA Users)

To achieve ~10x faster generation, install the CUDA version of torch:
```powershell
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
The script will automatically detect and use `cuda` if available.

---

### .gitignore Recommendations

To keep your repository clean, ensure these are ignored:
- `venv/`
- `*.wav`
- `*.m4a`
- `__pycache__`
- `requirements.txt`
