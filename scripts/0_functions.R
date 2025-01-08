
# Preliminaries ---
library("httr")
library("sf")
library("dplyr")

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


# Functions ---

# Download link
get_link <- \(basemap, quads) {
  year <- gsub(".*_(20[0-9]{2})-.*", "\\1", basemap)
  id_basemap <- BASEMAPS_ID[[year]][[basemap]]
  paste("https://link.planet.com/basemaps/v1/mosaics", 
    id_basemap, "quads", quads, "full?api_key=", sep = "/")
}


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
  if(status == 429) { # Too many requests -- wait and retry
    Sys.sleep(1.05)
    response <- paste(API_URL, id_basemap, "quads", sep = "/") |> 
      httr::GET(query = query, httr::authenticate(API_KEY, ""))
    status <- httr::status_code(response)
  }
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
  if(status == 429) { # Too many requests -- wait and retry
    Sys.sleep(1.05)
    response <- paste(API_URL, id_basemap, "quads", id_quad, "items", sep = "/") |> 
      httr::GET(query = query, httr::authenticate(API_KEY, ""))
    status <- httr::status_code(response)
  }
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
  if(status == 429) { # Too many requests -- wait and retry
    Sys.sleep(1.05)
    response <- httr::POST(
      url = "https://api.planet.com/data/v1/quick-search",
      body = payload, encode = "json", httr::authenticate(API_KEY, ""), httr::content_type_json()
    )
    status <- httr::status_code(response)
  }
  if(status < 100 || status > 300) {
    if(retry) {
      warning("Received status code ", status, " when requesting scene '", id_scene, "'.")
    } else {
      stop("Received status code ", status, " when requesting scene '", id_scene, "'.")
    }
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
      lapply(\(ids) { # Stop recursive halving at a basecase
      get_metadata(ids, geometry = geometry, retry = length(ids) >= 8)
    }) |> dplyr::bind_rows()
    tbl <- bind_rows(tbl, extra_rows)
  }
  tbl
}

