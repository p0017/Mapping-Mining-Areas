import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio.merge
import shapely
import shapely.geometry
import shapely.ops
import random
import os
import skimage
import cv2
import requests
import urllib.request
from argparse import ArgumentParser
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import get_bbox, global_to_local_coords, check_if_inside_bbox, replace_at_bbox_borders

'''
This script generates image datasets for training and inference of segmentation models.
It reads two polygon datasets, requests satellite imagery of the corresponding locations from Planet,
and fills directories containing the satellite images and segmentation masks,
each split into 0.8/0.1/0.1 train/test/val splits.
The following directory structure is required (an example):

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
gdf['tile_ids'] = [np.array([], dtype=object, ndmin=1) for i in gdf.index] # id of tiles on which the polygon is located
gdf['tile_urls'] = [np.array([], dtype=object, ndmin=1) for i in gdf.index] # url of tiles on which the polygon is located
gdf['tile_bboxes'] = None #bboxes of tiles on which the polygon is located
gdf['x_poly'] = None #x coordinates of polygon inside tile coordinate system
gdf['y_poly'] = None #y coordinates of polygon inside tile coordinate system
gdf['x_bbox'] = None #x coordinates of polygon bbox inside tile coordinate system
gdf['y_bbox'] = None #y coordinates of polygon bbox inside tile coordinate system

gdf.reset_index(drop=True, inplace=True)


iso_non_nicfi = ['USA', 'CHN', 'RUS', 'CAN', 'AUS', 'SAU', 'MRT', 'DZA', 'LBA', 'EGY', 'OMN', 'YEM', 'NCL', 'MAR', 'ESH', 'LBY', 'TUN', 'JOR', 'ISR', 'PSE', 'SYR', 'LBN', 'IRQ', 'KWT', 'IRN', 'AFG', 'PAK', 'URY', 'TWN', 'KOR', 'PRK', 'JPN', 'ARE', 'QAT', 'PRI']
nicfi_bbox = gpd.GeoDataFrame(index=[0], crs=4326, geometry=[shapely.Polygon([(-180, 30), (180, 30), (180, -30), (-180, -30), (-180, 30)])])

in_nicfi = gdf.intersects(nicfi_bbox.geometry[0])
gdf = gdf[in_nicfi]

nicfi_subset = [False if iso in iso_non_nicfi else True for iso in gdf['ISO3_CODE']]
gdf = gdf[nicfi_subset]

gdf.reset_index(drop=True, inplace=True)

PLANET_API_KEY = 'YOUR_API_KEY_HERE'
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


# Planet does not cover a great amount of polygons
no_tiles_found = [False if tile_id.size == 0 else True for tile_id in gdf['tile_ids']]
print('no tiles found for {} out of {} polygons'.format(str(no_tiles_found.count(False)), str(len(gdf))))
gdf = gdf[no_tiles_found]
gdf.reset_index(drop=True, inplace=True)


# calculating each polygons position on their own tile/mosaic, we will need those later one by one
for i in range(len(gdf)):
    gdf['x_poly'][i], gdf['y_poly'][i] = global_to_local_coords(gdf['geometry'][i], gdf['tile_bboxes'][i])
    gdf['x_bbox'][i], gdf['y_bbox'][i] = global_to_local_coords(gdf['bbox'][i], gdf['tile_bboxes'][i], is_bbox=True)


def process_cloudfree(j:int, gdf:gpd.geodataframe.GeoDataFrame, cloudfree_quads_this_year:pd.DataFrame):
    """
    Processes cloudfree tiles by updating the tile URLs in the GeoDataFrame based on the availability of cloudfree quads.
    Parameters
    -------------
    j : int
        The index of the tile in the GeoDataFrame.
    gdf : geopandas.geodataframe.GeoDataFrame
        A GeoDataFrame containing tile information, including tile IDs and URLs.
    Example
    -------------
    process_cloudfree(0, gdf)
    """
    # Extract tile IDs and URLs for the given index
    tile_ids = gdf['tile_ids'][j]
    tile_urls = gdf['tile_urls'][j]

    # Reshape if the arrays are 0-dimensional
    if tile_ids.ndim == 0:
        tile_ids = tile_ids.reshape(1)

    if tile_urls.ndim == 0:
        tile_urls = tile_urls.reshape(1)
    
    # Iterate over each tile ID
    for i in range(len(tile_ids)):
        tile_id = tile_ids[i]
        # Check if the tile ID is in the cloudfree quads for the current year
        if tile_id in cloudfree_quads_this_year['quad'].to_list():
            # Get the cloudfree quad URL and append the API key
            cloudfree_quad_url = cloudfree_quads_this_year[cloudfree_quads_this_year['quad'] == tile_id]['link'].iloc[0]
            tile_urls[i] = cloudfree_quad_url + PLANET_API_KEY
        else:
            # Print a message if no cloudfree tile is found
            print('No cloudfree tile found for', tile_id, 'therefore leaving it as is')

    # Update the tile URLs in the GeoDataFrame
    gdf['tile_urls'][j] = tile_urls


def parallel_process_cloudfree(gdf:gpd.geodataframe.GeoDataFrame, cloudfree_quads_this_year:pd.DataFrame):
    """
    Processes cloudfree tiles in parallel by delegating each tile's processing to worker threads.

    Parameters
    -------------

    gdf: A GeoDataFrame.
    type: geopandas.geodataframe.GeoDataFrame
    values: A valid GeoDataFrame.
    default: No default value.

    cloudfree_quads_this_year: A DataFrame.
    type: pandas.core.frame.DataFrame
    values: A valid DataFrame containing cloudfree quad information for the current year.
    default: No default value.

    Example
    -------------

    parallel_process_cloudfree(gdf, cloudfree_quads_this_year)
    """

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(process_cloudfree, j, gdf, cloudfree_quads_this_year)
            for j in range(len(gdf))
        ]

        for future in as_completed(futures):
            future.result()


print('checking for cloudfree tiles')
# reading a dataframe which contains information on cloudfree quads/tiles for the ground truth dataset used in our study
cloudfree_quads = pd.read_csv('./data/segmentation/cloudfree_quads_info.csv', sep=',')
cloudfree_quads_this_year = cloudfree_quads[cloudfree_quads['year'] == int(year)]
parallel_process_cloudfree(gdf, cloudfree_quads_this_year)


def prepare_and_save(k:int, gdf:gpd.geodataframe.GeoDataFrame, set_type:str):
    """
    Processes a single polygon in the GeoDataFrame, downloads corresponding tiles,
    calculates polygon positions, creates mosaics, and saves the results as images
    and segmentation masks.

    Parameters
    -------------

    k: The index of the polygon in the GeoDataFrame.
    type: int
    values: Positive integers corresponding to the row index in the GeoDataFrame.
    default: No default value.

    gdf: A GeoDataFrame.
    type: geopandas.geodataframe.GeoDataFrame
    values: A valid GeoDataFrame.
    default: No default value.

    set_type: The set type which is being processed, only needed for specifying in the right directory.
    type: str
    values: 'train', 'test', or 'val'.
    default: No default value.

    Example
    -------------

    prepare_and_save(0, gdf, 'train', '2019')
    """

    try:
        gdf['tile_urls'] = gdf['tile_urls'].apply(lambda x: np.array(x, ndmin=1))
        gdf['tile_ids'] = gdf['tile_ids'].apply(lambda x: np.array(x, ndmin=1))

        # downloading all required tiles
        for url, id in zip(gdf['tile_urls'][k], gdf['tile_ids'][k]):
            filename = './data/tiff_tiles/{}/{}.tiff'.format(year, id)
            # checks if file already exists
            if not os.path.isfile(filename):
                urllib.request.urlretrieve(url, filename)

        # getting all secondary polygons which are located on one of the tiles the primary polygon is located on
        # and subsetting the dataset accordingly
        on_same_tile = [any(id in id_list for id in gdf['tile_ids'][k]) for id_list in gdf['tile_ids']]
        gdf_on_same_tile = gdf[on_same_tile]
        gdf_on_same_tile.reset_index(drop=True, inplace=True)



        # tile/mosaic bbox of the primary polygon
        tile_bboxes = gdf['tile_bboxes'][k]

        # calculating the position of all secondary polygons on the tile/mosaic, so we can calculate which are located inside the primary polygons bbox
        for i in range(len(gdf_on_same_tile)):
            x_poly_in_tile, y_poly_in_tile = global_to_local_coords(gdf_on_same_tile['geometry'][i], tile_bboxes)
            gdf_on_same_tile['x_poly'][i] = x_poly_in_tile
            gdf_on_same_tile['y_poly'][i] = y_poly_in_tile

            x_bbox, y_bbox = global_to_local_coords(gdf_on_same_tile['bbox'][i], tile_bboxes, is_bbox=True)
            gdf_on_same_tile['x_bbox'][i] = x_bbox
            gdf_on_same_tile['y_bbox'][i] = y_bbox

        # bbox of the primary polygon and its offset on the tile/mosaic
        x_bbox = gdf['x_bbox'][k]
        y_bbox = gdf['y_bbox'][k]
        x_offset = int(x_bbox[2])
        y_offset = int(y_bbox[0])
        bbox_size = int(x_bbox[1] - x_bbox[3])



        # checking which of the polygons on the tile/mosaic are actually located inside the primary polygons bbox
        # since some polygons are located closely to each other, it can occur that secondary polygons are partly located inside the bbox of the primary polygon
        in_same_bbox = []
        for i in range(len(gdf_on_same_tile)):
            x_poly = gdf_on_same_tile['x_poly'][i].copy()
            y_poly = gdf_on_same_tile['y_poly'][i].copy()
            poly_positions = check_if_inside_bbox(x_poly, y_poly, x_offset, y_offset, bbox_size)

            #we will only count secondary polygons which have more than two points inside the primary polygons bbox
            if poly_positions.count(True) > 2:
                in_same_bbox.append(True)
            else:
                in_same_bbox.append(False)

        # and again subsetting the dataset accordingly
        gdf_in_same_bbox = gdf_on_same_tile[in_same_bbox]
        gdf_in_same_bbox.reset_index(drop=True, inplace=True)



        # merging all required tiles into a mosaic
        tile_mosaic = []
        for id in gdf['tile_ids'][k]:
            img = rasterio.open('./data/tiff_tiles/{}/{}.tiff'.format(year, id))
            tile_mosaic.append(img)

        # we have got four color channels, red, green, blue, and NIR
        mosaic, _ = rasterio.merge.merge(tile_mosaic, indexes=[1,2,3,4])
        # array needs to be cut according to the primary polygons bbox
        rgb = mosaic[:, y_offset:y_offset+bbox_size, x_offset:x_offset+bbox_size]

        # channels need to be scaled down to 512x512 if needed, using bicubic interpolation
        rgb_resized = []
        for channel in rgb:
            channel_resized = cv2.resize(channel, dsize=(512,512), interpolation=cv2.INTER_CUBIC)
            rgb_resized.append(channel_resized)

        rgb_resized = np.array(rgb_resized).T
        if not cv2.imwrite('./data/segmentation/{}/img_dir/{}/{}.png'.format(year, set_type, gdf['id'][k]), 255*rgb_resized):
            print("Failed to save image of polygon", k)

        if year == '2019':
            # turning the polygons into a target array of zeros and ones
            bbox_size = int(gdf['x_bbox'][k][1] - gdf['x_bbox'][k][3])
            target = np.zeros((bbox_size, bbox_size), 'uint8')

            for i in range(len(gdf_in_same_bbox)):
                x_poly = gdf_in_same_bbox['x_poly'][i].copy()
                y_poly = gdf_in_same_bbox['y_poly'][i].copy()
                poly_positions = check_if_inside_bbox(x_poly, y_poly, x_offset, y_offset, bbox_size)

                if poly_positions.count(True) > 2:
                    x_poly -= x_offset
                    y_poly -= y_offset
                    x_poly, y_poly = replace_at_bbox_borders(x_poly, y_poly, bbox_size, poly_positions)

                    rr, cc = skimage.draw.polygon(y_poly, x_poly, target.shape)
                    target[rr,cc] = 1

            # also downscaling the polygon target arrays to 512x512, using bicubic interpolation
            target_resized = cv2.resize(target, dsize=(512,512), interpolation=cv2.INTER_CUBIC)
            target_resized = np.array(target_resized).T
            if not cv2.imwrite('./data/segmentation/{}/ann_dir/{}/{}.png'.format(year, set_type, gdf['id'][k]), target_resized):
                print("Failed to save segmentation mask of polygon", k)

    except OSError as e:
        print('Caught OSError', e, 'on polygon', k)
        pass

    except FloatingPointError as e:
        print('Caught normalization error caused by empty color channel on polygon', k)
        print(e)
        pass

    except cv2.error:
        print('Caught error caused by empty color channel on polygon', k)
        pass

    except Exception as e:
        print('Caught', e, 'on polygon', k)
        pass


def parallel_prepare_and_save(gdf: gpd.geodataframe.GeoDataFrame, set_type: str):
    """
    Iterates over all mining polygons in gdf, reads their corresponding .tiff tiles, calculates their positions on these tiles,
    and produces .png images and segmentation masks of size 512x512 for training and prediction, using parallel processing.

    Parameters
    -------------

    gdf: A GeoDataFrame.
    type: geopandas.geodataframe.GeoDataFrame
    values: Any.
    default: No default value.

    set_type: The set type which is being processed, only needed for specifying in the right directory.
    type: str
    values: 'train', 'test', or 'val'.
    default: No default value.

    Example
    -------------

    parallel_prepare_and_save(gdf_train, set_type='train')
    parallel_prepare_and_save(gdf_test, set_type='test')
    parallel_prepare_and_save(gdf_val, set_type='val')
    """

    print('Processing', set_type)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(prepare_and_save, k, gdf, set_type, year)
            for k in range(len(gdf))
        ]

        for future in as_completed(futures):
            future.result()  # Handle exceptions from threads if needed


np.random.seed(2023)
# These ids were hand validated
# These polygons are validated to be well delineated mining areas for 2019
HAND_VALIDATED_IDS = [1867, 2720, 3660, 3743, 3757, 3849, 3853, 4288, 4323, 4704, 4838, 4853, 
                        5139, 5162, 6808, 6809, 9227, 9945, 10256, 10258, 10338, 10514, 10753, 10844, 
                        11109, 11139, 11507, 11726, 12540, 13004, 13144, 13540, 14844, 15550, 15619, 
                        15872, 16087, 16242, 16516, 16656, 17616, 17764, 17766, 17895, 18058, 18126, 
                        18196, 18210, 18314, 18315, 18321, 18323, 18381, 18412, 18427, 18452, 18502, 
                        18520, 18529, 18545, 18558, 18586, 18596, 18603, 18605, 18624, 18636, 18691, 
                        18747, 18787, 18844, 18977, 18994, 19134, 19227, 19284, 19315, 19401, 19534, 
                        19716, 20578, 21048, 21194, 21217, 21234, 21532, 21938, 22017, 22215, 22386, 
                        23466, 23502, 23970, 24052, 24788, 26464, 26598, 26788, 26808, 27189, 27244, 
                        27249, 27250, 27573, 27588, 27672, 27698, 27823, 28043, 28235, 28245, 28299, 
                        28368, 28418, 28422, 28426, 28642, 28680, 28721, 28742, 29305, 29336, 29463, 
                        29538, 29766, 29978, 29994, 30216, 30268, 30276, 30643, 30931, 31638, 36191, 
                        36601, 37344, 37367, 37397, 37455, 37458, 37534, 37541, 37568, 37646, 37771, 
                        37786, 37813, 38412, 38459, 38510, 38555, 38579, 41338, 41855, 42268, 42783, 
                        43194, 43217, 43255, 43996, 44044, 44047, 44071, 44531, 44532, 44572, 45042, 
                        45878, 46161, 59191, 60251, 60501, 60522, 60528, 60573, 61268, 61330, 61758, 
                        62302, 62345, 63034, 63036, 64468, 64490, 64511, 64666, 65496, 66038, 67045, 
                        72444, 72479, 72733, 72779, 73184, 73470, 73528, 75192, 75926, 76524, 79590]

# Filter out the indices that are not in HAND_VALIDATED_IDS for training and validation
non_hand_validated_indices = [i for i in range(len(gdf)) if (gdf['id'].iloc[i] not in HAND_VALIDATED_IDS)]

# 0.89 train 0.1 val split, and a hand validated 0.01 test set of 200 samples
val_indices = []
while len(val_indices) < np.round(len(gdf) * 0.1):
    r = np.random.choice(non_hand_validated_indices)
    if r not in val_indices:
        val_indices.append(r)

train_indices = [i for i in non_hand_validated_indices if (i not in val_indices) ]

gdf_train = gdf.iloc[train_indices].copy()
gdf_train.reset_index(drop=True, inplace=True)

gdf_val = gdf.iloc[val_indices].copy()
gdf_val.reset_index(drop=True, inplace=True)

has_hand_validated_indices = len(non_hand_validated_indices) < len(gdf)
if has_hand_validated_indices:
    gdf_test = gdf[gdf['id'].isin(HAND_VALIDATED_IDS)]
    gdf_test.reset_index(drop=True, inplace=True)

print('train', len(gdf_train), 'test', len(gdf_test), 'val', len(gdf_val))
print('preparing and saving data')
parallel_prepare_and_save(gdf_train, set_type='train')
parallel_prepare_and_save(gdf_val, set_type='val')

if has_hand_validated_indices:
    parallel_prepare_and_save(gdf_test, set_type='test')


if demo:
    print(year, 'demo done.')
    
else:
    print(year, 'done')
