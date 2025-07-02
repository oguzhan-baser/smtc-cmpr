import os
import subprocess
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
OPERATION_DIR = "/home/ob3942/Downloads/MAVREC/"

os.chdir(OPERATION_DIR)
# Configuration
input_video = "input_video.mp4"  # Replace with your video path
output_template = "output_crf{}.mp4"
crf_values = [18, 22, 26, 30, 34]
quality_metric = "psnr"  # Can be 'psnr' or 'ssim'

# Prepare lists for results
bitrates = []
psnr_values = []

# Function to get bitrate using ffprobe
def get_bitrate(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=bit_rate", "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return int(result.stdout.strip()) / 1000  # in kbps

# Function to get PSNR
def get_psnr(reference, encoded):
    result = subprocess.run(
        ["ffmpeg", "-i", encoded, "-i", reference, "-lavfi", "psnr", "-f", "null", "-"],
        stderr=subprocess.PIPE,
        text=True
    )
    for line in result.stderr.splitlines():
        if "average:" in line:
            avg_psnr = float(line.split("average:")[-1].split()[0])
            return avg_psnr
    return None

# Process CRF encodings
for crf in tqdm(crf_values):
    output_file = output_template.format(crf)

    # Encode video
    subprocess.run(["ffmpeg", "-y", "-i", input_video, "-c:v", "libx264", "-crf", str(crf), output_file],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Get bitrate and quality
    bitrate = get_bitrate(output_file)
    psnr = get_psnr(input_video, output_file)

    bitrates.append(bitrate)
    psnr_values.append(psnr)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(bitrates, psnr_values, marker='o')
plt.xlabel("Bitrate (kbps)")
plt.ylabel("PSNR (dB)")
plt.title("Rate-Distortion Curve")
plt.grid(True)
plt.tight_layout()
plt.savefig(f"Rate_Distortion_Curve_For_{input_video}.png")
