# determine the best way to determine the quantization offset for the given roi
# there will be min and max qp values that our algorithm adjusts the qps per RoIs accordingly

import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from fractions import Fraction

# Re-load attention map
attention_map_path = "/home/ob3942/datasets/nuscenes/sample_attention_map.npy"
attention_map = np.load(attention_map_path)

# Step 1: Cluster into 5 groups
flat_values = attention_map.flatten().reshape(-1, 1)
kmeans = KMeans(n_clusters=7, random_state=0)
cluster_labels = kmeans.fit_predict(flat_values)
clustered_map = cluster_labels.reshape(attention_map.shape)

# Step 2: Sort clusters by descending attention
cluster_order = np.argsort(kmeans.cluster_centers_.flatten())[::-1]

# Step 3: Extract RoIs and attention values
rois = []
roi_lines = []

for cluster_idx in cluster_order:
    mask = (clustered_map == cluster_idx).astype(np.uint8)
    if mask.sum() == 0:
        continue
    ys, xs = np.where(mask)
    top = ys.min()
    bottom = ys.max()
    left = xs.min()
    right = xs.max()
    
    # Calculate average attention in ROI
    roi_attention = attention_map[top:bottom+1, left:right+1]
    roi_mask = mask[top:bottom+1, left:right+1]
    avg_attention = roi_attention[roi_mask == 1].mean()
    
    # Estimate rational number approximation
    frac = Fraction(float(avg_attention)).limit_denominator(1000)

    
    # Store
    rois.append((left, top, right, bottom))
    roi_lines.append(f"{left},{top},{right},{bottom},{frac.numerator},{frac.denominator}")

# Step 4: Plot attention map with rectangles
fig, ax = plt.subplots(figsize=(16, 9))
ax.imshow(attention_map, cmap='hot')

for i, (left, top, right, bottom) in enumerate(rois):
    rect = patches.Rectangle((left, top), right - left, bottom - top,
                             linewidth=2, edgecolor='cyan', facecolor='none')
    ax.add_patch(rect)
    ax.text(left, top - 5, f'ROI {i+1}', color='cyan', fontsize=10, weight='bold')

plt.axis('off')
image_output_path = "/home/ob3942/datasets/nuscenes/attention_with_rois.png"
plt.savefig(image_output_path, bbox_inches='tight', pad_inches=0)
plt.close()

# Step 5: Save ROI data to .txt
roi_output_path = "/home/ob3942/datasets/nuscenes/roi_extraction_output.txt"
with open(roi_output_path, "w") as f:
    f.write(";".join(roi_lines))

print(f"RoIs are saved into: {image_output_path}, {roi_output_path}.")
