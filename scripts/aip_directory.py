# Purpose: Makes the AIP directory structure (objects and metadata folder within the AIP folder) and moves the
# digital objects to the objects folder.

import os
import sys
from variables import move_error

# The AIP is passed as arguments from aip_av.py.
# It is used to identify the folder the script should work on.
aip = sys.argv[1]

# Makes the objects folder within the AIP folder, if it doesn't exist. If there is already a folder named objects in
# the first level within the AIP folder, moves the AIP to an error folder and quits this script. Do not want to alter
# the original directory structure by adding to an original folder named objects.
try:
    os.mkdir(f'{aip}/objects')
except FileExistsError:
    move_error('preexisting_objects_folder', aip)
    exit()

# Moves the contents of the AIP folder into the objects folder.
# Skips the objects folder because it is an error to try to move something into itself.
for item in os.listdir(aip):
    if item == 'objects':
        continue
    os.replace(f'{aip}/{item}', f'{aip}/objects/{item}')
  
# Makes the metadata folder within the AIP folder.
# Do not have to check if it already exists since everything is moved to the objects folder in the previous step.
os.mkdir(f'{aip}/metadata')
