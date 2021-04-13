# Regional Time Series Correlation
*Regional Time Series Correlations* can be used to detect and analyze regions in ensemble data that are highly correlated and also exhibit a correlation to other regions. The approach follows a two-step visual analysis approach. In the first step, a so-called similarity image is created by mapping the spatial samples to a 3D embedding and interpreting the embedded coordinates as colors. In the second step, a hierarchical segmentation is computed, and the application can be used to analyze the correlations among the single segments while also taking into account time lags and uncertainty caused by the ensemble.

More information can be found in the paper *Uncertainty-aware Visualization of Regional Time SeriesCorrelation in Spatio-temporal Ensembles* by Marina Evers, Karim Huesmann and Lars Linsen.

## Requirements
The dependencies for the python backend and preprocessing scripts can be installed by:
```
pip install numpy netCDF4 higra alphashape scipy geopandas flask flask-cors nibabel matplotlib
```

For the frontend, the only requirement is node.js (www.nodejs.org, tested on v12.16.1). Then switch to the 'frontend' folder and run:

```bash
# install dependencies
$ npm install
```

We tested this with the following dependencies:
```
    "@nuxtjs/axios": "^5.12.2",
    "@nuxtjs/style-resources": "^1.0.0",
    "bootstrap": "^4.5.3",
    "chart.js": "2.7.3",
    "chartjs-plugin-zoom": "^0.7.7",
    "core-js": "^3.6.5",
    "d3": "^6.2.0",
    "hammerjs": "^2.0.8",
    "node-sass": "^5.0.0",
    "nuxt": "^2.14.6",
    "sass": "^1.32.8",
    "sass-loader": "^10.1.1"
```

For a detailed explanation of how things work, check out [Nuxt.js docs](https://nuxtjs.org).

## How to Run?
### Preprocessing
Switch to the 'backend' folder
1. Create the similarity image
```
python create_correlation_mds.py
```
2. Create the hierarchical segmentation
```
python preprocessing_segmentation.py
```
3. Add segment boundaries
```
python add_hulls.py
```
4. Add minimal and maximal correlation in each segment to evaluate smoothness (optional)
```
python add_minmax.py
```
5. Color the segments according to their mean color
```
python add_color.py
```
### Start the backend
Switch to the 'backend' folder and run
```
python api.py
```
By default, the API web server should run on port 5000. If this is not the case, you may need to change the `BACKEND_URL`-Variable in `frontend/store/vis.js` from `http://127.0.0.1:5000` to your local API address prompted in your Python console. 

### Start the frontend
Switch to the 'frontend' folder and run
```
# serve with hot reload at localhost:3000. Use this command for development.
$ npm run dev

# build for production and launch server
$ npm run build
$ npm run start

# generate static project
$ npm run generate
```

### Run with own data
We included the artificial dataset described in the paper such that the tool can be executed and tested directly. However, it is also easy to apply it to own data.

The ensemble data should be in a folder where each subfolder contains a single ensemble member's data. Inside each folder, there is a single .nc file containing the spatial time series information.

In each of the preprocessing files, there is a set of capitalized variables located at the beginning of the script. Please adapt these paths and configurations to your needs. Additionally, adapt the paths and configurations in the Global-class of the file ``api.py`` to your needs.

## How to Use?
### Segmentation View
Hover: Highlight segment (linked to Correlation Heatmap)
Shift + mouse left click: Select segment (linked to Correlation Heatmap and Statistics View)
Shift + mouse left double click: Open pop up to assign a label to segment
Filter selection button: Opens a new tab with similar views, but only the selected segments are available
Refinement watershed level slider: Refines the selected segments to the chose watershed level

### Correlation Heatmap
Hover: Highlight segment (linked to Similarity Image)
Shift + mouse left click: Select segment (linked to Segmentation View and Statistics View)
Shift + mouse left drag: Select corresponding segments in the region (linked to Segmentation View and Statistics View)
Correlation threshold: If more than one threshold was used in the precalculations, it could be selected here
Linkage method: Choose the linkage method used for reordering the matrix based on hierarchical clustering
Time Lags: Click 'show' to visualize the color-coded time lag in each cell. 
Mouse left click on color legends: Filter according to the correlation certainty or time lag respectively (linked to Correlation Heatmap and Statistics view)

### Statistics View
Mouse wheel: Zoom along the y-axis
Hover over curve: Show value on the respective point

If you have further questions, please do not hesitate to contact us.
