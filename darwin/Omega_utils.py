import re


def set_omega_bands(control, bandwidth):
    model = read_model_from_string(control)
    # check if omega is diagonal
    # can be multiple $OMEGA blocks, but overall OMEGA must be diagonal
    omega_dict = model.random_variables.etas.parameter_names
    omega_size = len(omega_dict)
    # see if any of the values have n != m
    for this_omega in omega_dict:
        this_omega = this_omega.replace("OMEGA(", "").replace(")", "").split(",")
        if this_omega[0] != this_omega[0]:
            return control, False  # if not diagonal, just return control and False

    init_vals = model.parameters.inits

    # find OMEGAs
    omega_init_vals = []

    for this_init in init_vals:
        if re.search(r"OMEGA\(", this_init):
            omega_init_vals.append(init_vals[this_init])

    # construct new OMEGA block
    if bandwidth == 0:
        omega_block = "\n$OMEGA DIAG(" + str(omega_size) + ")\n"
        for this_row in range(1, omega_size + 1):
            omega_block += str(omega_init_vals[this_row - 1]) + "\n"
    else:
        omega_block = "\n$OMEGA BLOCK(" + str(omega_size) + ")\n"
        # for diagonal matrix of 1's, 1/(p−1)
        # so take the maximum value of a diagonal, divide by size -1
        # then take half of that, should be a modest +ive correlation
        min_diag = min(omega_init_vals)
        min_off_diag = 0.5 * min_diag / (omega_size - 1)
        # and construct $OMEGA,one matrix only
        for this_row in range(1, omega_size + 1):
            line = " "
            for this_col in range(1, this_row + 1):
                if this_col == this_row:
                    line += str(omega_init_vals[this_row - 1]) + " "
                else:
                    if (this_row - this_col) <= bandwidth:
                        line += " " + str(min_off_diag) + " "
                    else:
                        line += " 0 "

            omega_block += line + "\n"

    return omega_block, True


def insert_omega_block(control, omega_block):
    omega_start = re.search(r"\n\s*\$OMEGA", control)
    omega_part = control[omega_start.regs[0][0]:]
    first_part = control[:omega_start.regs[0][0]]

    # find next $ that isn't $OMEGA
    omega_end = re.search(r"\n\s*\$(?!OMEGA)", omega_part)  #
    last_part = omega_part[omega_end.regs[0][0]:]

    new_control = first_part + omega_block + last_part

    return new_control
