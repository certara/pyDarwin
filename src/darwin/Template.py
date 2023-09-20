import sys
import json
import math
import collections
import os
import re

from darwin.Log import log
from darwin.options import options
from darwin.omega_search import get_omega_block_masks


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
    def _file_check(self, template_file, tokens_file) -> bool:
        """
        Generates list of "target" tokens from the tokens file and of "source" tokens from
        the template and tokens file. Checks to see if all source tokens are available in the target
        tokens list. Also prints a warning if the number of text string in a token set are not
        consistent.
        Returns True if consistent tokens/template is found, otherwise False
        """
        if os.path.isfile(tokens_file):
            target_tokens = self._get_source_tokens(tokens_file)
            token_file_tokens = self._get_tokenfile_tokens(tokens_file)
        else:
            print("Cannot find " + tokens_file)
        if os.path.isfile(template_file):
            source_keys = self._get_target_keys(template_file)
        else:
            print("Cannot find " + template_file)
        source_keys.extend(token_file_tokens)
        # are all of all_keys in full_tokens
        # and for each key in all_keys, see if it is i keys[]
        missing = []
        for this_token in source_keys:
            if not (any(this_token in i for i in target_tokens)):
                missing.append(this_token)
        if len(missing) > 0:
            log.error("Text string for following tokens sets missing in " + missing[0])
            for i in range(1, len(missing)):
                log.error("and " + missing[i])
            return False
        else:
            return True

    def _get_tokenfile_tokens(self, token_file) -> list:
        f = open(token_file)
        tokens = json.load(f)
        keys = list(tokens.keys())
        foundtokens = []
        search_exp = "\{.+\[[1-9].*\]\}"
        for this_key in keys:
            this_group = tokens[this_key]
            for this_set in this_group:
                for this_text in this_set:
                    if re.search(";", this_text) is not None:
                        this_text = this_text[0:re.search(";", this_text).regs[0][0]]
                    pos = re.search(search_exp, this_text)
                    if pos is not None:
                        foundtokens.append(this_text[re.search(search_exp, this_text).regs[0][0]:
                                                     re.search(search_exp, this_text).regs[0][1]])
        return foundtokens

    def _get_target_keys(self, template_file) -> list:
        f = open(template_file)
        text = f.read()
        token_keys = re.findall("\{.+?\[[\s*1-9.*?]\s*?\]\}", text)
        return token_keys

    def _get_source_tokens(self, token_file) :
        f = open(token_file)
        tokens = json.load(f)
        keys = list(tokens.keys())
        full_tokens = []
        for this_key in keys:
            this_group = tokens[this_key]
            # find the minimum # of text string in any token set
            # give warning if not all equal
            n_text = len(this_group[0])
            for new_group in this_group[1:]:
                new_n_text = len(new_group)
                if not new_n_text == n_text:
                    log.error("Warning: Inconsistent number of text strings for " + this_key + " in " + token_file)
                if new_n_text < n_text:
                    n_text = len(new_group)
            for this_text in range(1, (n_text + 1)):
                # check each token, e.g., ADVAN[1], then ADVAN[3] is OK in template, but warning
                # note that the token text are, by definition sequential in the tokens file, but there need not be
                # a matching one in template - but give a warning for this.
                text_string = "{" + this_key + "[" + str(this_text) + "]}"
                full_tokens.append(text_string)
        return full_tokens

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
        if self._file_check(template_file, tokens_file):
            log.message(f"Tokens in template and tokens file agree")
        else:
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
            log.error('The search space is empty - exiting')
            exit('The search space is empty')

        return num_groups
