import re
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

# ── Device selection ──────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[INFO] Using device: {device}")

# ── Load model ────────────────────────────────────────────────────────────────
print("[INFO] Loading ChatterboxTTS model...")
model = ChatterboxTTS.from_pretrained(device=device)
print("[INFO] Model loaded.")

# ── Config ────────────────────────────────────────────────────────────────────
REFERENCE_CLIP = "reference.wav"
TEXT_FILE      = "The_Walls_Were_Breathing.txt"
OUTPUT_PATH    = "test-output.wav"
EXAGGERATION   = 0.5
CFG_WEIGHT     = 0.5
TEMPERATURE    = 0.8
MAX_CHARS      = 200    # safe per-chunk limit for chatterbox

# ── Load text ─────────────────────────────────────────────────────────────────
with open(TEXT_FILE, "r", encoding="utf-8") as f:
    full_text = f.read().strip()
print(f"[INFO] Loaded {len(full_text)} chars from {TEXT_FILE}")

# ── Split into safe chunks ────────────────────────────────────────────────────
def chunk_text(text, max_chars=MAX_CHARS):
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            sub_parts = re.split(r'(?<=,)\s+', sentence)
            for part in sub_parts:
                part = part.strip()
                if not part:
                    continue
                if len(current) + len(part) + 1 <= max_chars:
                    current = (current + " " + part).strip()
                else:
                    if current:
                        chunks.append(current)
                    current = part
        else:
            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + " " + sentence).strip()
            else:
                if current:
                    chunks.append(current)
                current = sentence
    if current:
        chunks.append(current)
    return chunks

chunks = chunk_text(full_text)
print(f"[INFO] Split into {len(chunks)} chunks")

# ── Generate chunk by chunk ───────────────────────────────────────────────────
audio_segments = []
for i, chunk in enumerate(chunks):
    print(f"[INFO] Chunk {i+1}/{len(chunks)}: {chunk[:60]}...")
    try:
        wav = model.generate(
            chunk,
            audio_prompt_path=REFERENCE_CLIP,
            exaggeration=EXAGGERATION,
            cfg_weight=CFG_WEIGHT,
            temperature=TEMPERATURE,
        )
        audio_segments.append(wav)
    except Exception as e:
        print(f"[WARN] Chunk {i+1} failed: {e} — skipping.")

# ── Stitch and save ───────────────────────────────────────────────────────────
if audio_segments:
    final_wav = torch.cat(audio_segments, dim=-1)
    ta.save(OUTPUT_PATH, final_wav, model.sr)
    duration = final_wav.shape[-1] / model.sr
    print(f"[INFO] Done! Saved → {OUTPUT_PATH} ({duration:.1f}s)")
else:
    print("[ERROR] No audio segments were generated.")