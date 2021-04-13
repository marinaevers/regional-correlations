import segment as s
import higra as hg # pip install higra
import utils as u
import scipy.cluster.hierarchy as sch
import alphashape
import numpy as np
import statsmodels.api as sm
import math

# Load data and calculate herarchical segmentation
def setup(g):
    # Load data
    calculate_tree(g)
    g.segments = s.load(g.segment_path)
    pass

# Calculate hierarchical segmentation
def calculate_tree(g):
    # MDS image in RGB space
    mds_image = create_mds_img(g)
    size = (g.shape[1], g.shape[0])
    # Grad image
    grad_img = None
    if(g.circular):
        stiched_mds_image = np.hstack((mds_image,) * 3)
        stitched_grad_img = u.gradient_image(stiched_mds_image)

        stitched_grad_img = np.transpose(stitched_grad_img, (1,2,0))
        stitched_grad_img = np.linalg.norm(stitched_grad_img, axis=2)
        grad_img = stitched_grad_img[:, size[1]:2*size[1]]
    else:
        grad_img = u.gradient_image(mds_image)
        grad_img = np.transpose(grad_img, (1,2,0))
        grad_img = np.linalg.norm(grad_img, axis=2)
    # Graph
    graph = hg.get_4_adjacency_graph(size)
    if(g.circular):
        sources = np.arange(0, graph.num_vertices(), size[1])
        targets = np.arange(size[1]-1, graph.num_vertices(), size[1])
        graph.add_edges(sources, targets)
    edge_weights = None
    if(g.sobel):
        edge_weights = hg.weight_graph(graph, grad_img, hg.WeightFunction.mean)
    else:
        edge_weights = hg.weight_graph(graph, mds_image, hg.WeightFunction.L2)
    g.tree, g.altitudes = hg.watershed_hierarchy_by_area(graph, edge_weights)

# Load mds data and create image in RGB space
def create_mds_img(g):
    mds_points = np.load(g.mds_point_path)
    image_shape = (g.shape[1], g.shape[0])
    mds_points = u.normalize_point(mds_points)
    mds_image = np.reshape(mds_points, (*image_shape, mds_points.shape[-1]))
    return mds_image

# Determine list of dictionaries for given watershed level
# with segment, hull, color, is_line, refinement_level
# as keys
def get_segment_list(g, watershed_level):
    nodes = get_list_of_nodes(g, watershed_level)
    # fill list
    seg_list = []
    for n in nodes:
        hulls, is_line = calculate_hull(g, n)
        color = g.segments[n].get_color()
        for i in range(len(hulls)):
            seg_list.append({
                "segment": int(n),
                "hull": hulls[i],
                "color": color,
                "is_line": is_line[i],
                "refinement_level": None,
                "min": "%.2f"%g.segments[n].min,
                "max":"%.2f"%g.segments[n].max
                })
    return seg_list

# Refine segments with new waterhshed level
def refine_segment(g, segments, watershed_level):
    nodes = get_refined_nodes(g, segments, watershed_level)
    # fill list
    seg_list = []
    for n in nodes:
        hulls, is_line = calculate_hull(g, n)
        for i in range(len(hulls)):
            seg_list.append({
                "segment": int(n),
                "hull": hulls[i],
                "color": g.segments[n].get_color(),
                "is_line": is_line[i],
                "refinement_level": watershed_level,
                "min": "%.2f"%g.segments[n].min,
                "max":"%.2f"%g.segments[n].max
            })
    return seg_list

# Return the boundary of segment n
def calculate_hull(g, n):
    return g.segments[n].hulls, g.segments[n].is_lines

# List of nodes in level
def get_list_of_nodes(g, watershed_level):
    cut_helper = hg.HorizontalCutExplorer(g.tree, g.altitudes)
    cut = cut_helper.horizontal_cut_from_altitude(watershed_level)
    nodes = cut.nodes()
    return nodes

# Ordered correlation matrix for the given watershed level and thresholds
# The matrix is calculated for the given segments or otherwise for all
# segments on the given watershed level
def get_correlation_matrix(g, segments, watershed_level, threshold):
    if(segments == None):
        print("Test")
        nodes = get_list_of_nodes(g, watershed_level)
    else:
        nodes = list(map(int, segments.split(',')))
        print(len(nodes))
        print(len(np.unique(nodes)))
        nodes = list(set(map(int, segments.split(','))))
    if(len(nodes) == 1):
        return [[1]], nodes, nodes
    corr, time_lags = get_correlation_matrix_from_nodes(g, nodes, threshold)
    print("Corr Matrix dims:")
    print(corr.shape)
    matrix, time_lags, row, column = sort_correlation_matrix(g, corr, time_lags, nodes)
    return matrix, time_lags, row, column

