"""Purpose: Creates AIPs from folders of digital audiovisual objects that are ready for ingest into the digital
preservation system (ARCHive). Works for all Russell audiovisual objects and Hargrett oral history collections.

Dependencies: bagit.py, md5deep, mediainfo, saxon, xmllint

Prior to running the script:

    1. The contents of each AIP should be in a folder named with the AIP title (Russell) or AIP ID_Title (Hargrett).
    2. Each AIP folder should contain all media or all metadata files.
    3. All AIP folders should be in a single folder (AIPs directory).

Script steps:

    1. Verifies the script argument (AIPs directory) is correct.
    2. Makes folders for script outputs within the AIPs directory.
    3. Deletes unwanted file types.
    4. Determines the department, AIP ID, and AIP title from the AIP folder and file formats.
    5. Organizes the AIP contents into the AIP directory structure.
    6. Extracts technical metadata using MediaInfo.
    7. Converts technical metadata to Dublin Core and PREMIS (preservation.xml) using a stylesheet.
    8. Packages the AIPs: bag, tar, and zip.
    9. Makes a md5 manifest of all packaged AIPs.

The script also generates a log of the AIPs processed and their final status, either an anticipated error or "complete".
"""

# Script usage: python3 'path/aip_av.py' 'path/aips_directory'

import csv
import datetime
import os
import re
import shutil
import subprocess
import sys
from configuration import *


def log(aip, message):
    """Saves the AIP name and a message (the error or that processing completed) to the log file,
    which is a CSV saved in the AIPs directory. """

    with open('log.csv', 'a', newline='') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow([aip, message])


def move_error(error_name, aip):
    """Moves the AIP folder to an error folder, named with the error, so the rest of the workflow steps are not run on
    the AIP. Also adds the AIP and the error to a log for easier staff review."""

    # Makes the error folder, if it does not already exist, and moves the AIP to that folder.
    if not os.path.exists(f'errors/{error_name}'):
        os.makedirs(f'errors/{error_name}')
    os.replace(aip, f'errors/{error_name}/{aip}')

    # Adds the error to a log in the AIPs directory.
    log(aip, error_name)


def check_argument(argument_list):
    """Verify the script argument aips_directory is present and a valid directory

    Parameters:
        argument_list: sys.argv list of script arguments

    Returns:
        aips_dir: the path to the folder which contains the folders to be made into AIPs
        error: a string with the error message or None if there were no errors
    """

    error = None
    aips_dir = None

    # Checks if the required argument (aips_directory) is present.
    # If it is not present, the argument_list will have the script name (len of 1).
    if len(argument_list) > 1:
        # Checks if the provided argument is a valid directory.
        if os.path.exists(argument_list[1]):
            aips_dir = argument_list[1]
        else:
            error = f"AIPs directory argument '{argument_list[1]}' is not a valid directory."
    else:
        error = "Required AIPs directory argument is missing."

    return aips_dir, error


def delete_files(aip_folder_name):
    """Deletes unwanted files based on their file extension."""

    # Deletes files if the file extension is not in the keep list.
    # Using a lowercase version of filename so the match isn't case sensitive.
    keep = ['.dv', '.m4a', '.mkv', '.mov', '.mp3', '.mp4', '.wav', '.pdf', '.xml']
    for root, directories, files in os.walk(aip_folder_name):
        for file in files:
            if not (any(file.lower().endswith(s) for s in keep)):
                os.remove(f'{root}/{file}')

    # If deleting the unwanted files left the AIP folder empty, moves the AIP to an error folder.
    if len(os.listdir(aip_folder_name)) == 0:
        move_error("all_files_deleted", aip_folder_name)


