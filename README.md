# Russell Library Workflow for AV AIPs

# Purpose and overview
This is the workflow to make archival information packages (aips) for Russel Library digital audiovisual objects that are ready for ingest into the UGA Libraries' digital preservation system (ARCHive). The workflow organizes files, extracts and formats metadata, and packages the files. The Brown Media Archives has their own [workflow for audiovisual materials](https://github.com/uga-libraries/av-aip) which has specialized rules for the different formats they use. UGA Libraries also has a [general workflow for mixed formats](https://github.com/uga-libraries/general-aip) and a [specialized workflow for web archives](https://github.com/uga-libraries/web-aip).

# Script approach
Each step of the workflow is in its own Python script. The script aip_av.py is used to iterate over the folders being made into aips, calling the script for each step in turn. Each aip is fully processed before the next one is started. This modular approach makes it easier to set up variations on the workflow by not running a step or substituting a different script for a step in aip_av.py. It also makes it easier to find and edit code since each script is small and has a clear purpose.

# Error handling
If a known error is encountered, such as failing a validation test, the aip is moved to an error folder with the name of the error and the rest of the steps are skipped for that aip. 

# Script usage
python3 '/path/aip_av.py' '/path/aip-directory'
* aip_av.py is the script that controls the workflow and calls the other scripts.
* aip-directory is the folder which contains all the folders to make into aips.

# Dependencies
* Mac or Linux operating system
* [bagit.py](https://github.com/LibraryOfCongress/bagit-python)
* [md5deep](https://github.com/jessek/hashdeep)
* [MediaInfo](https://mediaarea.net/en/MediaInfo)
* [saxon9he](http://saxon.sourceforge.net/)
* [xmllint](http://xmlsoft.org/xmllint.html)

# Installation
1. Install the dependencies (listed above). Saxon and md5deep may be come with your OS.


2. Download the scripts and stylesheets folders and save to your computer.
3. Update the file path variables (lines 8-10) in the variables.py script for your local machine.
4. Update the group uri in the mediainfo-to-master.xslt stylesheet in variable name="uri" (line 51). 
5. Update the base uri in the premis.xsd in restriction pattern for objectIdentifierType (line 35).
5. Change permissions on the scripts so they are executable.

# Workflow Details
See also the [graphical representation of this workflow](https://github.com/uga-libraries/av-aip_russell/blob/master/Russell%20AV%20Preservation%20Script%20Flow%20Diagram.png).

1. Deletes files that are not on the keep list (.dv, .mov, .mp3, .mp4, .wav, .pdf, or .xml) from the aip folder.


2. Determines if the aip contains metadata or media files based on the filenames. This is used in the names of all script outputs.
3. Structures the aip folder contents:
    1. Makes a folder named objects and moves all files and folders into it.
    2. Makes a folder named metadata for script outputs. 
4. Runs MediaInfo on the objects folder and saves the result in the metadata folder.
5. Transforms the MediaInfo xml into the master.xml (PREMIS technical metadata) file using saxon and xslt.
6. Validates the master.xml with xmllint and xsd's.
7. Bags the aips in place with md5 and sha256 manifests using bagit.py.
8. Validates the bags using bagit.py.
9. Runs the perl script prepare_bag on the aip to tar and zip it and saves output to aips-ready-to-ingest.
10. When all aips are processed, makes a md5 manifest of the packaged aips in the aips-to-ingest folder.

# Initial Author
Adriane Hanson, Head of Digital Stewardship, January 2020

# Acknowledgements
These scripts were adapted from [bash scripts developed by Iva Dimitrova](https://github.com/uga-libraries/aip-mac-bash-mediainfo). These were used by the Russell Library for making AV aips from 2017 to 2019.
