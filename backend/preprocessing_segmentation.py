import numpy as np
import utils as u
import higra as hg
import time
import os
import netCDF4
import json
from joblib import Parallel, delayed
import segment

# # Artificial
ENSEMBLE_PATH = "../artificialData/" # Path to ensemble data
MDS_POINTS_PATH = '../tmp/y_full.npy'  # Path to the mds embedding (normally located in the folder set as OUT in create_correlation_mds.py)
SHAPE = (300, 16, 24) # Shape of the data, where the first number indicate number of timesteps
FIELD_VARIABLE = 'data'  # Name of the field in the nc file
THRESHOLDS = [0.9, 0.8, 0.95] # If the absolute value of the correlation exceeds this value, the time series are considered correlated. If more than one value is used, the user can switch interactively in the application (keep an eye on the memory for larger datasets)
CIRCULAR = True # Is the dataset periodic along the x-axis?
SOBEL = False # If True, the Sobel filter is used for gradient calculations, otherwise the Euclidean distance
MAX_TIME_LAG = 20 # Which maximal time lag should be taken into account?
OUT_FILE = '../tmp/segments.dat' # Output path

# Global variables
leaf_counter = 0
node_counter = 0

# Store segments from tree
def add_segments(tree, altitudes, shape, segments, root_index, parent_index):
    children = tree.children(root_index)
    if(altitudes[root_index]>0):
        segments[int(root_index)] = segment.Segment(parent_index, children, shape)
        for child in children:
            add_segments(tree, altitudes, shape, segments, child, root_index)
    else:
        # Leaf
        segments[int(root_index)] = segment.Segment(parent_index, children, img_shape, True)


# Add correlations to tree structure
def add_correlations(node, segments, branch_list, t):
    # Basic idea: Calculate correlations among the segments under consideration and all segments in the branches determined
    # by the root nodes stored in branch_list
    global leaf_counter
    global node_counter
    print(str(node_counter) + " node")
    node_counter = node_counter + 1
    time_before = time.time()
    for b in branch_list:
        store_correlations(node, segments, b, t)
    h = get_height(segments, node, 0)
    if(not segments[node].is_leaf):
        if(len(segments[node].children) > 1 and h>10):
            Parallel(n_jobs=-1, backend="threading")(delayed(treat_child)(segments, node, branch_list, c) for c in segments[node].children)
        elif(len(segments[node].children) > 1):
            for c in segments[node].children:
                treat_child(segments, node, branch_list, c)
        else:
            add_correlations(segments[node].children[0], segments, branch_list, t)
    else:
        print("Leaf: " + str(leaf_counter))
        leaf_counter = leaf_counter+1

# Height for node in dendrogram tree
def get_height(segments, node, height):
    m = height
    if(not segments[node].is_leaf):
        for c in segments[node].children:
            m = max(m, get_height(segments, c, height))
    return m+1

# Add correlations for child
def treat_child(segments, node, branch_list, c):
    additional_branches = segments[node].children.copy()
    additional_branches.remove(c)
    add_correlations(c, segments, branch_list+additional_branches, t)

# Calculate correlations if necessary and store in respective segment
def store_correlations(node, segments, branch, t):
    if(str(t) in segments[branch].correlations and node in segments[branch].correlations[str(t)]):
        segments[node].add_correlation(branch, segments[branch].correlations[str(t)][node][0], segments[branch].correlations[str(t)][node][1], t)
    else:
        # First element of list is the node itself. On this point only necessary
        # to allows easy access later on
        corr, lag = get_correlation(node, branch, segments, t)
        segments[node].add_correlation(branch, corr, lag, t)
    if(not segments[branch].is_leaf):
        for c in segments[branch].children:
            store_correlations(node, segments, c, t)

# Determine thresholds correlations between seg_a and seg_b
def get_correlation(seg_a, seg_b, segments, t):
    means_a = segments[seg_a].means
    means_b = segments[seg_b].means
    corrs= calculate_shifted_correlations(means_a, means_b)
    max_corr_i = np.argmax(np.absolute(corrs), axis=0)
    counts = np.bincount(max_corr_i)
    lag = np.argmax(counts)
    max_corr = corrs[lag]
    max_corr[max_corr >= t] = 1
    max_corr[np.logical_and(max_corr < t, max_corr > -t)] = 0
    max_corr[max_corr <= -t] = -1
    if(1 in np.unique(max_corr) and -1 in np.unique(max_corr)):
        print("Strong positive and negative correlations!")
        print(corrs.shape)
        print(max_corr.shape)
    corr = np.mean(max_corr)
    if(len(np.unique(max_corr_i))>1 and corr != 0):
        print("Lots of values...")
        print(np.unique(max_corr_i))
    return corr, lag

