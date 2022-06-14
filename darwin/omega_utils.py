import re 
import math
import numpy as np
import copy
from .utils import remove_comments 
def set_omega_bands(control: str, bandwidth: int):
    """Removes ALL existing omega blocks from control, then inserts a serirs of $OMEGAs. These will be unchanges if the source is BLOCK or DIAG. Not not specified
    BLOCK or DIAG (and so is by default DIAG), will convert to BLOCK with the number of bands specified in the model code

    :param control: existing control file
    :type control: str
    :param bandwidth: require band width
    :type bandwidth: int
    :return: modified control file
    :rtype: str
    """
    #try:
    org_control = control # save in case this fails, return 
    control_list = control.splitlines()
    lines =  remove_comments(control).splitlines()
    omega_starts = [idx for idx, element in enumerate(lines) if re.search("^\$OMEGA",element)] 
    new_omega_block = [] 
    omega_ends = []
    omega_blocks = []
    for thisstart in omega_starts: 
        rest_of_text = lines[thisstart:]
        next_block_start = [idx for idx, element in enumerate(rest_of_text[1:]) if re.search("^\$",element)]
        if next_block_start is None:
            next_block_start = len(rest_of_text)
        else:
            next_block_start = next_block_start[0]
        this_omega_ends = next_block_start + thisstart + 1
        omega_ends.append(this_omega_ends)
        omega_blocks.append(copy.copy(lines[thisstart:this_omega_ends]))
    all_omega_blocks = []
    for thisstart in omega_blocks:
        ## see if BLOCK(*) of DIAG appears, if user explicitly states it is DIAG, it will remain DIAG
        is_block_or_diag = any(re.search("BLOCK",line) for line in thisstart) or any(re.search("DIAG",line) for line in thisstart)
        # if so, keep block as is,
        if is_block_or_diag:
            all_omega_blocks.append(copy.deepcopy(thisstart))
                
        else: # is diagonal, but not explicity stated to be diagonal
            # get values, start by replacing $OMEGA, and if present, DIAG
            thisblock = copy.deepcopy(thisstart)
            thisblock[0] = thisblock[0].replace("$OMEGA","")
            # and collect the values, to be used on diagonal
            thisblock = ' '.join([str(elem) for elem in thisblock]).replace("\n","").replace("  "," ").replace("  "," ").strip()
            thisblock = thisblock.split(" ")
            thisblock = np.array(thisblock, dtype=np.float32) # this_block.split(" ")
            
            size = len(thisblock)
            # get max value, for first guess at diagonals
            off_diag = math.sqrt(float(max(thisblock))/2) # no good reason to start here, assum +ive covariances
            # build matrix, check if positive definate
            is_pos_def = False
            
            count = 0
            #this_band = 0
            while not is_pos_def and count < 100:
                off_diag *= 0.5 
                matrix = np.zeros([size,size])
                # bands up to bandwidth
                for this_row in range(size-1):
                    if this_row < bandwidth:
                        val = off_diag
                    else:
                        val = 0 
                    for this_col in range(this_row):
                        matrix[this_row,this_col] = val
                
                np.fill_diagonal(matrix, thisblock)
                is_pos_def = np.all(np.linalg.eigvals(matrix) > 0) # works if matrix is symetrical
                count += 1
            # only include band width up to band width
            new_block = ["$OMEGA BLOCK(" + str(size) + ")"]
            for this_eta in range(size):
                new_block.append(np.array2string(matrix[this_eta][:(1+this_eta)]).replace("[","").replace("]",""))
            new_omega_block = copy.copy(new_block)
            new_omega_block  = '\n'.join(str(x) for x in new_omega_block) 
            new_omega_block = new_omega_block.replace(",","\n").replace("[","").replace("]","")
            all_omega_blocks.append(copy.deepcopy(new_omega_block))
        # start from the bottom (so the line number doesn't change) delete all $OMEGA, but replace the first one with the new_omega_block
            
    num_omega_blocks = len(omega_starts) 
    for num in range(num_omega_blocks):
        line_in_block = 0
        # split this omegablock into lines ONLY if it is just a string (will already be array if BLOCK)
        if isinstance(all_omega_blocks[num],str):
            this_new_omega_block = all_omega_blocks[num].split("\n")
        else:
            this_new_omega_block = all_omega_blocks[num]
        for this_line in range(omega_starts[num],omega_ends[num]):
            if line_in_block < len(this_new_omega_block):
                control_list[this_line] = this_new_omega_block[line_in_block]
            else:
                control_list[this_line] = ""
            line_in_block += 1
            # reassemble into a single string
    control =  '\n'.join(control_list) 
    
    return control

    #except Exception as e:
    #    return (org_control,False,str(e)) 

