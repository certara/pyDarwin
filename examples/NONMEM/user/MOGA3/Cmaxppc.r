library(dplyr)
orgdata <-  read.table("ORG.DAT",skip=1,header=TRUE)
orgdata <- orgdata[orgdata$EVID==0&orgdata$TIME<=24,] # only first 24 hours
simdata <-  read.table("SIM.DAT",skip=1,header=TRUE) # only first 24 hours
simdata <- simdata[orgdata$EVID==0&orgdata$TIME<=24,] 
observed_maxes <- orgdata %>% group_by(ID) %>% 
  summarise(max = max(DV))
sim_maxes <- simdata %>% group_by(ID) %>% 
                        summarise(max = max(IOBS))
# penalty of 4 points for each % difference
obs_geomean = exp(mean(log(observed_maxes$max)))
sim_geomean = exp(mean(log(sim_maxes$max)))
penalty <- 4*abs((obs_geomean-sim_geomean)/obs_geomean)*100
c(penalty,penalty+1,penalty+111)
c()
