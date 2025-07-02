import os
import subprocess
import matplotlib.pyplot as plt
from tqdm import tqdm
OPERATION_DIR = "/home/ob3942/Downloads/MAVREC/"

os.chdir(OPERATION_DIR)
# Define CRF values to test
crf_values = list(range(18, 36, 2))  # From 18 to 34
bitrates_h264 = []
bitrates_h265 = []

# Input video path (should exist in the current directory)
input_file = "input_video.mp4"

def get_bitrate(output_file):
    """Extracts the bitrate of a video file using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "format=bit_rate", "-of", "default=noprint_wrappers=1:nokey=1", output_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.stdout.strip():
        return int(result.stdout.strip()) / 1000  # in kbps
    return None

# Encode with H.264 and H.265 for each CRF value
for crf in tqdm(crf_values):
    # H.264
    output_h264 = f"output_crf{crf}_h264.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", input_file, "-c:v", "libx264", "-crf", str(crf), output_h264],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bitrate = get_bitrate(output_h264)
    bitrates_h264.append(bitrate)

    # H.265
    output_h265 = f"output_crf{crf}_h265.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", input_file, "-c:v", "libx265", "-crf", str(crf), output_h265],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bitrate = get_bitrate(output_h265)
    bitrates_h265.append(bitrate)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(crf_values, bitrates_h264, marker='o', label="H.264 (libx264)")
plt.plot(crf_values, bitrates_h265, marker='x', label="H.265 (libx265)")
plt.xlabel("CRF Value")
plt.ylabel("Bitrate (kbps)")
plt.title("Bitrate vs CRF for H.264 and H.265")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(f"BitRate_vs_CRF_For_{input_file}.png")
