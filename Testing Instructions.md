# Script Testing Instructions

Use the following instructions for thoroughly testing the aip_av.py script after making changes to verify it still works correctly with AIPs in the expected format and still catches all anticipated errors. In all scenarios, the script should print "Script is finished running." just before it ends. If it does not, that means an error was not handled correctly. 

## Testing Valid AIPs

###AIPs to include in the test suite
For each scenario, make one metadata and one media AIP. At least one media and metadata AIP should have the same base AIP ID, e.g., har-ua20-123_0001_media and harg-ua20-123_0001_metadata.

* An AIP with one file in an accepted format.
* An AIP with at least one file, and sometimes multiple files, in each of the accepted formats.
* An AIP with some files in accepted formats and some in unaccepted formats. 

###Things to check for
* The script output folders (aips-to-ingest, mediainfo-xml, preservation-xml) are made and have the expected content.
* No files in accepted formats were deleted.
* All files in unaccepted formats were deleted.
* The media or metadata suffix was added correctly to each AIP.
* A mediainfo.xml file was made for each AIP and has reasonable format identification information.  
* A valid preservation.xml file was made for each AIP and has the expected information.
* A valid bag with MD5 and SHA256 manifests was made for each AIP, and it is tarred and zipped.
* The manifest in aips-to-ingest includes all the AIPs.
* The log includes all AIPs, with a status of "Complete".

## Testing Error Handling

### AIPs to include in the test suite

1. An AIP with an AIP ID that does not start with one of the expected department prefixes.
2. An AIP with an AIP ID that has an expected department prefix but does not match any of the expected patterns.
3. A Hargrett AIP without an underscore between the AIP ID and title in the AIP folder name.
4. An AIP that only contains files in unaccepted formats.
5. An AIP with a folder named "objects" within the AIP folder.
6. The media version of an AIP that is correct to use when tests involve changing the script.
7. The metadata version of AIP 6.

### Things to check for

The following script argument errors should cause an error message to display in the terminal and the script to quit.
* Do not include the AIPs directory.
* Include an AIPs directory that is not a valid path.
* Include an AIPs directory that is a file instead of a folder.

Run the script on AIPs 1-5, which should result in the following:    
* AIP 1 is in an error folder named "department_unknown".
* AIP 2 and AIP 3 are in an error folder named "aip_folder_name".
* AIP 4 is in an error folder named "all_files_deleted", and the AIP folder is empty.
* AIP 5 is in an error folder named "preexisting_objects_folder".
* Other than AIP 4, the contents of the AIP folders are unchanged.  
* The aips-to-ingest, mediainfo-xml, and preservation-xml folders are empty.
* The error "Could not make manifest. aips-to-ingest is empty." is displayed the terminal.
* All AIPs should be in the log with a status matching the error folder name.

Use AIPs 6-7 for the remaining tests, which require editing the code to force errors to occur. Run the tests one at a time, undoing the change to the code required for one test before making the change for the next test. When testing is complete, run the script on a valid AIP folder to confirm that all changes for the tests have removed correctly from the script.

In each scenario, verify the log has the correct status for the AIPs and that no manifest is made in addition to verifying the expected results detailed in each test description.

* Save a copy of both mediainfo.xml files to the mediainfo-xml folder prior to running the script. The AIPs should be in an error folder named "preexisting_mediainfo_copy". They will have a mediainfo.xml file, but not a preservation.xml file, in the AIP metadata folder. The mediainfo.xml files in the mediainfo-xml folder should not be overwritten.


* Comment out the following code in the aip_av.py script, which is towards the end of the script, so it does not run. The AIPs should be in an error folder named "no_mediainfo_xml". There will be no mediainfo.xml or preservation.xml files made.
    ```
    # Extracts technical metadata from the files using MediaInfo.
    if aip_folder in os.listdir('.'):
        mediainfo(aip_folder, aip_id, aip_type)

* Replace the first template in the mediainfo-to-preservation.xslt file with the following code to create invalid preservation.xml. The AIPs should be in an error folder named "preservation_invalid" and there should also be a text file in that folder for each AIP with the error messages from validating. The AIP metadata folders will contain the mediainfo.xml and preservation.xml files. The mediainfo-xml folder will contain the mediainfo.xml files, and the preservation-xml folder will be empty.
    
   ```
   <xsl:template match="/">
      <preservation>
         <dc:title/>
         <dc:rights>http://error/InC/1.0/</dc:rights>
         <aip>
            <premis:object>
               <premis:error>Unexpected PREMIS element</premis:error>
               <xsl:call-template name="aip-version"/>
               <xsl:call-template name="object-category"/>
               <premis:objectCharacteristics>
                  <xsl:call-template name="aip-size"/>
                  <xsl:call-template name="aip-unique-formats"/>
               </premis:objectCharacteristics>
               <xsl:call-template name="relationship-collection"/>
            </premis:object>
         </aip>
      </preservation>
   </xsl:template>

* Edit the package() function in aip_av.py as shown below to add a line of code prior to bag validation to delete the sha256 manifest and cause the script to create invalid bags. The AIPs should be in an error folder named "bag_invalid" and there should also be a text file in that folder for each AIP with the error message from validating. There will be a mediainfo.xml and preservation.xml file in the AIP metadata and script output folders.
  
  ```
  # Validates the bag. If the bag is not valid, moves the AIP to an error folder, saves the validation error to a document in the error folder, and ends this function.
  os.remove(f'{bag_name}/manifest-sha256.txt')
  validate = subprocess.run(f'bagit.py --validate "{bag_name}"', stderr=subprocess.PIPE, shell=True)`