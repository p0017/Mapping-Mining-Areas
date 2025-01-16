import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
import shapely.geometry
import shapely.ops
import random
import os
import cv2
import requests
import torch
import mmcv
from argparse import ArgumentParser
from mmengine.config import Config
from mmseg.apis import init_model, inference_model
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import get_bbox, count_tiles, global_to_local_coords, isnan, postprocess, close_holes

'''
This script is used for the generation of .gpkg polygon datasets using trained segmentation models and image datasets prepared for inference.
It reads two polygon datasets for the corresponding polygon locations, fetches the corresponding image, gets the model's prediction,
and calculates its position and extent in the global coordinate system.
The image datasets which are needed for inference first need to be generated using segmentation_dataset_generation.py.

For this script, we used the Mask2Former by Cheng, et al.
"Masked-attention mask transformer for universal image segmentation." Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. 2022.
https://openaccess.thecvf.com/content/CVPR2022/html/Cheng_Masked-Attention_Mask_Transformer_for_Universal_Image_Segmentation_CVPR_2022_paper.html

We implemented it using MMSegmentation by OpenMMLab.
https://github.com/open-mmlab/mmsegmentation
Therefore, a trained mmsegmentation model is required.
The following directory structure is required (an example).

/mmsegmentation
/data
    /segmentation
            /mining_polygons_combined.gpkg
            /2016
                    /img_dir
                            /train
                            /test
                            /val
                    /gpkg
            /2017
                    ...
            /2018
                    ...
            /2019
                    /ann_dir
                            /train
                            /test
                            /val
                    /img_dir
                            /train
                            /test
                            /val
                    /gpkg
            /2020
                    ...
            ...

    /tiff_tiles
            /2016
            /2017
            /2018
            ...

Note: The ann_dir is only required for 2019, as the model was trained on this year.
'''


pd.options.mode.chained_assignment = None

parser = ArgumentParser()
parser.add_argument('-y', '--year', required=True, help="Year to process.")
parser.add_argument('-d', '--demo',  action='store_true', help="Set this flag to run the script in demo mode.")

# Eight options for year, from '2016' up to '2024'
# If one wants to include data of more recent years, the corresponding Planet parameter needs to be added to the nicfi_urls dict below

args = parser.parse_args()
year = args.year
demo = args.demo

if demo:
    print("Running in demo mode.")
    gdf = gpd.read_file("./data/segmentation/mining_polygons_combined_demo.gpkg")
    
else:
    print("Running in regular mode.")
    gdf = gpd.read_file("./data/segmentation/mining_polygons_combined.gpkg")

# Reading the union of two datasets
'''
We are using the union since they intersect a lot
Maus, Victor, et al. "An update on global mining land use." Scientific data 9.1 (2022): 1-11.
https://www.nature.com/articles/s41597-022-01547-4.
Tang, Liang, and Tim T. Werner. "Global mining footprint mapped from high-resolution satellite imagery." Communications Earth & Environment 4.1 (2023): 134.
https://www.nature.com/articles/s43247-023-00805-6
'''

countries = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
# Loading a country code dataset
# Will be deprecated sometime in the future

a = gdf['geometry'].apply(lambda x: x.intersects(countries.geometry))
gdf['ISO3_CODE'] = (a * countries['iso_a3']).replace('', np.nan).ffill(axis='columns').iloc[:, -1]
gdf['COUNTRY_NAME'] = (a * countries['name']).replace('', np.nan).ffill(axis='columns').iloc[:, -1]
# Checking in which country the individual polygons are located
gdf['AREA'] = gdf.geometry.area
gdf['id'] = gdf.index

gdf['bbox'] = None # bbox of polygon as shapely polygon object
gdf['tile_ids'] = [np.array([], dtype=object, ndmin=1) for _ in gdf.index] # id of tiles on which the polygon is located
gdf['tile_urls'] = [np.array([], dtype=object, ndmin=1) for _ in gdf.index] # url of tiles on which the polygon is located
gdf['tile_bboxes'] = None # bboxes of tiles on which the polygon is located
gdf['x_poly'] = None # x coordinates of polygon inside tile coordinate system
gdf['y_poly'] = None # y coordinates of polygon inside tile coordinate system
gdf['x_bbox'] = None # x coordinates of polygon bbox inside tile coordinate system
gdf['y_bbox'] = None # y coordinates of polygon bbox inside tile coordinate system

gdf.reset_index(drop=True, inplace=True)


