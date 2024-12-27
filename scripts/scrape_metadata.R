
# Preliminaries ---
library("httr")
library("sf") # for geometries
library("dplyr") # for bind_rows

API_KEY <- Sys.getenv("API_KEY")
API_URL <- "https://api.planet.com/basemaps/v1/mosaics"
BASEMAPS_ID <- list(
  "2016" = c("planet_medres_normalized_analytic_2016-06_2016-11_mosaic" = "d514a774-2bb8-45c5-b552-1577b6711fca"),
  "2017" = c("planet_medres_normalized_analytic_2017-06_2017-11_mosaic" = "86a3070d-c49b-4d66-b232-f6cf8112c0c7"),
  "2018" = c("planet_medres_normalized_analytic_2018-06_2018-11_mosaic" = "41ceab16-f41e-47fd-9438-cac8ffef6a82"),
  "2019" = c("planet_medres_normalized_analytic_2019-06_2019-11_mosaic" = "be47e0f2-c91b-41b5-865e-eb4d212b59e6"),
  "2020" = c("planet_medres_normalized_analytic_2020-06_2020-08_mosaic" = "b1a5e592-a608-4e61-b588-015bf6331eca"),
  "2021" = c(
    "planet_medres_normalized_analytic_2021-06_mosaic" = "733473f6-b85c-4d31-b10e-d73ea3186310",
    "planet_medres_normalized_analytic_2021-07_mosaic" = "a22d3de4-f597-47ee-849e-5408f8cbbce5",
    "planet_medres_normalized_analytic_2021-08_mosaic" = "ce7bad0f-a4a0-45fd-904b-eb6cc6eee373",
    "planet_medres_normalized_analytic_2021-09_mosaic" = "168b5f2e-e0ad-474b-bfe6-c0d4c17df905",
    "planet_medres_normalized_analytic_2021-10_mosaic" = "4a18d02d-2a17-4548-b705-9834ed866478",
    "planet_medres_normalized_analytic_2021-11_mosaic" = "d7e95d46-64a9-4553-b1ea-574e21b49562"
  ),
  "2022" = c(
    "planet_medres_normalized_analytic_2022-06_mosaic" = "540b304e-ecfb-449d-a13b-3f16ee6923d6",
    "planet_medres_normalized_analytic_2022-07_mosaic" = "a39f3482-f960-4800-95fc-bd2542fafa66",
    "planet_medres_normalized_analytic_2022-08_mosaic" = "9eff8b55-451b-4d08-9a80-a47c8ac1cb93",
    "planet_medres_normalized_analytic_2022-09_mosaic" = "cb934fb3-63aa-4a6c-849f-84f599030ea9",
    "planet_medres_normalized_analytic_2022-10_mosaic" = "9aef7f2c-9ed1-42d5-81cd-721b04eef49e",
    "planet_medres_normalized_analytic_2022-11_mosaic" = "0bdd9cae-2eb0-4fb3-8042-3478e18e7ba4"
  ),
  "2023" = c(
    "planet_medres_normalized_analytic_2023-06_mosaic" = "c7d9af9d-56e5-445a-b9e2-42570826594e",
    "planet_medres_normalized_analytic_2023-07_mosaic" = "20ceddc3-0601-4da8-aa2d-0894ad5a8740",
    "planet_medres_normalized_analytic_2023-08_mosaic" = "4433f903-97f6-4529-9002-2428d75a0baa",
    "planet_medres_normalized_analytic_2023-09_mosaic" = "8801ebff-38ad-4615-982f-994949be5eb8",
    "planet_medres_normalized_analytic_2023-10_mosaic" = "0c96274e-ca4a-4541-9ee5-94ec35e5dda8",
    "planet_medres_normalized_analytic_2023-11_mosaic" = "318bcbe2-cd4b-46f8-aaa9-79505004ac3c"
  ),
  "2024" = c(
    "planet_medres_normalized_analytic_2024-06_mosaic" = "8b6ce4f5-9987-4b0d-afcd-39000eb395b8",
    "planet_medres_normalized_analytic_2024-07_mosaic" = "62fec4a1-7ef7-45a3-b903-e92e0967260f",
    "planet_medres_normalized_analytic_2024-08_mosaic" = "c4d4bb96-42d7-4275-8781-7745c90a7867",
    "planet_medres_normalized_analytic_2024-09_mosaic" = "02e1d63d-21d6-4355-beed-504c8e3595db",
    "planet_medres_normalized_analytic_2024-10_mosaic" = "ac5b033c-fefb-4fb2-9165-a6f81ecab722",
    "planet_medres_normalized_analytic_2024-11_mosaic" = "34ead9f8-c7af-4daf-a266-e514251eeea7"
  )
)
# Otherwise – request using the names and store the IDs
# BASEMAPS <- list( # Names of the basemaps – composites until 2020, monthly afterwards
#   '2016' = 'planet_medres_normalized_analytic_2016-06_2016-11_mosaic',
#   '2017' = 'planet_medres_normalized_analytic_2017-06_2017-11_mosaic', 
#   '2018' = 'planet_medres_normalized_analytic_2018-06_2018-11_mosaic',
#   '2019' = 'planet_medres_normalized_analytic_2019-06_2019-11_mosaic',
#   '2020' = 'planet_medres_normalized_analytic_2020-06_2020-08_mosaic',
#   '2021' = paste0('planet_medres_normalized_analytic_2021-', formatC(6:11, width = 2, flag = "0"), '_mosaic'),
#   '2022' = paste0('planet_medres_normalized_analytic_2022-', formatC(6:11, width = 2, flag = "0"), '_mosaic'),
#   '2023' = paste0('planet_medres_normalized_analytic_2023-', formatC(6:11, width = 2, flag = "0"), '_mosaic'),
#   '2024' = paste0('planet_medres_normalized_analytic_2024-', formatC(6:11, width = 2, flag = "0"), '_mosaic')
# )
# This should be the equivalent of BASEMAPS with IDs instead of names
# BASEMAPS_ID <- lapply(BASEMAPS, \(elements) { # Per year
#   vapply(elements, \(name) { # Per basemap
#     response <- httr::GET(API_URL, query = list("name__is" = name), httr::authenticate(API_KEY, ""))
#     content <- httr::content(response)
#     out <- content[["mosaics"]][[1]][["id"]]
#     if(!grepl("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", out)) {
#       warning("ID '", out, "' for '", name, "' does not match the expected pattern.")
#     }
#     out
#   }, character(1L))
# })

