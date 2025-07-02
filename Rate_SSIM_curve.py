import matplotlib.pyplot as plt
import numpy as np
import cv2
import subprocess
import os
from skimage.metrics import structural_similarity as ssim
from tqdm import tqdm
OPERATION_DIR = "/home/ob3942/Downloads/MAVREC/"

os.chdir(OPERATION_DIR)
input_file = "input_video.mp4"
# Function to extract a single frame as reference
def extract_reference_frame(video_path, output_path):
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-vf", "select=eq(n\\,0)",
        "-q:v", "1", "-frames:v", "1", output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Function to calculate SSIM between two images
def calculate_ssim(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

# Prepare variables
crf_values = list(range(18, 36, 2))
bitrate_h264 = []
ssim_h264 = []
bitrate_h265 = []
ssim_h265 = []

# Extract reference frame
extract_reference_frame(input_file, "reference_frame.jpg")

# Loop over CRF values for H.264 and H.265
for crf in tqdm(crf_values):
    for codec, bitrate_list, ssim_list, suffix in [("libx264", bitrate_h264, ssim_h264, "h264"), ("libx265", bitrate_h265, ssim_h265, "h265")]:
        output_video = f"output_H{suffix[-3:]}_crf{crf}.mp4"
        frame_output = f"frame_{crf}_{suffix}.jpg"

        # Encode video with given CRF
        subprocess.run([
            "ffmpeg", "-y", "-i", "sample.mp4", "-vframes", "1",
            "-c:v", codec, "-crf", str(crf), output_video
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Extract the first frame from encoded video
        extract_reference_frame(output_video, frame_output)

        # Calculate bitrate (file size for one frame * 8 bits)
        filesize = os.path.getsize(output_video)
        bitrate = filesize * 8
        bitrate_list.append(bitrate)

        # Compute SSIM with reference
        score = calculate_ssim("reference_frame.jpg", frame_output)
        ssim_list.append(score)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(bitrate_h264, ssim_h264, marker='o', label='H.264')
plt.plot(bitrate_h265, ssim_h265, marker='s', label='H.265')
plt.xlabel('Bitrate (bits)')
plt.ylabel('SSIM')
plt.title('Rate-Distortion Curve (SSIM vs Bitrate)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(f"Rate_SSIM_Curve_For_{input_file}.png")