iso_non_nicfi = ['USA', 'CHN', 'RUS', 'CAN', 'AUS', 'SAU', 'MRT', 'DZA', 'LBA', 'EGY', 'OMN', 'YEM', 'NCL', 'MAR', 'ESH', 'LBY', 'TUN', 'JOR', 'ISR', 'PSE', 'SYR', 'LBN', 'IRQ', 'KWT', 'IRN', 'AFG', 'PAK', 'URY', 'TWN', 'KOR', 'PRK', 'JPN', 'ARE', 'QAT', 'PRI']
nicfi_bbox = gpd.GeoDataFrame(index=[0], crs=4326, geometry=[shapely.Polygon([(-180, 30), (180, 30), (180, -30), (-180, -30), (-180, 30)])])

in_nicfi = gdf.intersects(nicfi_bbox.geometry[0])
gdf = gdf[in_nicfi]

nicfi_subset = [False if iso in iso_non_nicfi else True for iso in gdf['ISO3_CODE']]
gdf = gdf[nicfi_subset]

gdf.reset_index(drop=True, inplace=True)

# copying the dataframe for generation of a new dataframe with predicted polygons
gdf_pred = gdf.copy()
gdf_pred['geometry'] = None
gdf_pred['AREA'] = None


# Read the API key from .env
PLANET_API_KEY = os.environ['API_KEY']
# setup Planet base URL
API_URL = "https://api.planet.com/basemaps/v1/mosaics"
# setup session
session = requests.Session()
# authenticate
session.auth = (PLANET_API_KEY, "")

print()
print('processing', year)

# This is the dict in which one needs to add the corresponding Planet parameters if one wants to include more recent data
NICFI_URLS = {'2016':'planet_medres_normalized_analytic_2016-06_2016-11_mosaic',
              '2017':'planet_medres_normalized_analytic_2017-06_2017-11_mosaic',
              '2018':'planet_medres_normalized_analytic_2018-06_2018-11_mosaic',
              '2019':'planet_medres_normalized_analytic_2019-06_2019-11_mosaic',
              '2020':'planet_medres_normalized_analytic_2020-06_2020-08_mosaic',
              '2021':'planet_medres_normalized_analytic_2021-11_mosaic',
              '2022':'planet_medres_normalized_analytic_2022-11_mosaic',
              '2023':'planet_medres_normalized_analytic_2023-11_mosaic',
              '2024':'planet_medres_normalized_analytic_2024-11_mosaic'}

# set params for search using name of primary mosaic
parameters = {"name__is" : NICFI_URLS[year]}
# make get request to access mosaic from basemaps API
res = session.get(API_URL, params = parameters)
mosaic = res.json()

# get id
MOSAIC_ID = mosaic['mosaics'][0]['id']


def process_tile(j:int, gdf:gpd.geodataframe.GeoDataFrame, session:requests.Session):
    """
    Processes a single tile by retrieving its bounding box, searching for mosaic tiles 
    using the area of interest (AOI), and extracting required tile URLs, IDs, and bounding boxes.

    Parameters
    -------------

    j: The index of the tile in the GeoDataFrame.
    type: int
    values: Positive integers corresponding to the row index in the GeoDataFrame.
    default: No default value.

    gdf: A GeoDataFrame.
    type: geopandas.geodataframe.GeoDataFrame
    values: A valid GeoDataFrame.
    default: No default value.

    session: The session object for making API requests.
    type: requests.sessions.Session
    values: A valid `Session` instance from the `requests` library.
    default: No default value.

    Example
    -------------

    process_tile(0, gdf, session)
    """

    try:
        if gdf['tile_urls'][j].size == 0:
            # Getting bboxes of all polygons
            random.seed(int(gdf['id'][j]))
            gdf['bbox'][j] = get_bbox(gdf['geometry'][j])

            # Converting bbox to string for search params
            bbox_for_request = list(gdf['bbox'][j].bounds)
            string_bbox = ','.join(map(str, bbox_for_request))

            # Search for mosaic tile using AOI
            search_parameters = {
                'bbox': string_bbox,
                'minimal': False
            }

            # Accessing tiles using metadata from mosaic
            quads_url = "{}/{}/quads".format(API_URL, MOSAIC_ID)
            res = session.get(quads_url, params=search_parameters, stream=True)
            quads = res.json()
            items = quads['items']

            # Getting all required tile IDs and URLs
            urls = np.array([], dtype=object)
            ids = np.array([], dtype=object)
            bboxes = []

            for item in items:
                if 'download' in item['_links'].keys():
                    urls = np.append(urls, item['_links']['download'])
                    ids = np.append(ids, item['id'])
                bboxes.append(item['bbox'])

            gdf['tile_urls'][j] = urls
            gdf['tile_ids'][j] = ids
            gdf['tile_bboxes'][j] = bboxes

    except json.JSONDecodeError as e:
        print('Requested tile which is not covered by NICFI', e)
        pass


