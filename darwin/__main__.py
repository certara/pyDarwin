import sys
from darwin.run_search import run_search, run_search_in_folder

if __name__ == '__main__':
    if len(sys.argv) == 4:
        run_search(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        run_search_in_folder(sys.argv[1])