#' Get quad and scene IDs for a bbox and selected years
#'
#' @param bbox Bounding box of a polygon, as returned by `sf::st_bbox`
#' @param years Years between 2016 and 2024 to retrieve
#'
#' @return
#'
#' @examples
#' ids <- get_ids(c(-54.4631, 4.3838, -54.461, 4.3853), years = 2024)
get_ids <- function(bbox, years = 2016:2024) {
  
  bbox <- paste(as.numeric(bbox), collapse = ", ")
  search_query <- list(bbox = bbox, minimal = TRUE)

  years <- as.character(years)
  
  # Get the quad ID and scene IDs
  ids <- lapply(BASEMAPS_ID[years], \(elements) { # per year
    lapply(elements, \(id) { # per basemap
      id_quads <- request_quad(search_query, id)
      id_scenes <- lapply(id_quads[["ids"]], \(id_quad) {
        request_scenes(search_query, id, id_quad)
      })
      names(id_scenes) <- id_quads[["ids"]]
      attr(id_scenes, "links") <- id_quads[["links"]]
      id_scenes
    })
  })
  names(ids) <- years # Year > Basemap > Quad > Scenes
  ids
}

# Request quad IDs and downloads links, called by `get_ids()`
request_quad <- function(query, id_basemap, check_id = FALSE) {
  
  # Request the quad ID for the bbox and basemap
  response <- paste(API_URL, id_basemap, "quads", sep = "/") |> 
    httr::GET(query = query, httr::authenticate(API_KEY, ""))
  
  # Check the status code
  status <- httr::status_code(response)
  if(status < 100 || status > 300) {
    stop("Received status code ", status, " when requesting quads for bbox '", 
      query[["bbox"]], "' and basemap '",  id_basemap, "'.")
  }
  content <- httr::content(response)
  
  quad_ids <- vapply(content[["items"]], \(item) item[["id"]], character(1L))
  if(isTRUE(check_id) && !all(grepl("[0-9a-f]{3}-[0-9a-f]{4,6}", quad_ids))) {
    warning("Quad ID '", quad_ids[!grepl("[0-9a-f]{3}-[0-9a-f]{4,6}", quad_ids)], 
      "' at bbox '", query[["bbox"]], "' and basemap '", 
      id_basemap, "' does not match the expected pattern.")
  }
  quad_dl <- vapply(content[["items"]], \(item) {
    gsub("(.*api_key=).*", "\\1", item[["_links"]][["download"]])
  }, character(1L))
  
  list("ids" = quad_ids, "links" = quad_dl)
}

