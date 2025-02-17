rm(list=ls())
setwd("c:/Users/msale/pydarwin/MOGA2/non_dominated_models")
sourceFolder <- "c:/Users/msale/pydarwin/MOGA2/non_dominated_models"
source("c:/git/pyDarwin/examples/NONMEM/user/MOGAPlots/GetNMParms.r")
library(ggplot2)
 
MakeFrontPlot <- function(sourceFolder){
  data <- data.frame(Generation = as.integer(),
                     Model = as.integer(),
                     OFV = as.numeric(),
                     n_estimated_Parms = as.integer(),
                     Success = as.logical(),
                     Covar = as.logical())
  Generations <- list.files(sourceFolder) 
  this_gen = 2
  for(this_gen in Generations){
    models <- list.files(file.path(sourceFolder,this_gen)) 
    this_model = 1
    for(this_model in models){
      xml_file <- list.files(file.path(sourceFolder, this_gen, this_model),
                             pattern = "\\.xml",
                             full.names = TRUE)
      parms <- ReadXML(xml_file)
      OFV <- parms$OFV
      n_estimated_Parms <- parms$n_estimated_parms
      Success <- parms$success
      Covar <- parms$covar
      this_data <- data.frame(Generation = this_gen,
                              Model = this_model,
                              OFV = OFV,
                              n_estimated_Parms = n_estimated_Parms,
                              Success = Success,
                              Covar = Covar)
      
      data <- rbind(data,this_data)
    }
  }
  data <- data %>% group_by(Generation, Covar, Success)
  min_parms <- min(data$n_estimated_Parms)
  max_parms <- max(data$n_estimated_Parms)
  if((min_parms %% 2) == 1) min_parms <- min_parms - 1
  if((max_parms %% 2) == 1) max_parms <- max_parms + 1
  shapes <- c(21,22)
  names(shapes) <- c(TRUE, FALSE)
  ggplot(data,aes(x=n_estimated_Parms, y=OFV)) +
    geom_point(aes(shape = Covar, fill = Success), size=2)+
    scale_shape_manual(values=shapes) +
    geom_line(aes(color = Generation )) +
    scale_x_continuous(breaks=seq(min_parms,max_parms,2))+
    xlab("Number of Estimated Parameters")+
    ylab("OFV (-2LL)")
}