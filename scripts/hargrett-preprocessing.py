"""Script for preparing a batch of Hargrett oral history AIP folders for the aip-av.py script. A batch of folders to be
transformed into AIPs is transferred to Russell in a single bag to verify that no errors were introduced during
transfer. This script validates the bag and, if it is valid, removes the AIP folders from the transfer bag. If the
bag is not valid, the script prints the validation error and ends. """

# Script usage: python3 path/hargrett-preprocessing.py path/transfer_bag

import os
import subprocess
import sys

# Gets the path to the bag for the batch from the script argument.
# If it is missing, prints an error message and quits the script.
try:
    bag_path = sys.argv[1]
except IndexError:
    print("The bag path, which is required, is missing.")
    print("To run the script: python3 path/hargrett-preprocessing.py path/bag")
    exit()

# Changes the current directory to the bag directory.
# If the bag path is not a valid path, prints an error message and quits the script.
try:
    os.chdir(bag_path)
except (FileNotFoundError, NotADirectoryError):
    print("The provided bag path is not valid path:", bag_path)
    print("To run the script: python3 path/hargrett-preprocessing.py path/bag")
    exit()

# Validates the bag and prints the validation results.
# If the bag is not valid, quits the script.
validate = subprocess.run(f'bagit.py --validate "{bag_path}"', stderr=subprocess.PIPE, shell=True)
if 'invalid' in str(validate):
    print("\nBag is not valid. Details follow:")
    print(validate)
    print("\nThe script will quit.")
    exit()
else:
    print("\nBag is valid")

# The rest of the script removes the batch of AIP folders from the transfer bag.
# The end result is a folder (AIPs directory) which contains all the folders to be made into AIPs.

# Deletes the bag metadata files, which are all text files directly within the bag.
# After these are deleted, the only thing left is the data folder which contains the AIP folders.
for doc in os.listdir('.'):
    if doc.endswith('.txt'):
        os.remove(doc)

# Moves the contents of the data folder (the AIP folders) into the parent directory.
for item in os.listdir('data'):
    os.replace(f'data/{item}', item)

# Deletes the now-empty data folder.
os.rmdir('data')

print("\nScript is complete. AIPs directory should be ready for av_aip.py script.")
