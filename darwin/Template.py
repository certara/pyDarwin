import os
import sys
import re
import json
import math
from sympy import false
import collections
import subprocess

import darwin.utils as utils
from darwin.options import options

from darwin.Log import log


def _go_to_folder(folder: str):
    if folder:
        if not os.path.isdir(folder):
            os.mkdir(folder)

        log.message("Changing directory to " + folder)
        os.chdir(folder)


class Template:
    def __init__(self, template_file: str, tokens_file: str, options_file: str, folder: str = None):
        """
        Template contains all the results of the template file and the tokens, and the options
        Tokens are parsed to define the search space. The Template object is inherited by the model object
        """

        # if running in folder, options_file may be a relative path, so need to cd to the folder first
        _go_to_folder(folder)

        options.initialize(folder, options_file)

        # if folder is not provided, then it must be set in options
        if not folder:
            _go_to_folder(options.homeDir)

        log_file = os.path.join(options.homeDir, "messages.txt")

        if os.path.exists(log_file):
            os.remove(log_file)

        log.initialize(log_file)

        log.message(f"Options file found at {options_file}")

        try:
            self.TemplateText = open(template_file, 'r').read()

            log.message(f"Template file found at {template_file}")
        except Exception as error:
            log.error(str(error))
            log.error("Failed to open Template file: " + template_file)
            sys.exit()

        try:
            self.tokens = collections.OrderedDict(json.loads(open(tokens_file, 'r').read()))

            log.message(f"Tokens file found at {tokens_file}")
        except Exception as error:
            log.error(str(error))
            log.error("Failed to parse JSON tokens in " + tokens_file)
            sys.exit()

        self.gene_max = []  # zero based
        self.gene_length = []  # length is 1 based

        self._get_gene_length()
        self._check_omega_search()

        self.lastFixedTHETA, self.lastFixedETA, self.lastFixedEPS, THETABlock, OMEGABlock, SIGMABlock\
            = _get_fixed_params(self.TemplateText)

        # list of only the variable tokens in $THETA in template, will population with
        self.varTHETABlock = _get_variable_block(THETABlock)
        self.varOMEGABlock = _get_variable_block(OMEGABlock)
        self.varSIGMABlock = _get_variable_block(SIGMABlock)

    def _get_gene_length(self):
        """ argument is the token sets, returns maximum value of token sets and number of bits"""

        for this_set in self.tokens.keys():
            if this_set.strip() != "Search_OMEGA" and this_set.strip() != "max_Omega_size":
                val = len(self.tokens[this_set])
                # max is zero based!!!!, everything is zero based (gacode, intcode, gene_max)
                self.gene_max.append(val - 1)
                self.gene_length.append(math.ceil(math.log(val, 2)))

    def _check_omega_search(self):
        """see if Search_OMEGA and Omega_band_width are in the token set
        if so, find how many bits needed for band width, and add that gene
        final gene in genome is omega band width, values 0 to max omega size -1"""
        if "Search_OMEGA" in self.tokens.keys():
            self.search_omega_band = True
            if "max_Omega_size" in self.tokens.keys():
                self.omega_bandwidth = self.tokens['max_Omega_size']
                self.gene_max.append(self.omega_bandwidth - 1)
                self.gene_length.append(math.ceil(math.log(self.omega_bandwidth, 2)))
                log.message(f"Including search of band OMEGA, with width up to {self.omega_bandwidth - 1}")
                del self.tokens['max_Omega_size']
            else:
                log.message("Cannot find omega size in tokens set, but omega band width search request \n,"
                            " omitting omega band width search")
                # remove max_Omega_size and Search_OMEGA from token sets
            del self.tokens['Search_OMEGA']
        else:
            self.search_omega_band = false


def _get_fixed_params(template_text):
    NFixedTHETA, THETABlock = _get_fixed_block(template_text, "$THETA")
    NFixedOMEGA, OMEGABlock = _get_fixed_block(template_text, "$OMEGA")
    NFixedSIGMA, SIGMABlock = _get_fixed_block(template_text, "$SIGMA")

    return NFixedTHETA, NFixedOMEGA, NFixedSIGMA, THETABlock, OMEGABlock, SIGMABlock


def _get_variable_block(code):
    clean_code = utils.removeComments(code)
    lines = clean_code.splitlines()

    # remove any blanks
    while "" in lines:
        lines.remove("")

    var_block = []

    # how many $ blocks - assume only 1 (for now??)

    for line in lines:
        if re.search("{.+}", line) is not None:
            var_block.append(line)

    return var_block


def _get_fixed_block(code, key):
    nkeys = code.count(key)
    # get the block from NONMEM control/template
    # e.g., $THETA, even if $THETA is in several sections
    # were key is $THETA,$OMEGA,$SIGMA
    block = ""
    start = 0
    full_block = []

    for _ in range(nkeys):
        start = code.find(key, start)
        end = code.find("$", start + 1)
        block = block + code[start: end] + '\n'
        start = end
        # remove blank lines, and trim

    lines = block.splitlines()
    full_block.append(lines)
    fixed_count = 0

    for line in lines:
        # remove blanks, options and tokens, comments
        line = utils.removeComments(line).strip()
        # count fixed only, n
        # visual studio code shows warning for "\$" below, but that is just literal $ at beginning of line, eg., $THETA
        if (line != "" and (not (re.search("^{.+}", line)))) and not re.search("^\$.+", line):
            fixed_count += 1

    return fixed_count, full_block
