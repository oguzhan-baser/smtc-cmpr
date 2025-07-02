import json
import os
from PIL import Image, ImageDraw, ImageFont
# --- Configuration ---
image_id_to_plot = 32
labels_path = '/home/ob3942/Downloads/MAVREC/supervised_annotations/aerial/aerial_valid.json'  # Replace with actual path
images_dir = '/home/ob3942/Downloads/MAVREC/val/aerial/'       # Replace with actual image directory
output_path = '/home/ob3942/Downloads/MAVREC/mavrec_bb_example.png'
# --- Load labels ---
with open(labels_path, 'r') as f:
    labels = json.load(f)

# --- Build category_id to name mapping ---
category_id_to_name = {cat['id']: cat['name'] for cat in labels['categories']}

# --- Find image info ---
image_info = next(img for img in labels['images'] if img['id'] == image_id_to_plot)
image_path = os.path.join(images_dir, image_info['file_name'])

# --- Open image ---
image = Image.open(image_path).convert("RGB")
draw = ImageDraw.Draw(image)

# Optional: Load font (fallback to default if not found)
font = ImageFont.load_default(size=50)

# --- Draw bounding boxes and category labels ---
for ann in labels['annotations']:
    if ann['image_id'] == image_id_to_plot:
        x, y, w, h = ann['bbox']
        category_name = category_id_to_name.get(ann['category_id'], 'unknown')
        draw.rectangle([x, y, x + w, y + h], outline='red', width=5)
        draw.text((x, y - 10), category_name, fill='red', font=font)

# --- Save output ---
image.save(output_path)
print(f"Saved labeled image to {output_path}")