def parallel_process_tile(gdf:gpd.geodataframe.GeoDataFrame, session:requests.Session):
    """
    Processes tiles in parallel by delegating each tile's processing to worker threads.

    Parameters
    -------------

    gdf: A GeoDataFrame.
    type: geopandas.geodataframe.GeoDataFrame
    values: A valid GeoDataFrame.
    default: No default value.

    session: The session object for making API requests.
    type: requests.sessions.Session
    values: A valid `Session` instance from the `requests` library.
    default: No default value.

    Example
    -------------

    parallel_process_tile(gdf, session)
    """

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(process_tile, j, gdf, session)
            for j in range(len(gdf))
        ]

        for future in as_completed(futures):
            future.result()


print('requesting tiles')
parallel_process_tile(gdf, session)


# Planet only covers tropical regions
no_tiles_found = [False if tile_id.size == 0 else True for tile_id in gdf['tile_ids']]
print('no tiles found for {} out of {} polygons'.format(str(no_tiles_found.count(False)), str(len(gdf))))
gdf = gdf[no_tiles_found]
gdf.reset_index(drop=True, inplace=True)
gdf_pred = gdf_pred[no_tiles_found]
gdf_pred.reset_index(drop=True, inplace=True)

gdf['tile_urls'] = gdf['tile_urls'].apply(lambda x: np.array(x, ndmin=1))
gdf['tile_ids'] = gdf['tile_ids'].apply(lambda x: np.array(x, ndmin=1))


# calculating each polygons position on their own tile, we will need those later one by one
for i in range(len(gdf)):
    gdf['x_poly'][i], gdf['y_poly'][i] = global_to_local_coords(gdf.iloc[i]['geometry'], gdf.iloc[i]['tile_bboxes'])
    gdf['x_bbox'][i], gdf['y_bbox'][i] = global_to_local_coords(gdf.iloc[i]['bbox'], gdf.iloc[i]['tile_bboxes'], is_bbox=True)

gdf_pred['tile_ids'] = gdf['tile_ids']
gdf_pred['tile_urls'] = gdf['tile_urls']
gdf_pred['tile_bboxes'] = gdf['tile_bboxes']
gdf_pred['x_bbox'] = gdf['x_bbox']
gdf_pred['y_bbox'] = gdf['y_bbox']

# since we did not use any early stopping technique, we use the training checkpoints with the highest validation scores
# loading the mmsegmentation config of the model and a training checkpoint for inference
# add your model config and checkpoint path here
# cfg = Config.fromfile('./mmsegmentation/configs/YOUR_MODEL_CONFIG.py')
model_config = os.environ['MODEL_CONFIG']
cfg = Config.fromfile(model_config)
model_checkpoint = os.environ['MODEL_CHECKPOINT']
checkpoint = model_checkpoint
cfg.load_from = checkpoint
cfg.work_dir = checkpoint + '/'

print('loading model from {}'.format(checkpoint))

cfg.test_evaluator['output_dir'] = './mmsegmentation/output/'
cfg.test_evaluator['keep_results'] = False
# inititalizing the model and passing it to the gpu
model = init_model(cfg, checkpoint, "cuda:0" if torch.cuda.is_available() else "cpu")



