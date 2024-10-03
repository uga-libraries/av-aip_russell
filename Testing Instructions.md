# Script Testing Instructions

Use the following instructions for thoroughly testing the aip_av.py script after making changes 
to verify it still works correctly with AIPs in the expected format and still catches all anticipated errors. 
In all scenarios, the script should print "Script is finished running." just before it ends. 
If it does not, that means an error was not handled correctly. 

## Testing Valid AIPs

### AIPs to include in the test suite
For each scenario, make one media and one metadata AIP. 
At least one media and metadata AIP should have the same base AIP ID, 
e.g., har-ua20-123_0001_media and harg-ua20-123_0001_metadata.

* An AIP with one file in an accepted format.
* An AIP with at least one file, and sometimes multiple files, in each of the accepted formats.
* An AIP with some files in accepted formats and some in unaccepted formats. 

### Things to check for
* The script output folders (aips-to-ingest, mediainfo-xml, preservation-xml) are made and have the expected content.
* No files in accepted formats were deleted.
* All files in unaccepted formats were deleted.
* A mediainfo.xml file was made for each AIP and has reasonable format identification information.  
* A valid preservation.xml file was made for each AIP and has the expected information.
* A valid bag with MD5 and SHA256 manifests was made for each AIP.
* The final version of the AIP in the aips-to-ingest folder is tarred and zipped, and includes the file size as part of the file name.
* The manifest in the aips-to-ingest folder includes all the AIPs.
* The log includes all AIPs, with a status of "Complete".

## Testing Error Handling

### AIPs to include in the test suite

1. An AIP that only contains files in unaccepted formats.
2. An AIP with a folder named "objects" within the AIP folder.
3. An AIP that is correct to use for test that require changing the script.

### Things to check for

Make the following errors with the script argument.
Each should cause an error message to display in the terminal and the script to quit.
* Do not include the AIPs directory.
* Include an AIPs directory that is not a valid path.

Make the following errors with the metadata.csv.
Each should cause an error message to display in the terminal and the script to quit.
* No metadata.csv in the aips_directory.
* The column names in the metadata.csv are not correct ('Department', 'Collection', 'Folder', 'AIP_ID', 'Title', 'Version').
* The department(s) do not match the GROUPS in configuration.py
* There is an AIP folder in the metadata.csv more than once.
* There are AIP folders in the metadata.csv that are not in the aips_directory.
* There are AIP folders in the aips_directory that are not in the metadata.csv.

Run the script on AIPs 1-2, which should result in the following:    
* AIP 1 is in an error folder named "all_files_deleted", and the AIP folder is empty.
* AIP 2 is in an error folder named "preexisting_objects_folder", and the contents are unchanged. 
* The aips-to-ingest, mediainfo-xml, and preservation-xml folders are empty.
* The error "Could not make manifest. aips-to-ingest is empty." is displayed in the terminal.
* All AIPs are in the log with a status matching the error folder name.

Use AIP 3 for the remaining tests, which require editing the code to force errors to occur. 
Run the tests one at a time, undoing the change to the code required for one test before making the change for the next test. 
When testing is complete, run the script on a valid AIP folder to confirm that all changes for the tests have removed correctly from the script.

In each scenario, verify the log has the correct status for the AIPs and that no manifest is made 
in addition to verifying the expected results detailed in each test description.

* Save a copy of the mediainfo.xml files for both AIPs to the mediainfo-xml folder prior to running the script. 
  The AIPs should be in an error folder named "preexisting_mediainfo_copy". 
  They will have a mediainfo.xml file, but not a preservation.xml file, in the AIP metadata folder. 
  The mediainfo.xml files that were in the mediainfo-xml folder should not be overwritten.


* Comment out the following code in the aip_av.py script, which is towards the end of the script, so it does not run. 
  The AIPs should be in an error folder named "no_mediainfo_xml". No mediainfo.xml or preservation.xml files will be made.
    ```
    # Extracts technical metadata from the files using MediaInfo.
    if aip_folder in os.listdir('.'):
        mediainfo(aip_folder, aip_id, aip_type)

* Edit the mediainfo-to-preservation.xslt to make an invalid preservation.xml. 
  Edit <dc:rights> so the supplied value is not a URL and delete required field <xsl:call-template name="aip-id"/> .
  The AIP should be in an error folder named "preservation_invalid".
  That folder will also contain a file with the preservation xml validation error.

* Edit the package() function in aip_av.py as shown below to add a line of code prior to bag validation 
  to delete the SHA256 manifest and cause the script to create invalid bags. 
  The AIPs should be in an error folder named "bag_invalid". 
  There should also be a text file for each AIP in the error folder with the error messages from validating, 
  which include a warning that manifest-sha256.txt exists in the manifest but not the file system 
  and checksum validation errors for sha256 and md5 for manifest-sha256.txt.
  There will be a mediainfo.xml and preservation.xml file in the AIP metadata folder and script output folders.
  
  ```
  # Validates the bag. If the bag is not valid, moves the AIP to an error folder, saves the validation error to a document in the error folder, and ends this function.
  os.remove(f'{bag_name}/manifest-sha256.txt')
  validate = subprocess.run(f'bagit.py --validate "{bag_name}"', stderr=subprocess.PIPE, shell=True)`
