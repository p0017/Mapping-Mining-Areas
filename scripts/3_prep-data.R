
# Dependencies
source("scripts/0_functions.R")

# Load the ids and metadata
ids <- readRDS("data/segmentation/ids_full.rds")

meta_df <- readRDS("data/segmentation/metaframe_full.rds")

# Create a long dataframe of basemaps and quads
df <- do.call(rbind, lapply(names(ids), \(id_shape) {
  do.call(rbind, lapply(names(ids[[id_shape]]), \(years) {
    do.call(rbind, lapply(names(ids[[id_shape]][[years]]), \(basemaps) {
      do.call(rbind, lapply(names(ids[[id_shape]][[years]][[basemaps]]), \(quads) {
        data.frame(
          id_shape = id_shape,
          year = years,
          basemap = basemaps,
          quad = quads,
          scenes = ids[[id_shape]][[years]][[basemaps]][[quads]]
        )
      }))
    }))
  }))
}))

# Add the scene metadata
df_meta <- left_join(df, meta_df, by = c("scenes" = "id_scene"))
saveRDS("data/segmentation/metadata.rds")

# Compute summary statistics
df_sm <- df_meta |> group_by(id_shape, year, basemap, quad) |>
  dplyr::summarise( # Summary statistics per basemap
      badness_avg = mean(cloud_percent + heavy_haze_percent, na.rm = TRUE),
      cloud_avg = mean(cloud_cover, na.rm = TRUE),
      cloud_cover_avg = mean(cloud_percent, na.rm = TRUE),
      heavy_haze_avg = mean(heavy_haze_percent, na.rm = TRUE),
      light_haze_avg = mean(light_haze_percent, na.rm = TRUE),
      anomaly_avg = mean(anomalous_pixels, na.rm = TRUE),
      clear_avg = mean(clear_percent, na.rm = TRUE),
      clear_conf_avg = mean(clear_confidence_percent, na.rm = TRUE),
      shadow_avg = mean(shadow_percent, na.rm = TRUE),
      visible_avg = mean(visible_percent, na.rm = TRUE),
      visible_conf_avg = mean(visible_confidence_percent, na.rm = TRUE),
    )
saveRDS("data/segmentation/metadata_summary.rds")

# Select the best basemap per quad per year
df_sel <- df_sm |> group_by(id_shape, year, quad) |>
    dplyr::arrange(dplyr::desc(dplyr::row_number())) |> # Keep the last month on a tie
    dplyr::slice_min(badness_avg, n = 1, with_ties = FALSE) # Best basemap

# Prepare a CSV with the download link
df_sel |>
  select(id_shape, year, basemap, quad) |> 
  mutate(link = get_link(basemap, quad)) |> 
  write.csv("data/segmentation/to_download.csv", row.names = FALSE)
