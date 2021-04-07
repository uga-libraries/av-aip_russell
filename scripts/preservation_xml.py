# Purpose: Creates PREMIS and Dublin Core metadata from the MediaInfo xml and saves it as a preservation.xml file.
# Dependencies: saxon, xmllint, xslt stylesheet, xsd schema files

import os
import shutil
import subprocess
import sys
from variables import move_error, saxon, stylesheets


# The AIP and AIP type (metadata or media) are passed as arguments from aip_av.py.
# AIP is used to identify the folder the script should work on.
# Both are used to construct the name of the AIP.
aip = sys.argv[1]
aip_type = sys.argv[2]

# Makes the preservation.xml file from the mediainfo.xml using a stylesheet and saves it to the AIP's metadata folder.
# If the mediainfo.xml is not present, moves the AIP to an error folder and quits this script.
mediainfo = f'{aip}/metadata/{aip}_{aip_type}_mediainfo.xml'
stylesheet = f'{stylesheets}/mediainfo-to-preservation.xslt'
preservationxml = f'{aip}/metadata/{aip}_{aip_type}_preservation.xml'

if os.path.exists(mediainfo):
    subprocess.run(f'java -cp "{saxon}" net.sf.saxon.Transform -s:"{mediainfo}" -xsl:"{stylesheet}" -o:"{preservationxml}" type={aip_type}', shell=True)
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
