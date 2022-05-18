from pharmpy.modeling import read_model_from_string ## v 0.66.0 works
import re  
import numpy as np
def is_pos_def(x):
    return np.all(np.linalg.eigvals(x) > 0)

def set_omega_bands(control,bandwidth):
    model = read_model_from_string(control)
    ## check if omega is diagonal
    ## can be multiple $OMEGA blocks, but overall OMEGA must be diagonal
    OMEGA_dict = model.random_variables.etas.parameter_names
    Omega_size = len(OMEGA_dict)
    ## see if any of the values have n != m
    for this_omega in OMEGA_dict:
        this_omega = this_omega.replace("OMEGA(","").replace(")","").split(",")
        if this_omega[0] !=this_omega[0]:
            return (control,False) # if not diagonal, just return control and False 
    
    Inits = model.parameters.inits
     
    # find OMEGAs
    Omega_inits = []
    for this_init in Inits:
        if re.search("OMEGA\(",this_init): 
            Omega_inits.append(Inits[this_init])
    # construct new OMEGA block
    if bandwidth == 0:
        OMEGA_block = "\n$OMEGA DIAG(" + str(Omega_size) + ")\n"
        for this_row in range(1,Omega_size + 1):  
            OMEGA_block += str(Omega_inits[this_row-1]) + "\n"
    else:
        OMEGA_block = "\n$OMEGA BLOCK(" + str(Omega_size) + ")\n"
        # for diagonal matrix of 1's, 1/(p−1)
        # so take the maximum value of a diagaonl, divide by size -1
        # then take half of that, should be a modest +ive correlation
        min_diag = min(Omega_inits)
        min_off_diag = 0.5*min_diag/(Omega_size-1)
        # and construct $OMEGA,one matrix only
        for this_row in range(1,Omega_size + 1): 
            line = " "
            for this_col in range(1,this_row+1):
                if this_col == this_row:
                    line +=  str(Omega_inits[this_row-1])  + " "
                else: 
                    if (this_row - this_col) <= bandwidth:
                        line += " " + str(min_off_diag) + " "
                    else: 
                        line += " 0 "
            OMEGA_block += line + "\n"
    
    return OMEGA_block, True
def insert_omega_block(control,omega_block):
    omega_start = re.search("\n\s*\$OMEGA",control) 
    omega_part = control[omega_start.regs[0][0]:]
    first_part = control[:omega_start.regs[0][0]]
    # find next $ that isn't $OMEGA
    omega_end = re.search("\n\s*\$(?!OMEGA)",omega_part) # 
    #re.search("\n\s*\$!OMEGA.*",omega_part) 
    last_part = omega_part[omega_end.regs[0][0]:]
    new_control = first_part + omega_block + last_part
    return new_control