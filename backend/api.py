import argparse
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')

import api_helper as ah
import numpy as np
import nibabel as nib
# pip install flask flask-cors
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import imageio

from utils import mds_image


class Cachable:
    cache = {}

    def find_or_calculate(self, key, logic, arguments):
        if key in self.cache:
            return self.cache[key]
        self.cache[key] = logic(*arguments)

        return self.cache[key]
        # pass


# Artificial
class Global(Cachable):
   segments = {} # Do not change
   segment_path = '../tmp/segments.dat' # Path to the output file created by preprocessing_segmentation.py
   mds_point_path = '../tmp/y_full.npy'  # Path to the mds embedding (normally located in the folder set as OUT in create_correlation_mds.py)
   circular = True # Is the dataset periodic along the x-axis? Should fit the setting in preprocessing_segmentation.py
   sobel = False # If True, the Sobel filter is used for gradient calculations, otherwise the Euclidean distance.  Should fit the setting in preprocessing_segmentation.py
   linkage_method = 'centroid' # Do not change (can be adapted interactively in the GUI)
   shape = (24,16)  # Spatial shape of the data
   tree = None # Do not change
   altitudes = [] # Do not change
   thresholds = [0.9, 0.8, 0.95] # Must fit the settings in preprocessing_segmentation.py
   timelag_range = [-20, 20] # See MAX_TIME_LAG in preprocessing_segmentation.py. Set to -MAX_TIME_LAG and MAX_TIME_LAG.
   coastline = None # Set to file with coastline overlay, if desired
   # e. g. base64.b64encode(open('assets/coastline-world2.png', "rb").read()).decode("utf-8")

app = Flask(__name__)
CORS(app)

g = Global()


def error(message):
    return jsonify({
        "status": 419,
        "data": message
    })


def json(data):
    return jsonify(data)


@app.route("/get-mds-image/<swap>", methods=['GET'])
def get_mds_image(swap=False):
    global g
    mds_points = mds_image(np.load(g.mds_point_path), [g.shape[1], g.shape[0]])
    b = BytesIO()
    mds_img = (mds_points * 255).astype(np.uint8)

    if swap == 'true':
        print('swapping')
        mds_img = np.hstack([mds_img[:, mds_img.shape[1] // 2:], mds_img[:, :mds_img.shape[1] // 2]])

    im = Image.fromarray(mds_img)
    im.save(b, format='PNG')

    return jsonify({
        "image": base64.b64encode(b.getvalue()).decode("utf-8"),
        "overlay": g.coastline
    })


@app.route("/get-time-lag-range", methods=['GET'])
def get_time_lag_range():
    return json(g.timelag_range)


@app.route("/", methods=['GET'])
def index():
    # volume = np.random.rand(180, 180, 210)
    # new_image = nib.Nifti1Image(volume, affine=np.eye(4))
    # nib.save(new_image, 'tmp/test.nii')
    # request.headers['Content-Security-Policy'] = 'octet-stream'
    # request.headers['Content-Type'] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    return send_from_directory(directory='/home/karim/Projects/phd/correlation-mds/tmp/', filename='eun_uchar_8.nii.gz')


@app.route("/get-thresholds", methods=['GET'])
def get_thresholds():
    return jsonify(g.thresholds)


@app.route("/get-volume/<filename>", methods=['GET'])
def get_volume(filename):
    # return send_from_directory(directory='/home/karim/Projects/phd/correlation-mds/tmp/', filename='eun_uchar_8.nii.gz')
    volume = (np.random.rand(180, 180, 210) * 100).astype(np.uint8)
    new_image = nib.Nifti1Image(volume, affine=np.eye(4))
    nib.save(new_image, 'tmp/test.nii')
    return send_from_directory(directory='tmp/', filename='test.nii')

@app.route("/get-volume/<filename>", methods=['GET'])
def get_volume3(filename):
    volume = np.random.rand(180, 180, 210)
    nrrd.write('tmp/test.nrrd', volume)
    return send_from_directory(directory='tmp', filename='test.nrrd')




@app.route("/get-segments-by-watershed-level/<watershedLevel>", methods=['GET'])
def get_segments_by_watershed_level(watershedLevel):
    watershedLevel = int(watershedLevel)
    segments = g.find_or_calculate(f'segments-ws-{watershedLevel}', ah.get_segment_list, (g, watershedLevel))
    return json({
        "dimensions": [g.shape[0], g.shape[1]],
        "watershed_level": watershedLevel,
        "segments": segments
    })


# TODO: Remove initWatershedLevel
@app.route("/refine-segment/<segments>/<initWatershedLevel>/<watershedLevel>", methods=['GET'])
def refine_segment(segments, initWatershedLevel, watershedLevel):
    watershedLevel = int(watershedLevel)
    segments = list(map(int, segments.split(',')))
    segments_out = ah.refine_segment(g, segments, watershedLevel)
    return json({
        "dimensions": [g.shape[0], g.shape[1]],
        "watershed_level": watershedLevel,
        "segments": segments_out
    })


@app.route("/get-correlation-matrix-by-watershed-level/<watershedLevel>/<threshold>/<linkage>", methods=['GET'])
@app.route("/get-correlation-matrix-by-watershed-level/<watershedLevel>/<threshold>/<linkage>/<segments>", methods=['GET'])
def get_correlation_matrix_by_watershed_level(watershedLevel, threshold=None, linkage='single', segments=None):
    watershedLevel = int(watershedLevel)
    g.linkage_method = linkage
    if(threshold == None):
        threshold = 0.9
    matrix, time_lags, row, col = ah.get_correlation_matrix(g, segments, watershedLevel, threshold)
    l = len(row)
    #print(l)
    if(l == 1):
        return json(None)
    else:
        return json({
            "dimensions": [l, l],
            "linkage": linkage,
            "threshold": threshold,
            "matrix": {
                "row_segments": row,
                "col_segments": col,  # falls nicht symmetrisch, sonst = row_segments setzen,
                "segment_colors": ah.get_color_dict(g, row),
                "rows": matrix,
                "time_lags": time_lags
            }
        })

# TODO: Remove?
@app.route("/refine-segment-for-level/<segment>/<watershedLevel>", methods=['GET'])
def refine_segment_for_level(segment, watershedLevel):
    return json([
        {
            "segment": 1337,
            "hull": [[1, 2], [2, 3], [4, 5]],
            "color": [1, 0, 0, 1],
            "is_line": False
        },
        {
            "segment": 1338,
            "hull": [[1, 2], [2, 3], [4, 5]],
            "color": [1, 0, 0, 1],
            "is_line": False
        }
    ])

@app.route("/get-curves-for-segments/<segments>", methods=['GET'])
def get_curves_for_segments(segments):
    curves = []
    segments = list(map(int, segments.split(',')))
    for s in segments:
        curves.append(ah.get_curves_for_segment(g, s))
    result = {s['segment']: s for s in curves}
    return json(result)

@app.route("/hello-world", methods=['GET', 'POST'])
def hello_world():
    if request.method == 'GET':
        return 'Hi, i am the response to a GET request'
    if request.method == 'POST':
        return 'Hi, i am the response to a POST request'

if __name__ == '__main__':
    ah.setup(g)
    parser = argparse.ArgumentParser(description='Start the webserver.')
    parser.add_argument('--port', type=int, help='Port for the webserver (default 5000)', default=5000)
    parser.add_argument('--host', help='Host for the webserver (default 0.0.0.0)', default='0.0.0.0')
    args = vars(parser.parse_args())
    app.run(debug=False, port=args['port'], host=args['host'])
