a = 4
b <- rep(getwd(),2)
Sys.sleep(1)
library(ggplot2)
library(readr)
data <-  read_table("org.dat",skip=1)
plot <- ggplot(data,aes(x=data$DV)) +
  geom_histogram()
ggsave("simplePlot.jpeg",plot,device="jpeg",width = 6,height = 4)
write.csv(b,"test.csv") # just to make sure we're in the right folder
c(a,"test test test")


 

