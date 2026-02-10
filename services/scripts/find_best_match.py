import os
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from pathlib import Path

# Setup
PROJECT_DIR = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine"
PHOTO_ROOT = os.path.join(PROJECT_DIR, "haetsali_photos")
PHOTO_ROOT = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/햇살이_정리/05_자연스러운"
SEARCH_FOLDERS = ["."]

# Search Prompts
QUERIES = {
    "strawberry_match": ["a golden retriever staring at red strawberry", "dog looking at red fruit", "dog eating red fruit"],
    "begging_food": ["dog licking lips hungry", "dog begging for food", "dog looking at treat", "dog tongue out ready to eat"],
    "puppy_eyes": ["cute dog looking at camera begging", "dog giving puppy eyes", "dog resting chin asking for food"]
}

def main():
    print("🔄 Loading CLIP Model...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    print("📂 Scanning photos...")
    images = []
    image_paths = []
    
    for folder in SEARCH_FOLDERS:
        dir_path = os.path.join(PHOTO_ROOT, folder)
        if not os.path.exists(dir_path): continue
        
        for f in os.listdir(dir_path):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(os.path.join(dir_path, f))
                
    print(f"📸 Total candidates: {len(images)}")
    
    # Process in batches to avoid memory issues if too many (though 2000 is fine-ish, let's just do loop for safety or simple batch)
    # Simple loop for specific queries
    
    results = {k: [] for k in QUERIES.keys()}
    
    # Pre-encode text queries
    text_inputs = {}
    for key, prompts in QUERIES.items():
        text_inputs[key] = processor(text=prompts, return_tensors="pt", padding=True)
    
    # Score images
    # Using a subset for speed if needed, but let's try full scan
    # For speed, we can assume 'eating' and 'happy' are best places
    
    for idx, img_path in enumerate(images):
        if idx % 100 == 0: print(f"Processing {idx}/{len(images)}...")
        try:
            image = Image.open(img_path).convert('RGB')
            # Check inputs for all queries
            
            # We aggregate score for each query group
            for key, inputs in text_inputs.items():
                processed_image = processor(images=image, return_tensors="pt")
                # Combine inputs manually? transformers handles this differently.
                # Let's do: processor(text=prompts, images=image, ...)
                
                # Correct way using the processor for pairs:
                # But to avoid re-encoding text every time, we typically encode text once.
                # However, with HF Processor helper, it's easier to just pass both.
                
                # To save time, let's just run inference per image against flattened list of ALL prompts
                pass 
        except:
             continue

    # Optimized approach: Encode text once, then encode images and compute cosine similarity
    print("🧠 Encoding queries...")
    flat_prompts = []
    prompt_map = [] # index -> (query_key, prompt_text)
    
    for key, prompts in QUERIES.items():
        for p in prompts:
            flat_prompts.append(p)
            prompt_map.append((key, p))
            
    with torch.no_grad():
        text_features = model.get_text_features(**processor(text=flat_prompts, return_tensors="pt", padding=True))
        text_features /= text_features.norm(dim=-1, keepdim=True)
    
    top_scores = {k: [] for k in QUERIES.keys()} # List of (score, filepath)
    
    print("🖼️ Scoring images...")
    for idx, img_path in enumerate(images):
        if idx % 200 == 0: print(f"  {idx}/{len(images)}")
        try:
            img = Image.open(img_path).convert('RGB')
            img_input = processor(images=img, return_tensors="pt")
            
            with torch.no_grad():
                img_features = model.get_image_features(**img_input)
                img_features /= img_features.norm(dim=-1, keepdim=True)
                
                # Similarity (Cosine Similarity since vectors are normalized)
                probs = (img_features @ text_features.T)
                # probs = probs.softmax(dim=-1) # Don't use softmax for retrieval ranking
                
                # For each query key, get max score among its prompts
                current_scores = {}
                for p_idx, (q_key, p_text) in enumerate(prompt_map):
                    score = probs[0][p_idx].item()
                    if q_key not in current_scores or score > current_scores[q_key]:
                        current_scores[q_key] = score
                
                # Update top lists
                for q_key, score in current_scores.items():
                    top_scores[q_key].append((score, img_path))
                    top_scores[q_key].sort(key=lambda x: x[0], reverse=True)
                    top_scores[q_key] = top_scores[q_key][:10] # Keep top 10
                    
        except Exception as e:
            # print(f"Error {img_path}: {e}")
            pass
            
    print("\n🏆 Top Matches:")
    for key, items in top_scores.items():
        print(f"\n[{key}]")
        for sc, path in items:
            print(f"  {sc:.4f} : {os.path.basename(path)}")

if __name__ == "__main__":
    main()
