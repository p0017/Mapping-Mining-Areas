
# Dependencies
source("scripts/0_functions.R")

# Load the ids
ids <- readRDS("data/segmentation/ids_full.rds")

# Get all scene IDs
id_scenes <- unlist(ids) |> unique() # Each appears about 8 times
# We can request metadata for 250 scenes at a time
id_chunks <- id_scenes |> split(ceiling(seq_along(id_scenes) / 250))

meta_df <- lapply(id_chunks, \(chunk) {
  tryCatch(get_metadata(chunk, geometry = TRUE, retry = FALSE), 
    error = \(e) {
      warning("Issue processing chunk:\n", e$message, "\nReattempting ...")
      tryCatch({ # On error, we split further and enable retry
        chunk |> split(ceiling(seq_along(chunk) / 32)) |>
          lapply(\(smaller_chunk) 
            get_metadata(smaller_chunk, geometry = TRUE, retry = TRUE)) |>
          dplyr::bind_rows()
        }, error = \(e) { # If there's another error, the results will be NA
          warning("Error processing chunk:\n", e$message, "\nReturning empty dataframe.")
          return(data.frame(id_scene = chunk)) # The rest will be NA
        }
      )
    }
  )
}) |> dplyr::bind_rows()

meta_df <- data.frame(id_scene = id_scenes) |> 
  dplyr::left_join(meta_df, by = "id_scene")

saveRDS(meta_df, "data/segmentation/metaframe_full.rds")