# def set_omega_bands(control: str, bandwidth: int) -> str:
#     """Removes ALL existing omega blocks from control, then inserts a series of $OMEGAs.
#     These will be unchanged if the source is BLOCK or DIAG. Not specified BLOCK or DIAG (and so is by default DIAG),
#     will convert to BLOCK with the number of bands specified in the model code

#     :param control: existing control file
#     :type control: str
#     :param bandwidth: require band width
#     :type bandwidth: int
#     :return: modified control file
#     :rtype: str
#     """
#     control_list = control.splitlines()
#     lines = remove_comments(control).splitlines()
#     omega_starts = [idx for idx, element in enumerate(lines) if re.search(r"^\$OMEGA", element)]
#     omega_ends = []
#     omega_blocks = []

#     for start in omega_starts:
#         rest_of_text = lines[start:]
#         next_block_start = [idx for idx, element in enumerate(rest_of_text[1:]) if re.search(r"^\$", element)]
#         if next_block_start is None:
#             next_block_start = len(rest_of_text)
#         else:
#             next_block_start = next_block_start[0]
#         this_omega_ends = next_block_start + start + 1
#         omega_ends.append(this_omega_ends)
#         omega_blocks.append(copy.copy(lines[start:this_omega_ends]))

#     all_omega_blocks = []

#     for start in omega_blocks:
#         # see if BLOCK(*) of DIAG appears, if user explicitly states it is DIAG, it will remain DIAG
#         is_block_or_diag = any(re.search("BLOCK", line) for line in start)\
#                            or any(re.search("DIAG", line) for line in start)

#         # if so, keep block as is
#         if is_block_or_diag:
#             all_omega_blocks.append(copy.deepcopy(start))
#         else:  # is diagonal, but not explicitly stated to be diagonal
#             # get values, start by replacing $OMEGA, and if present, DIAG
#             this_block = copy.deepcopy(start)
#             this_block[0] = this_block[0].replace("$OMEGA", "")
#             # and collect the values, to be used on diagonal
#             this_block = ' '.join([str(elem) for elem in this_block])\
#                 .replace("\n", "").replace("  ", " ").replace("  ", " ").strip()
#             this_block = this_block.split(" ")
#             this_block = np.array(this_block, dtype=np.float32)
            
#             size = len(this_block)
#             # get max value, for first guess at diagonals
#             off_diag = math.sqrt(float(max(this_block))/2)  # no good reason to start here, assum +ive covariances
#             # build matrix, check if positive definite
#             is_pos_def = False
            
#             count = 0
#             matrix = []

#             while not is_pos_def and count < 100:
#                 off_diag *= 0.5 
#                 matrix = np.zeros([size, size])
#                 # bands up to bandwidth
#                 for this_row in range(size-1):
#                     if this_row < bandwidth:
#                         val = off_diag
#                     else:
#                         val = 0 
#                     for this_col in range(this_row):
#                         matrix[this_row, this_col] = val
                
#                 np.fill_diagonal(matrix, this_block)
#                 is_pos_def = np.all(np.linalg.eigvals(matrix) > 0)  # works if matrix is symmetrical
#                 count += 1

#             # only include band width up to band width
#             new_block = ["$OMEGA BLOCK(" + str(size) + ")"]
#             for this_eta in range(size):
#                 new_block.append(np.array2string(matrix[this_eta][:(1+this_eta)]).replace("[", "").replace("]", ""))

#             new_omega_block = copy.copy(new_block)
#             new_omega_block = '\n'.join(str(x) for x in new_omega_block)
#             new_omega_block = new_omega_block.replace(",", "\n").replace("[", "").replace("]", "")
#             all_omega_blocks.append(copy.deepcopy(new_omega_block))
#         # start from the bottom (so the line number doesn't change) delete all $OMEGA,
#         # but replace the first one with the new_omega_block
            
#     num_omega_blocks = len(omega_starts) 

#     for num in range(num_omega_blocks):
#         line_in_block = 0
#         # split this omega block into lines
#         this_new_omega_block = all_omega_blocks[num-1].split("\n")
#         for this_line in range(omega_starts[num-1], omega_ends[num-1]):
#             if line_in_block < len(this_new_omega_block):
#                 control_list[this_line] = this_new_omega_block[line_in_block]
#             else:
#                 control_list[this_line] = "; removed for band omega"
#             line_in_block += 1
#             # reassemble into a single string

#     control = '\n'.join(control_list)
     
#     return control
