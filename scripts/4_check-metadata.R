
library("dplyr")
library("ggplot2")
library("ggdist")


# Summary statistics ---
df_sm <- readRDS("data/segmentation/metadata_summary.rds")

# Select the best basemap per quad per year
df_sel <- df_sm |> group_by(id_shape, year, quad) |>
    dplyr::arrange(dplyr::desc(dplyr::row_number())) |> # Keep the last month on a tie
    dplyr::slice_min(badness_avg, n = 1, with_ties = FALSE) # Best basemap


# Badness

df_sm |> ggplot(aes(x = year, y = badness_avg)) +
  geom_boxplot() + ylim(c(0, 100))
df_sel |> ggplot(aes(x = year, y = badness_avg)) +
  geom_boxplot() + ylim(c(0, 100))

df_sel |> filter(!is.na(badness_avg)) |> mutate(Year = year) |> 
  ggplot(aes(x = year, y = badness_avg, fill = Year)) +
  # stat_dotsinterval(position = "dodgejust", quantiles = 25) +
  stat_histinterval(position = "dodgejust") +
  ylim(c(0, 100)) + ggtitle("Image quality histogram") +
  ylab("Average cloud & heavy haze (%)") + xlab("Year") +
  scale_fill_brewer(palette = "Set3") +
  scale_x_discrete(breaks = seq(2016, 2024, by = 2)) +
  ggthemes::theme_pander() +
  theme(panel.background = element_rect(color = "grey70"))
ggsave("outputs/selected-image_quality.pdf", height = 4, width = 7)

op <- par(mfrow = c(2, 1), mar = c(2, 2, 2, .5))
hist(df_sm$badness_avg, xlim = c(0, 100), main = "Badness, All")
hist(df_sel$badness_avg, xlim = c(0, 100), main = "Badness, Selected")
par(op)

df_sm |> group_by(year) |> 
  summarize(
    mean = mean(badness_avg, na.rm = TRUE),
    q1 = quantile(badness_avg, 0.1, na.rm = TRUE),
    q5 = median(badness_avg, na.rm = TRUE),
    q9 = quantile(badness_avg, 0.9, na.rm = TRUE)
  )

df_sel |> group_by(year) |> 
  summarize(
    mu = mean(badness_avg, na.rm = TRUE),
    q1 = quantile(badness_avg, 0.1, na.rm = TRUE),
    q5 = median(badness_avg, na.rm = TRUE),
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
    q1 = quantile(cloud_avg, 0.1, na.rm = TRUE),
    q5 = median(cloud_avg, na.rm = TRUE),
    q9 = quantile(cloud_avg, 0.9, na.rm = TRUE)
  )

df_sel |> group_by(year) |> 
  summarize(
    mu = mean(cloud_avg, na.rm = TRUE),
    q1 = quantile(cloud_avg, 0.1, na.rm = TRUE),
    q5 = median(cloud_avg, na.rm = TRUE),
    q9 = quantile(cloud_avg, 0.9, na.rm = TRUE)
  )

