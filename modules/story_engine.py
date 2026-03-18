import os
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
        try:
            completion = self.client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                top_p=0.95,
                max_tokens=16384, # Note: large stories might need stream logic to avoid context/token overflow
                stream=True
            )

            for chunk in completion:
                if not chunk.choices: continue
                content = chunk.choices[0].delta.content
                if content is not None:
                    print(content, end="", flush=True)
                    story_text += content
            
            return story_text
        except Exception as e:
            print(f"\n[ERROR] Nemotron failed: {e}")
            return None