# Sort the given correlation matrix as well as the timelags and
# nodes array by using a hierarchical clustering
# Assume symmetric matrix here
def sort_correlation_matrix(g, corr, time_lags, nodes):
    #corr, time_lags, nodes = remove_empty_rows(corr, time_lags, nodes)
    Y = sch.linkage(corr, method=g.linkage_method)
    Z1 = sch.dendrogram(Y)
    idx1 = Z1['leaves']
    corr = corr[idx1,:]
    corr = corr[:,idx1]
    time_lags = time_lags[idx1, :]
    time_lags = time_lags[:, idx1]
    nodes = np.array(nodes)
    row = nodes[idx1]
    col = nodes[idx1]
    return corr.tolist(), time_lags.tolist(), row.tolist(), col.tolist()

# Removes row without pairwise correlations from matrix
def remove_empty_rows(data, time_lags, nodes):
    np.fill_diagonal(data, 0)
    xAxis=np.sum(np.abs(data), axis=0)==0
    yAxis=np.sum(np.abs(data),axis=1)==0
    remove = ~np.logical_and(xAxis,yAxis)
    data = data[remove]
    data = data[:,remove]
    time_lags = time_lags[remove]
    time_lags = time_lags[:,remove]
    nodes = np.array(nodes)[remove]
    np.fill_diagonal(data, 1)
    return data, time_lags, nodes

# Determines the correlation matrix from a list of nodes
# and a given threshold
def get_correlation_matrix_from_nodes(g, nodes, threshold):
    corr = np.empty((len(nodes), len(nodes)))
    time_lags = np.empty((len(nodes), len(nodes)))
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if(i==j):
                corr[i,j]=1
                time_lags[i,j] = 0
            else:
                if(str(threshold) in g.segments[nodes[i]].correlations and nodes[j] in g.segments[nodes[i]].correlations[str(threshold)]):
                    corr[i,j]=g.segments[nodes[i]].correlations[str(threshold)][nodes[j]][0]
                    time_lags[i,j]=g.segments[nodes[i]].correlations[str(threshold)][nodes[j]][1]+g.timelag_range[0]
                else:
                    corr[i,j]=-2
                    time_lags[i,j] = 0
    return corr, time_lags

# Creates a dictionary that maps each segment to a color
def get_color_dict(g, row):
    dict = {}
    for s in row:
        dict[s] = g.segments[s].get_color()
    return dict

# Return a list of nodes for a local refinement
# The function expects the segments to be refined
# and the watershed level to which the nodes should be refined
def get_refined_nodes(g, segments, watershed_level):
    # Definition from Higra-Documentation:
    #Two leaves are in the same region (ie. have the same label) if the altitude of their lowest common ancestor is strictly greater than the specified threshold.
    nodes = []
    for s in segments:
        if(g.altitudes[s]<=watershed_level):
            print("No refinement")
            nodes = nodes + [s]
        else:
            nodes = nodes + get_children_below_level(g, s, watershed_level)
    return nodes

# Returns the children of the given segment on the chosen watershed level
def get_children_below_level(g, segment, watershed_level):
    if(g.segments[segment].is_leaf):
        return [segment]
    nodes = []
    for c in g.segments[segment].children:
        if(g.altitudes[c]<=watershed_level):
            nodes.append(c)
        else:
            nodes = nodes + get_children_below_level(g, c, watershed_level)
    return nodes

# Calculate the dictioniary with the data for the in detail view
def get_curves_for_segment(g, s):
    median, lower, upper = get_functional_boxplot_variant(g, s)
    color = g.segments[s].get_color()
    # TODO: Adapt and remove unnecessary stuff
    return {
        "segment": s,
        "median": median,
        "lower_bound": lower,
        "lower_quartile": lower,
        "upper_quartile": upper,
        "upper_bound": upper,
        "outliers": None,
        "color": color,
        "width": (np.array(upper) - np.array(lower)).tolist()[:100]
    }

# Determines median curve and the curves that encapsulate the
# whole data
def get_functional_boxplot_variant(g, s):
    series = np.array(g.segments[s].means)
    fig, depth, ix_depth, ix_outliers = sm.graphics.fboxplot(series)
    median = series[ix_depth[0]].tolist()
    lower = np.array(series).min(axis=0).tolist()
    upper = np.array(series).max(axis=0).tolist()
    return median, lower, upper
