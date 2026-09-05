"""Automated Test Suite for vox-clone.

Validates TTS text sanitization (removing tags, edits, formatting),
output directory generation, duration heuristics, and watermarker patching.
"""

import os
import shutil
import tempfile
import unittest

from modules.audio_engine import clean_text_for_tts, _NullWatermarker
from modules.utils import create_output_folder, get_audio_duration


class TestVoxCloneEngine(unittest.TestCase):
    """Tests the Vox-Clone text normalization and utility functions."""

    def test_clean_text_for_tts_paralinguistic_tags(self):
        """Ensure bracketed paralinguistic cues are removed so they aren't spoken literally."""
        raw_text = "I heard a noise outside [gasp] and then total silence [sigh]."
        cleaned = clean_text_for_tts(raw_text)
        self.assertEqual(cleaned, "I heard a noise outside and then total silence.")

    def test_clean_text_for_tts_edits_and_formatting(self):
        """Ensure Reddit [EDIT] headers and markdown asterisks are stripped."""
        raw_text = """
        **Never** enter the basement at 3:00 AM.
        [EDIT 1]: My door just unlocked itself.
        [EDIT]: The power is out.
        </think>
        """
        cleaned = clean_text_for_tts(raw_text)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("[EDIT 1]", cleaned)
        self.assertNotIn("[EDIT]", cleaned)
        self.assertNotIn("</think>", cleaned)
        self.assertIn("Never enter the basement", cleaned)
        self.assertIn("My door just unlocked itself", cleaned)

    def test_output_folder_sanitization(self):
        """Ensure output directory name is sanitized and created."""
        temp_base = tempfile.mkdtemp(prefix="vox_test_")
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_base)
            topic = 'Haunted Forest: What Lurks in Blackwood? [100% Real]'
            folder = create_output_folder(topic)
            self.assertTrue(os.path.isdir(folder))
            self.assertNotIn("?", folder)
            self.assertNotIn(":", folder)
            self.assertNotIn("[", folder)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(temp_base, ignore_errors=True)

    def test_null_watermarker_passthrough(self):
        """Ensure fallback watermarker returns waveform untouched."""
        watermarker = _NullWatermarker()
        fake_wav = [0.1, 0.2, 0.3]
        result = watermarker.apply_watermark(fake_wav, sample_rate=22050)
        self.assertEqual(result, fake_wav)

    def test_missing_audio_duration_returns_zero(self):
        """Ensure missing audio files gracefully return 0.0 duration."""
        duration = get_audio_duration("non_existent_audio_file.wav")
        self.assertEqual(duration, 0.0)


if __name__ == "__main__":
    unittest.main()
