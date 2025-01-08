
# This is the (deprecated) alternative to only scraping individual scenes

# Dependencies
source("scripts/0_functions.R")

# Load the shapefile of mines that we need images for
shape <- sf::st_read("data/segmentation/mining_polygons_combined_bbox.gpkg")
# dplyr::filter(ISO3_CODE == "SUR") # Suriname for tests

# Add an ID to make rows identifiable
shape[["id"]] <- paste0(shape[["ISO3_CODE"]], formatC(seq_len(NROW(shape)), width = 5, flag = 0))

# Load the ids
ids <- readRDS("data/segmentation/ids_full.rds")


# Pull all the relevant metadata --- 
meta_dt <- vector("list", NROW(ids))

for(i in seq(1, NROW(meta_dt))) {
  
  if(TRUE && i %% 100 == 0) message("At ", i, " out of ", NROW(ids), " IDs.")
  # Skip empty IDs
  if(length(ids[[i]]) <= 1 && (is.na(ids[[i]]) || is.null(ids[[i]]))) next
  if(length(unlist(ids[[i]])) == 0) next
  
  # Prepare to merge in the information on basemaps and quads
  id_df <- data.frame(
    id_scene = unlist(ids[[i]]),
    id_shape = shape[["id"]][i],
    unlist(ids[[i]]) |> names() |> 
      strsplit("\\.") |> sapply(\(names) names) |> t(),
    row.names = NULL
  ) |> dplyr::rename(year = X1, basemap = X2, id_quad = X3)
  # This is a bit messy, as 'id_quad' duplicates get an iterator in the tail

  # - Scenes can appear in multiple quads
  # - Scenes with "RapidEye" (from 2016) in their name don't return info
  id_lookup <- id_df[["id_scene"]][!grepl("RapidEye", id_df[["id_scene"]])] |> unique()
  # - We can request scene metadata in chunks of 250
  id_chunks <- id_lookup |> split(ceiling(seq_along(id_lookup) / 250))
  
  metadata <- lapply(id_chunks, \(chunk) {
    tryCatch(get_metadata(chunk, geometry = TRUE, retry = FALSE), 
      error = \(e) { # If there's an error, we split into smaller chunks
        warning("Issue processing chunk:\n", e$message, "\nReattempting ...")
        tryCatch({ # On error, we split further and enable retry
          chunk |> split(ceiling(seq_along(chunk) / 32)) |>
            lapply(\(chunk) get_metadata(chunk, geometry = TRUE, retry = TRUE)) |>
            dplyr::bind_rows()
          }, error = \(e) { # If there's another error, the results will be NA
            warning("Error processing chunk:\n", e$message, "\nReturning empty dataframe.")
            return(data.frame(id_scene = chunk)) # The rest will be NA
          }
        )
      }
    )
  }) |> dplyr::bind_rows()
  
  # Add the scene metadata
  metadata <- dplyr::left_join(id_df, metadata, by = "id_scene")
  
  # Some IDs may not work via this API
  if(any(!id_df[["id_scene"]] %in% metadata$id_scene)) {
    skipped <- id_df[["id_scene"]][!id_df[["id_scene"]] %in% metadata$id_scene]
    warning("No information found for ", length(skipped), " scenes:\n\t",
      paste0("'", skipped, "'", collapse = "\n\t"))
  }

  meta_dt[[i]] <- metadata
}
saveRDS(meta_dt, "data/segmentation/metadata_full.rds")


# Check the results ---

# Compare IDs and metadata
id_len <- vapply(ids, length, numeric(1L))
mt_len <- vapply(meta_dt, length, numeric(1L))

# Here, we have IDs, but no metadata
idx <- which(id_len != 0 & mt_len == 0)
# However, these IDs are actually empty
vapply(ids[idx], \(x) unlist(x) |> length(), numeric(1L))
