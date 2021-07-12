# Testing alternative to md5deep because not installing correctly on the Russell Mac labs.
# Once it works, it will be integrated with aip_av.py.

import datetime
import os
import subprocess

# Extra code to get to the state that we would be after running the previous code in aip_av.py
aips_directory = "C:/Users/amhan/Desktop/Test_Russell"
os.chdir(aips_directory)

# Makes a MD5 manifest of all packaged AIPs for each department in the aips-to-ingest folder using md5sum.
# The manifest is named current-date_department_manifest.txt and saved in the aips-to-ingest folder.
# The manifest has one line per AIP, formatted md5<tab>filename
# Checks that aips-to-ingest is not empty (due to errors) before making the manifest.
os.chdir('aips-to-ingest')
current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
if not len(os.listdir()) == 0:
    for file in os.listdir():

        # Get fixity output for the file and reformat to be md5<tab>filename.
        md5deep_output = subprocess.run(f"md5deep64 -b {file}", stdout=subprocess.PIPE, shell=True)
        fixity = bytes.decode(md5deep_output.stdout).strip()

        # Save the fixity to the correct department manifest.
        if file.startswith("har"):
            with open(f"{current_date}_hargrett_manifest.txt", "a") as manifest:
                manifest.write(f"{fixity}\n")
        elif file.startswith("rbrl"):
            with open(f"{current_date}_russell_manifest.txt", "a") as manifest:
                manifest.write(f"{fixity}\n")
else:
    print('\nCould not make manifest. aips-to-ingest is empty.')

"""
Test Results:
Correctly prints error if aips-to-ingest is empty.
Correctly makes the hargrett and/or russell manifests and saves the filename(s) to them.
Correctly makes manifests for all test cases with md5deep on Windows.

To Do:
Only Russell, Only Hargrett, and Mix of Both, one file at a time, with md5sum (Mac only).
"""