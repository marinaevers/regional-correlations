import segment as s
import numpy as np
import utils as u
import time
import os
import netCDF4
from skimage import color

# Artificial
FILE_NAME = '../tmp/segments.dat' # Path to the output file created by preprocessing_segmentation.py
MDS_POINTS_PATH = '../tmp/y_full.npy'  # Path to the mds embedding (normally located in the folder set as OUT in create_correlation_mds.py)
CORRELATION_PATH = '../tmp/corr_full.npy'  # Path to the correlation matrix (normally located in the folder set as OUT in create_correlation_mds.py)
ENSEMBLE_PATH = "../artificialData/" # Path to ensemble data
FIELD_VARIABLE = 'data' # Name of the field in the nc file
SHAPE = (300, 16, 24) # Shape of the data, where the first number indicate number of timesteps

# Calculate mean color for segment n
def get_mean_color(n, segments, mds_image):
    pixel, _ = segments[n].get_pixel(segments)
    pixel = np.array(pixel)
    mean = (np.mean(mds_image[pixel[:,1], pixel[:,0]], axis=0)*255).tolist()
    mean.append(255)
    return mean

# Convert maximum standard deviation to color
def get_max_std_color(std, max_std):
    v = (1.0-std/max_std) * 255
    return [v, v, v, 255]

# Get number of child segments for segment n
# converted to a color
def get_num_child_segments(n, segments, max):
    # Count children
    children = get_children(n, segments)
    v = (1.0-children/max) * 255
    return [v, v, v, 255]

# Determine number of leaves belonging to segment n
def get_children(n, segments):
    if(segments[n].is_leaf):
        return 1
    else:
        children = 0
        for c in segments[n].children:
            children = children + get_children(c, segments)
        return children

# Determine the maximum standard deviation for segment seg
def get_max_std_dev(seg, segments):
    pixels, _ = segments[seg].get_pixel(segments)
    pixels = np.array(pixels)
    ensemble_runs = os.listdir(ENSEMBLE_PATH)
    time_series = None
    for e in ensemble_runs:
        ensemble_run_path = os.path.join(ENSEMBLE_PATH, e)
        f = netCDF4.Dataset(os.path.join(ensemble_run_path, os.listdir(ensemble_run_path)[0]))
        field = f.variables[FIELD_VARIABLE]
        field = np.transpose(field, (1, 2, 0))
        if(np.any(time_series == None)):
            time_series = field[pixels[:,1], pixels[:,0]]
        else:
            time_series = time_series + field[pixels[:,1], pixels[:,0]]
    time_series = time_series/len(ensemble_runs)
    std = np.std(time_series, axis = 0)
    max = np.max(std)
    return max

# Determine minimum correlation with segment seg involved, converted to color
def get_min_corr(seg, segments, threshold):
    v = 0
    # Get nodes
    if(segments[seg].is_leaf):
        return [v, v, v, 255]
    nodes = get_leaf_nodes(seg, segments)
    # Get matrix
    matrix = get_correlation_matrix_from_nodes(nodes, segments, threshold)
    min = np.min(matrix)
    # Create color from min
    v = (1.0-0.5*(min+1))*255
    return [v, v, v, 255]

# Determine leaves belonging to segment n
def get_leaf_nodes(seg, segments):
    nodes = []
    if(segments[seg].is_leaf):
        nodes = [seg]
    else:
        for c in segments[seg].children:
            nodes = nodes + get_leaf_nodes(c, segments)
    return nodes

# Determine correlation matrix for a list of segments
def get_correlation_matrix_from_nodes(nodes, segments, threshold):
    corr = np.empty((len(nodes), len(nodes)))
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if(i==j):
                corr[i,j]=1
            else:
                if(str(threshold) in segments[nodes[i]].correlations and nodes[j] in segments[nodes[i]].correlations[str(threshold)]):
                    corr[i,j]=segments[nodes[i]].correlations[str(threshold)][nodes[j]][0]
                else:
                    print("Ups, Problem")
                    exit()
    return corr

start_load = time.time()
segments = s.load(FILE_NAME)
print("Loading: " + str(time.time()-start_load))

start_calc = time.time()
mds_points = np.load(MDS_POINTS_PATH)
image_shape = SHAPE[1:]
mds_image_lab = u.mds_image(mds_points, image_shape)

# Number of segments
num_segs = 0
for seg in segments:
    if(segments[seg].is_leaf):
        num_segs = num_segs + 1

for seg in segments:
    print(seg)
    segments[seg].colors = {}
    segments[seg].colors["mean_lab"] = get_mean_color(seg, segments, mds_image_lab)
print("Calculation: " + str(time.time()-start_calc))


start_save = time.time()
s.save(FILE_NAME, segments)
print("Saving: " + str(time.time()-start_save))
