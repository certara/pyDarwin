import os
import sys
import json

class Options:
    def __init__(self):
        self._options = {}

        self._init_options(None, {})

    def __getitem__(self, key):
        return self._options[key]

    def get(self, key, default):
        return self._options.get(key, default)

    def _init_options(self, folder, opts: dict):
        self._options = opts

        self.homeDir = folder or self._options.get('homeDir')
        self.crash_value = self._options.get('crash_value', 99999999)

    def initialize(self, folder, options_file):
        if not os.path.exists(options_file):
            print(f"!!! Couldn't find options file '{options_file}', exiting")
            sys.exit()

        try:
            self._init_options(folder, json.loads(open(options_file, 'r').read()))
        except Exception as error:
            print('!!! ' + str(error))
            print(f"!!! Failed to parse JSON options in {options_file}, exiting")
            sys.exit()


options = Options()
