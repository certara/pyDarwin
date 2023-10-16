obsData <-  read.csv("ObsData.csv")

obsData <-
  subset(obsData, select = which(colnames(obsData) %in% c("id5", "time", "CObs"), arr.ind = TRUE)) |>
  na.omit()

obsCmax <- tapply(obsData$CObs, obsData$id5, max)

simData <-  read.csv("SimData.csv")
colnames(simData)[1] <- "repl"

simData <-
  subset(simData, select = which(
    colnames(simData) %in% c("repl", "id5", "time", "CObs"),
    arr.ind = TRUE
  )) |>
  na.omit()

simCmax <-
  tapply(simData$CObs, list(simData$repl, simData$id5), max) |>
  apply(2, median)

## penalty of 4 points for each % difference in geometric mean
geoMean <- exp(mean(log(simCmax/obsCmax)))

penalty <-
  4 * abs(1 - geoMean) * 100

text <-
  paste0(
    "Observed Cmax geometric means sim/obs ratio = ",
    signif(geoMean, 1)
  )
c(penalty, text)
