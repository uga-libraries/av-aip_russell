﻿"""Purpose: Creates AIPs from folders of digital audiovisual objects that are ready for ingest into the digital
preservation system (ARCHive). Works for all Russell audiovisual objects and Hargrett oral history collections.

Dependencies: bagit.py, md5deep, mediainfo, saxon, xmllint

Prior to running the script:

    1. The contents of each AIP should be in a folder named with the AIP ID (Russell) or AIP-ID_Title (Hargrett).
            Each AIP folder should contain all media or all metadata files.
    2. All AIP folders should be in a single folder (AIPs directory).

Script steps:

    1. Verifies the script argument (AIPs directory) is correct.
    2. Makes folders for script outputs within the AIPs directory.
    3. Determines the department, and for Hargrett the title, from the AIP folder.
    4. Deletes unwanted file types.
    5. Determines if the AIP contains media or metadata files.
    6. Organizes the AIP contents into the AIP directory structure.
    7. Extracts technical metadata using MediaInfo.
    8. Converts technical metadata to PREMIS (preservation.xml) using a stylesheet.
    9. Packages the AIPs: bag, tar, and zip.
   10. Makes a md5 manifest of all packaged AIPs.

The script also generates a log of the AIPs processed and their final status, either an anticipated error or "complete".
"""

# Script usage: python3 '/path/aip_av.py' '/path/aips-directory'

import csv
import datetime
import os
import shutil
import subprocess
import sys
from variables import *


def log(aip, message):
    """Saves the aip and a message (the error or that processing completed) to the log file, which is a CSV saved in
    the AIPs directory. This is a function, even though it is only a few lines, because it is used in multiple places
    in the script. """

    with open('log.csv', 'a', newline='') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow([aip, message])


def move_error(error_name, item):
    """Move the AIP folder to an error folder, named with the error, so the rest of the workflow steps are not run on
    the AIP. Also adds the AIP and the error to a log for easier staff review."""

    # Makes error folder and moves the AIP to that folder.
    if not os.path.exists(f'errors/{error_name}'):
        os.makedirs(f'errors/{error_name}')
    os.replace(item, f'errors/{error_name}/{item}')

    # Adds the error to a CSV in the AIPs directory.
    log(item, error_name)


def aip_metadata(aip_folder_name):
    """Returns the department, AIP ID, and title based on the AIP folder name.
    If any values cannot be calculated, raises an error."""

    # Determines the department based on the start of the AIP folder name.
    # If it does not start with an expected value, raises an error so processing can stop on this AIP.
    if aip_folder_name.startswith('harg'):
        department = 'hargrett'
    elif aip_folder_name.startswith('rbrl'):
        department = 'russell'
    else:
        move_error("department_unknown", aip_folder_name)
        raise ValueError

    # For Hargrett, gets the AIP ID and title from the AIP folder name and renames the folder to the AIP ID only.
    # If the AIP folder cannot be parsed, moves the AIP to an error folder and starts processing the next AIP.
    # For Russell, the AIP folder is the AIP ID and the title is None.
    if department == "hargrett":
        try:
            # todo: title can have underscores so need to use regex
            aip_id, title = aip_folder.split("_")
        except ValueError:
            move_error("aip_folder_name", aip_folder_name)
            raise ValueError
        os.replace(aip_folder, aip_id)
    else:
        aip_id = aip_folder_name
        title = None

    return department, aip_id, title


def delete_files(aip):
    """Deletes unwanted files based on their file extension and raises an error if no files are left."""

    # Deletes files if the file extension is not in the keep list.
    # Using a lowercase version of filename so the match isn't case sensitive.
    keep = ['.dv', '.m4a', '.mov', '.mp3', '.mp4', '.wav', '.pdf', '.xml']
    for root, directories, files in os.walk(aip):
        for file in files:
            if not (any(file.lower().endswith(s) for s in keep)):
                os.remove(f'{root}/{file}')

    # If deleting the unwanted files left the AIP folder empty, moves the AIP to an error folder.
    if len(os.listdir(aip)) == 0:
        move_error("all_files_deleted", aip)


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


