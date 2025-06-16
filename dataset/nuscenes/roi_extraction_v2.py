import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

# === Step 1: Load attention map ===
attention_map_path = "/home/ob3942/datasets/nuscenes/sample_attention_map.npy"  # update path if needed
attention_map = np.load(attention_map_path)  # shape: H x W

# === Step 2: Cluster into 5 groups ===
flat_values = attention_map.flatten().reshape(-1, 1)
kmeans = KMeans(n_clusters=7, random_state=0)
cluster_labels = kmeans.fit_predict(flat_values)
clustered_map = cluster_labels.reshape(attention_map.shape)

# === Step 3: Sort clusters by attention (descending) ===
cluster_order = np.argsort(kmeans.cluster_centers_.flatten())[::-1]

# === Step 4: Compute rectangular RoIs for each cluster ===
rois = []
for cluster_idx in cluster_order:
    mask = (clustered_map == cluster_idx).astype(np.uint8)
    if mask.sum() == 0:
        continue
    ys, xs = np.where(mask)
    top = ys.min()
    bottom = ys.max()
    left = xs.min()
    right = xs.max()
    rois.append((left, top, right, bottom))

# === Step 5: Plot and save image with RoIs ===
fig, ax = plt.subplots(figsize=(16, 9))
ax.imshow(attention_map, cmap='hot')

# Draw each ROI rectangle
for i, (left, top, right, bottom) in enumerate(rois):
    rect = patches.Rectangle((left, top), right - left, bottom - top,
                             linewidth=2, edgecolor='cyan', facecolor='none')
    ax.add_patch(rect)
    ax.text(left, bottom-10, f'ROI {i+1}', color='cyan', fontsize=15, weight='bold')

plt.axis('off')
output_path = "/home/ob3942/datasets/nuscenes/attention_with_rois.png"
plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
plt.close()

output_path
