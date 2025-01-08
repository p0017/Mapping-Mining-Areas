
# Summary statistics ---
df_sm <- saveRDS("data/segmentation/metadata_summary.rds")

# Select the best basemap per quad per year
df_sel <- df_sm |> group_by(id_shape, year, quad) |>
    dplyr::arrange(dplyr::desc(dplyr::row_number())) |> # Keep the last month on a tie
    dplyr::slice_min(badness_avg, n = 1, with_ties = FALSE) # Best basemap


# Badness
op <- par(mfrow = c(2, 1), mar = c(2, 2, 2, .5))
hist(df_sm$badness_avg, xlim = c(0, 100), main = "Badness, All")
hist(df_sel$badness_avg, xlim = c(0, 100), main = "Badness, Selected")
par(op)

df_sm |> group_by(year) |> 
  summarize(
    mu = mean(badness_avg, na.rm = TRUE),
    q5 = median(badness_avg, na.rm = TRUE),
    q1 = quantile(badness_avg, 0.1, na.rm = TRUE),
    q9 = quantile(badness_avg, 0.9, na.rm = TRUE)
  )

df_sel |> group_by(year) |> 
  summarize(
    mu = mean(badness_avg, na.rm = TRUE),
    q5 = median(badness_avg, na.rm = TRUE),
    q1 = quantile(badness_avg, 0.1, na.rm = TRUE),
    q9 = quantile(badness_avg, 0.9, na.rm = TRUE)
  )

# Cloud
op <- par(mfrow = c(2, 1), mar = c(2, 2, 2, .5))
hist(df_sm$cloud_avg, xlim = c(0, 1), main = "Clouds, All")
hist(df_sel$cloud_avg, xlim = c(0, 1), main = "Clouds, Selected")
par(op)

df_sm |> group_by(year) |> 
  summarize(
    mu = mean(cloud_avg, na.rm = TRUE),
    q5 = median(cloud_avg, na.rm = TRUE),
    q1 = quantile(cloud_avg, 0.1, na.rm = TRUE),
    q9 = quantile(cloud_avg, 0.9, na.rm = TRUE)
  )

df_sel |> group_by(year) |> 
  summarize(
    mu = mean(cloud_avg, na.rm = TRUE),
    q5 = median(cloud_avg, na.rm = TRUE),
    q1 = quantile(cloud_avg, 0.1, na.rm = TRUE),
    q9 = quantile(cloud_avg, 0.9, na.rm = TRUE)
  )

