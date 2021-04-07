# Purpose: Extracts technical metadata from the files in the objects folder using MediaInfo.
# Dependencies: mediainfo

import os
import shutil
import subprocess
import sys
from variables import move_error


# The AIP and AIP type (metadata or media) are passed as arguments from aip_av.py.
# AIP is used to identify the folder the script should work on.
# Both are used to construct the name of the AIP.
aip = sys.argv[1]
aip_type = sys.argv[2]

# Runs MediaInfo on the contents of the objects folder and saves the xml output to the metadata folder.
# --'Output=XML' uses the XML structure that started with MediaInfo 18.03
# --'Language=raw' outputs the size in bytes.
subprocess.run(f'mediainfo -f --Output=XML --Language=raw "{aip}/objects" > "{aip}/metadata/{aip}_{aip_type}_mediainfo.xml"', shell=True)

# Copies mediainfo xml to a separate folder (mediainfo-xml) for staff reference.
# If a file by that name is already in mediainfo-xml,
#   moves the AIP to an error folder instead since the AIP may be a duplicate.
if os.path.exists(f'mediainfo-xml/{aip}_{aip_type}_mediainfo.xml'):
    move_error('preexisting_mediainfo_copy', aip)
else:
    shutil.copy2(f'{aip}/metadata/{aip}_{aip_type}_mediainfo.xml', 'mediainfo-xml')
