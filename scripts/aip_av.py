# TODO: Update description of the script based on April 2021 changes.
"""Purpose: Creates AIPs from folders of digital audiovisual objects that are ready for ingest into the digital
preservation system (ARCHive).

Dependencies: bagit.py, md5deep, mediainfo, saxon, xmllint

Prior to running the script:

    1. The contents of each AIP should be in a folder named with the AIP ID.
    2. All AIP folders should be in a single folder (AIPs directory).

Script steps:

    1. Verifies the script arguments are correct.
    2. Makes folders for script outputs within the AIPs directory.
    3. Deletes unwanted file types.
    4. Determines if the AIP contains media or metadata files.
    5. Organizes the AIP contents into the AIP directory structure.
    6. Extracts technical metadata using MediaInfo.
    7. Converts technical metadata to PREMIS (preservation.xml) using stylesheets.
    8. Packages the AIPs: bag, tar, and zip.
    9. Makes a md5 manifest of all packaged AIPs.
"""

# TODO: Add optional argument for Hargrett.
# Script usage: python3 '/path/aip_av.py' '/path/aips-directory'

import datetime
import os
import subprocess
import sys
from variables import move_error, scripts


# Gets the AIPs directory from the script argument.
# The AIPs directory contains all the folders to be made into AIPs.
# Prints an error message and ends the script if the argument is missing.
try:
    aips_directory = sys.argv[1]
except IndexError:
    # TODO: more helpful error message.
    print('Incorrect number of arguments.')
    print("To run the script: python3 '/path/aip_av.py' '/path/aips-directory'")
    exit()

# Changes the current directory to the AIPs directory.
# Prints an error message and ends the script if the directory doesn't exist.
# TODO: also catch if it is a file instead of a folder
try:
    os.chdir(aips_directory)
except FileNotFoundError:
    print(f'The AIPs directory "{aips_directory}" does not exist.')
    print("To run the script: python3 '/path/aip_av.py' '/path/aips-directory'")
    exit()

# TODO: get department from optional argument or default of Russell if none.

# Starts counts for tracking script progress.
total_aips = len(os.listdir(aips_directory))
current_aip = 0

# Makes folders for script outputs in the AIPs directory, if they don't already exist.
if not os.path.exists('mediainfo-xml'):
    os.mkdir('mediainfo-xml')

if not os.path.exists('preservation-xml'):
    os.mkdir('preservation-xml')

if not os.path.exists('aips-to-ingest'):
    os.mkdir('aips-to-ingest')


# For one AIP at a time, runs the scripts for all of the workflow steps. If a known error occurs, the AIP is moved to
# a folder with the error name and the rest of the steps are not completed for that AIP. Checks if the AIP is still
# present before running each script in case it was moved due to an error in the previous script.
# TODO: make these functions instead of scripts.
# TODO: Add a csv log.
for aip in os.listdir(aips_directory):

    # Skips folders for script outputs.
    if aip == 'mediainfo-xml' or aip == 'preservation-xml' or aip == 'aips-to-ingest':
        continue

    # Updates the current AIP number and displays the script progress.
    current_aip += 1
    print(f'\n>>>Processing {aip} ({current_aip} of {total_aips}).')

    # TODO: for Hargrett, parse title from AIP ID and rename folder to AIP ID only [unless rename when package?].

    # Deletes files that don't contain one of the strings in the keep list.
    # Using a lowercase version of filename so the match isn't case sensitive.
    # TODO: add .m4a to keep
    keep = ['.dv', '.mov', '.mp3', '.mp4', '.wav', '.pdf', '.xml']
    for root, directories, files in os.walk(aip):
        for item in files:
            # TODO: test endswith instead of in.
            if not(any(s in item.lower() for s in keep)):
                os.remove(f'{root}/{item}')

    # If deleting the unwanted files left the AIP folder empty,
    # moves the AIP to an error folder and starts processing the next AIP.
    if len(os.listdir(aip)) == 0:
        move_error('all_files_deleted', aip)
        continue

    # Determines the AIP type (metadata or media) based on keywords in the filenames of the digital objects.
    # Using a lowercase version of filename so the match isn't case sensitive.
    # The AIP type is part of the AIP name, along with the AIP ID.
    for item in os.listdir(aip):
        # TODO: test endswith instead of in.
        if 'pdf' in item.lower() or 'xml' in item.lower():
            aip_type = 'metadata'
        else:
            aip_type = 'media'

    # Runs script to organize the AIP contents into the AIP directory structure.
    if aip in os.listdir('.'):
        subprocess.run(f'python3 "{scripts}/aip_directory.py" "{aip}"', shell=True)

    # Runs script to extract technical metadata from the files using MediaInfo.
    if aip in os.listdir('.'):
        subprocess.run(f'python3 "{scripts}/mediainfo.py" "{aip}" {aip_type}', shell=True)

    # Runs script to transform the MediaInfo XML into the PREMIS preservation.xml file.
    # TODO: work with Hargrett IDs and include Hargrett title.
    if aip in os.listdir('.'):
        subprocess.run(f'python3 "{scripts}/preservation_xml.py" "{aip}" {aip_type}', shell=True)

    # Runs script to bag the AIP, validate the bag, and tar and zip the AIP.
    if aip in os.listdir('.'):
        subprocess.run(f'python3 "{scripts}/package.py" "{aip}" {aip_type}', shell=True)

# Makes a MD5 manifest of all packaged AIPs in the aips-to-ingest folder using md5deep.
# The manifest is named current-date_manifest.txt and saved in the aips-to-ingest folder. 
# The manifest has one line per AIP, formatted md5<tab>filename
# Checks that aips-to-ingest is not empty (due to errors) before making the manifest.
os.chdir('aips-to-ingest')
current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
if not len(os.listdir()) == 0:
    subprocess.run(f'md5deep -b * > {current_date}_manifest.txt', shell=True)
else:
    print('Could not make manifest. aips-to-ingest is empty.')

print('\nScript is finished running.')
