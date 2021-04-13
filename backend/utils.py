import bz2
import hashlib
import _pickle as cPickle

from skimage import color
import numpy as np
from scipy import signal
import os
import netCDF4
from scipy.spatial import ConvexHull
from scipy.spatial.distance import cdist
import math

# Normalize with the same scaling factor in all directions
def normalize_point(points):
    points_min_vector = np.min(points)
    points_max_vector = np.max(points)
    points_normalized = (points - points_min_vector) / (points_max_vector - points_min_vector)
    return points_normalized
    
# Identify most distant points
# https://stackoverflow.com/questions/31667070/max-distance-between-2-points-in-a-data-set-and-identifying-the-points
def bestpair(points):
    hull = ConvexHull(points)
    hullpoints = points[hull.vertices,:]
    # Naive way of finding the best pair in O(H^2) time if H is number of points on
    # hull
    hdist = cdist(hullpoints, hullpoints, metric='euclidean')
    # Get the farthest apart points
    bestpair = np.unravel_index(hdist.argmax(), hdist.shape)
    return hullpoints[bestpair[0]], hullpoints[bestpair[1]]
    
# Puts maximum distance on diagonal
def rotate_points(points):
    p1, p2 = bestpair(points)
    # Get the angle between the points and the diagonal
    vec = p2-p1
    vec_norm = vec/np.linalg.norm(vec)
    # Rotate around vector perpendicular to the other two
    direction = np.array([1,1,1])/np.sqrt(3)
    n = np.cross(vec_norm, direction)
    n = n/np.linalg.norm(n)
    rot_angle = math.acos(np.dot(vec_norm, direction))
    cosA = math.cos(rot_angle)
    sinA = math.sin(rot_angle)
    rot_mat = np.array([[n[0]**2*(1-cosA)+cosA, n[0]*n[1]*(1-cosA)-n[2]*sinA, n[0]*n[2]*(1-cosA)+n[1]*sinA],
                        [n[1]*n[0]*(1-cosA)+n[2]*sinA, n[1]**2*(1-cosA)+cosA, n[1]*n[2]*(1-cosA)-n[0]*sinA],
                        [n[2]*n[0]*(1-cosA)-n[1]*sinA, n[2]*n[1]*(1-cosA)+n[0]*sinA, n[2]**2*(1-cosA)+cosA]])
    # Rotate points:
    points_rot = np.empty(points.shape)
    for i in range(len(points)):
        points_rot[i] = np.matmul(rot_mat, points[i])
    return points_rot

# Use the sobel operator to create a gradient image
def gradient_image(image_data):
    gradient_image = []
    sobel = np.array([[-1, 0, 1], [-4, 0, 4], [-1, 0, 1]])
    for i in range(0, image_data.shape[2]):
        chan = image_data[..., i]
        dx = np.abs(signal.convolve2d(chan, sobel, 'same'))
        dy = np.abs(signal.convolve2d(chan, sobel.T, 'same'))
        for row in range(dx.shape[0]):
            p = 1 / (dx.shape[0] - 1) * row  # scale btwn 0 and 1 pi
            sin = np.sin(p * np.pi)
            dx[row] = dx[row] * sin
        gradient_image.append(dx + dy)
    return np.array(gradient_image)

# Create mds image in L*a*b* space
def mds_image(mds_points, img_shape):
    mds_points = rotate_points(mds_points)
    mds_points = normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*img_shape, mds_points.shape[-1]))
    mds_image[:,:,0]=mds_image[:,:,0]*100
    mds_image[:,:,1]=mds_image[:,:,1]*100-50
    mds_image[:,:,2]=mds_image[:,:,2]*100-50
    mds_image = color.lab2rgb(mds_image)
    return mds_image


def calculate_shifted_correlations(timelines, dt=0):
    if dt == 0:
        return np.corrcoef(timelines)
    timelines_shifted_back = timelines[:, :-dt]
    timelines_shifted_front = timelines[:, dt:]
    dt_corr = []
    for i, row in enumerate(timelines):
        row_timelines = np.copy(timelines_shifted_back)
        row_timelines[i] = timelines_shifted_front[i]
        corr = np.corrcoef(row_timelines)
        dt_corr.append(corr[i])
    return np.array(dt_corr)


def calculate_ensemble_segment_means(ensemble_path, segmented_image, variable='ts', transpose_field=None):
    ensemble_runs = os.listdir(ensemble_path)
    ensemble_segment_means = []
    for ensemble_run in ensemble_runs:
        ensemble_run_path = os.path.join(ensemble_path, ensemble_run)
        f = netCDF4.Dataset(os.path.join(ensemble_run_path, os.listdir(ensemble_run_path)[0]))
        field = f.variables[variable]
        if transpose_field is not None:
            field = np.transpose(field, transpose_field)
        segment_means = calculate_segment_means(segmented_image, field)
        ensemble_segment_means.append(segment_means)
    return np.array(ensemble_segment_means)

# Helper function for load_or_calculate
def compressed_pickle(data, path):
    with bz2.BZ2File(path, 'w') as f:
        cPickle.dump(data, f)
        return data

# Helper function for load_or_calculate
def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    data = cPickle.load(data)
    return data

# Test if already calculated, then load, otherwise calculate and save
def load_or_calculate(callback, **kwargs):
    hash = hashlib.md5((str(kwargs) + callback.__name__).encode()).hexdigest()
    path = os.path.join('tmp', hash + '.pbz2')
    if os.path.exists(path):
        print('Loaded from tmp')
        return decompress_pickle(path)
    res = callback(**kwargs)
    compressed_pickle(res, path)
    return res

# Remove diagonal elements from matrix
def remove_diagonal(A):
    return np.delete(A, range(0, A.shape[0] ** 2, A.shape[0])).reshape(A.shape[0], A.shape[1] - 1)