# Request scene IDs, called by `get_ids()`
request_scenes <- function(query, id_basemap, id_quad, check_id = FALSE) {
  
  # Request scenes in the quad for the bbox and basemap
  response <- paste(API_URL, id_basemap, "quads", id_quad, "items", sep = "/") |> 
    httr::GET(query = query, httr::authenticate(API_KEY, ""))
  
  # Check the status code
  status <- httr::status_code(response)
  if(status < 100 || status > 300) {
    stop("Received status code ", status, " when requesting scenes for quad '",
      id_quad, "', bbox '", query[["bbox"]], "', and basemap '",  id_basemap, "'.")
  }
  
  content <- httr::content(response)
  # Pull the scene IDs
  vapply(content[["items"]], \(item) { # We need values from 'response > items > link'
    out <- gsub(".*\\/items\\/([^#]*)#.*", "\\1", item[["link"]])
    if(isTRUE(check_id) && !grepl("[0-9]{8}_[0-9]{2,6}.[0-9]{0,6}_[0-9a-f]{4}$", out)) {
      message("Scene ID '", out, "' for the quad '", id_quad, "' at bbox '", query[["bbox"]], 
        "' and basemap '", id_basemap, "' does not match the expected pattern.")
    }
    out
  }, character(1L))
}

#' Get metadata and polygons for scenes
#'
#' @param id_scene Vector of scene ID(s).
#' @param geometry Whether to also return the geometry of the scene(s).
#' @param retry Whether to retry if there is no usable response.
#'
#' @return
#'
#' @examples
#' get_metadata(c("20241120_133254_39_24d0", "20241127_133235_53_24bf"), FALSE)
get_metadata <- function(id_scene, geometry = TRUE, retry = TRUE) {
  
  if(length(id_scene) > 250) {stop("Only up to 250 scenes are returned at a time.")}
  
  # Arcane query
  payload <- list(filter = list(type = "AndFilter", config = list(list(type = "AndFilter", 
    config = list(
      list(type = "StringInFilter", field_name = "id", config = as.list(unname(id_scene))),
      list(type = "StringInFilter", field_name = "item_type", config = list("PSScene"))
    )
  ))), item_types = list("PSScene"))
  
  response <- httr::POST(
    url = "https://api.planet.com/data/v1/quick-search",
    body = payload, encode = "json", httr::authenticate(API_KEY, ""), httr::content_type_json()
  )
  status <- httr::status_code(response)
  if(status < 100 || status > 300) {
    stop("Received status code ", status, " when requesting scene '", id_scene, "'.")
  }
  content <- httr::content(response)
  
  # Pull the metadata and geometry into one table
  lst <- lapply(content[["features"]], function(feature) {
    out <- feature[["properties"]] |> as.data.frame()
    out[["id_scene"]] <- gsub(".*/(.*)$", "\\1", feature[["_links"]][["_self"]])
    if(isTRUE(geometry)) { # Geometry of the scene
      coords <- vapply(feature[["geometry"]][["coordinates"]][[1]], \(x) unlist(x), numeric(2L)) |> t()
      out <- st_set_geometry(out, list(coords) |> sf::st_polygon() |> st_sfc(crs = 4326))
    }
    out
  })
  
  tbl <- dplyr::bind_rows(lst) # More robust (not all columns are always present)
  
  # Check which IDs are in the table
  is_missing <- !id_scene %in% tbl[["id_scene"]]
  if(isTRUE(retry) && any(is_missing)) { # Retry if IDs are missing
    extra_rows <- id_scene[is_missing] |> # Split the ID vector into half
      split(seq_along(id_scene[is_missing]) <= ceiling(length(id_scene[is_missing]) / 2)) |> 
      lapply(\(ids) { # Stop recursion at a basecase (less than 8 elements / 5 recursions)
      get_metadata(ids, geometry = geometry, retry = length(ids) >= 8)
    }) |> dplyr::bind_rows()
    tbl <- bind_rows(tbl, extra_rows)
  }
  tbl
}


