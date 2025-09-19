library(xml2)
library(dplyr)
library(stringr)
ReadXML <- function(xml_file){
  tryCatch(
    {
  n_estimated_parms = -9999 # may be able to get estimated parms even if model crashed, so need default
  data <- read_xml(xml_file, encoding = "ASCII")
  problems_node <- xml_find_all(data, "//nm:problem_information")
  n_problems <- length(problems_node)
  OFV <-   xml_find_all(data, "//nm:final_objective_function")   %>%
    xml_text() %>%
    as.numeric()
  
  for(this_problem in problems_node){
    problems_child <- xml_children(this_problem)
  } 
  control_node <- data %>%
    xml_find_all("//nm:control_stream") %>%
    xml_text()  %>%
    str_split("\n")
  data_file <- control_node[[1]][grep("^\\$DATA",control_node[[1]])] %>%
    str_replace("\\$DATA ","") %>%
    str_replace("IGNORE\\=@","") %>%
    str_replace("REWIND","") %>%
    str_replace("ACCEPT\\=@","") %>%
    str_trim()
  
  iterations_node <- xml_find_all(data, "//nm:monitor")
  iterations <- as.integer(xml_attr(iterations_node,"iteration"))
  if(length(iterations_node) == 0){
    # something failed
    iterations <- -999
  }else{ 
    this_node = iterations_node[1]
    iterations <- c() 
    this_node <- iterations_node[1]
    for(this_node in iterations_node){
      if(length(xml_children(this_node)) > 1) {
        iterations_children <- xml_children(this_node)[2]
        iterations <- c(iterations,as.integer(xml_attr(iterations_children,"iteration")))
      }else{
        iterations_children <- xml_children(this_node)[1]
        iterations <- c(iterations, as.integer(xml_attr(iterations_children,"iteration")))
      }
             
    }
  }
  messages_node <- xml_find_all(data, "//nm:termination_txtmsg")
  messages_children <- xml_children(messages_node)
  message_contents <- xml_contents(messages_node)
  messages <- as.numeric(xml_text(message_contents))
  finished <- success <- covar <- c()
  for(this_message in messages){
    if(length(this_message) == 0){
      finished <- c(finished, FALSE)
    }else{
      finished <- c(finished, TRUE)
    }
    if(37 %in% this_message){
      success <- c(success,TRUE)
    }else{
      success <- c(success, FALSE)
    }
  }
  message_char <- paste(messages, collapse = "|")
  status <- data %>%
    xml_find_all("//nm:termination_status") %>%
    xml_text() %>%
    as.numeric()
  Est_Method <- data %>%
    xml_find_all("//nm:estimation_method") %>%
    xml_text() 
  Est_time <- data %>%
    xml_find_all("//nm:estimation_elapsed_time") %>%
    xml_text() %>%
    as.numeric()
  
  Cov_time <- data %>%
     xml_find_all("//nm:covariance_elapsed_time") %>%
     xml_text() %>%
     as.numeric() 
  
  covar <- xml_find_all(data, "//nm:covariance_status")  %>% 
    xml_attr("error") %>% 
    as.numeric()
  covar <- covar == 0
  #
  theta_node <- xml_find_all(data, "//nm:theta") 
  thetas <- list()
  this_node <- 1
  n_theta <-  length(xml_children(theta_node[1]))
  for(this_node in 1:length(theta_node)){
    cur_node <- theta_node[this_node]
    theta_children <- xml_children(cur_node)
    this_theta <- as.numeric(xml_text(theta_children))
    thetas[[this_node]] <-  this_theta
  } 
  omega_node <- xml_find_all(data, "//nm:omega") %>%
    xml_children()
  omegas <- list() 
  omega_dim <- length(omega_node)/n_problems 
  n_omega <- omega_dim
  this_prob <- 1
  for(this_prob in 1:n_problems){
    cur_node <- omega_node[((this_prob-1) * n_omega + 1):(this_prob*n_omega)]
    this_omega <- matrix(0, ncol=  n_omega, nrow = n_omega)
    omega_vec <-   xml_children(cur_node) %>%
      xml_text()
    # omega filled down rows first 
    cur_omega <- 0
    for(thiscol in 1:n_omega){
      for(thisrow in 1:thiscol){
        cur_omega <- cur_omega + 1
        this_omega[thiscol,thisrow] <- as.numeric(omega_vec[cur_omega])
      }
    }
    omegas[[this_prob]] <- this_omega
  }
  if(Est_Method[1] !="fo"){ # use fo only for naive pool??
    
    sigma_node <- xml_find_all(data, "//nm:sigma") %>%
      xml_children()
    n_sigma <- sigma_node[1] %>% 
      xml_text() %>% 
      length()
    sigmas <- list()
    this_prob <- 1
      for(this_prob in 1:n_problems){
        cur_node <- sigma_node[((this_prob-1) * n_sigma + 1):(this_prob*n_sigma)]
        this_sigma <- matrix(0, ncol=  n_sigma, nrow = n_sigma)
        sigma_vec <-   xml_children(cur_node) %>%
          xml_text()
        # sigma filled down rows first 
        cur_sigma <- 0
        for(thiscol in 1:n_sigma){
          for(thisrow in 1:thiscol){
            cur_sigma <- cur_sigma + 1
            this_sigma[thiscol,thisrow] <- as.numeric(sigma_vec[cur_sigma])
          }
        }
         sigmas[[this_prob]] <- this_sigma
      }
    
    ETAbarVec <- xml_find_all(data, "//nm:etabar") %>%
      xml_children() %>%
      xml_contents() %>% 
      xml_text()
    class(ETAbarVec) <- "numeric" 
    ETABars <- list()
    for(this_ETAbar in 1:n_problems){
       cur_ETAbar <- ETAbarVec[((this_ETAbar -1)*n_omega + 1):(this_ETAbar*n_omega)]
       ETABars[[this_ETAbar]] = cur_ETAbar
    }
    
    
    ETAbarPvalVec <- xml_find_all(data, "//nm:etabarpval") %>%
      xml_children() %>%
      xml_contents() %>% 
      xml_text()
    class(ETAbarPvalVec) <- "numeric" 
    ETABarPvals <- list()
    for(this_ETAbar in 1:n_problems){
      cur_ETAbarPval <- ETAbarPvalVec[((this_ETAbar -1)*n_omega + 1):(this_ETAbar*n_omega)]
      ETABarPvals[[this_ETAbar]] = cur_ETAbarPval
    }
  }else{
    sigmas  = ETAbar = ETABarPvals= -9999
  }
  CovarMatrices <- theta_ses <- omega_ses <- sigma_ses <- list()
   
  if(any(covar)){
    cur_prob <- 0
    cov_nodes <- xml2::xml_find_all(data, "//nm:covariance")
    thisProb <- 1
    for(thisProb in 1:length(covar)){
      if(covar[thisProb]){
        cur_prob <- cur_prob + 1
        cov_node <- cov_nodes[cur_prob]
        children <- xml_children(cov_node)
        dim <- xml_length(cov_node, only_elements = TRUE)
        xml_text(children[[2]])
        cov <- matrix(-999, nrow=dim,ncol=dim)
        cur_row <- 0
        for(this_row in children){
          row_children <- xml_children(this_row)
          cur_row <-  cur_row + 1
          cur_col <- 0
          for(this_col in row_children){
            cur_col <- cur_col + 1
            cov[cur_row,cur_col] <- cov[cur_col,cur_row] <- as.numeric(xml_text(this_col))
          }
        }
        
        class(cov) <- "numeric"
        # remove 0 cols and rows
        zero_rows = apply(cov, 1, function(row) any(row != 0 )) 
        CovarMat <-  cov[zero_rows,zero_rows]
        theta_se <- xml_find_all(cov_node, "//nm:thetase") 
        theta_se <- theta_se[cur_prob] %>%
          xml_children() %>%
          xml_text()
        
        class(theta_se) <- "numeric"
        omegase <- xml_find_all(cov_node, "//nm:omegase") 
        omegase <- omegase[cur_prob] %>%
          xml_children()
        
        omegase_vec <-   xml_children(omegase) %>%
          xml_text()
        # omega filled down rows first
        omega_se <- matrix(0,nrow=omega_dim, ncol=omega_dim)
        cur_omega <- 0
        for(thiscol in 1:omega_dim){
          for(thisrow in 1:thiscol){
            cur_omega <- cur_omega + 1
            omega_se[thiscol,thisrow] <- as.numeric(omegase_vec[cur_omega])
          }
        }
        
        class(omega_se) <- "numeric"
        sigma_se <- xml_find_all(data, "//nm:sigmase") %>%
          xml_children()
        
        sigmase_vec <-   xml_children(sigma_se) %>%
          xml_text()
        # sigma filled down rows first
        sigma_se <- matrix(0,nrow = n_sigma, ncol = n_sigma)
        cur_sigma <- 0
        for(thiscol in 1:n_sigma){
          for(thisrow in 1:thiscol){
            cur_sigma <- cur_sigma + 1
            sigma_se[thiscol,thisrow] <- as.numeric(sigmase_vec[cur_sigma])
          }
          
          class(sigma_se) <- "numeric"
        }
          CovarMatrices[[thisProb]] = CovarMat
          theta_ses[[thisProb]] = theta_se
          omega_ses[[thisProb]] = omega_se
          sigma_ses[[thisProb]] = sigma_se
      }else{
        
        CovarMatrices[[thisProb]] = -9999
        theta_ses[[thisProb]] = -9999
        omega_ses[[thisProb]] = -9999
        sigma_ses[[thisProb]] = -9999
      }
    }
  } else{
    covar = FALSE
    CovarMatrices = -9999
    theta_ses = -9999
    omega_ses = -9999
    sigma_ses = -9999
  }
  n_parms <- n_theta + n_omega + n_sigma
  # note that the number of eigen values may vary from one problem to another
  if(any(covar)){
    EigenNodes <- xml_find_all(data, "//nm:eigenvalues") %>%
      xml_children() 
    Eigens <- EigenNodes %>%
      xml_text()
    if(length(Eigens) > 0){
      EigenPos <- xml_attr(EigenNodes,"name") %>% 
        as.integer()
      class(Eigens) <- "numeric"
      starts <- which(EigenPos %in% 1)
      starts <- c(starts,length(Eigens) + 1)
      Eigenvalues <- list()
      for(this_prob in 1:n_problems){
        Eigenvalues[[this_prob]] = Eigens[starts[this_prob]:(starts[this_prob+1] - 1)]
      } 
  }else{
    Eigenvalues <- -9999
    }
    }else{
      Eigenvalues <- -9999
    }
    
  nsubs_node <- xml_find_all(data, "//nm:problem_options") 
  nsubs <- nobs <-   c()
  for(this_node in nsubs_node){ 
    nsubs <- c(nsubs,as.integer(xml_attr(this_node,"data_nind")))
    nobs <- c(nobs,as.integer(xml_attr(this_node,"data_nobs")))
  }  
  lstfile <- str_replace(xml_file,"\\.xml",".lst")
  lst <- readtext::readtext(lstfile, verbosity = 0)$text
  lst <- unlist(str_split(lst,"\n"))
  pos1 <- grep("^0ITERATION NO.: ",lst)[1] 
  pos2 <- grep("^ #TERM:" ,lst)[1] 
  lst <- lst[(pos1+1):pos2]
  pos1 <- grep("^ GRADIENT",lst)[1] 
  pos2 <- grep("^0ITERATION NO.:",lst)[1]
  grd <- lst[pos1:(pos2-1)]
  grd <- str_replace(grd,"GRADIENT:","") 
  grd <- paste0(grd, collapse = "")
  while(grepl("  ", grd, fixed = TRUE)){
    grd <- str_replace(grd,"  "," ") 
  }
  grd <- str_trim(grd)
  grd <- unlist(str_split(grd," "))
  n_estimated_parms <- length(grd)
  
  return(list(
    OFV = OFV,
    theta = thetas,
    omega = omegas,
    sigma = sigmas,
    theta_ses = theta_ses,
    omega_ses = omega_ses,
    sigma_ses = sigma_ses,
    dataFile = data_file,
    iterations = iterations,
    messages = messages,
    success = success,
    covar= covar,
    Eigenvalues = Eigenvalues,
    ETABarPvals = ETABarPvals,
    ETABars = ETABars,
    CovarMat = CovarMatrices,
    EstTime = Est_time,
    CovTime = Cov_time,
    nsubs = nsubs,
    nobs = nobs,
    Est_Method = Est_Method,
    n_total_parms = n_parms,
    n_estimated_parms = n_estimated_parms
  ))
  },error=function(error){
    return(list(
      OFV = -9999,
      theta = -9999,
      omega = -9999,
      sigma = -9999,
      theta_ses = -9999,
      omega_ses = -9999,
      sigma_ses = -9999,
      dataFile = -9999,
      iterations = -9999,
      messages = -9999,
      success = -9999,
      covar= -9999,
      Eigenvalues = -9999,
      ETABarPvals = -9999,
      ETABars = -9999,
      CovarMat = -9999,
      EstTime = -9999,
      CovTime = -9999,
      nsubs = -9999,
      nobs = -9999,
      Est_Method = -9999,
      n_total_parms = -9999,
      n_estimated_parms = n_estimated_parms
    ))
  })
}

