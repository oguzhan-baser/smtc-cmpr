# run this before running the script
# ffprobe -select_streams v -show_frames -show_entries frame=pkt_pts_time,pict_type,pkt_size -of json input_video.mp4 > frame_data.json
import json
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# Load JSON file containing ffprobe output with frame info
with open("/home/ob3942/Downloads/MAVREC/frame_data.json") as f:
    data = json.load(f)

total_size = 0
# Parse the frames
frames = []
for i, frame in enumerate(data["frames"]):
    frame_type = frame.get("pict_type")
    pkt_pts_time = float(frame.get("pkt_pts_time", 0))
    pkt_size = int(frame.get("pkt_size", 0))
    frames.append({
        "Frame Number": i,
        "Time (s)": pkt_pts_time,
        "Size (bytes)": pkt_size,
        "Type": frame_type
    })
    total_size +=pkt_size 

print(total_size)
# Create DataFrame
df = pd.DataFrame(frames)
# Plot using seaborn
plt.figure(figsize=(12, 6))
sns.set(style="darkgrid")
sns.scatterplot(data=df, x="Frame Number", y="Size (bytes)", hue="Type", palette="Set1", style="Type")
sns.lineplot(data=df, x="Frame Number", y="Size (bytes)", color="gray", alpha=0.3)
plt.title("Frame Size Over Time by Frame Type")
plt.xlabel("Frame Number")
plt.ylabel("Frame Size (bytes)")
plt.legend(title="Frame Type")
plt.grid(True)
plt.tight_layout()
plt.savefig("/home/ob3942/Downloads/MAVREC/size_vs_t.png")