# Script -----

# Load the shapefile that we use
shape <- st_read("data/segmentation/global_mining_polygons_v2.gpkg") |> 
  dplyr::filter(ISO3_CODE == "SUR") # Suriname for tests

# Add an ID to make rows identifiable
shape[["id"]] <- paste0(shape[["ISO3_CODE"]], formatC(seq_len(NROW(shape)), width = 5, flag = 0))
# Slot for the basemap, quad, and scene IDs
ids <- vector("list", NROW(shape))

# Pull all relevant IDs ---
for(i in seq_len(NROW(shape))) {
  ids[[i]] <- tryCatch({shape[i, ] |> st_bbox() |> get_ids()}, error = \(e) {
    warning("Error retrieving IDs for '", shape[["id"]][[i]], "'.")
    return(NA_real_)
  })
}
saveRDS(ids, "data/segmentation/global_mining_polygons_v2_ids.rds")


# Obtain metadata using the IDs ---

meta_dt <- meta_sm <- vector("list", NROW(shape))

for(i in seq_len(NROW(shape))) {
  
  # Merge in the information on basemaps
  id_df <- data.frame(
    id_scene = unlist(ids[[i]]),
    unlist(ids[[i]]) |> names() |> 
      strsplit("\\.") |> sapply(\(names) names) |> t(),
    row.names = NULL
  ) |> dplyr::rename(year = X1, basemap = X2, id_quad = X3)

  # We can request up to 250 at a time
  # - Scene IDs can appear in multiple quads)
  # - Ones with "RapidEye" (from 2016) in their name don't seem to work
  id_lookup <- id_df[["id_scene"]][!grepl("RapidEye", id_df[["id_scene"]])] |> unique()
  id_chunks <- id_lookup |> split(ceiling(seq_along(id_lookup) / 250))
  
  # We request the metadata in chunks of 250
  # - If there's an error in a chunk, IDs are split into chunks of 32
  metadata <- lapply(id_chunks, \(chunk) {
    tryCatch(get_metadata(chunk, geometry = FALSE, retry = FALSE), 
      error = \(e) {
        warning("Issue processing chunk:\n", e$message, "\nReattempting ...")
        Sys.sleep(.5) # Wait (half) a sec
        tryCatch({# On error, split further and retry (with retry enabled)
          chunk |> split(ceiling(seq_along(chunk) / 32)) |>
            lapply(\(chunk) get_metadata(chunk, geometry = FALSE, retry = TRUE)) |>
            dplyr::bind_rows()
          }, error = \(e) {
            warning("Error processing chunk – returning empty dataframe.")
            return(data.frame(id_scene = chunk)) # The rest will be NA
          }
        )
      }
    )
  }) |> dplyr::bind_rows()
  
  metadata <- dplyr::left_join(id_df, metadata, by = "id_scene")
  
  # Some IDs do not seem to work via this API ---
  if(any(!id_df[["id_scene"]] %in% metadata$id_scene)) {
    skipped <- id_df[["id_scene"]][!id_df[["id_scene"]] %in% metadata$id_scene]
    warning("No information found for ", length(skipped), " scenes:\n\t",
      paste0("'", skipped, "'", collapse = "\n\t"))
  }

  meta_dt[[i]] <- metadata
}

