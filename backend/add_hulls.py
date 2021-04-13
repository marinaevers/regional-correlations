import segment as s
import numpy as np
import utils as u
import time
import alphashape

FILE_NAME = '../tmp/segments.dat' # Path to the output file created by preprocessing_segmentation.py

def calculate_hull(segments, n):
    segment_points, is_line = segments[n].get_pixel(segments)
    is_split, split_idx = test_split_segment(segment_points)
    # Here only split in x-direction
    if not is_line:
        hull = alphashape.alphashape(segment_points, 1)
        try:
            hull = np.array([hull.exterior.coords.xy[1], hull.exterior.coords.xy[0]]).T.tolist()
        except Exception as e:
            if len(hull) > 0:
                hulls = []
                is_lines = []
                for h in hull:
                    hulls.append(np.array([h.exterior.coords.xy[1], h.exterior.coords.xy[0]]).T.tolist())
                    pixel_array = np.array(hulls[-1])
                    is_lines.append(len(np.unique(pixel_array[:,0]))==1 or len(np.unique(pixel_array[:,1]))==1)
                return hulls, is_lines
            else:
                return [[[]]], [is_line]
    else:
        if(is_split):
            hull = split_points(segment_points, split_idx)
            return hull, np.full((len(hull)), True).tolist()
        else:
            hull = segment_points
    return [hull], [is_line]

def test_split_segment(points):
    points = np.array(points)
    # x-direction
    x_diff = np.diff(np.unique(points[:,0]))
    if(np.any(x_diff > 1)):
        return True, int(np.arange(len(x_diff))[x_diff>1])
    # y-direction not relevant for our dataset
    return False, 0

def split_points(segment_points, idx):
    # Split only in x-direction possible (choice of datasets)
    points = np.array(segment_points)
    first = points[points[:,0]<=idx].tolist()
    second = points[points[:,0]>idx].tolist()
    return [first, second]

start_load = time.time()
segments = s.load(FILE_NAME)
print("Loading: " + str(time.time()-start_load))

start_calc = time.time()

for seg in segments:
    segments[seg].hulls, segments[seg].is_lines = calculate_hull(segments, seg)
print("Calculation: " + str(time.time()-start_calc))

start_save = time.time()
s.save(FILE_NAME, segments)
print("Saving: " + str(time.time()-start_save))
