#!/usr/bin/env python3
"""
Project Sunshine - Retry Food Image Generation (Flux Pro via Fal.ai)
Generates 5 specific food images with hourly retries on failure.
"""

import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
import fal_client
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("retry_food_images.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

if not os.getenv("FAL_KEY"):
    logging.error("FAL_KEY not found in .env")
    exit(1)

# Target directory
OUTPUT_DIR = ROOT_DIR / "01_contents" / "000_CleanReady" / "02_food"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Target foods and prompts
TARGETS = [
    {
        "filename": "148_ChickenNuggets.png",
        "prompt": "Chicken Nuggets (치킨너겟), Fresh close-up photograph, golden crispy texture, 2-3 whole pieces, placed on clean white background or bright marble surface, soft natural lighting, food magazine style, warm tones, shallow depth of field with blurred background, shot from 45-degree angle above, high resolution, 4K, professional food photography"
    },
    {
        "filename": "154_Odeng.png",
        "prompt": "Odeng (Korean Fish Cake Skewers, 오뎅), Fresh close-up photograph, folded fish cakes on wooden skewers, natural refreshing texture, placed on clean white background or bright marble surface, soft natural lighting, food magazine style, warm tones, shallow depth of field with blurred background, shot from 45-degree angle above, high resolution, 4K, professional food photography"
    },
    {
        "filename": "155_Mandu.png",
        "prompt": "Mandu (Korean Steamed Dumplings, 만두), Fresh close-up photograph, soft translucent skin showing filling, moist texture, 2-3 whole pieces, placed on clean white background or bright marble surface, soft natural lighting, food magazine style, warm tones, shallow depth of field with blurred background, shot from 45-degree angle above, high resolution, 4K, professional food photography"
    },
    {
        "filename": "156_FriedDumplings.png",
        "prompt": "Fried Dumplings (Gunmandu, 군만두), Fresh close-up photograph, golden brown crispy skin, 2-3 whole pieces, placed on clean white background or bright marble surface, soft natural lighting, food magazine style, warm tones, shallow depth of field with blurred background, shot from 45-degree angle above, high resolution, 4K, professional food photography"
    },
    {
        "filename": "135_CoconutOil.png",
        "prompt": "Coconut Oil (코코넛오일), Fresh close-up photograph, clear glass jar of white solidified or clear liquid oil next to a fresh split coconut, placed on clean white background or bright marble surface, soft natural lighting, food magazine style, warm tones, shallow depth of field with blurred background, shot from 45-degree angle above, high resolution, 4K, professional food photography"
    }
]

def generate_image(prompt, filepath):
    try:
        logging.info(f"Generating: {filepath.name} ...")
        
        result = fal_client.subscribe(
            "fal-ai/flux-2-pro",
            arguments={
                "prompt": prompt,
                "image_size": {"width": 1080, "height": 1080},
                "num_images": 1,
                "output_format": "png",
                "safety_tolerance": "5",
            }
        )
        
        image_url = result["images"][0]["url"]
        logging.info(f"Image generated at: {image_url}")
        
        img_data = requests.get(image_url).content
        
        with open(filepath, 'wb') as f:
            f.write(img_data)
            
        logging.info(f"SUCCESS: Saved to {filepath}")
        return True
        
    except Exception as e:
        logging.error(f"FAILED: {filepath.name} - {str(e)}")
        return False

def main():
    while True:
        pending_count = 0
        success_in_batch = 0
        
        logging.info("--- Starting Batch Check (Fal.ai / Flux Pro) ---")
        
        for item in TARGETS:
            filepath = OUTPUT_DIR / item["filename"]
            
            if filepath.exists():
                logging.info(f"Skipping (Exists): {item['filename']}")
                continue
                
            pending_count += 1
            if generate_image(item["prompt"], filepath):
                success_in_batch += 1
                # Optional: Sleep briefly between successful generations to be nice to API
                time.sleep(2)
            else:
                pass
                
        if pending_count == 0:
            logging.info("All images generated successfully! Exiting.")
            break
        
        if pending_count > 0:
            logging.info(f"Batch finished. {success_in_batch}/{pending_count} succeeded.")
            if pending_count - success_in_batch == 0:
                 logging.info("All pending items in this batch succeeded! Exiting.")
                 break
            
            logging.info("Waiting 1 hour before retrying failed items...")
            time.sleep(3600)

if __name__ == "__main__":
    main()
