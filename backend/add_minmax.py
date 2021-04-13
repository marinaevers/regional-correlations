import numpy as np
import segment as s
import os
import netCDF4

# Artificial
FILE_NAME = '../tmp/segments.dat' # Path to the output file created by preprocessing_segmentation.py
MDS_POINTS_PATH = '../tmp/y_full.npy'  # Path to the mds embedding (normally located in the folder set as OUT in create_correlation_mds.py)
CORRELATION_PATH = '../tmp/corr_full.npy'  # Path to the correlation matrix (normally located in the folder set as OUT in create_correlation_mds.py)
ENSEMBLE_PATH = "../artificialData/" # Path to ensemble data
FIELD_VARIABLE = 'data' # Name of the field in the nc file
SHAPE = (300, 16, 24) # Shape of the data, where the first number indicate number of timesteps

segments = s.load(FILE_NAME)
print("Loaded")


def get_timeline_indices(seg):
    # Return indices of timelines
    pixels = np.array(segments[seg].get_pixel(segments)[0])
    # I have no idea why it is this way around but otherwise the results makes no sense
    indices = pixels[:, 1] * SHAPE[2] + pixels[:, 0]
    return indices


times = np.empty((0, 0))
numberOfRuns = len(os.listdir(ENSEMBLE_PATH))
i = 0
for run in os.listdir(ENSEMBLE_PATH):
    print("Loading run %s (%i)" % (run, (100.0 * i) / numberOfRuns))
    path = os.path.join(os.path.join(ENSEMBLE_PATH, run), os.listdir(os.path.join(ENSEMBLE_PATH, run))[0])
    f = netCDF4.Dataset(path)
    temp = f.variables[FIELD_VARIABLE]
    timelines = np.transpose(temp, axes=[1, 2, 0])
    timelines = timelines.reshape((timelines.shape[0] * timelines.shape[1], timelines.shape[2]))
    if times.shape == (0, 0):
        times = timelines
    else:
        times = np.append(times, timelines, axis=1)
    f.close()
    i += 1

for seg in segments:
    times_seg_idx = get_timeline_indices(seg)
    corrs = np.corrcoef(times[times_seg_idx])
    corrs = corrs - np.identity(corrs.shape[0]) * (1 - corrs[0, 1])
    segments[seg].min = np.min(corrs)
    segments[seg].max = np.max(corrs)

s.save(FILE_NAME, segments)
