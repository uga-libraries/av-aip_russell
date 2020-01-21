# Purpose: Creates PREMIS and Dublin Core metadata from the MediaInfo xml and saves it as a master.xml file.
# Dependencies: saxon, xmllint, xslt stylesheet, xsd schema files

import os
import shutil
import subprocess
import sys
from variables import move_error, saxon, stylesheets

# The aip and aip type (metadata or media) are passed as arguments from aip_av.py.
# aip is used to identify the folder the script should work on.
# Both are used to construct the name of the aip.

aip = sys.argv[1]
aip_type = sys.argv[2]


# Makes the master.xml file from the mediainfo.xml using a stylesheet and saves it to the aip's metadata folder.
# If the mediainfo.xml is not present, moves the aip to an error folder and quits this script.

mediainfo = f'{aip}/metadata/{aip}_{aip_type}_mediainfo.xml'
stylesheet = f'{stylesheets}/mediainfo-to-master.xslt'
masterxml = f'{aip}/metadata/{aip}_{aip_type}_master.xml'

if os.path.exists(mediainfo):
    subprocess.run(f'java -cp "{saxon}" net.sf.saxon.Transform -s:"{mediainfo}" -xsl:"{stylesheet}" -o:"{masterxml}" type={aip_type}', shell=True)

else:
    move_error('no_mediainfo_xml', aip)
    exit()


# Validates the master.xml against the requirements of the UGA Libraries' digital preservation system (ARCHive).
# Possible validation errors: 
#   master.xml was not made (failed to loaded)
#   master.xml does not match the metadata requirements (fails to validate)

validate = subprocess.run(f'xmllint --noout -schema "{stylesheets}/master.xsd" "{masterxml}"', stderr=subprocess.PIPE, shell=True)


# If the master.xml isn't valid, moves the aip to an error folder and
#   saves the validation error to a text document in the error folder.
# The validation output is converted from a byte type to a string for easier formatting.
# The error document is formatted so each error is its own line.

if 'failed to load' in str(validate) or 'fails to validate' in str(validate):
    move_error('master_invalid', aip)

    with open(f'errors/master_invalid/{aip}_masterxml_validation_error.txt', 'a') as error:
        lines = str(validate.stderr).split('\\n')
        for line in lines:    
            error.write(f'{line}\n\n')

# If the master.xml is valid, copies the master.xml to local server for staff use.

else:
    shutil.copy2(masterxml, 'master-xml')