# Determine ensemble means for segment seg
def get_ensemble_means(seg, segments):
    if(segments[seg].means != None):
        return segments[seg].means
    ensemble_runs = os.listdir(ENSEMBLE_PATH)
    ensemble_means = []
    pixels = segments[seg].get_pixel(segments)[0]
    ensemble_means = Parallel(n_jobs=-1, backend="threading")(delayed(load_and_calc_mean)(e, pixels) for e in ensemble_runs)
    segments[seg].means = ensemble_means
    return np.array(ensemble_means)

# Load data and caclculate segment means for ensemble run for respective pixels
def load_and_calc_mean(ensemble_run, pixels):
    ensemble_run_path = os.path.join(ENSEMBLE_PATH, ensemble_run)
    f = netCDF4.Dataset(os.path.join(ensemble_run_path, os.listdir(ensemble_run_path)[0]))
    field = f.variables[FIELD_VARIABLE]
    field = np.transpose(field, (1, 2, 0))
    segment_means = calculate_segment_means(pixels, field)
    return segment_means

# Calculate mean over given pixels
def calculate_segment_means(pixel, field):
    before_mean = time.time()
    pixel = np.array(pixel)
    mean = np.mean(field[pixel[:,1], pixel[:,0]], axis=0)
    return mean

# Determine correlations with a given time lag
def calculate_shifted_correlations(means_a, means_b):
    a_sub = np.array([np.mean(means_a, axis=1)]).transpose(1,0)
    a = np.subtract(means_a, a_sub)
    b_sub = np.array([np.mean(means_b, axis=1)]).transpose(1,0)
    b = np.subtract(means_b, b_sub)
    corrs = np.array([np.correlate(a[i],b[i],mode='full')[len(a[i])-1-MAX_TIME_LAG:len(a[i])+MAX_TIME_LAG]/(np.sqrt(np.correlate(a[i],a[i]))*np.sqrt(np.correlate(b[i],b[i]))) for i in range(len(means_a))]).transpose(1,0)
    if(np.any(corrs<-1.00001) or np.any(corrs>1.00001)):
        print("Problem!")
        print(np.min(corrs))
        print(np.max(corrs))
        exit()
    return corrs

# Calculate mean for the respective segment (node) and store in it
def add_means(node, segments):
    start = time.time()
    if(not segments[node].is_leaf):
        size = len(segments[node].get_pixel(segments)[0])
        means = []
        area_size = 0
        for c in segments[node].children:
            add_means(c, segments)
            num_pixel = len(segments[c].get_pixel(segments)[0])
            if(len(means) == 0):
                means = num_pixel*segments[c].means
            else:
                means = means + num_pixel*segments[c].means
            area_size = area_size + num_pixel
        segments[node].means = means/area_size
    else:
        segments[node].means = get_ensemble_means(node, segments)

# -------------------------
#         Skript
# -------------------------

start = time.time()

#Load data
mds_points = np.load(MDS_POINTS_PATH)
image_shape = SHAPE[1:]
mds_points = u.normalize_point(mds_points)
mds_image = np.reshape(mds_points, (*image_shape, mds_points.shape[-1]))

size = mds_image.shape[:2]

graph = hg.get_4_adjacency_graph(size)
grad_img = None
if(CIRCULAR):
    stiched_mds_image = np.hstack((mds_image,) * 3)
    stitched_grad_img = u.gradient_image(stiched_mds_image)

    stitched_grad_img = np.transpose(stitched_grad_img, (1,2,0))
    stitched_grad_img = np.linalg.norm(stitched_grad_img, axis=2)
    grad_img = stitched_grad_img[:, size[1]:2*size[1]]

    sources = np.arange(0, graph.num_vertices(), size[1])
    targets = np.arange(size[1]-1, graph.num_vertices(), size[1])
    graph.add_edges(sources, targets)

if(SOBEL):
    if(grad_img == None):
        grad_img = u.gradient_image(mds_image)
        grad_img = np.transpose(grad_img, (1,2,0))
        grad_img = np.linalg.norm(grad_img, axis=2)
    edge_weights = hg.weight_graph(graph, grad_img, hg.WeightFunction.mean)
else:
    edge_weights = hg.weight_graph(graph, mds_points, hg.WeightFunction.L2)
tree, altitudes = hg.watershed_hierarchy_by_area(graph, edge_weights)

img_shape = (size[1], size[0])

segments = {}
root_index = tree.root()
add_segments(tree, altitudes, img_shape, segments, root_index, -1)

print("Segmentation in " + str((time.time()-start)*1000) + "ms")

print("Start means")
root_index = tree.root()
add_means(root_index, segments)
segment.save(OUT_FILE, segments)
start_calc = time.time()
for s in segments:
    segments[s].correlations = {}

print("Start correlations")

for t in THRESHOLDS:
    add_correlations(root_index, segments, [], t)
    print("Calculation done")
    segment.save(OUT_FILE, segments)
    print(str(t) + " Done")
    leaf_counter = 0
    node_counter = 0

print("Done: " + str(time.time()-start_calc))