def aip_metadata(aip_folder_name):
    """Returns the department, AIP ID, and title based on the AIP folder name and file formats.
    If any values cannot be calculated, raises an error."""

    # Determines the AIP type (metadata or media) based on the file extension of the first digital object.
    # KNOWN ISSUE: assumes the folder only contains metadata or media files, not both.
    # Using a lowercase version of filename so the match isn't case sensitive.
    first_file = os.listdir(aip_folder_name)[0]
    if first_file.lower().endswith('.pdf') or first_file.lower().endswith('.xml'):
        aip_type = 'metadata'
    else:
        aip_type = 'media'

    # Determines the department based on the start of the AIP folder name.
    # If it does not start with an expected value, raises an error so processing can stop on this AIP.
    if aip_folder_name.startswith('har'):
        department = 'hargrett'
    elif aip_folder_name.startswith('rbrl'):
        department = 'russell'
    else:
        move_error('department_unknown', aip_folder_name)
        raise ValueError

    # For Hargrett, gets the identifier and title from the AIP folder name, which is formatted identifier_Title.
    # Then makes the AIP ID by adding the type (metadata or media) to the identifier.
    # If the AIP folder cannot be parsed, raises an error so processing can stop on this AIP.
    if department == "hargrett":
        try:
            regex = re.match('(har-ua[0-9]{2}-[0-9]{3}_[0-9]{4})_(.*)', aip_folder_name)
            aip_id = f'{regex.group(1)}_{aip_type}'
            title = regex.group(2)
        except AttributeError:
            move_error("aip_folder_name", aip_folder_name)
            raise AttributeError

    # For Russell, the title is the AIP folder, which is formatted identifier_lastname.
    # Then makes the AIP ID by getting the identifier from the AIP folder and adding the type (metadata or media).
    # If the AIP folder cannot be parsed, raises an error so processing can stop on this AIP.
    else:
        try:
            regex = re.match('([a-z0-9-]+)_', aip_folder_name)
            aip_id = f'{regex.group(1)}_{aip_type}'
            title = aip_folder_name
        except AttributeError:
            move_error("aip_folder_name", aip_folder_name)
            raise AttributeError

    return department, aip_id, title


def aip_directory(aip_folder_name, aip):
    """Makes the AIP directory structure (objects and metadata folder within the AIP folder),
    moves the digital objects to the objects folder, and renames the AIP folder to the AIP ID. """

    # Makes the objects folder within the AIP folder, if it doesn't exist. If there is already a folder named objects
    # in the first level within the AIP folder, moves the AIP to an error folder and ends this function. Do not want
    # to alter the original directory structure by adding to an original folder named objects.
    try:
        os.mkdir(f'{aip_folder_name}/objects')
    except FileExistsError:
        move_error('preexisting_objects_folder', aip_folder_name)
        return

    # Moves the contents of the AIP folder into the objects folder.
    for item in os.listdir(aip_folder_name):
        if item == 'objects':
            continue
        os.replace(f'{aip_folder_name}/{item}', f'{aip_folder_name}/objects/{item}')

    # Makes the metadata folder within the AIP folder.
    # Do not have to check if it already exists since everything is moved to the objects folder in the previous step.
    os.mkdir(f'{aip_folder_name}/metadata')

    # Renames the AIP folder to the AIP ID.
    os.replace(aip_folder_name, aip)


def mediainfo(aip):
    """Extracts technical metadata from the files in the objects folder using MediaInfo."""
    # KNOWN ISSUE: mediainfo can identify PDF versions but only identifies OHMS xml by the file extension.

    # Runs MediaInfo on the contents of the objects folder and saves the XML output to the metadata folder.
    # --'Output=XML' uses the XML structure that started with MediaInfo 18.03
    # --'Language=raw' outputs the size in bytes.
    subprocess.run(
        f'mediainfo -f --Output=XML --Language=raw "{aip}/objects" > "{aip}/metadata/{aip}_mediainfo.xml"', shell=True)

    # Copies the MediaInfo XML to a separate folder (mediainfo-xml) for staff reference.
    # If a file by that name is already in mediainfo-xml,
    #   moves the AIP to an error folder instead since the AIP may be a duplicate.
    if os.path.exists(f'mediainfo-xml/{aip}_mediainfo.xml'):
        move_error('preexisting_mediainfo_copy', aip)
    else:
        shutil.copy2(f'{aip}/metadata/{aip}_mediainfo.xml', 'mediainfo-xml')


