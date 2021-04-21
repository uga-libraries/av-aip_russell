# Script for preparing a batch of Hargrett oral history AIPs for the aip-av.py script. A batch is transferred in a
# single bag to verify that no errors were introduced on transfer.

import bagit
import os
import re
import sys

# Gets the path to the bag for the batch from the script argument.
# If it is missing, prints an error message and quit the script.
try:
    bag_path = sys.argv[1]
except IndexError:
    print("The bag path, which is required, is missing.")
    print("To run the script: python3 /path/hargret-preprocessing.py /path/bag")

# Changes the current directory to the bag.
# If the bag path is not a valid path, prints an error message and quits the script.
try:
    os.chdir(bag_path)
except (FileNotFoundError, NotADirectoryError):
    print("The bag path is not valid path.")
    print("To run the script: python3 /path/hargrett-preprocessing.py /path/bag")

# Validate the bag and print the validation results.
# If the bag is not valid, quits the script.
# TODO: switch to using bagit.py.
try:
    bag_path.validate()
    print("Bag is valid")
except bagit.BagValidationError as e:
    print("Bag is not valid")
    print(e)

# Removes the batch of AIP folders from the bag by deleting the bag metadata files (text files), moving the contents
# of the data folder into the parent directory, and deleting the now-empty data folder.
for doc in os.listdir('.'):
    if doc.endswith('.txt'):
        os.remove(doc)

for item in os.listdir('data'):
    os.replace(f'data/{item}', item)

os.rmdir('data')
