# Russell Library Workflow for AV AIPs

## Purpose and overview
This is the workflow to make archival information packages (AIPs) for Russel Library digital audiovisual objects 
that are ready for ingest into the UGA Libraries' digital preservation system (ARCHive). 
The workflow organizes files, extracts and formats metadata, and packages the files. 
The Brown Media Archives has their own [workflow for audiovisual materials](https://github.com/uga-libraries/av-aip) 
which has specialized rules for the different formats they use. 
UGA Libraries also has a [general workflow for mixed formats](https://github.com/uga-libraries/general-aip) and a [specialized workflow for web archives](https://github.com/uga-libraries/web-aip).

The UGA Libraries has two types of AV AIPs: media and metadata. 
The only difference is media AIPs contain the AV files 
and metadata AIPs contain supporting documentation such as OHMS XML, transcripts, and releases. 
The media and metadata are kept in two separate AIPs so that the media, which is generally ready for preservation first, 
can be ingested into ARCHive without delay. Once the metadata is created, it can be added to ARCHive as a separate AIP. 
If the media and metadata were in the same AIP, when the metadata was ready a new version of the AIP 
would have to be ingested into ARCHive that contained an identical copy of the media, 
which is not a good use of our preservation storage space.

As of August 2021, this script also works for creating Hargrett oral history AIPs.

## Script approach
Metadata (department, collection id, AIP id, title, and version) are given to the script via a CSV.
Previously, this information was parsed from the folder name, 
which was prone to breaking due to new id naming conventions.

The script completes all steps for a single AIP before starting the next. 
If a known error is encountered, such as failing a validation test, the folder is moved to an error folder, 
and the rest of the steps are skipped for that folder.

Because this script can take some time to complete, particularly when tarring and zipping larger files, 
it prints to the terminal whenever it is starting a new AIP folder so staff can monitor the script's progress.

A log is created by the script with the name of each AIP folder and its final status, 
which is whether the AIP encountered a known error or if it completed, 
so staff can quickly review the result of a batch of AIPs.

## Script usage
python3 'path/aip_av.py' 'path/aip-directory'

See "Script Input" (below) for details on the AIPs directory.

## Dependencies
* Mac or Linux operating system
* [bagit.py](https://github.com/LibraryOfCongress/bagit-python)
* [MediaInfo](https://mediaarea.net/en/MediaInfo)
* [saxon9he](http://saxon.sourceforge.net/)
* [xmllint](http://xmlsoft.org/xmllint.html)

## Installation
1. Install the dependencies (listed above). Saxon may come with your OS.
2. Download this repository and save to your computer.
3. Use the configuration_template.py to make a file named configuration.py with file path variables for your local machine.
4. Change permissions on the scripts so they are executable.

## Script Input (AIPS Directory)
The content to be transformed into AIPs must be in a single folder, which is the AIPs directory. 
Within the AIPs directory, there is one folder for each AIP. Each folder must be only media or only metadata files.

### Metadata file
Create a file named metadata.csv in the AIPs directory, following this [example metadata.csv](scripts/metadata.csv).
This contains required information about each of the AIPs to be included in this batch.

- Department: ARCHive group name
- Collection: collection identifier
- Folder: the current name of the folder to be turned into an AIP
- AIP_ID: AIP identifier
- Title: AIP title
- Version: AIP version number, which must be a whole number

### Hargrett script input
The AIPs directory should be in a bag, since files are transferred over the network before they are transformed into AIPs. 
The AIP folders were previously named AIPID_Title, although they can be named anything now that metadata.csv is implemented. 
Example AIPs directory:

![Screenshot of Hargrett AIPs Directory](https://github.com/uga-libraries/av-aip_russell/blob/main/hargrett-aips-directory.png?raw=true)

Hargrett oral history AIP IDs are formatted har-ua##-###_####, for example har-ua12-003_0001

Hargrett title naming conventions are:
   * Firstname Lastname Interview Recording (for media AIPs)
   * Firstname Lastname Interview Metadata (for metadata AIPs)

Use the hargrett-preprocessing.py script to validate the AIPs directory bag and remove the AIP folders from the bag 
prior to running this script.

### Russell script input
Russell AIP folders should be named with the AIP title. 
The naming convention is identifier_lastname where the identifier is the AIP ID without the type (media or metadata) suffix.
The naming convention is not required for the script now that metadata.csv is implemented.

## Workflow Details

1. Deletes files that do not have any of the expected file extensions (.dv, .m4a, .mov, .mp3, .mp4, .wav, .pdf, or .xml) from the AIP folder.
2. Verifies the metadata.csv is in the AIPs directory and is correct; reads the metadata.csv.
3. Makes folders for script outputs within the AIPs directory.

For each AIP:
4. Renames folder to the AIP ID.
5. Deletes unwanted file types based on the file extension.
6. Organizes the folder into the AIP directory structure:
    1. Makes a folder named objects and moves all files and folders into it.
    2. Makes a folder named metadata for script outputs.
    3. Renames the AIP folder to the AIP ID.
7. Extracts technical metadata using MediaInfo and saves the result in the metadata folder.
8. Converts technical metadata to Dublin Core and PREMIS (preservation.xml)
   1. Makes the preservation.xml with saxon and xslt.
   2. Validates the preservation.xml with xmllint and xsd.
9. Packages the AIP
   1. Deletes .DS_Store that have been auto-generated while the script is running.
   2. Bags the AIP in place with md5 and sha256 manifests with bagit.py.
   3. Validates the bag with bagit.py.
   4. Runs the perl script prepare_bag on the AIP to tar and zip it and saves output to aips-ready-to-ingest. 
10. When all AIPs are processed, makes a md5 manifest of the packaged AIPs in the aips-to-ingest folder using md5sum.

## Initial Author
Adriane Hanson, Head of Digital Stewardship, January 2020

## Acknowledgements
These scripts were adapted from [bash scripts developed by Iva Dimitrova](https://github.com/uga-libraries/aip-mac-bash-mediainfo). 
These were used by the Russell Library for making AV AIPs from 2017 to 2019.
