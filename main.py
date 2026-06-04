from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import uuid
import json
import requests
import re
import time
from collections import defaultdict
from typing import Dict, List
from datetime import datetime
from config import config


app = FastAPI(title="Artifex AI Secured Backend")

# RESTRICT CORS: Build allowed origins dynamically from config
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if config.NEXTAUTH_URL and config.NEXTAUTH_URL not in allowed_origins:
    allowed_origins.append(config.NEXTAUTH_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_DIR = os.path.join(BASE_DIR, "public", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

# Shared security checks
async def verify_secret_token(x_secret_token: str = Header(None)):
    expected_token = config.BACKEND_SECRET_TOKEN
    if not expected_token:
        raise HTTPException(status_code=500, detail="Backend configuration error: token is missing")
    if x_secret_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid API token")


async def get_user_email(x_user_email: str = Header(None)):
    if not x_user_email or "@" not in x_user_email:
        raise HTTPException(status_code=401, detail="User context is invalid or missing")
    return x_user_email.strip().lower()

# In-memory rate limiting dictionary
class TokenBucketRateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, key: str):
        now = time.time()
        # Keep only requests within the window
        self.history[key] = [t for t in self.history[key] if now - t < self.window]
        if len(self.history[key]) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        self.history[key].append(now)

rate_limiter = TokenBucketRateLimiter(limit=5, window=60)

class GenerateRequest(BaseModel):
    prompt: str = Field(..., max_length=500)
    style: str = Field(..., max_length=50)
    enhance: bool

STYLE_PROMPTS = {
    "photorealistic": "photorealistic, highly detailed, raw photo, 8k resolution, sharp focus, cinematic lighting, dslr",
    "anime": "anime style, vibrant colors, detailed, aesthetic, masterpiece illustration, anime artwork",
    "3d": "3D render, blender style, hyperdetailed, realistic textures, raytracing, cinematic lighting, octanerender",
    "oil": "oil painting style, textured brush strokes, artistic, classical painting, high texture detail",
    "cyberpunk": "cyberpunk theme, neon lights, futuristic city, sci-fi aesthetic, detailed, high contrast",
    "watercolor": "watercolor painting style, soft colors, artistic, paper texture, delicate, artistic splash"
}

def sanitize_input(text: str) -> str:
    # Strip HTML tags
    text = re.sub(r"<[^>]*>", "", text)
    # Strip non-printable characters
    text = "".join(c for c in text if c.isprintable())
    return text.strip()

@app.post("/api/generate", dependencies=[Depends(verify_secret_token)])
async def generate_image(payload: GenerateRequest, user_email: str = Depends(get_user_email)):
    # Rate limit check per user
    rate_limiter.check_rate_limit(user_email)

    try:
        # Sanitize prompt
        prompt_text = sanitize_input(payload.prompt)
        if not prompt_text:
            raise HTTPException(status_code=400, detail="Prompt is empty or invalid")

        style = sanitize_input(payload.style).lower()
        
        # Build enhanced prompt
        style_suffix = STYLE_PROMPTS.get(style, "")
        final_prompt = prompt_text
        if style_suffix:
            final_prompt = f"{final_prompt}, {style_suffix}"
        
        if payload.enhance:
            final_prompt = f"{final_prompt}, masterpiece, award-winning, stunning visual, highly detailed, 8k"

        image_data = None
        engine_used = ""

        # METHOD 1: Pollinations AI (with API key)
        if config.POLLINATIONS_API_KEY and config.POLLINATIONS_API_KEY != "YOUR_POLLINATIONS_SK_KEY_HERE":
            try:
                print("Attempting generation via Pollinations AI...")
                api_url = "https://gen.pollinations.ai/v1/images/generations"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.POLLINATIONS_API_KEY}"
                }
                api_payload = {
                    "prompt": final_prompt,
                    "model": "flux",
                    "size": "1024x1024",
                    "n": 1,
                    "response_format": "url"
                }
                response = requests.post(api_url, json=api_payload, headers=headers, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    image_url = result.get("data", [{}])[0].get("url", "")
                    if image_url:
                        img_headers = {"Authorization": f"Bearer {config.POLLINATIONS_API_KEY}"}
                        img_response = requests.get(image_url, headers=img_headers, timeout=60)
                        if img_response.status_code == 200:
                            image_data = img_response.content
                            engine_used = "Pollinations AI"
                else:
                    print(f"Pollinations generation failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Pollinations generation error: {e}")

        # METHOD 2: Hugging Face Inference API (if key is present)
        if not image_data and config.HUGGINGFACE_API_KEY and config.HUGGINGFACE_API_KEY != "YOUR_HUGGINGFACE_FREE_TOKEN_HERE" and config.HUGGINGFACE_API_KEY != "hf_your_huggingface_free_token_here":
            try:
                print("Attempting generation via Hugging Face...")
                hf_model = "black-forest-labs/FLUX.1-schnell"
                api_url = f"https://api-inference.huggingface.co/models/{hf_model}"
                headers = {
                    "Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"
                }
                api_payload = {
                    "inputs": final_prompt
                }
                response = requests.post(api_url, json=api_payload, headers=headers, timeout=60)
                if response.status_code == 200:
                    image_data = response.content
                    engine_used = f"Hugging Face ({hf_model})"
                else:
                    print(f"Hugging Face generation failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Hugging Face generation error: {e}")

        # METHOD 3: AI Horde (Anonymous mode fallback - always free & no key required)
        if not image_data:
            try:
                print("Attempting generation via AI Horde (Free/Anonymous)...")
                horde_url = "https://stablehorde.net/api/v2"
                headers = {
                    "apikey": "0000000000",
                    "Content-Type": "application/json",
                    "Client-Agent": "Artiflex:1.0"
                }
                api_payload = {
                    "prompt": final_prompt,
                    "params": {
                        "steps": 25,
                        "width": 512,
                        "height": 512,
                        "n": 1
                    }
                }
                response = requests.post(f"{horde_url}/generate/async", json=api_payload, headers=headers, timeout=40)
                if response.status_code == 202:
                    job_id = response.json()["id"]
                    
                    # Poll for status (max 15 attempts, 4s interval = 60s total)
                    for attempt in range(15):
                        time.sleep(4)
                        status_r = requests.get(f"{horde_url}/generate/check/{job_id}", timeout=20)
                        if status_r.status_code == 200:
                            status_data = status_r.json()
                            if status_data.get("done"):
                                result_r = requests.get(f"{horde_url}/generate/status/{job_id}", timeout=20)
                                if result_r.status_code == 200:
                                    img_url = result_r.json()["generations"][0]["img"]
                                    img_response = requests.get(img_url, timeout=30)
                                    if img_response.status_code == 200:
                                        image_data = img_response.content
                                        engine_used = "AI Horde (Free/Anonymous)"
                                        break
                else:
                    print(f"AI Horde generation failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"AI Horde generation error: {e}")

        # Final check if image was generated
        if not image_data:
            raise HTTPException(status_code=502, detail="All image generation models are currently unavailable. Please try again later.")

        # Generate unique ID for this image
        image_id = str(uuid.uuid4())
        image_filename = f"{image_id}.jpg"
        metadata_filename = f"{image_id}.json"

        image_path = os.path.join(GENERATED_DIR, image_filename)
        metadata_path = os.path.join(GENERATED_DIR, metadata_filename)

        # Save image file
        with open(image_path, "wb") as f:
            f.write(image_data)

        # Save metadata file with user context
        metadata = {
            "id": image_id,
            "url": f"/generated/{image_filename}",
            "prompt": prompt_text,
            "style": style.capitalize(),
            "userEmail": user_email,
            "engine": engine_used,
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "message": "Image generated successfully",
            "imageUrl": metadata["url"],
            "enhancedPrompt": final_prompt
        }

    except HTTPException:
        raise
    except Exception as e:
        # Hide detailed trace info from client
        print(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during generation")

@app.get("/api/images", dependencies=[Depends(verify_secret_token)])
async def get_images(user_email: str = Depends(get_user_email)):
    try:
        images_list = []
        # Find all JSON metadata files in the directory
        for filename in os.listdir(GENERATED_DIR):
            if filename.endswith(".json"):
                metadata_path = os.path.join(GENERATED_DIR, filename)
                try:
                    with open(metadata_path, "r") as f:
                        meta_data = json.load(f)
                        # Verify ownership (contextual RBAC)
                        if meta_data.get("userEmail") == user_email:
                            # Verify the corresponding image file exists
                            image_filename = f"{meta_data['id']}.jpg"
                            if os.path.exists(os.path.join(GENERATED_DIR, image_filename)):
                                images_list.append(meta_data)
                except Exception:
                    continue
        
        # Sort by creation time descending
        images_list.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return {"images": images_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch images list")

if __name__ == "__main__":
    import uvicorn
    # Use HOST and PORT variables with required fallbacks
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=False)

