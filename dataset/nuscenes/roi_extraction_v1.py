import numpy as np
from sklearn.cluster import KMeans
import os

# Define the path to the attention map .npy file
attention_map_path = "/home/ob3942/datasets/nuscenes/sample_attention_map.npy"

# Load attention map from .npy file
if os.path.exists(attention_map_path):
    attention_map = np.load(attention_map_path)
else:
    raise FileNotFoundError(f"Attention map file not found at: {attention_map_path}")

# Flatten for clustering
flat_values = attention_map.flatten().reshape(-1, 1)

# Step 2: KMeans clustering into 5 clusters
kmeans = KMeans(n_clusters=5, random_state=0) # TODO indicate why the clustering is required for this application as there might be noisy pixels around.
cluster_labels = kmeans.fit_predict(flat_values)
clustered_map = cluster_labels.reshape(attention_map.shape)

# Step 3: Rank clusters from highest to lowest attention (based on cluster center value)
cluster_order = np.argsort(kmeans.cluster_centers_.flatten())[::-1]

# Step 4: For each cluster (starting from highest), compute the minimal bounding rectangle
rois = []
for cluster_idx in cluster_order:
    mask = (clustered_map == cluster_idx).astype(np.uint8)
    if mask.sum() == 0:
        continue
    # Find non-zero coordinates
    ys, xs = np.where(mask)
    top = ys.min()
    bottom = ys.max()
    left = xs.min()
    right = xs.max()
    rois.append((left, top, right, bottom))

for i in rois:
    print(f"ROI frame left, top, right, bottom: {i}")