for split in ['train/', 'test/', 'val/']:
    print('processing', split)
    img_names = os.listdir('./data/segmentation/{}/img_dir/{}/'.format(year, split))
    for img_name in img_names:
        # processing all data from all splits

        # loading the image and getting the models predictions
        img = mmcv.imread('./data/segmentation/{}/img_dir/{}/{}'.format(year, split, img_name))
        pred = inference_model(model, img).pred_sem_seg.values()[0][0]
        # predictions need to be passed back to the cpu for further processing
        pred = pred.cpu().detach().numpy()
        pred = postprocess(pred)
        pred = pred.T

        # using findContours for processing the segmentation predictions into polygon coordinates
        borders, _ = cv2.findContours(pred.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        multipoly = []
        for border in borders:
            #skipping polygons with less than 3 edges
            if border.shape[0] >= 3:
                border = np.reshape(border, (border.shape[0], 2))
                multipoly.append(shapely.Polygon(border))

        x_poly = []
        y_poly = []
        # getting the mine id from the image name
        id = int(img_name.split('.')[0])
        current_poly = gdf_pred[gdf_pred['id'] == id]

        # there are some invalid API responses for some polygons, which result in nan values as their bboxes
        if len(current_poly) == 0:
            continue
        else:
            # check requires at least one entry in current_poly
            if (isnan(current_poly.iloc[0]['x_bbox']) | isnan(current_poly.iloc[0]['y_bbox'])):
                continue
            

        # offset of the polygons inside the bounding box
        x_offset = current_poly.iloc[0]['x_bbox'][2]
        y_offset = current_poly.iloc[0]['y_bbox'][0]
        bbox_scaling_factor = (current_poly.iloc[0]['x_bbox'][0] - current_poly.iloc[0]['x_bbox'][2]) / 512

        # calculating the bbox and shape of the tile mosaic
        mosaic_bbox, x_tile_counter, y_tile_counter = count_tiles(current_poly.iloc[0]['tile_bboxes'])

        for poly in multipoly:
            # simplifying the polygons for data reduction
            poly_simple = poly.simplify(1, preserve_topology=False)
            # in some cases, a polygon may be split up into a multiple polygons making up a multipolygon wenn calling simplify
            if type(poly_simple) == shapely.geometry.multipolygon.MultiPolygon:
                for geom in poly_simple.geoms:
                    # skipping tiny polygons
                    if geom.area > 50:
                        # getting the polygon coordinates inside the bbox coordinate system
                        # and adding the bbox offset
                        x,y = geom.exterior.xy
                        x = [(x_i * bbox_scaling_factor) + x_offset for x_i in x]
                        y = [(y_i * bbox_scaling_factor) + y_offset for y_i in y]
                        x_poly.append(x)
                        y_poly.append(y)
            # processing polygons which have not been split up
            else:
                # skipping tiny polygons
                if poly_simple.area > 50:
                    # getting the polygon coordinates inside the bbox coordinate system
                    # and adding the bbox offset
                    x,y = poly_simple.exterior.xy
                    x = [(x_i * bbox_scaling_factor) + x_offset for x_i in x]
                    y = [(y_i * bbox_scaling_factor) + y_offset for y_i in y]
                    x_poly.append(x)
                    y_poly.append(y)

        id_position = np.where((gdf_pred['id'] == id) == True)[0][0]
        gdf_pred.at[id_position, 'x_poly'] = x_poly
        gdf_pred.at[id_position, 'y_poly'] = y_poly

        # factor for scaling from the bbox coordinate system to the global coordinate system
        x_scaling_factor = (mosaic_bbox[0] - mosaic_bbox[2]) / (4096 * x_tile_counter)
        y_scaling_factor = (mosaic_bbox[1] - mosaic_bbox[3]) / (4096 * y_tile_counter)
        # prediction usually returns multiple polygons which will be merged into a multipolygon
        multipoly = []

        # processing the polygon coordinates into actual polygons
        for x,y in zip(x_poly, y_poly):
            x = [mosaic_bbox[0] - (x_i * x_scaling_factor) for x_i in x]
            y = [4096 * y_tile_counter - y_i for y_i in y]
            y = [mosaic_bbox[1] - (y_i * y_scaling_factor) for y_i in y]
            poly = shapely.Polygon(list(zip(x, y)))
            multipoly.append(poly)

        gdf_pred.at[id_position, 'geometry'] = shapely.geometry.MultiPolygon(multipoly)

# invalid Planet API responses can occur
invalid_geom = [False if geometry == None else True for geometry in gdf_pred['geometry']]
print('No geometry found for {} out of {} polygons.'.format(str(invalid_geom.count(False)), str(len(gdf_pred))))
gdf = gdf[invalid_geom]
gdf.reset_index(drop=True, inplace=True)

# we copy the dataframe again for postprocessing
buffer = gdf_pred.copy()
buffer.drop('bbox', axis=1, inplace=True)
buffer.drop('tile_ids', axis=1, inplace=True)
buffer.drop('tile_urls', axis=1, inplace=True)
buffer.drop('tile_bboxes', axis=1, inplace=True)
buffer.drop('x_poly', axis=1, inplace=True)
buffer.drop('y_poly', axis=1, inplace=True)
buffer.drop('x_bbox', axis=1, inplace=True)
buffer.drop('y_bbox', axis=1, inplace=True)
buffer["originalid"] = range(buffer.shape[0])


# since some polygons are located closely to each other, it can occur that secondary polygons are partly located inside the bbox of the primary polygon,
# and therefore also located in the corresponding prediction of the primary polygon
# to solve the multiple occurences of polygons, either as primary or secondary polygon, we just take the union of all predicted polygons
buffer_exp = buffer.explode('geometry', index_parts=True)
buffer_exp['expid'] = range(buffer_exp.shape[0])
buffer_exp['exparea'] = buffer_exp['geometry'].area

cluster = buffer_exp.dissolve().explode("geometry", index_parts=True)
cluster["clusterid"] = range(0, cluster.shape[0])

cluster_to_save = cluster.copy()
cluster_to_save['geometry'] = cluster_to_save['geometry'].apply(lambda p: close_holes(p))
cluster_to_save.drop('originalid', axis=1, inplace=True)
cluster_to_save.drop('expid', axis=1, inplace=True)
cluster_to_save.drop('exparea', axis=1, inplace=True)
cluster_to_save.drop('clusterid', axis=1, inplace=True)

cluster_to_save.to_file("./data/segmentation/{}/gpkg/global_mining_polygons_predicted_{}.gpkg".format(year, year), driver='GPKG')

if demo:
    print(year, 'demo done.')
    
else:
    print(year, 'done.')
