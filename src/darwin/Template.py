import re
import sys
import json
import math
import collections
import darwin.utils
from darwin.Log import log
import copy
from darwin.options import options 
from darwin.utils import remove_comments


class Template:
    """
    The Template object contains information common to all the model objects, including the template code
    (from the template file) and the tokens set. It DOES NOT include any model specific information,
    such as the phenotype, the control file text, or any of the output results from NONMEM.
    Other housekeeping functions are performed, such as defining the gene structure (by counting the number of
    token groups for each token set), parsing out the THETA/OMEGA/SIGMA blocks, and counting
    the number of fixed/non-searched THETAs/OMEGAs/SIGMAs.

    :param template_file: Path to the plain ascii text template file
    :type template_file: str
    :param tokens_file: Path to the json tokens file
    """

    def __init__(self, template_file: str, tokens_file: str):
        """
        Template contains all the results of the template file and the tokens, and the options.
        Tokens are parsed to define the search space. The Template object is inherited by the model object.
        
        :raises: If the file paths do not exist, or the json file has syntax error, an error is raised.
        """

        try:
            self.template_text = open(template_file, 'r').read()

            log.message(f"Template file found at {template_file}")
        except Exception as error:
            log.error(str(error))
            log.error("Failed to open Template file: " + template_file)
            sys.exit()

        try:
            self.tokens = collections.OrderedDict(json.loads(open(tokens_file, 'r').read()))

            for group in self.tokens.values():
                for tokens in group:
                    for i, token in enumerate(tokens):
                        if type(token) == list:
                            tokens[i] = '\n'.join(token)

            log.message(f"Tokens file found at {tokens_file}")
        except Exception as error:
            log.error(str(error))
            log.error("Failed to parse JSON tokens in " + tokens_file)
            sys.exit()

        self.gene_max = []  # zero based
        self.gene_length = []  # length is 1 based

        self._get_gene_length()
        self._check_omega_search()

        # to be initialized by adapter
        self.theta_block = self.omega_block = self.sigma_block = []
        self.template_text = options.apply_aliases(self.template_text)

        if self._check_for_prior():
            log.message(f"$PRIOR found in template, PRIOR routine is not supported, exiting")
            sys.exit()

        if options.search_omega_bands and not self._check_for_multiple_probs():
            log.message(f"Search Omega bands is not supported with multiple $PROBs, exiting")
            sys.exit()

    def _check_for_prior(self):

        all_lines = darwin.utils.remove_comments(self.template_text)

        any_prior = re.search(r"\$PRIOR", all_lines, flags=re.MULTILINE)

        return any_prior is not None

    def _check_for_multiple_probs(self):
        # can't have multiple problems, issues with counting $OMEGA and
        # putting all $OMEGA at end of control
        # next version, put $OMEGAs back in original place?
        all_lines = darwin.utils.remove_comments(self.template_text)

        prob_lines = re.findall(r"\$PROB", all_lines)  #

        return len(prob_lines) < 2

    def _get_gene_length(self):
        """ argument is the token sets, returns maximum value of token sets and number of bits"""

        for this_set in self.tokens.keys():
            if this_set.strip() != "Search_OMEGA" and this_set.strip() != "max_Omega_size":
                val = len(self.tokens[this_set])

                # max is zero based!!!!, everything is zero based (gacode, intcode, gene_max)
                self.gene_max.append(val - 1)
                self.gene_length.append(math.ceil(math.log(val, 2)))

                if val == 1:
                    log.warn(f'Token {this_set} has the only option.')

    def any_block_diag(self):
        # find all OMEGA blocks
        control_list = self.template_text.splitlines()
        lines = control_list
        omega_starts = [idx for idx, element in enumerate(lines) if re.search(r"^\$OMEGA", element)]
        omega_ends = []

        for this_start in omega_starts:
            # if FIX (fix) do not add off diagonals
            rest_of_text = lines[this_start:]
            next_block_start = [idx for idx, element in enumerate(rest_of_text[1:]) if re.search(r"^\$", element)]
            if next_block_start is None:
                next_block_start = len(rest_of_text)
            else:
                next_block_start = next_block_start[0]
            this_omega_ends = next_block_start + this_start + 1
            omega_ends.append(this_omega_ends)
            cur_block = remove_comments(copy.copy(lines[this_start:this_omega_ends])).splitlines()
            # check for DIAG|BLOCK|FIX|SAME         # look for DIAG|BLOCK|FIX|SAME
            for this_line in cur_block:
                uline = this_line.upper()
                if uline.find("BLOCK") > 0:
                    return True, "BLOCK"
                if uline.find("DIAG") > 0:
                    return True, "DIAG"
                if uline.find("SAME") > 0:
                    return True, "SAME"
                if uline.find("FIX") > 0:
                    return True, "FIX"
        return False, "None"

    def _check_omega_search(self): 
        """
        see if Search_OMEGA and omega_band_width are in the token set
        if so, find how many bits needed for band width, and add that gene
        final gene in genome is omega band width, values 0 to max omega size -1
        Note that if submatrices are already defined with any BLOCK or DIAG, can't do omega_search"""

        if not options.search_omega_bands:
            return

        fix_omega_check = self.any_block_diag()

        if fix_omega_check[0]:
            log.warn(f"{fix_omega_check[1]}"
                        f" OMEGA STRUCTURE IS NOT COMPATIBLE WITH OMEGA search. Turning off OMEGA search.")

            options.search_omega_bands = False
            options.search_omega_sub_matrix = False

            return

        if options.search_omega_bands is False and options.search_omega_sub_matrix is True:
            log.warn(
                f"Cannot do omega sub matrix search without omega band search. Turning off omega submatrix search.")

            options.search_omega_sub_matrix = False

            return

        # this is the number of off diagonal bands (diagonal is NOT included)
        self.gene_max.append(options.max_omega_band_width)
        self.gene_length.append(math.ceil(math.log(options.max_omega_band_width + 1, 2)))

        log.message(f"Including search of band OMEGA, with width up to {options.max_omega_band_width}")

        self.Omega_band_pos = len(self.gene_max) - 1

        # OMEGA submatrices?
        if options.search_omega_sub_matrix:
            log.message(f"Including search for OMEGA submatrices, with size up to {options.max_omega_sub_matrix}")

            for i in range(options.max_omega_sub_matrix):
                self.gene_length.append(1)
                self.gene_max.append(1)
