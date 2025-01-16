# Mapping Mining Areas in the Tropics

This repository provides instructions for creating a panel dataset of tropical mining areas using state-of-the-art semantic segmentation techniques, following our [study](https://www.kuschnig.eu/files/wp_mapping-mines_wip.pdf):

<details>
  <summary>
    Sepin, P., Vashold, L., and Kuschnig N. (2025): Mapping Mining Areas in the Tropics from 2016–2024. R&R at Nature Sustainability.
  </summary>
  Mining provides crucial materials for the global economy and the climate transition, but has potentially severe adverse environmental and social impacts. Currently, the analysis of such impacts is obstructed by the poor availability of data on mining activity — particularly in regions most affected. 
  In this paper, we present a novel panel dataset of mining areas in the tropical belt from 2016 to 2024. We use a transformer-based segmentation model, trained on an extensive dataset of mining polygons from the literature, to automatically delineate mining areas in satellite imagery over time. 
  The resulting dataset features improved accuracy and reduced noise from human errors, and can readily be extended to cover new locations and points in time as they become available. Our comprehensive dataset of mining areas can be used to assess local environmental, social, and economic impacts of mining activity in regions where conventional data is not available or incomplete. 
</details>

<p float="center">
  <img src="resources/toka_mine.PNG" width="250" />
  <img src="resources/toka_mine_prob.PNG" width="250" /> 
  <img src="resources/toka_mine_pred.PNG" width="250" />
</p>

**Toka Tindung** mine, one of the largest gold mines in Southeast Asia (Indonesia).
- **Left**: Ground truth of the mining area in 2019.
- **Center**: Model output showing the probability of mining presence.
- **Right**: Predicted mining area for 2020.


## Getting Started
### 1. Clone the repository
   ```bash
   git clone -b main https://github.com/p0017/Mapping-Mining-Areas.git
   cd Mapping-Mining-Areas
   ```

### 2. Install required packages
Set up a *conda* environment. This can take a minute.
   ```bash
   conda env create -f environment.yml
   conda activate mining
   ```
You will also need to install [MMSegmentation](https://mmsegmentation.readthedocs.io/en/main/get_started.html) and [CUDA](https://docs.NVIDIA.com/cuda/cuda-installation-guide-linux/) (see Steps 5 and 6).

### 3. Set up data access

- Add your own [*Planet/NICFI*](https://www.planet.com/nicfi/) **API key** to the `.env` file under `API_KEY`.
- Our **ground truth** dataset combines mining polygons from [*Maus et al.*](https://www.nature.com/articles/s41597-022-01547-4) and [*Tang and Werner*](https://www.nature.com/articles/s43247-023-00805-6) and is available [here](https://owncloud.wu.ac.at/index.php/s/QHr5K9w3HN97bJm/download/mining_polygons_combined.gpkg) or via:
   ```bash
   cd data/segmentation/
   wget https://owncloud.wu.ac.at/index.php/s/QHr5K9w3HN97bJm/download/mining_polygons_combined.gpkg
   cd ../../
   ```

*Note:* You may also use other `.gpkg` datasets, provided they are covered by Planet/NICFI. Ensure the file path is updated, and that the dataset is large enough to use for training.

### 4. Generate segmentation datasets
Generate image data for training and prediction by running the following command for each year.
The 2019 data will be used for training, with segmentation masks created exclusively for this year. Images are  generated for all years to enable prediction.
The images and segmentation masks can be found at `/data/segmentation/YOUR_YEAR/img_dir/` and `/data/segmentation/2019/ann_dir/` respectively.
There are two modes:

- **Regular Mode**: Processes the *complete dataset* (this can take one to two days):
   ```bash
   for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
     python3 0_segmentation_dataset_generation.py --year=$year &
   done
   ```
- **Demo Mode**: Processes a smaller *demo dataset*. Demo mode is useful for testing and debugging:
   ```bash
   for year in '2016' '2019' '2024'; do
     python3 0_segmentation_dataset_generation.py --year=$year --demo &
   done
   ```

*Note:* You may choose to run on a subset of sample years, but should always include 2019, which is required for training.
*Note:* The composite satellite images are selected based on their clarity, as stored in `data/segmentation/cloudfree_quads_info.csv`. Scripts to obtain this metadata are located in `scripts`.

### 5. Set up *MMSegmentation*
- Follow the installation guide for [*MMSegmentation*](https://mmsegmentation.readthedocs.io/en/main/get_started.html).
- Add the 2019 mining dataset you generated to the *MMSegmentation* training datasets as per these [instructions](https://mmsegmentation.readthedocs.io/en/main/advanced_guides/add_datasets.html).

### 6. Install *NVIDIA CUDA*
Processing and training relies on an *NVIDIA* GPU with *CUDA* support. Training benefits from two or more high-performance GPUs (such as the NVIDIA A30); a single GPU is sufficient for prediction.
To install *CUDA*, follow these [instructions](https://docs.NVIDIA.com/cuda/cuda-installation-guide-linux/).

*Note:* It may still be possible to achieve results on less performant GPUs when smaller segmentation models are used.

### 7. Train the model
Train your selected model on the 2019 mining dataset using *MMSegmentation* by following these [instructions](https://mmsegmentation.readthedocs.io/en/main/user_guides/4_train_test.html). Training may take a few days, depending on the model complexity and the size of the dataset. 

*Note:* The demo dataset is too small for effective model training.

### 8. Generate predicted polygons
- Add your model config and checkpoints to the `.env` file under `MODEL_CONFIG` and `MODEL_CHECKPOINT`.
- To generate a `.gpkg` dataset with predicted polygons for each year, run the following script in one of the modes:
  - **Regular Mode**: Predict on the full `.gpkg` dataset. This can take one to two days.
   ```bash
   for year in '2016' '2017' '2018' '2019' '2020' '2021' '2022' '2023' '2024'; do
     python3 1_gpkg_dataset_generation.py --year=$year &
   done
   ```
  - **Demo Mode**:  Predict on a demo dataset.
   ```bash
   for year in '2016' '2019' '2024'; do
     python3 1_gpkg_dataset_generation.py --year=$year --demo &
   done
   ```

### 9. Postprocess the Predictions
Run the post-processing script to refine predictions. This step is executed by the CPU and should only take a few minutes.
  ```bash
    python3 2_gpkg_dataset_postprocessing.py
  ```

Now you can access your post-processed predictions in `data/segmentation/data/segmentation/YOUR_YEAR/gpkg/`.

---

## Acknowledgements
The authors gratefully acknowledge financial support from the Austrian National Bank (OeNB anniversary fund, project No. 18799) and the City of Vienna (Hochschuljubiläumsfonds, project No. H-457973/2023).

## Contact
For any inquiries, please contact: [philipp.sepin@wu.ac.at](mailto:philipp.sepin@wu.ac.at).
