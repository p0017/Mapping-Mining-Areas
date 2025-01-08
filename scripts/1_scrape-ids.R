
# Dependencies
source("scripts/0_functions.R")

# Load the shapefile of mines that we need images for
shape <- sf::st_read("data/segmentation/mining_polygons_combined_bbox.gpkg")
# dplyr::filter(ISO3_CODE == "SUR") # Suriname for tests

# Add an ID to make rows identifiable
shape[["id"]] <- paste0(shape[["ISO3_CODE"]], formatC(seq_len(NROW(shape)), width = 5, flag = 0))


# Pull all relevant IDs ---

ids <- vector("list", NROW(shape))
names(ids) <- shape[["id"]]
# There are slots for (1) basemap, (2) quad, and (3) scene IDs

for(i in seq_len(length(ids))) {
  if(TRUE && i %% 100 == 0) message("At ", i, " out of ", NROW(shape), " IDs.")

  # Check the bounding box for NICFI coverage
  bbox <- shape[i, ] |> st_bbox()
  if(as.numeric(bbox)[2] < -30 | as.numeric(bbox)[4] > 30) next
  
  
  ids[[i]] <- tryCatch(get_ids(bbox), error = \(e) {
    warning("Error retrieving IDs for '", shape[["id"]][[i]], "'.")
    return(NA_real_)
  })
}
saveRDS(ids, "data/segmentation/ids_full.rds")


# Reiterate over NAs and NULLs
for(i in seq_len(length(ids))) {
  if(TRUE && i %% 100 == 0) message("At ", i, " out of ", NROW(shape), " IDs.")
  
  # Skip if there is no NA or NULL
  if(length(ids[[i]]) > 1 || (!is.na(ids[[i]]) && !is.null(ids[[i]]))) next
  
  # Check the bounding box for coverage
  bbox <- shape[i, ] |> st_bbox()
  if(as.numeric(bbox)[2] < -30 | as.numeric(bbox)[4] > 30) next
  
  ids[[i]] <- tryCatch(get_ids(bbox), error = \(e) {
    warning("Error retrieving IDs for '", shape[["id"]][[i]], "'.")
    return(NA_real_)
  })
}
saveRDS(ids, "data/segmentation/ids_full-re.rds")