def preservation_xml(aip, department, aip_title):
    """Creates PREMIS and Dublin Core metadata from the MediaInfo XML and saves it as a preservation.xml file."""

    # Paths to files used in the saxon command.
    media_xml = f'{aip}/metadata/{aip}_mediainfo.xml'
    xslt = f'{STYLESHEETS}/mediainfo-to-preservation.xslt'
    pres_xml = f'{aip}/metadata/{aip}_preservation.xml'

    # Arguments to add to the saxon command.
    args = f'aip-id={aip} department={department} title="{aip_title}" namespace={NAMESPACE}'

    # Makes the preservation.xml file from the mediainfo.xml using a stylesheet and saves it to the AIP's metadata
    # folder. If the mediainfo.xml is not present, moves the AIP to an error folder and ends this function.
    if os.path.exists(media_xml):
        subprocess.run(f'java -cp "{SAXON}" net.sf.saxon.Transform -s:"{media_xml}" -xsl:"{xslt}" -o:"{pres_xml}" {args}',
                       shell=True)
    else:
        move_error('no_mediainfo_xml', aip)
        return

    # Validates the preservation.xml against the requirements of the Libraries' digital preservation system (ARCHive).
    # Possible validation errors:
    #   preservation.xml was not made (failed to loaded)
    #   preservation.xml does not match the metadata requirements (fails to validate)
    validate = subprocess.run(f'xmllint --noout -schema "{STYLESHEETS}/preservation.xsd" "{pres_xml}"',
                              stderr=subprocess.PIPE, shell=True)

    # If the preservation.xml isn't valid, moves the AIP to an error folder and saves the validation error to a text
    # document in the error folder. If the preservation.xml is valid, copies the preservation.xml to another folder for
    # staff use.
    if 'failed to load' in str(validate) or 'fails to validate' in str(validate):
        move_error('preservation_invalid', aip)
        with open(f'errors/preservation_invalid/{aip}_preservationxml_validation_error.txt', 'a') as error:
            lines = str(validate.stderr).split('\\n')
            for line in lines:
                error.write(f'{line}\n\n')
    else:
        shutil.copy2(pres_xml, 'preservation-xml')


def package(aip):
    """Bags, tars, and zips the AIP. Renames the AIP folder to AIPID_bag."""

    # Deletes any .DS_Store files because they cause errors with bag validation. They would have been deleted by
    # delete_files() earlier in the script, but can be regenerated while the script is running.
    for root, dirs, files in os.walk('.'):
        for item in files:
            if item == '.DS_Store':
                os.remove(f'{root}/{item}')

    # Bags the AIP folder in place.
    # Both md5 and sha256 checksums are generated to guard against tampering.
    subprocess.run(f'bagit.py --md5 --sha256 --quiet "{aip}"', shell=True)

    # Renames the AIP folder to add the AIP type and '_bag' to the end.
    # This is saved to a variable first since it is used a few more times in the function.
    bag_name = f'{aip}_bag'
    os.replace(aip, bag_name)

    # Validates the bag. If the bag is not valid, moves the AIP to an error folder, saves the validation error to a
    # document in the error folder, and ends this function.
    validate = subprocess.run(f'bagit.py --validate "{bag_name}"', stderr=subprocess.PIPE, shell=True)

    if 'invalid' in str(validate):
        move_error('bag_invalid', bag_name)
        with open(f'errors/bag_invalid/{bag_name}_bag_validation_error.txt', 'a') as error:
            lines = str(validate.stderr).split(';')
            for line in lines:
                error.write(f'{line}\n\n')
        return

    # Tars and zips the AIP using a Perl script.
    # The script also adds the uncompressed file size to the filename.
    # The tarred and zipped AIP is saved to the aips-to-ingest folder.
    subprocess.run(f'perl "{PREPARE_BAG}" "{bag_name}" aips-to-ingest', shell=True)

    # Adds the AIP to the log for successfully completing, since this function is the last step.
    log(aip_folder, "Complete")


