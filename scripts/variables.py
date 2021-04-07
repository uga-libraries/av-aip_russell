# Purpose: Defines variables and a function that are used by the other aip workflow scripts.

import os


# Variables that have a constant value, determined by local machine.
# Script tested with SaxonHE9-9-1J.
saxon = '/INSERT-PATH/saxon9he.jar'
scripts = '/INSERT-PATH/scripts'
stylesheets = '/INSERT-PATH/stylesheets'


def move_error(error_name, item):
    """Move the AIP folder to an error folder, named with the error, so the rest of the workflow steps are not run on
    the AIP. """
    if not os.path.exists(f'errors/{error_name}'):
        os.makedirs(f'errors/{error_name}')
    os.replace(item, f'errors/{error_name}/{item}')