def preservation_xml(aip, aip_type, department, aip_title=None):
    """Creates PREMIS and Dublin Core metadata from the MediaInfo xml and saves it as a preservation.xml file."""

    # Paths to files used in the saxon command.
    mediaxml = f'{aip}/metadata/{aip}_{aip_type}_mediainfo.xml'
    xslt = f'{stylesheets}/mediainfo-to-preservation.xslt'
    presxml = f'{aip}/metadata/{aip}_{aip_type}_preservation.xml'

    # Arguments to add to the saxon command. Always has type and department; only Hargrett has title.
    args = f'type={aip_type} department={department}'
    if aip_title:
        args += f' title={aip_title}'

    # Makes the preservation.xml file from the mediainfo.xml using a stylesheet and saves it to the AIP's metadata
    # folder. If the mediainfo.xml is not present, moves the AIP to an error folder and quits this script.
    if os.path.exists(mediaxml):
        subprocess.run(f'java -cp "{saxon}" net.sf.saxon.Transform -s:"{mediaxml}" -xsl:"{xslt}" -o:"{presxml}" {args}',
                       shell=True)
    else:
        move_error('no_mediainfo_xml', aip)
        exit()

    # Validates the preservation.xml against the requirements of the Libraries' digital preservation system (ARCHive).
    # Possible validation errors:
    #   preservation.xml was not made (failed to loaded)
    #   preservation.xml does not match the metadata requirements (fails to validate)
    validate = subprocess.run(f'xmllint --noout -schema "{stylesheets}/preservation.xsd" "{presxml}"',
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
        shutil.copy2(presxml, 'preservation-xml')


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
    subprocess.run(f'perl "{prepare_bag}" "{bag_name}" aips-to-ingest', shell=True)


# Gets the AIPs directory from the script argument.
# The AIPs directory contains all the folders to be made into AIPs.
# Prints an error message and ends the script if the argument is missing.
try:
    aips_directory = sys.argv[1]
except IndexError:
    print('The AIPs directory is missing and is a required argument.')
    print("To run the script: python3 '/path/aip_av.py' '/path/aips-directory' [department]")
    exit()

# Changes the current directory to the AIPs directory.
# Prints an error message and ends the script if the directory doesn't exist.
try:
    os.chdir(aips_directory)
except (FileNotFoundError, NotADirectoryError):
    print(f'The AIPs directory "{aips_directory}" does not exist.')
    print("To run the script: python3 '/path/aip_av.py' '/path/aips-directory' [department]")
    exit()

# Starts counts for tracking script progress.
total_aips = len(os.listdir(aips_directory))
current_aip = 0

# Makes folders for script outputs in the AIPs directory, if they don't already exist.
for directory in ['mediainfo-xml', 'preservation-xml', 'aips-to-ingest']:
    if not os.path.exists(directory):
        os.mkdir(directory)

# Makes a log file, with a header row, in the AIPs directory.
log("AIP", "Status")

# For one AIP at a time, runs the scripts for all of the workflow steps. If a known error occurs, the AIP is moved to
# a folder with the error name and the rest of the steps are not completed for that AIP. Checks if the AIP is still
# present before running each script in case it was moved due to an error in the previous script.
for aip_folder in os.listdir(aips_directory):

    # Skips folders for script outputs.
    if aip_folder in ['mediainfo-xml', 'preservation-xml', 'aips-to-ingest', 'log.csv']:
        continue

    # Updates the current AIP number and displays the script progress.
    current_aip += 1
    print(f'\n>>>Processing {aip_folder} ({current_aip} of {total_aips}).')

    # Determines the department, AIP ID, and for Hargrett the title, from the AIP folder name.
    try:
        department, aip_id, title = aip_metadata(aip_folder)
    except ValueError:
        continue

    # Deletes files if the file extension is not in the keep list.
    if aip_id in os.listdir('.'):
        delete_files(aip_id)

    # Determines the AIP type (metadata or media) based on the file extensions of the digital objects.
    # Known issue: for this to work, the folder must only contain metadata or media files, not both.
    # Using a lowercase version of filename so the match isn't case sensitive.
    # The AIP type is part of the AIP name, along with the AIP ID.
    if aip_id in os.listdir('.'):
        for file in os.listdir(aip_id):
            if file.lower().endswith('.pdf') or file.lower().endswith('.xml'):
                aip_type = 'metadata'
            else:
                aip_type = 'media'

    # Organizes the AIP contents into the AIP directory structure.
    if aip_id in os.listdir('.'):
        aip_directory(aip_id)

    # Extracts technical metadata from the files using MediaInfo.
    if aip_id in os.listdir('.'):
        mediainfo(aip_id, aip_type)

    # Transforms the MediaInfo XML into the PREMIS preservation.xml file.
    # Only include optional title parameter for Hargrett.
    if aip_id in os.listdir('.'):
        if department == 'hargrett':
            preservation_xml(aip_id, aip_type, department, title)
        else:
            preservation_xml(aip_id, aip_type, department)

    # Bags the AIP, validates the bag, and tars and zips the AIP.
    if aip_id in os.listdir('.'):
        package(aip_id, aip_type)

    # Adds the AIP to the log for successfully completing.
    log(aip_id, "Complete")

# Makes a MD5 manifest of all packaged AIPs for each department in the aips-to-ingest folder using md5deep.
# The manifest is named current-date_department_manifest.txt and saved in the aips-to-ingest folder.
# The manifest has one line per AIP, formatted md5<tab>filename
# Checks that aips-to-ingest is not empty (due to errors) before making the manifest.
os.chdir('aips-to-ingest')
current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
if not len(os.listdir()) == 0:
    if any(file.startswith('harg') for file in os.listdir('.')):
        subprocess.run(f'md5deep -b * > {current_date}_hargrett_manifest.txt', shell=True)
    if any(file.startswith('rbrl') for file in os.listdir('.')):
        subprocess.run(f'md5deep -b * > {current_date}_russell_manifest.txt', shell=True)
else:
    print('Could not make manifest. aips-to-ingest is empty.')

print('\nScript is finished running.')
