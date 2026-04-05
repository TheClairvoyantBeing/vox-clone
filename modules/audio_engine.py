# modules/audio_engine.py
import re
import torch
import torchaudio as ta


class _NullWatermarker:
    """
    Drop-in replacement for the perth watermarker when the native extension
    fails to load on Windows. Simply returns the audio untouched.
    """
    def apply_watermark(self, wav, sample_rate=None):
        return wav


def _ensure_perth_works():
    """
    Monkey-patches the perth module at runtime to prevent crashes on Windows.
    This replaces the 'PerthImplicitWatermarker' with a null version if the
    native library is missing or incompatible.
    """
    try:
        import perth
        perth.PerthImplicitWatermarker()
        print("[AUDIO] Perth watermarker: OK")
        return
    except Exception as e:
        print(f"[AUDIO] Perth failed ({type(e).__name__}: {e})")

    print("[AUDIO] Applying null watermarker...")
    import perth
    perth.PerthImplicitWatermarker = _NullWatermarker
    try:
        import chatterbox.tts as _tts_mod
        if hasattr(_tts_mod, "PerthImplicitWatermarker"):
            _tts_mod.PerthImplicitWatermarker = _NullWatermarker
        if hasattr(_tts_mod, "perth"):
            _tts_mod.perth.PerthImplicitWatermarker = _NullWatermarker
    except Exception:
        pass
    print("[AUDIO] Null watermarker installed.")


def clean_text_for_tts(text):
    """Strip or convert tags that would be read aloud literally."""
    # remove EDIT headers — don't narrate [EDIT 1]: etc.
    text = re.sub(r'\[EDIT\s*\d*\]\s*:?', '', text, flags=re.IGNORECASE)
    # remove bracket paralinguistic tags — [gasped], [scream]ed, [sniffed], etc.
    text = re.sub(r'\[([a-z\s]+)\]', '', text, flags=re.IGNORECASE)
    # remove markdown leftovers
    text = re.sub(r'\*+', '', text)
    # collapse multiple spaces/newlines
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    # strip think artifacts if any slipped through
    text = re.sub(r'</think>', '', text)
    return text.strip()


class AudioEngine:
    def __init__(self, device=None):
        _ensure_perth_works()

        from chatterbox.tts import ChatterboxTTS

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[AUDIO] Device: {self.device}")

        if self.device == "cuda":
            free, total = torch.cuda.mem_get_info()
            print(f"[AUDIO] VRAM: {free/1e9:.1f} GB free / {total/1e9:.1f} GB total")
        else:
            print("[AUDIO] WARNING: CPU mode — generation will be very slow.")

        print("[AUDIO] Loading ChatterboxTTS...")
        self.model = ChatterboxTTS.from_pretrained(device=self.device)
        print("[AUDIO] Model ready.")

    def normalize_rms(self, wav, target_rms=0.08):
        """
        Calculates the RMS (Root Mean Square) of the audio chunk and scales it 
        to a consistent target level. This prevents volume jumps between 
        independently generated segments.
        """
        rms = torch.sqrt(torch.mean(wav.float() ** 2))
        if rms > 1e-6:  # avoid division by near-zero silence
            wav = wav * (target_rms / rms)
        # hard clip to prevent any rare spike above ±1.0
        wav = torch.clamp(wav, -1.0, 1.0)
        return wav

    def chunk_text(self, text, max_chars=120):
        """
        Cleans the input text and splits it into small, manageable chunks
        for the TTS engine. Uses punctuation-aware splitting.
        """
        text = clean_text_for_tts(text)  # clean BEFORE chunking
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks, current = [], ""
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
                        current = part[:max_chars]
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

    def generate_narration(self, text, reference_path, output_path):
        chunks = self.chunk_text(text)
        print(f"[AUDIO] {len(chunks)} chunks to process.")
        audio_segments = []

        for i, chunk in enumerate(chunks):
            print(f"[AUDIO] Chunk {i+1}/{len(chunks)}: {chunk[:60]}...")

            if self.device == "cuda":
                free = torch.cuda.mem_get_info()[0] / 1e9
                print(f"         VRAM free: {free:.2f} GB")

            try:
                with torch.no_grad():
                    wav = self.model.generate(
                        chunk,
                        audio_prompt_path=reference_path,
                        exaggeration=0.5,
                        cfg_weight=0.5,
                        temperature=0.8,
                    )
                wav = wav.cpu()
                wav = self.normalize_rms(wav)  # normalize volume per chunk
                audio_segments.append(wav)

            except torch.cuda.OutOfMemoryError:
                print(f"[WARN] CUDA OOM on chunk {i+1}, retrying on CPU...")
                torch.cuda.empty_cache()
                try:
                    self.model.to("cpu")
                    with torch.no_grad():
                        wav = self.model.generate(
                            chunk,
                            audio_prompt_path=reference_path,
                            exaggeration=0.5,
                            cfg_weight=0.5,
                            temperature=0.8,
                        )
                    wav = wav.cpu()
                    wav = self.normalize_rms(wav)
                    audio_segments.append(wav)
                    self.model.to(self.device)
                except Exception as e2:
                    print(f"[WARN] CPU retry failed ({e2}). Skipping chunk.")

            except Exception as e:
                print(f"[WARN] Chunk {i+1} failed ({e}). Skipping.")

            finally:
                if self.device == "cuda":
                    torch.cuda.empty_cache()

        if audio_segments:
            # brief silence between chunks (0.2s) for natural pacing
            silence = torch.zeros(1, int(0.2 * self.model.sr))
            with_pauses = []
            for seg in audio_segments:
                with_pauses.append(seg)
                with_pauses.append(silence)

            print(f"[AUDIO] Stitching {len(audio_segments)} segments...")
            final_wav = torch.cat(with_pauses, dim=-1)
            ta.save(output_path, final_wav, self.model.sr)
            print(f"[AUDIO] Saved → {output_path}")
            return True

        print("[ERROR] No audio segments generated.")
        return False