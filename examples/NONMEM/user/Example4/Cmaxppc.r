library(dplyr)
orgdata <-  read.table("ORG.DAT",skip=1,header=TRUE)
orgdata <- orgdata[orgdata$EVID==0&orgdata$TIME<=24,] # only first 24 hours
simdata <-  read.table("SIM.DAT",skip=1,header=TRUE) # only first 24 hours
simdata <- simdata[simdata$EVID==0&simdata$TIME<=24,] 
observed_maxes <- orgdata %>% group_by(ID) %>% 
  summarise(max = max(DV))
sim_maxes <- simdata %>% group_by(ID) %>% 
                        summarise(max = max(IOBS))
# penalty of 4 points for each % difference
obs_geomean = exp(mean(log(observed_maxes$max)))
sim_geomean = exp(mean(log(sim_maxes$max)))
penalty <- 4*abs((obs_geomean-sim_geomean)/obs_geomean)*100
text <- paste0("Observed day 1 Cmax geomean = ", round(obs_geomean,1), " simulated day 1 Cmax geo mean = ", round(sim_geomean,1))
c(penalty,text)


 

