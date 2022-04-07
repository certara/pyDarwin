suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(readr))  
#suppressPackageStartupMessages(library(PKNCA))   
NCA <- function(data){
  AUC <- 0
  Cmax <- data$CONC[1]
  Tmax <- data$TIME[1]
  
  for (thisob in 2:dim(data)[1]){ 
    if(data$CONC[thisob]>Cmax){
      Cmax <- data$CONC[thisob]
      Tmax <- data$TIME[thisob]
    }
    AUC <- AUC + 
      (data$TIME[thisob]-data$TIME[thisob-1])*((data$CONC[thisob]+data$CONC[thisob-1])/2)
  }
  c(log(AUC),log(Cmax),Tmax)
}
RPenalty <- function(dir=NULL,...){ 
  args <- list(...) [[1]] 
  Text <- "Unknown Error"
  sumpenalty <- 999999 # error case
  CmaxPPCTxt <- "Unknown Error in Cmax PPC\n"
  TmaxPPCtext <- "Unknown Error in Tmax PPC\n"
  AUCPPCtext <- "Unknown Error in AUC PPC\n"
  
  AUCPPCPenalty_per_percent <- args[[1]]
  CmaxPPCPenalty_per_percent <-args[[2]] # must be hard coded in R code
                          #5 points penalty for each 1% difference between simulated an observed Cmax
  TmaxPPCPenalty_per_percent <-args[[3]]
  AUCStart <- 0
  AUCLast <- 24
  if(is.null(dir)){ 
    gc(FALSE)
    return(c(99999,"Directory is Null"))
  }
  if(!dir.exists(dir)){ 
    gc(FALSE)
    return(c(99999,paste("Directory",dir," does not exist")))
  }
  if(!file.exists(file.path(dir,"org.dat"))){ 
    gc(FALSE) 
    return(c(99999,paste("File org.dat does not exist in ",dir)))
  } 
  if(!file.exists(file.path(dir,"sim.dat"))){ 
    gc(FALSE)
    return(c(99999,paste("File sim.dat does not exist in ",dir)))
  }
  tryCatch({  
    
    path <- file.path(dir,"org.dat")  
    raworgdata <- read_table(path,col_types = "dddd",
        col_names = c("REP","ID","TIME","CONC"),progress=FALSE) 
    # 
    path = file.path(dir,"sim.dat") 
    rawsimdata <- read_table(path,col_types = "dddd",
                      col_names = c("REP","ID","TIME","CONC"),progress=FALSE) %>% 
                  mutate(REPID = REP*100+ID)
     
    orgmeans <- data.frame(matrix(-99,nrow=100*50,ncol=4))
    colnames(orgmeans) <-  c("ID","AUC","Cmax","Tmax")
    orgmeans <- c(0,0,0)
     
      for (n in 1:50){
        # outputrow <- outputrow + 1
        inddata <- raworgdata %>% filter(ID==n) %>% select(TIME,CONC)
        orgmeans <- orgmeans + NCA(inddata) # returns log of Cmax and AUC
      }
  
    orgmeans <- orgmeans/50
    orgmeans[1:2] <- exp(orgmeans[1:2])
      # remove negative conc
    rawsimdata <- rawsimdata %>% mutate(CONC = ifelse(CONC<0.001,0.001,CONC)) %>% 
      filter(TIME<=AUCLast)
    
   
   # simresults <- data.frame(matrix(-99,nrow=100*50,ncol=5))
    #colnames(simresults) <-  c("REP","ID","AUC","Cmax","Tmax")
    #outputrow <- 0 
    simmeans <- c(0,0,0)
    for (i in 1:20){
      data <- rawsimdata %>% filter(REP == i) %>% select(ID,TIME,CONC)
        for (n in 1:50){
         # outputrow <- outputrow + 1
          inddata <- data %>% filter(ID==n) %>% select(TIME,CONC)
          simmeans <- simmeans + NCA(inddata) # returns log of Cmax and AUC
        }
      }
    simmeans <- simmeans/(50*20)
    simmeans[1:2] <- exp(simmeans[1:2])
    diff <- abs((simmeans-orgmeans)/orgmeans)*100
    penalty <- diff*c(AUCPPCPenalty_per_percent,CmaxPPCPenalty_per_percent,TmaxPPCPenalty_per_percent)
    sumpenalty <- sum(penalty)
    AUCPPCTxt <- paste0("R code AUC Penalty for ",dir,"=",round(penalty[1],3),  
                        ",\nabsolute AUC difference % =",round(diff[1],1), 
                        "%, data AUC = ",round(orgmeans[1],1),", simulated AUC = ",round(simmeans[1],1) )
    CmaxPPCTxt <- paste0("R code Cmax Penalty for ",dir,"=",round(penalty[2],3),
                      ",\nabsolute Cmax difference % =",round(diff[2],1),
                      "%, data Cmax = ",round(orgmeans[2],1),", simulated Cmax = ",round(simmeans[2],1) )
 
    TmaxPPCTxt <- paste0("R code Tmax Penalty for ",dir,"=",round(penalty[3],3),  
                         ",\nabsolute Tmax difference % =",round(diff[3],1), 
                         "%, data Tmax = ",round(orgmeans[3],1),", simulated Tmax = ",round(simmeans[3],1) )
   
    
    Text <- paste(AUCPPCTxt,CmaxPPCTxt,TmaxPPCTxt)
    },
     error=function(cond) {
       rm(list=ls())
       gc(FALSE)
       return(c(99999,paste("Unknown error in R code reading from directory",dir)))
       
     }
      ) 
  #rmlist <- ls()   
  if(file.exists(file.path(dir,"ORG.DAT"))) file.remove(file.path(dir,"ORG.DAT")) 
  if(file.exists(file.path(dir,"SIM.DAT"))) file.remove(file.path(dir,"SIM.DAT"))
  gc(FALSE) # need to free up memory??
  return(c(sumpenalty,Text))
  }

 

