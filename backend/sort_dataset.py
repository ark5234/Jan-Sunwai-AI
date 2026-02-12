import os
import shutil
from pathlib import Path

# Define the root of the dataset
DATASET_ROOT = Path("dataset")
SORTED_ROOT = Path("sorted_dataset")

# Mapping keywords in folder names to new Categories
CATEGORY_MAPPING = {
    # Municipal - PWD (Roads)
    "pothole": "Municipal - PWD (Roads)",
    "road": "Municipal - PWD (Roads)",
    "footpath": "Municipal - PWD (Roads)",
    "divider": "Municipal - PWD (Roads)",
    "malba": "Municipal - PWD (Roads)",
    "bricks": "Municipal - PWD (Roads)",
    "unpaved": "Municipal - PWD (Roads)",
    "cemented": "Municipal - PWD (Roads)",

    # Municipal - Sanitation
    "garbage": "Municipal - Sanitation",
    "dustbin": "Municipal - Sanitation",
    "dhalao": "Municipal - Sanitation",
    "toilet": "Municipal - Sanitation",
    "waste": "Municipal - Sanitation",
    "cleaning": "Municipal - Sanitation",

    # Municipal - Horticulture
    "tree": "Municipal - Horticulture",
    "plant": "Municipal - Horticulture",
    "park": "Municipal - Horticulture",
    "grass": "Municipal - Horticulture",

    # Municipal - Street Lighting
    "light": "Municipal - Street Lighting",
    "lamp": "Municipal - Street Lighting",
    "dark": "Municipal - Street Lighting",

    # Municipal - Water & Sewerage
    "drain": "Municipal - Water & Sewerage",
    "water": "Municipal - Water & Sewerage",
    "sewer": "Municipal - Water & Sewerage",
    "leak": "Municipal - Water & Sewerage",
    "flood": "Municipal - Water & Sewerage",

    # Utility - Power (DISCOM)
    "wire": "Utility - Power (DISCOM)",
    "electric": "Utility - Power (DISCOM)",
    "transformer": "Utility - Power (DISCOM)",
    "cable": "Utility - Power (DISCOM)",
    
    # State Transport
    "bus": "State Transport",
    "terminal": "State Transport",
    
    # Pollution Control Board
    "smoke": "Pollution Control Board",
    "pollution": "Pollution Control Board",
    "industry": "Pollution Control Board",
    "factory": "Pollution Control Board",
    "burning": "Pollution Control Board",

    # Police - Local Law Enforcement
    "encroach": "Police - Local Law Enforcement",
    "illegal": "Police - Local Law Enforcement",
    "parking": "Police - Local Law Enforcement",
    "nuisance": "Police - Local Law Enforcement",
    
    # Police - Traffic
    "traffic": "Police - Traffic",
    "signal": "Police - Traffic",
    "jam": "Police - Traffic",
    "congestion": "Police - Traffic"
}

def sort_dataset():
    if not DATASET_ROOT.exists():
        print(f"Dataset root {DATASET_ROOT} not found!")
        return

    print(f"Creating sorted dataset at {SORTED_ROOT}...")
    if not SORTED_ROOT.exists():
        SORTED_ROOT.mkdir()

    # Create category folders
    known_categories = set(CATEGORY_MAPPING.values())
    for cat in known_categories:
        safe_cat_name = cat.replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and")
        (SORTED_ROOT / safe_cat_name).mkdir(exist_ok=True)

    # Walk through the dataset
    count = 0
    for root, dirs, files in os.walk(DATASET_ROOT):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                file_path = Path(root) / file
                
                # Determine category from folder name
                folder_name = os.path.basename(root).lower()
                parent_folder_name = os.path.basename(os.path.dirname(root)).lower()
                
                # Combine context for matching
                context_str = f"{parent_folder_name}_{folder_name}"
                
                target_category = "Uncategorized"
                
                # Check for keywords
                for keyword, category in CATEGORY_MAPPING.items():
                    if keyword in context_str:
                        target_category = category
                        break
                
                # Sanitize category name for folder
                safe_cat_name = target_category.replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and")
                target_dir = SORTED_ROOT / safe_cat_name
                target_dir.mkdir(exist_ok=True)
                
                # Copy file
                # Use a unique name to prevent collisions
                new_filename = f"{count}_{file}"
                shutil.copy2(file_path, target_dir / new_filename)
                count += 1
                
                if count % 100 == 0:
                    print(f"Processed {count} images...")

    print(f"Done! Sorted {count} images into {SORTED_ROOT}")

if __name__ == "__main__":
    sort_dataset()
