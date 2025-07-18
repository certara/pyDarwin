import sys
import json
import math
import collections

from darwin.Log import log
from darwin.options import options
from darwin.omega_search import get_omega_block_masks
from darwin.DarwinError import DarwinError


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
            self.template_text = open(template_file, 'r', encoding='utf-8').read()

            log.message(f"Template file found at {template_file}")
        except Exception as error:
            log.error(str(error))
            log.error("Failed to open Template file: " + template_file)
            sys.exit()

        try:
            self.tokens = collections.OrderedDict(json.loads(open(tokens_file, 'r', encoding='utf-8').read()))

            for key, val in self.tokens.items():
                if type(val) == dict:
                    self.tokens[key] = [x for x in val.values()]

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

        # to be initialized by adapter
        self.theta_block = self.omega_block = self.sigma_block = []

        # initialized outside
        self.omega_band_pos = None

        self.template_text = options.apply_aliases(self.template_text)

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

    def get_search_space_coordinates(self) -> list:
        num_groups = [list(range(len(token_group))) for token_group in self.tokens.values()]

        if options.search_omega_blocks:
            for i in options.max_omega_search_lens:
                if options.max_omega_band_width is not None:
                    # if no submatrices add no-block mask as band_width = 0
                    start = 1 if options.search_omega_sub_matrix else 0

                    # need to add another group if searching on omega bands
                    num_groups.append(list(range(start, options.max_omega_band_width + 1)))

                # need to add another group if searching on omega submatrices
                num_groups.append(list(range(len(get_omega_block_masks(i)))))

        if not num_groups:
            raise DarwinError('The search space is empty')

        return num_groups

    def get_search_space_size(self) -> int:
        try:
            num_groups = self.get_search_space_coordinates()

            size = 1

            for x in num_groups:
                size *= len(x)

            return size
        except DarwinError:
            raise
        except:
            pass

        return -1
