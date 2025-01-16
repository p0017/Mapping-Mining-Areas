import numpy as np
import geopandas as gpd

#This script is used for the postprocessing of .gpkg polygon datasets.
#It removes any polygons that do not have an intersecting polygon in the previous or subsequent year.
#This means that the years 2016 and 2024, which only have a single ‘neighboring’ year, which we can compare the polygons to, feature a lower number of polygons.
#Further, it assigns the correct country name and iso3 code to every polygon.

# Optional buffer for more generous postprocessing
use_buffer = True
# 0.0005 corresponds to roughly 50 meters, increase for even more generous postprocessing
buffer_size = 0.0005 


global_datasets = {}

#Reading the predictions for every year
for year in np.arange(2016, 2025).astype(str):
    path = './data/segmentation/{}/gpkg/global_mining_polygons_predicted_{}.gpkg'.format(year, year)
    global_data = gpd.read_file(path)
    global_data = global_data.to_crs('EPSG:4326')

    for column in ['AREA', 'level_0', 'level_1', 'id', 'COUNTRY_NAME', 'ISO3_CODE']:
        if column in global_data.keys():
            global_data.drop(column, axis=1, inplace=True)
            
    global_data.reset_index(drop=True, inplace=True)
    global_datasets[year] = global_data


global_datasets_postprocessed = {}
for year, dataset in global_datasets.items():
    global_datasets_postprocessed[year] = dataset.copy()


#Removing any polygons that do not have an intersecting polygon in the previous or subsequent year
for i in range(len(global_datasets.keys())):
    year = list(global_datasets.keys())[i]
    previous_year = None
    following_year = None

    if i != 0:
        previous_year = str(int(year) - 1)
        global_datasets_postprocessed[year]['tempid'] = range(global_datasets_postprocessed[year].shape[0])

        if use_buffer:
            # Adding a buffer for more generous postprocessing
            buffered_current_year = global_datasets_postprocessed[year].copy()
            buffered_current_year['geometry'] = buffered_current_year['geometry'].buffer(buffer_size)
            matches_previous_year = gpd.sjoin(
                left_df=buffered_current_year,
                right_df=global_datasets[previous_year],
                how="inner"
            ).tempid

        else:
            matches_previous_year = gpd.sjoin(
                left_df=global_datasets_postprocessed[year],
                right_df=global_datasets[previous_year],
                how="inner"
            ).tempid


    if i != len(global_datasets.keys())-1:
        following_year = str(int(year) + 1)
        global_datasets_postprocessed[year]['tempid'] = range(global_datasets_postprocessed[year].shape[0])

        if use_buffer:
            # Adding a buffer for more generous postprocessing
            buffered_current_year = global_datasets_postprocessed[year].copy()
            buffered_current_year['geometry'] = buffered_current_year['geometry'].buffer(buffer_size)
            matches_following_year = gpd.sjoin(
                left_df=buffered_current_year,
                right_df=global_datasets[following_year],
                how="inner"
            ).tempid

        else:
            matches_following_year = gpd.sjoin(
                left_df=global_datasets_postprocessed[year],
                right_df=global_datasets[following_year],
                how="inner"
            ).tempid

    if (previous_year is not None) and (following_year is not None):
        subset = [any(tup) for tup in zip(global_datasets_postprocessed[year].tempid.isin(matches_previous_year), global_datasets_postprocessed[year].tempid.isin(matches_following_year))]
        global_datasets_postprocessed[year] = global_datasets_postprocessed[year].loc[subset].drop(columns="tempid")

    elif (previous_year is not None):
        global_datasets_postprocessed[year] = global_datasets_postprocessed[year].loc[global_datasets_postprocessed[year].tempid.isin(matches_previous_year)].drop(columns="tempid")

    else:
        global_datasets_postprocessed[year] = global_datasets_postprocessed[year].loc[global_datasets_postprocessed[year].tempid.isin(matches_following_year)].drop(columns="tempid")

    global_datasets_postprocessed[year].reset_index(drop=True, inplace=True) 


#Reading a country dataset provided by NaturalEarth
#https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip
countries = gpd.read_file('./data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
countries = countries.to_crs('EPSG:4326')


#Assigning the correct country names and iso3 codes by comparing the polygons to the NaturalEarth dataset
for year in global_datasets_postprocessed.keys():
    global_data = global_datasets_postprocessed[year]

    a = global_data['geometry'].apply(lambda x: x.intersects(countries.geometry))
    global_data['iso_a3'] = (a * countries['ISO_A3']).replace('', np.nan).ffill(axis='columns').iloc[:, -1]
    global_data['country_name'] = (a * countries['NAME']).replace('', np.nan).ffill(axis='columns').iloc[:, -1]

    copy_for_area = global_data.copy().to_crs('+proj=igh +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs +type=crs')
    global_data['area'] = copy_for_area.geometry.area
    global_data['id'] = global_data.index
    global_data.geometry = global_data.geometry.make_valid()
    global_data['year'] = [year] * len(global_data)
    global_data = global_data[['id', 'iso_a3', 'country_name', 'year', 'area', 'geometry']]

    global_datasets_postprocessed[year] = global_data
    print(year, 'done')


#Dealing with missing values
for year in global_datasets_postprocessed.keys():
    iso_codes = global_datasets_postprocessed[year]['iso_a3']
    global_datasets_postprocessed[year]['iso_a3'] = [i if i != '-99' else 'nan' for i in iso_codes]


#Saving the postprocessed .gpkg datasets
for year, dataset in global_datasets_postprocessed.items():
    if use_buffer:
        dataset.to_file('./data/segmentation/{}/gpkg/global_mining_polygons_predicted_{}_postprocessed.gpkg'.format(year, year), driver='GPKG')

    else:
        dataset.to_file('./data/segmentation/{}/gpkg/global_mining_polygons_predicted_{}_postprocessed_nobuffer.gpkg'.format(year, year), driver='GPKG')