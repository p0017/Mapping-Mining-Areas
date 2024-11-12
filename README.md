# Mapping Mining Areas in the Tropics

This repository provides instructions for creating a panel dataset of tropical mining areas, using state-of-the-art semantic segmentation techniques as employed in our study.

<p float="center">
  <img src="resources/toka_mine.PNG" width="250" />
  <img src="resources/toka_mine_prob.PNG" width="250" /> 
  <img src="resources/toka_mine_pred.PNG" width="250" />
</p>

*Toka Tindung* mine, one of the largest gold mines in Southeast Asia (Indonesia).
- *Left*: Ground truth of the mining area in 2019.
- *Center*: Model output showing the probability of mining presence.
- *Right*: Predicted mining area for 2020.

---

## Abstract
Mining provides crucial materials for the global economy and the climate transition, but has potentially severe adverse environmental and social impacts. Currently, the analysis of such impacts is obstructed by the poor availability of data on mining activity — particularly in regions most affected.

In this paper, we present a novel panel dataset of mining areas in the tropical belt from 2016 to 2024. We use a transformer-based segmentation model, trained on an extensive dataset of mining polygons from the literature, to automatically delineate mining areas in satellite imagery over time.

The resulting dataset features improved accuracy and reduced noise from human errors, and can readily be extended to cover new locations and points in time as they become available.
Our comprehensive dataset of mining areas can be used to assess local environmental, social, and economic impacts of mining activity in regions where conventional data is not available or incomplete.

---

## Getting started
### 1. Clone the repository.
   ```bash
   git clone -b main https://github.com/p0017/Mapping-Mining-Areas.git
   cd Mapping-Mining-Areas
   ```

### 2. Install the required packages.
Do so by setting up a *conda* environment.
   ```bash
   conda env create -f environment.yml
   conda activate mapping
   ```

### 3. Download the Ground Truth Data
The ground truth is the union of mining polygons by [*Maus et al.*](https://www.nature.com/articles/s41597-022-01547-4) and [*Tang and Werner*](https://www.nature.com/articles/s43247-023-00805-6). You can also use any other `.gpkg` polygon dataset if it is at least partially covered by Planet NICFI.
   ```bash
   cd data
   wget https://owncloud.wu.ac.at/index.php/s/QHr5K9w3HN97bJm/download/mining_polygons_combined.gpkg
   cd ..
   ```

### 4. Set up API Access
Add your own [*Planet NICFI*](https://www.planet.com/nicfi/) `API_KEY` to `segmentation_dataset_generation.py` and verify all file paths. If you are using a different `.gpkg` polygon dataset, make sure to update the path.

### 5. Generate Segmentation Datasets
Run the following command for each year to create image datasets for training and prediction. Only the 2019 dataset will be used for training, so segmentation masks are generated exclusively for this year, while prediction datasets are created for all years. This process runs on the CPU and may take one to two days to complete with the full `.gpkg` polygon dataset used in our study. Smaller `.gpkg` polygon datasets will process more quickly.
   ```bash
   for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
     python3 segmentation_dataset_generation.py -year=$year &
   done
   ```
   
### 6. Install *MMSegmentation*
Follow the installation guide for [*MMSegmentation*](https://mmsegmentation.readthedocs.io/en/main/get_started.html).
   
### 7. Configure *MMSegmentation*
Add the 2019 mining dataset you just generated to the *MMSegmentation* training datasets as per these [instructions](https://mmsegmentation.readthedocs.io/en/main/advanced_guides/add_datasets.html).

### 8. Install *NVIDIA* *CUDA*
For efficient processing and model training in this project, an *NVIDIA* GPU with *CUDA* support is essential, since it is impractical to run this poject on CPUs alone. Training the model ideally requires two or more high-performance *NVIDIA* GPUs, while a single GPU suffices for prediction. If only a single, outdated *NVIDIA* GPU is available, it may still be possible to get results by using a smaller segmentation model with fewer parameters, though these results will likely be significantly less accurate. To install *CUDA*, follow these [instructions](https://docs.NVIDIA.com/cuda/cuda-installation-guide-linux/).

### 9. Train the Model
Train a selected model on the 2019 mining dataset using *MMSegmentation* by following these [instructions](https://mmsegmentation.readthedocs.io/en/main/user_guides/4_train_test.html). This training ideally requires two or more high-performance *NVIDIA* GPUs, and even with two GPUs, it may take one to two days depending on the chosen model, its number of parameters, and the size of the `.gpkg` polygon dataset you used for generating the training and prediction datasets. If only a single, outdated *NVIDIA* GPU is available, choose a smaller segmentation model with fewer parameters, though this will likely affect model accuracy.
    
### 10. Generate predcited Polygon Datasets
Add your trained model's path to `gpkg_dataset_generation.py` and confirm all file paths. If using a different `.gpkg` polygon dataset, update the path as needed. Only a single high-performance *NVIDIA* GPU is required for prediction, though predicting for all years may take one to two days depending on the chosen model, and the size of the `.gpkg` polygon dataset you used for generating the training and prediction datasets.
   ```bash
    for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
    python3 gpkg_dataset_generation.py -year=$year &
    done
   ```
    
### 11. Postprocess the Predictions
Run the postprocessing script to refine predictions. This is executed on the CPU and may only take a few minutes.
  ```bash
    python3 gpkg_dataset_postprocessing.py
  ```
  
### 12. Redeem your Predictions.
Replace `YOUR_YEAR` with the requested year, and navigate to the directory containing your postprocessed predictions.
  ```bash
    cd segmentation/data/segmentation/YOUR_YEAR/gpkg/
   ```
