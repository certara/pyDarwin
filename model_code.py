import math


class model_code:
    """
    class for model code, just to keep straight whether this is full binary, minimal binary or integer
    and to interconvert between them
    """

    def __init__(self, code, which_type, gene_max, length):
        assert which_type in ["FullBinary", "MinBinary", "Int", "None"],\
            "Type of code must be one of 'FullBinary','MinBinary','Int'"
        assert isinstance(code, list), "'code' must list of integers or (0|1 if FullBinary or MinBinary)"
        assert isinstance(gene_max, list), "'gene_max' must list of integers "
        assert isinstance(length, list), "'length' must list of integers "

        self.max = gene_max
        self.length = length
        self.type = which_type
        if which_type == "FullBinary":
            self.FullBinCode = code
            self.convert_full_bin_int()
            self.convert_int_min_bin()

        if which_type == "MinBinary":
            self.MinBinCode = code
            self.convert_min_bin_int()
            self.convert_int_full_bin()

        if which_type == "Int":
            self.IntCode = code
            self.convert_int_min_bin()
            self.convert_int_full_bin()

    def convert_full_bin_int(self):
        """converts a "full binary" (e.g., from GA to integer (used to select token sets))
        arguments are:
        bin_pop - population of binaries
        gene_max - integer list,maximum value- number of tokens sets in that token group
        length - integer list, how long each gene is
        return integer array of which token goes into this model"""

        start = 0
        phenotype = []
        for thisNumBits, this_max in zip(self.length, self.max):
            # max = gene_max[gene_num]  # user specified maximum value of gene - how many token sets are there, max is 0 based?
            thisGene = self.FullBinCode[start:start + thisNumBits]
            baseInt = int("".join(str(x) for x in thisGene), 2)
            maxValue = 2 ** len(
                thisGene) - 1  ## # zero based, max number possible from bit string , 0 based (has the -1)
            maxnumDropped = maxValue - this_max  # maximum possoible number of indexes that must be skipped to get max values to fit into fullMax possible values.
            numDropped = math.floor(maxnumDropped * (baseInt / maxValue))
            full_int_val = baseInt - numDropped
            phenotype.append(full_int_val)  ## value here???
            start += thisNumBits
        self.IntCode = phenotype
        return

    def int2bin(self, n, length):
        value = bin(n)[2:]
        value = list(value.rjust(length, "0"))
        value = map(int, value)
        value = list(value)
        return value

    def convert_int_full_bin(self):
        """converts an integer arry to "full binary" (e.g., from integer (used to select token sets) back to GA compatible code, opposite of convert_full_bin_int)
        arguments are:
        int_pop - population of integers
        gene_max - integer list,maximum value- number of tokens sets in that token group
        length - integer list, how long each gene is
        return array of binaries compatible with GA"""

        result = []
        for baseInt, this_max, this_length in zip(self.IntCode, self.max, self.length):
            maxValue = (2 ** this_length) - 1  # zero based
            maxnumAdded = maxValue - this_max  # max is zero based
            numAdded = math.floor(maxnumAdded * (baseInt / (maxValue - maxnumAdded)))
            full_int_val = baseInt + numAdded
            full_bin_val = self.int2bin(full_int_val, this_length)

            result.extend(full_bin_val)
        self.FullBinCode = result
        return

    def convert_min_bin_int(self):  # bin_pop,max,length):
        """converts a "minimal binary" (e.g., used for downhill, just the integer value converted to binary - doesn't fill in the entire n bit array)
        arguments are:
        bin_pop - population of minimal binaries
        max - integer list,maximum value- number of tokens sets in that token group
        length - integer list, how long each gene is
        return integer array of which token goes into this model"""
        start = 0
        result = []
        for this_gene, this_max in zip(self.length, self.max):
            # max is 0 based, everything is zero based
            last = start + this_gene
            binary = self.MinBinCode[start:last]
            string_ints = [str(int) for int in binary]
            x = "".join(string_ints)
            int_val = int(x, 2)
            start = last
            if int_val > this_max:  # int_val and this_max are both zero based
                int_val -= this_max - 1  # e.g if 1,1, converts to 3, if max is 2 (3 values, 0,1,2) then rolls over to 0, so need to subtractg one more
                # of value is 7 and max is 4 (5 options), should wrap to 2
            result.append(int_val)
        self.IntCode = result
        return

    def convert_int_min_bin(self):
        """converts an integer arry to "minimal binary"  (e.g., used for downhill, just the integer value converted to binary - doesn't fill in the entire n bit array)"""
        full_results = []
        cur_gene = 0
        for this_length in self.length:
            this_gene = self.IntCode[cur_gene]
            full_results.extend(self.int2bin(this_gene, this_length))
            cur_gene += 1
        self.MinBinCode = full_results
        return
