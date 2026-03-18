import re
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

class AudioEngine:
    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print("=" * 60)
        print("AUDIO DIAGNOSTICS")
        print("=" * 60)
        print(f"  PyTorch version     : {torch.__version__}")
        print(f"  CUDA available      : {torch.cuda.is_available()}")
        print(f"  Target device       : {self.device}")
        
        if self.device == "cuda":
            print(f"  GPU name            : {torch.cuda.get_device_name(0)}")
            print(f"  GPU memory free     : {torch.cuda.mem_get_info()[0] / 1e9:.2f} GB")
        print("=" * 60 + "\n")

        print("[INFO] Loading ChatterboxTTS model...")
        self.model = ChatterboxTTS.from_pretrained(device=self.device)
        print("[INFO] Model loaded.")

    def chunk_text(self, text, max_chars=200):
        # Using the regex splitter from your previous script
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if not sentence: continue
            
            if len(sentence) > max_chars:
                # Break by commas if sentences are too long
                sub_parts = re.split(r'(?<=,)\s+', sentence)
                for part in sub_parts:
                    part = part.strip()
                    if not part: continue
                    if len(current) + len(part) + 1 <= max_chars:
                        current = (current + " " + part).strip()
                    else:
                        if current: chunks.append(current)
                        current = part
            else:
                if len(current) + len(sentence) + 1 <= max_chars:
                    current = (current + " " + sentence).strip()
                else:
                    if current: chunks.append(current)
                    current = sentence
        
        if current: chunks.append(current)
        return chunks

    def generate_narration(self, text, reference_path, output_path):
        chunks = self.chunk_text(text)
        print(f"\n[INFO] Split into {len(chunks)} chunks for narration.")
        
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            print(f"[INFO] Processing chunk {i+1}/{len(chunks)}: {chunk[:50]}...")
            
            # CUDA Memory check every 10 chunks if on GPU
            if self.device == "cuda" and i % 10 == 0:
                free_mem = torch.cuda.mem_get_info()[0] / 1e9
                print(f"         GPU memory free: {free_mem:.2f} GB")

            try:
                wav = self.model.generate(
                    chunk,
                    audio_prompt_path=reference_path,
                    exaggeration=0.5,
                    cfg_weight=0.5,
                    temperature=0.8
                )
                audio_segments.append(wav)
            except Exception as e:
                print(f"[WARN] Chunk {i+1} failed ({e}). Skipping.")

        if audio_segments:
            print(f"[INFO] Stitching {len(audio_segments)} segments...")
            final_wav = torch.cat(audio_segments, dim=-1)
            ta.save(output_path, final_wav, self.model.sr)
            return True
        return False
