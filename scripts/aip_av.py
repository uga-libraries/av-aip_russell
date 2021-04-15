﻿# TODO: Update description of the script based on April 2021 changes.
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
import shutil
import subprocess
import sys
from variables import move_error, scripts


def move_error(error_name, item):
    """Move the AIP folder to an error folder, named with the error, so the rest of the workflow steps are not run on
    the AIP. """
    if not os.path.exists(f'errors/{error_name}'):
        os.makedirs(f'errors/{error_name}')
    os.replace(item, f'errors/{error_name}/{item}')


def aip_directory(aip):
    """Makes the AIP directory structure (objects and metadata folder within the AIP folder) and moves the digital
    objects to the objects folder. """

    # Makes the objects folder within the AIP folder, if it doesn't exist. If there is already a folder named objects
    # in the first level within the AIP folder, moves the AIP to an error folder and quits this script. Do not want
    # to alter the original directory structure by adding to an original folder named objects.
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


def mediainfo(aip, aip_type):
    """Extracts technical metadata from the files in the objects folder using MediaInfo."""
    # Runs MediaInfo on the contents of the objects folder and saves the xml output to the metadata folder.
    # --'Output=XML' uses the XML structure that started with MediaInfo 18.03
    # --'Language=raw' outputs the size in bytes.
    subprocess.run(
        f'mediainfo -f --Output=XML --Language=raw "{aip}/objects" > "{aip}/metadata/{aip}_{aip_type}_mediainfo.xml"',
        shell=True)

    # Copies mediainfo xml to a separate folder (mediainfo-xml) for staff reference.
    # If a file by that name is already in mediainfo-xml,
    #   moves the AIP to an error folder instead since the AIP may be a duplicate.
    if os.path.exists(f'mediainfo-xml/{aip}_{aip_type}_mediainfo.xml'):
        move_error('preexisting_mediainfo_copy', aip)
    else:
        shutil.copy2(f'{aip}/metadata/{aip}_{aip_type}_mediainfo.xml', 'mediainfo-xml')


def preservation_xml(aip, aip_type):
    """Creates PREMIS and Dublin Core metadata from the MediaInfo xml and saves it as a preservation.xml file."""
    # Makes the preservation.xml file from the mediainfo.xml using a stylesheet and saves it to the AIP's metadata folder.
    # If the mediainfo.xml is not present, moves the AIP to an error folder and quits this script.
    mediainfo = f'{aip}/metadata/{aip}_{aip_type}_mediainfo.xml'
    stylesheet = f'{stylesheets}/mediainfo-to-preservation.xslt'
    preservationxml = f'{aip}/metadata/{aip}_{aip_type}_preservation.xml'

    if os.path.exists(mediainfo):
        subprocess.run(
            f'java -cp "{saxon}" net.sf.saxon.Transform -s:"{mediainfo}" -xsl:"{stylesheet}" -o:"{preservationxml}" type={aip_type}',
            shell=True)
    else:
        move_error('no_mediainfo_xml', aip)
        exit()

    # Validates the preservation.xml against the requirements of the UGA Libraries' digital preservation system (ARCHive).
    # Possible validation errors:
    #   preservation.xml was not made (failed to loaded)
    #   preservation.xml does not match the metadata requirements (fails to validate)
    validate = subprocess.run(f'xmllint --noout -schema "{stylesheets}/preservation.xsd" "{preservationxml}"',
                              stderr=subprocess.PIPE, shell=True)

    # If the preservation.xml isn't valid, moves the AIP to an error folder and saves the validation error to a text
    # document in the error folder. If the preservation.xml is valid, copies the preservation.xml to local server for
    # staff use.
    if 'failed to load' in str(validate) or 'fails to validate' in str(validate):
        move_error('preservation_invalid', aip)
        with open(f'errors/preservation_invalid/{aip}_preservationxml_validation_error.txt', 'a') as error:
            lines = str(validate.stderr).split('\\n')
            for line in lines:
                error.write(f'{line}\n\n')
    else:
        shutil.copy2(preservationxml, 'preservation-xml')


def package(aip, aip_type):
    """Bags, tars, and zips the AIP."""
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
