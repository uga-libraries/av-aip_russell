# Purpose: Defines variables and a function that are used by the other aip workflow scripts.

import os

# Variables that have a constant value, determined by local machine.
# Script tested with SaxonHE9-9-1J.

saxon = '/INSERT-PATH/saxon9he.jar'
scripts = '/INSERT-PATH/scripts'
stylesheets = '/INSERT-PATH/stylesheets'


# Function to move the aip folder to an error folder.
# The error folder is named with the error type.
# The error folder is made the first time an error is encountered,
#   and later aips with the same error can be added to it.
# Moving the aip prevents the rest of the scripts from running on that aip.

def move_error(error_name, item):
    if not os.path.exists(f'errors/{error_name}'):
        os.makedirs(f'errors/{error_name}')
    os.replace(item, f'errors/{error_name}/{item}')
