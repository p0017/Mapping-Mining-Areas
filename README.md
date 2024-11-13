# Mapping Mining Areas in the Tropics

This repository provides instructions for creating a panel dataset of tropical mining areas using state-of-the-art semantic segmentation techniques, as employed in our study.

<p float="center">
  <img src="resources/toka_mine.PNG" width="250" />
  <img src="resources/toka_mine_prob.PNG" width="250" /> 
  <img src="resources/toka_mine_pred.PNG" width="250" />
</p>

**Toka Tindung** mine, one of the largest gold mines in Southeast Asia (Indonesia).
- **Left**: Ground truth of the mining area in 2019.
- **Center**: Model output showing the probability of mining presence.
- **Right**: Predicted mining area for 2020.

---

## Abstract
Mining provides crucial materials for the global economy and the climate transition, but has potentially severe adverse environmental and social impacts. Currently, the analysis of such impacts is obstructed by the poor availability of data on mining activity — particularly in regions most affected. 

In this paper, we present a novel panel dataset of mining areas in the tropical belt from 2016 to 2024. We use a transformer-based segmentation model, trained on an extensive dataset of mining polygons from the literature, to automatically delineate mining areas in satellite imagery over time. 

The resulting dataset features improved accuracy and reduced noise from human errors, and can readily be extended to cover new locations and points in time as they become available. Our comprehensive dataset of mining areas can be used to assess local environmental, social, and economic impacts of mining activity in regions where conventional data is not available or incomplete. 

---

## Getting Started
### 1. Clone the Repository
   ```bash
   git clone -b main https://github.com/p0017/Mapping-Mining-Areas.git
   cd Mapping-Mining-Areas
   ```

### 2. Install Required Packages
Set up a *conda* environment.
   ```bash
   conda env create -f environment.yml
   conda activate mapping
   ```

### 3. Download the Ground Truth Data
The ground truth dataset combines mining polygons from [*Maus et al.*](https://www.nature.com/articles/s41597-022-01547-4) and [*Tang and Werner*](https://www.nature.com/articles/s43247-023-00805-6). 

   ```bash
   cd data
   wget https://owncloud.wu.ac.at/index.php/s/QHr5K9w3HN97bJm/download/mining_polygons_combined.gpkg
   cd ..
   ```

**Note:** You may also use any other `.gpkg` polygon dataset partially covered by *Planet NICFI*. If you plan on also using it for model training, make sure the dataset is large enough.

### 4. Set Up API Access
Add your own [*Planet NICFI*](https://www.planet.com/nicfi/) `API_KEY` to `segmentation_dataset_generation.py` and verify all file paths. If you are using a different `.gpkg` polygon dataset, ensure the file path is updated.

### 5. Generate Segmentation Datasets
Generate image datasets for training and prediction by running the following command for each year. The 2019 dataset will be used for training, with segmentation masks created exclusively for this year, while prediction datasets are generated for all years.

Choose between:
- **Regular Mode**: Processes the complete ground truth `.gpkg` dataset. This can take one to two days.
- **Demo Mode**: Processes a smaller demo dataset that is 1/80th of the full dataset, completing much faster. Demo mode is useful for testing and debugging.

#### Command for Regular Mode
To run in regular mode with the complete dataset, use:
   ```bash
   for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
     python3 segmentation_dataset_generation.py --year=$year &
   done
   ```

#### Command for Demo Mode
To run in demo mode with the smaller demo dataset, use the `--demo` flag:
   ```bash
   for year in '2016' '2019' '2024'; do
     python3 segmentation_dataset_generation.py --year=$year --demo &
   done
   ```

**Note:** For quick testing, you may also choose to run a subset of sample years, as done here, but should include 2019 since it is required for training.

### 6. Install *MMSegmentation*
Follow the installation guide for [*MMSegmentation*](https://mmsegmentation.readthedocs.io/en/main/get_started.html).

### 7. Configure *MMSegmentation*
Add the 2019 mining dataset you generated to the *MMSegmentation* training datasets as per these [instructions](https://mmsegmentation.readthedocs.io/en/main/advanced_guides/add_datasets.html).

### 8. Install *NVIDIA CUDA*
An *NVIDIA* GPU with *CUDA* support is essential for efficient processing and model training. Training ideally requires two or more high-performance *NVIDIA* GPUs, though a single GPU is sufficient for predictions. To install *CUDA*, follow the instructions [here](https://docs.NVIDIA.com/cuda/cuda-installation-guide-linux/).

**Note:** If only an outdated GPU is available, it may still be possible to achieve results by using a smaller segmentation model, though predictions may be worse.

### 9. Train the Model
Train your selected model on the 2019 mining dataset using *MMSegmentation* by following these [instructions](https://mmsegmentation.readthedocs.io/en/main/user_guides/4_train_test.html). Training ideally requires two or more high-performance *NVIDIA* GPUs, and even with two GPUs, may take one to two days depending on the model complexity and dataset size. 

**Note:** If only a single, outdated *NVIDIA* GPU is available, opt for a smaller model with fewer parameters, though predictions may be worse.

**Note:** When using only the demo dataset for training, expect significantly worse predictions, as the demo dataset is too small for effective model training.

### 10. Generate Predicted Polygon Datasets
Add the path to your trained model checkpoint in `gpkg_dataset_generation.py` and confirm all file paths. Only a single high-performance *NVIDIA* GPU is required for prediction.

Choose between:
- **Regular Mode**: Predicts on the complete ground truth `.gpkg` dataset. This can take one to two days, depending on the chosen model and dataset size.
- **Demo Mode**:  Predicts on a smaller demo dataset that is 1/80th of the full dataset, completing much faster. Demo mode is useful for testing and debugging.

#### Command for Regular Mode
To run in regular mode with the complete dataset, use:
   ```bash
   for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
     python3 gpkg_dataset_generation.py --year=$year &
   done
   ```

#### Command for Demo Mode
To run in demo mode with the smaller demo dataset, use the `--demo` flag:
   ```bash
   for year in '2016' '2019' '2024'; do
     python3 gpkg_dataset_generation.py --year=$year --demo &
   done
   ```

### 11. Postprocess the Predictions
Run the postprocessing script to refine predictions. This step is CPU-executed and may only take a few minutes.
  ```bash
    python3 gpkg_dataset_postprocessing.py
  ```

### 12. Access Your Predictions
Replace `YOUR_YEAR` with the desired year, and navigate to the directory containing your postprocessed predictions.
  ```bash
    cd segmentation/data/segmentation/YOUR_YEAR/gpkg/
   ```

---

## Acknowledgements
The authors gratefully acknowledge financial support from the Austrian National Bank (OeNB Anniversary Fund, project No. 18799).

---

## Author
This repository was developed by [Philipp Sepin](https://github.com/p0017). For any inquiries, please contact: [philipp.sepin@wu.ac.at](mailto:philipp.sepin@wu.ac.at).
