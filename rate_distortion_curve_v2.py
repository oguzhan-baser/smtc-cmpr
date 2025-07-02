import os
import subprocess
import matplotlib.pyplot as plt
from tqdm import tqdm
OPERATION_DIR = "/home/ob3942/Downloads/MAVREC/"

os.chdir(OPERATION_DIR)
input_file = "input_video.mp4"
crf_values = list(range(18, 36, 2))
# crf_values = list(range(5, 50, 5))
codecs = {
    "H.264": "libx264",
    "H.265": "libx265"
}
bitrate_results = {"H.264": [], "H.265": []}
psnr_results = {"H.264": [], "H.265": []}

# Encode with each CRF and codec, and extract bitrate and PSNR
for codec_label, codec_lib in codecs.items():
    for crf in tqdm(crf_values):
        output_file = f"output_{codec_label.replace('.', '')}_crf{crf}.mp4"
        
        # Encode
        encode_cmd = [
            "ffmpeg", "-y", "-i", input_file, "-c:v", codec_lib,
            "-crf", str(crf), "-preset", "medium", output_file
        ]
        subprocess.run(encode_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Get bitrate using ffprobe
        bitrate_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1", output_file
        ]
        bitrate_output = subprocess.run(bitrate_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            bitrate = int(bitrate_output.stdout.decode().strip()) / 1000  # convert to kbps
        except:
            bitrate = 0
        bitrate_results[codec_label].append(bitrate)

        # Get PSNR
        psnr_cmd = [
            "ffmpeg", "-i", output_file, "-i", input_file,
            "-lavfi", "psnr", "-f", "null", "-"
        ]
        psnr_output = subprocess.run(psnr_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        psnr_lines = psnr_output.stderr.decode().split('\n')
        psnr_value = 0
        for line in psnr_lines:
            if "average:" in line:
                try:
                    psnr_value = float(line.strip().split("average:")[1].split()[0])
                except:
                    psnr_value = 0
                break
        psnr_results[codec_label].append(psnr_value)

# Plotting
plt.figure(figsize=(10, 6))
for codec_label in codecs:
    plt.plot(bitrate_results[codec_label],psnr_results[codec_label], marker='o', label=codec_label)

plt.title("Rate-Distortion Curve (Bitrate vs PSNR)")
plt.xlabel("Bitrate (kbps)")
plt.ylabel("PSNR (dB)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
plt.savefig(f"Rate_Distortion_Curve_For_{input_file}_v2.png")
