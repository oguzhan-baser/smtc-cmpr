import torch
from transformers import CLIPProcessor, CLIPModel, CLIPVisionModelWithProjection
from transformers import CLIPVisionModel

from PIL import Image
import numpy as np
import cv2
import os
from tqdm import tqdm

OPERATION_DIR = "/home/ob3942/datasets/nuscenes"
MODEL_LOCATION = "openai/clip-vit-base-patch32"
os.chdir(OPERATION_DIR)

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model

model_id = MODEL_LOCATION

model = CLIPModel.from_pretrained(model_id).to(device)
vision_model = CLIPVisionModel.from_pretrained(model_id).to(device)
processor = CLIPProcessor.from_pretrained(model_id)

# Register attention hook
attention_maps = []

def get_attention_hook(module, input, output):
    if hasattr(module, 'attention_probs'):
        attention_maps.append(module.attention_probs.detach())

last_block = vision_model.vision_model.encoder.layers[-1]
handle = last_block.self_attn.register_forward_hook(get_attention_hook)

# Text prompt
text_prompt = "bus?"
tokenized_text = processor(text=[text_prompt], return_tensors="pt", padding=True).to(device)

# Input/Output video paths
input_video_path = "sample.mp4"
output_video_path = "sample_with_attention_heatmap.mp4"

# OpenCV video reader and writer setup
cap = cv2.VideoCapture(input_video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# Frame processing loop
with torch.no_grad():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Preprocess
        vision_inputs = processor(images=pil_image, return_tensors="pt").to(device)

        # Run vision model to get attention
        outputs = vision_model(pixel_values=vision_inputs['pixel_values'], output_attentions=True)

        # Use attention from the last layer
        attn = outputs.attentions[-1].mean(1).squeeze(0)  # [num_heads, num_patches+1, num_patches+1] -> [num_patches]
        cls_attn = attn[0, 1:]  # CLS token to patch tokens

        grid_size = int(cls_attn.shape[0] ** 0.5)
        cls_attn = cls_attn.reshape(grid_size, grid_size).cpu().numpy()
        cls_attn = cv2.resize(cls_attn, (frame.shape[1], frame.shape[0]))
        np.save("sample_attention_map.npy", np.array(cls_attn))
        break
#         # Normalize and overlay
#         heatmap = (cls_attn - cls_attn.min()) / (cls_attn.max() - cls_attn.min() + 1e-8)
#         heatmap = np.uint8(255 * heatmap)
#         heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
#         overlay = cv2.addWeighted(frame, 0.6, heatmap, 0.4, 0)

#         out.write(overlay)


# # Cleanup
# cap.release()
# out.release()
# handle.remove()

# print(f"Output video saved at: {output_video_path}")
