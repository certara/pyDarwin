import math

_code_separator = ', '


def _code_to_str(code: list) -> str:
    return _code_separator.join(str(x) for x in code)


def _restore_code(stored) -> list:
    if type(stored) != list:
        stored = [int(x) for x in stored.split(_code_separator)]

    return stored


class ModelCode:
    """
    Class for model code, just to keep straight whether this is full binary, minimal binary, or integer
    and to interconvert between them.
    """

    @classmethod
    def from_full_binary(cls, code: list, gene_max: list, length: list):
        """
        Create ModelCode object from “full binary”
        """

        res = cls()

        # it may be an instance of deap.Individual - converting to a regular list
        res.FullBinCode = []
        res.FullBinCode.extend(code)

        res._convert_full_bin_int(gene_max, length)
        res._convert_int_min_bin(length)

        return res

    @classmethod
    def from_min_binary(cls, code: list, gene_max: list, length: list):
        """
        Create ModelCode object from “minimal binary”
        """

        res = cls()

        res.MinBinCode = code
        res._convert_min_bin_int(gene_max, length)
        res._convert_int_full_bin(gene_max, length)

        return res

    @classmethod
    def from_int(cls, code: list, gene_max: list, length: list):
        """
        Create ModelCode object from integers
        """

        res = cls()

        # numpy.int32 is not JSON serializable - converting to python int
        int_code = [int(x) for x in code]

        res.IntCode = int_code
        res._convert_int_min_bin(length)
        res._convert_int_full_bin(gene_max, length)

        return res

    def to_dict(self):
        return {
            'IntCode': _codeto_str(self.IntCode),
            'MinBinCode': _code_to_str(self.MinBinCode),
            'FullBinCode': _code_to_str(self.FullBinCode)
        }

    @classmethod
    def from_dict(cls, src: dict):
        res = cls()

        res.IntCode = _restore_code(src['IntCode'])
        res.MinBinCode = _restore_code(src['MinBinCode'])
        res.FullBinCode = _restore_code(src['FullBinCode'])

        return res

    def _convert_full_bin_int(self, gene_max: list, length: list):
        """
        Converts a "full binary" (e.g., from GA to integer (used to select token sets))

        :param gene_max: integer list, maximum number of token sets in that token group
        :param length: integer list, how long each gene is

        Returns an integer array of which token goes into this model.
        """

        start = 0

        phenotype = []

        for this_num_bits, this_max in zip(length, gene_max):
            this_gene = self.FullBinCode[start:start + this_num_bits] or [0]
            base_int = int("".join(str(x) for x in this_gene), 2)
            max_value = 2 ** len(this_gene) - 1  # zero based, max number possible from bit string, 0 based (has the -1)
            # maximum possible number of indexes that must be skipped to get max values
            # to fit into fullMax possible values.
            max_num_dropped = max_value - this_max
            num_dropped = math.floor(max_num_dropped * (base_int / max_value))
            full_int_val = base_int - num_dropped

            phenotype.append(full_int_val)  # value here???

            start += this_num_bits

        self.IntCode = phenotype

        return

    def _convert_int_full_bin(self, gene_max: list, length: list):
        """
        Converts an integer array to "full binary"
        back to GA compatible code, opposite of convert_full_bin_int).

        :param gene_max: integer list, maximum number of token sets in that token group;
        :param length: integer list, how long each gene is.

        Returns array of binaries compatible with GA.
        """

        result = []

        for baseInt, this_max, this_length in zip(self.IntCode, gene_max, length):
            max_value = (2 ** this_length) - 1  # zero based
            max_num_added = max_value - this_max  # max is zero based

            num_added = 0

            if this_max != 0:
                num_added = math.floor(max_num_added * (baseInt / (max_value - max_num_added)))

            full_int_val = baseInt + num_added
            full_bin_val = _int_to_bin(full_int_val, this_length)

            result.extend(full_bin_val)

        self.FullBinCode = result

    def _convert_min_bin_int(self, gene_max: list, length: list):
        """
        Converts a "minimal binary" (e.g., used for downhill, just the integer value converted to binary - doesn't fill
        in the entire n bit array).
        Returns integer array of which token goes into this model.
        """
        start = 0
        result = []
        for this_gene, this_max in zip(length, gene_max):
            # max is 0 based, everything is zero based
            last = start + this_gene
            binary = self.MinBinCode[start:last] or [0]
            string_ints = [str(i) for i in binary]
            x = "".join(string_ints)
            int_val = int(x, 2)
            start = last

            if int_val > this_max:  # int_val and this_max are both zero based
                # e.g. if 1,1, converts to 3, if max is 2 (3 values, 0,1,2)
                # then rolls over to 0, so need to subtract one more
                int_val -= this_max - 1
                # of value is 7 and max is 4 (5 options), should wrap to 2

            result.append(int_val)

        self.IntCode = result

    def _convert_int_min_bin(self, length: list):
        """
        Converts an integer array to "minimal binary" (e.g., used for downhill, just the integer value converted
        to binary - doesn't fill in the entire n bit array).
        """
        full_results = []
        cur_gene = 0

        for this_length in length:
            this_gene = self.IntCode[cur_gene]
            full_results.extend(_int_to_bin(this_gene, this_length))
            cur_gene += 1

        self.MinBinCode = full_results


def _int_to_bin(n, length):
    value = bin(n)[2:]
    value = list(value.rjust(length, "0"))
    value = map(int, value)
    value = list(value)

    return value