# Verifies the required script argument (aips_directory) is correct.
# If there are any errors, exits the script.
aips_directory, error_message = check_argument(sys.argv)
if error_message:
    print(error_message)
    print("To run the script: python3 'path/aip_av.py' 'path/aips_directory'")
    sys.exit()

# Changes the current directory to the AIPs directory.
os.chdir(aips_directory)

# Starts counts for tracking the script progress.
total_aips = len(os.listdir(aips_directory))
current_aip = 0

# Makes folders for the script outputs in the AIPs directory, if they don't already exist.
for directory in ['mediainfo-xml', 'preservation-xml', 'aips-to-ingest']:
    if not os.path.exists(directory):
        os.mkdir(directory)

# Makes a log file, with a header row, in the AIPs directory.
log("AIP Folder", "Status")

# For one AIP at a time, runs the functions for all of the workflow steps. If a known error occurs, the AIP is moved to
# a folder with the error name and the rest of the steps are not completed for that AIP. Checks if the AIP is still
# present before running each function in case it was moved due to an error in the previous function.
for aip_folder in os.listdir(aips_directory):

    # Skips folders for script outputs, the log file, and .DS_Store (temp file on Macs).
    if aip_folder in ['mediainfo-xml', 'preservation-xml', 'aips-to-ingest', 'log.csv', '.DS_Store']:
        continue

    # Updates the current AIP number and displays the script progress.
    current_aip += 1
    print(f'\n>>>Processing {aip_folder} ({current_aip} of {total_aips}).')

    # Deletes undesired files based on the file extension.
    if aip_folder in os.listdir('.'):
        delete_files(aip_folder)

    # Determines the department, AIP ID, AIP title from the AIP folder name and file formats.
    if aip_folder in os.listdir('.'):
        try:
            department, aip_id, title = aip_metadata(aip_folder)
        except (ValueError, AttributeError):
            continue

    # Organizes the AIP folder contents into the AIP directory structure.
    # After this step, the AIP folder is renamed to be the AIP ID.
    if aip_folder in os.listdir('.'):
        aip_directory(aip_folder, aip_id)

    # Extracts technical metadata from the files using MediaInfo.
    if aip_id in os.listdir('.'):
        mediainfo(aip_id)

    # Transforms the MediaInfo XML into the PREMIS preservation.xml file.
    if aip_id in os.listdir('.'):
        preservation_xml(aip_id, department, title)

    # Bags the AIP, validates the bag, and tars and zips the AIP.
    if aip_id in os.listdir('.'):
        package(aip_id)

# Makes a MD5 manifest of all packaged AIPs for each department in the aips-to-ingest folder using md5sum.
# The manifest has one line per AIP, formatted md5<tab>filename
# Change the current directory to aips-to-ingest so that no path information is included with the filename.
os.chdir('aips-to-ingest')
current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
# Checks that aips-to-ingest is not empty (due to script errors) before making the manifest.
if not len(os.listdir()) == 0:
    for file in os.listdir():

        # Runs md5sum and extracts the desired information (md5 filename) from the md5sum output.
        md5sum_output = subprocess.run(f"md5sum {file}", stdout=subprocess.PIPE, shell=True)
        fixity = bytes.decode(md5sum_output.stdout).strip()

        # Saves the fixity information to the correct department manifest.
        # The manifest is named current-date_department_manifest.txt and saved in the aips-to-ingest folder.
        if file.startswith("har"):
            with open(f"{current_date}_hargrett_manifest.txt", "a") as manifest:
                manifest.write(f"{fixity}\n")
        elif file.startswith("rbrl"):
            with open(f"{current_date}_russell_manifest.txt", "a") as manifest:
                manifest.write(f"{fixity}\n")
else:
    print('\nCould not make manifest. aips-to-ingest is empty.')


print('\nScript is finished running.')
