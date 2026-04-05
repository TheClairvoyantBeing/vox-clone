import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class StoryEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("[ERROR] No NVIDIA_API_KEY found. Check your .env file.")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )

    def generate_story(self, topic, duration_str):
        # Calculate target word count
        # 30m -> ~4,000 | 45m -> ~6,000 | 60m -> ~8,000
        targets = {
            "30": (3800, 4500),
            "45": (5800, 6500),
            "60": (7800, 8500),
            "custom": (4000, 6000) # fallback
        }
        
        target_range = targets.get(duration_str, (4000, 6000))
        min_words, max_words = target_range

        prompt = f"""
You are a master Reddit horror/mystery storyteller.
Generate a story about: {topic}

STRUCTURE RULES:
- Start with a Reddit post title in the format: [Title] (Originally Posted to r/nosleep)
- Write in first person, past tense.
- Include a throwaway account disclaimer at the start.
- Include 2-3 EDIT sections at the end for authenticity.
- End on an unsettling, unresolved note.

CONTENT & LENGTH:
- Target length: {min_words} to {max_words} words. (Narration duration: ~{duration_str} mins).
- Build tension slowly. Include sensory details.
- Use paralinguistic tags like [laugh], [sigh], [gasp], [sniff], [clear throat], [hmm] naturally.
- Keep output to plain text, no bold or markdown headers.

Output ONLY the story text. Nothing else.
"""

        print(f"\n[INFO] Contacting Nemotron for a {duration_str}-min story...")
        story_text = ""
        partial_path = f"story_partial_{topic[:20]}.txt"  # add this
        try:
            completion = self.client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-ultra-253b-v1",  # verify in NIM dashboard
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                top_p=0.95,
                max_tokens=16384,
                stream=True
            )
            for chunk in completion:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content is not None:
                    print(content, end="", flush=True)
                    story_text += content
                    # save partial every ~500 chars so a crash doesn't lose work
                    if len(story_text) % 500 < 10:
                        with open(partial_path, "w", encoding="utf-8") as f:
                            f.write(story_text)

            if os.path.exists(partial_path):
                os.remove(partial_path)  # clean up on success

            # strip <think>...</think> blocks (leaked reasoning from Nemotron model)
            # This handles both complete blocks and partial "leaked" closing tags
            # so the final output contains only the intended story text.
            story_text = re.sub(r'<think>.*?</think>', '', story_text, flags=re.DOTALL)
            story_text = re.sub(r'^.*?</think>', '', story_text, flags=re.DOTALL)
            story_text = story_text.strip()

            return story_text
        except Exception as e:
            print(f"\n[ERROR] Nemotron failed: {e}")
            if story_text:
                print(f"[INFO] Partial story saved to {partial_path}")
            return story_text or None
