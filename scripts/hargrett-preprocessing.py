# Script for preparing a batch of Hargrett oral history AIPs for the aip-av.py script. A batch is transferred in a
# single bag to verify that no errors were introduced on transfer.

import bagit
import os
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

# The rest of the script removes the batch of AIP folders from the bag.

# Deletes the bag metadata files, which are all text files.
for doc in os.listdir('.'):
    if doc.endswith('.txt'):
        os.remove(doc)

# Moves the contents of the data folder (the AIP folders) into the parent directory.
for item in os.listdir('data'):
    os.replace(f'data/{item}', item)

# Deleting the now-empty data folder.
os.rmdir('data')