saveRDS(meta_dt, "data/segmentation/global_mining_polygons_v2_metadata.rds")


# We need to:
#   1) Compute summary statistics per basemap
#   2) Choose the optimal basemap (month) where appropriate
for(i in seq_len(length(meta_dt))) {
  meta_sm[[i]] <- meta_dt[[i]] |>
    dplyr::group_by(year, basemap) |>
    dplyr::summarise( # Summary statistics
      id = shape[["id"]][i], # Explicit, to help match to the shape
      cloud_avg = mean(cloud_cover, na.rm = TRUE),
      heavy_haze_avg = mean(heavy_haze_percent, na.rm = TRUE),
      light_haze_avg = mean(light_haze_percent, na.rm = TRUE),
      anomaly_avg = mean(anomalous_pixels, na.rm = TRUE),
      clear_avg = mean(clear_percent, na.rm = TRUE),
      clear_conf_avg = mean(clear_confidence_percent, na.rm = TRUE),
      shadow_avg = mean(shadow_percent, na.rm = TRUE),
      visible_avg = mean(visible_percent, na.rm = TRUE),
      visible_conf_avg = mean(visible_confidence_percent, na.rm = TRUE)
    ) |> dplyr::group_by(year) |> 
    dplyr::slice_min(cloud_avg, n = 1) # We only keep the best basemap per year
}

# It's easier to work with a long dataframe over a list
meta_sm <- meta_sm |> dplyr::bind_rows()
meta_dt <- meta_dt |> dplyr::bind_rows()

# Check erroneous responses ---
cloud_na <- meta_dt_df |> dplyr::group_by(year, basemap, id_quad, id_scene) |> 
  dplyr::summarise(s = sum(is.na(cloud_cover))) |> 
  dplyr::filter(s > 0)
cloud_na

# We could try and fill the gaps (should recompute summaries then)
id_missing <- cloud_na[["id_scene"]] |> unique() # Scenes can appear in multiple quads
chunk_missing <- id_missing |> split(ceiling(seq_along(id_missing) / 250))
redo <- lapply(chunk_missing, \(chunk) {
  tryCatch({get_metadata(chunk, geometry = FALSE)}, error = \(e) {
    warning("Error processing chunk – returning empty dataframe.")
    return(data.frame(id_scene = chunk)) # The rest will be NA
  })
}) |> dplyr::bind_rows()
# Missing completely
plot(id_missing %in% redo[["id_scene"]]) # All should be here
plot(id_missing %in% redo[["id_scene"]][is.na(redo[["cloud_cover"]])]) # Some don't work

saveRDS(meta_dt, "data/segmentation/global_mining_polygons_v2_metadata.rds")
saveRDS(meta_sm, "data/segmentation/global_mining_polygons_v2_meta-sm.rds")

# The quad download links are stored in an attribute of the quad, but they 
# always seem to follow from basemap and quad ID:
# https://link.planet.com/basemaps/v1/mosaics/34ead9f8-c7af-4daf-a266-e514251eeea7/quads/708-1052/full?api_key=


# Use the data ---

op <- par(mfrow = c(1, 2))
hist(meta_dt_df[["cloud_cover"]], main = "all scenes")
hist(meta_sm_df[["cloud_avg"]], main = "| best month per quad")
par(op)
