# Russell Library Workflow for AV AIPs

## Purpose and overview
This is the workflow to make archival information packages (AIPs) for Russel Library digital audiovisual objects that are ready for ingest into the UGA Libraries' digital preservation system (ARCHive). The workflow organizes files, extracts and formats metadata, and packages the files. The Brown Media Archives has their own [workflow for audiovisual materials](https://github.com/uga-libraries/av-aip) which has specialized rules for the different formats they use. UGA Libraries also has a [general workflow for mixed formats](https://github.com/uga-libraries/general-aip) and a [specialized workflow for web archives](https://github.com/uga-libraries/web-aip).

The UGA Libraries has two types of AV AIPs: media and  metadata. The only difference is media AIPs contain the AV files and metadata AIPs contain supporting documentation such as OHMS XML, transcripts, and releases. The media and metadata are kept in two separate AIPs so that the media, which is generally ready for preservation first, can be ingested into ARCHive without delay. Once the metadata is created, it can be added to ARCHive as a separate AIP. If the media and metadata were in the same AIP, when the metadata was ready a new version of the AIP would have to be ingested into ARCHive that contained an identical copy of the media, which is not a good use of our preservation storage space.

As of April 2021, this script also works for creating Hargrett oral history AIPs.

## Script approach
The script iterates over each folder to be made into an AIP, completing all steps for one folder before starting the next. If a known error is encountered, such as failing a validation test, the folder is moved to an error folder, and the rest of the steps are skipped for that folder.

Because this script can take some time to complete, particularly when tarring and zipping larger files, it prints to the terminal whenever it is starting a new AIP folder so staff can monitor the script's progress.

A log is created by the script with the name of each AIP folder and its final status, which is whether the AIP encountered a known error or if it completed, so staff can quickly review the result of a batch of AIPs.

## Script usage
python3 '/path/aip_av.py' '/path/aip-directory'

See "Script Input" (below) for details on the AIP Directory.

## Dependencies
* Mac or Linux operating system
* [bagit.py](https://github.com/LibraryOfCongress/bagit-python)
* [MediaInfo](https://mediaarea.net/en/MediaInfo)
* [saxon9he](http://saxon.sourceforge.net/)
* [xmllint](http://xmlsoft.org/xmllint.html)

## Installation
1. Install the dependencies (listed above). Saxon may be come with your OS.


2. Download the scripts and stylesheets folders and save to your computer.
3. Update the variables in the variables.py script for the file paths on your local machine.
4. Update the group uri in the mediainfo-to-preservation.xslt stylesheet in variable name="uri" (line 52). 
5. Update the base uri in the premis.xsd in the restriction pattern for objectIdentifierType (line 35).
5. Change permissions on the scripts so they are executable.

## Script Input (AIPS Directory)
The content to be transformed into AIPs must be in a single folder, which is the AIPs directory. Within the AIPs directory, there is one folder for each AIP. Each folder must be only media or only metadata files.

### Hargrett script input
The AIPs directory should be in a bag, since files are transferred over the network before they are transformed into AIPs. The AIP folders are named AIPID_Title. Example AIPs directory:

![Screenshot of Hargrett AIPs Directory](https://github.com/uga-libraries/av-aip_russell/blob/add-hargrett/hargrett-aips-directory.png?raw=true)

Hargrett oral history AIP IDs are formatted har-ua##-###_####

Hargrett title naming conventions are:
   * Firstname Lastname Interview Recording (for media AIPs)
   * Firstname Lastname Interview Metadata (for metadata AIPs)

Use the hargrett-preprocessing.py script to validate the AIPs Directory bag and remove the AIP folders from the bag prior to running this script.

## Workflow Details

See also the [graphical representation of this workflow](https://github.com/uga-libraries/av-aip_russell/blob/master/Russell%20AV%20Preservation%20Script%20Flow%20Diagram.png).

1. Deletes files that do not have any of the expected file extensions (.dv, .m4a, .mov, .mp3, .mp4, .wav, .pdf, or .xml) from the AIP folder.


2. Determines if the aip contains metadata or media files based on the file extensions. This is used in the names of all script outputs.
3. Structures the aip folder contents:
    1. Makes a folder named objects and moves all files and folders into it.
    2. Makes a folder named metadata for script outputs. 
4. Runs MediaInfo on the objects folder and saves the result in the metadata folder.
5. Transforms the MediaInfo xml into the preservation.xml (PREMIS technical metadata) file using saxon and xslt.
6. Validates the preservation.xml with xmllint and xsd's.
7. Bags the aips in place with md5 and sha256 manifests using bagit.py.
8. Validates the bags using bagit.py.
9. Runs the perl script prepare_bag on the aip to tar and zip it and saves output to aips-ready-to-ingest.
10. When all aips are processed, makes a md5 manifest of the packaged aips in the aips-to-ingest folder using md5sum.

## Initial Author
Adriane Hanson, Head of Digital Stewardship, January 2020

## Acknowledgements
These scripts were adapted from [bash scripts developed by Iva Dimitrova](https://github.com/uga-libraries/aip-mac-bash-mediainfo). These were used by the Russell Library for making AV aips from 2017 to 2019.
