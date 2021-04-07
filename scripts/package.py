# Purpose: Bags, tars, and zips the AIP.
# Dependencies: bagit.py, prepare_bag perl script

import os
import subprocess
import sys
from variables import move_error, scripts


# The AIP and AIP type (metadata or media) are passed as arguments from aip_av.py.
# AIP is used to identify the folder the script should work on.
# Both are used to construct the name of the AIP.
aip = sys.argv[1]
aip_type = sys.argv[2]

# Deletes any .DS_Store files because they cause errors with bag validation.
# They would have been deleted in aip_av.py, but can be regenerated while the script is running.
for root, dirs, files in os.walk('.'):
    for item in files:
        if item == '.DS_Store':
            os.remove(f'{root}/{item}')

# Bags the AIP folder in place.
# Both md5 and sha256 checksums are generated to guard against tampering.
subprocess.run(f'bagit.py --md5 --sha256 --quiet "{aip}"', shell=True)

# Renames the AIP folder to add the AIP type and '_bag' to the end.
# This is saved to a variable first since it is used a few more times in the script.
bag_name = f'{aip}_{aip_type}_bag'
os.replace(aip, bag_name)

# Validates the bag. If the bag is not valid, moves the AIP to an error folder, saves the validation error to a
# document in the error folder, and quits this script. The validation output is converted from a byte type to a
# string for easier formatting. The error document is formatted so each error is its own line.
validate = subprocess.run(f'bagit.py --validate --quiet "{bag_name}"', stderr=subprocess.PIPE, shell=True)

if 'invalid' in str(validate):
    move_error('bag_invalid', bag_name)
    with open(f'errors/bag_invalid/{aip}_bag_validation_error.txt', 'a') as error:
        lines = str(validate.stderr).split(';')
        for line in lines:    
            error.write(f'{line}\n\n')
    exit()

# Tars and zips the AIP using a Perl script.
# The script also adds the uncompressed file size to the filename.
# The tarred and zipped AIP is saved to the aips-to-ingest folder.
subprocess.run(f'perl "{scripts}/prepare_bag" "{bag_name}" aips-to-ingest', shell=True)
