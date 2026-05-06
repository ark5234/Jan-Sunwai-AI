import os
import re

image_dir = r'c:\Users\Vikra\OneDrive\Desktop\Jan-Sunwai AI\docs\images'
for filename in os.listdir(image_dir):
    if filename.endswith('.png'):
        new_name = filename.lower()
        new_name = new_name.replace(' ', '_').replace('-', '_')
        new_name = re.sub(r'_+', '_', new_name)
        # Specific fixes
        new_name = new_name.replace('avtivity', 'activity')
        new_name = new_name.replace('regestration', 'registration')
        new_name = new_name.replace('regstration', 'registration')
        
        old_path = os.path.join(image_dir, filename)
        new_path = os.path.join(image_dir, new_name)
        
        if old_path != new_path:
            print(f"Renaming: {filename} -> {new_name}")
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(old_path, new_path)
