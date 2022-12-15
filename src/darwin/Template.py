import re
import sys
import json
import math
import collections
import darwin.utils
from darwin.Log import log

from darwin.options import options 


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
        if self.check_for_prior():
            log.message(f"$PRIOR found in template, PRIOR routine is not supported, exiting")
            sys.exit()
        if options.search_omega_bands and not self.check_for_multiple_probs():
            log.message(f"Search Omega bands is not supported with multiple $PROBs, exiting")
            sys.exit()

        self.template_text = options.apply_aliases(self.template_text)
    def check_for_prior(self):

        all_lines = darwin.utils.remove_comments(self.template_text)
       # all_lines = all_lines.splitlines()
        any_prior = re.search(r"\$PRIOR", all_lines, flags=re.MULTILINE)#  re.findall("^\$THETA", all_lines
        if any_prior is None:
            return False
        else:
            return True

    def check_for_multiple_probs(self):
        # can't have multiple problems, issues with counting $OMEGA and
        # putting all $OMEGA at end of control
        # next version, put $OMEGAs back in original place?
        all_lines = darwin.utils.remove_comments(self.template_text)
        # all_lines = all_lines.splitlines()
        prob_lines = re.findall(r"\$PROB", all_lines)  #
        if len(prob_lines) > 1:
            return False
        else:
            return True

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

    def _check_omega_search(self): 
        """
        see if Search_OMEGA and omega_band_width are in the token set
        if so, find how many bits needed for band width, and add that gene
        final gene in genome is omega band width, values 0 to max omega size -1"""
        if options.search_omega_bands:
            # this is the number of off diagonal bands (diagonal is NOT included)
            self.gene_max.append(options.max_omega_band_width)
            self.gene_length.append(math.ceil(math.log(options.max_omega_band_width + 1, 2)))

            log.message(f"Including search of band OMEGA, with width up to {options.max_omega_band_width}")
            self.Omega_band_pos = len(self.gene_max) - 1
            # OMEGA submatrices??
            if options.search_omega_sub_matrix:
                log.message(f"Including search for OMEGA submatrices, with size up to {options.max_omega_sub_matrix}")
                for i in range(options.max_omega_sub_matrix):
                    self.gene_length.append(1)
                    self.gene_max.append(1)
