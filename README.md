# Mapping Mining Areas in the Tropics

## Abstract
Mining provides crucial materials for the global economy and the climate transition, but has potentially severe adverse environmental and social impacts. Currently, the analysis of such impacts is obstructed by the poor availability of data on mining activity --- particularly in regions most affected.

In this paper, we present a novel panel dataset of mining areas in the tropical belt from 2016 to 2024. We use a transformer-based segmentation model, trained on an extensive dataset of mining polygons from the literature, to automatically delineate mining areas in satellite imagery over time.

The resulting dataset features improved accuracy and reduced noise from human errors, and can readily be extended to cover new locations and points in time as they become available.
Our comprehensive dataset of mining areas can be used to assess local environmental, social, and economic impacts of mining activity in regions where conventional data is not available or incomplete.

## Getting started
1. Clone the repository.
   ```
   git clone -b main https://github.com/p0017/Mapping-Mining-Areas.git
   cd Mapping-Mining-Areas
   ```
2. Install the required Python packages.
   ```
   pip install -r requirements.txt
   ```
4. Add your own API_KEY to segmentation_dataset_generation.py and check all paths.
5. Execute segmentation_dataset_generation.py for all years to create the datasets for training the model and prediction.
   ```
   for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
     python3 segmentation_dataset_generation.py -year=$year &
   done
   ```
7. Download and install [MMSegmentation](https://mmsegmentation.readthedocs.io/en/main/get_started.html).
8. Train your own segmentation model on the 2019 dataset which you just generated using MMSegmentation according to the [instructions](https://mmsegmentation.readthedocs.io/en/main/user_guides/index.html).
9. Add the path of your trained model to gpkg_dataset_generation.py and check all other paths.
10. Execute gpkg_dataset_generation.py for all years to get the gpkg datasets containing the predictions.
    ```
    for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
     python3 gpkg_dataset_generation.py -year=$year -model='YOUR_MODEL' -iter='ITERATION_OF_YOUR_MODEL' &
    done
    ```
11. Redeem your predictions.
    ```
    cd segmentation/data/segmentation/YOUR_YEAR/gpkg/
    ```
