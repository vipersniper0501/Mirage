import os
import sys
import hashlib
from platform import uname

try:
    Path = sys.argv[1]
except Exception:
    Path = "./"

BUF_SIZE = 65536

# Recursively traverse through the OS from the specified path
# and append found files/directories to Names_Hashes along with the hash of the
# file.

Names_Hashes = {}


def Hash_Search_File():
    for root, d_names, f_names in os.walk(Path):
        print("OS Walk Result:")
        print(root, d_names, f_names)
        for f in f_names:
            sha256 = hashlib.sha256()
            print(f)
            try:
                with open(os.path.join(root, f), 'rb') as file:
                    while True:
                        data = file.read(BUF_SIZE)
                        if not data:
                            break
                        sha256.update(data)
            except Exception as e:
                print(
                    f"File '{f}' was found but could not be accessed because of the following exception: {e}"
                )
            Names_Hashes[os.path.join(root, f)] = sha256.hexdigest()
    print(Names_Hashes)


if __name__ == "__main__":
    Hash_Search_File()
