# Purpose: Defines variables there are specific to your local machine.
# These are imported by aip_av.py

"""
To use, make a copy of this file named configuration.py and update the paths to match your local machine.
    C: may need to be replaced with a different drive letter.
    INSERT-PATH is replaced with the path on your local machine.
    # is replaced by the number for your version of the programs.
"""

# Script tested with SaxonHE10.1.
SAXON = 'C:/INSERT-PATH/saxon-he-##.#.jar'
STYLESHEETS = 'C:/INSERT-PATH/stylesheets'
PREPARE_BAG = 'C:/INSERT-PATH/prepare_bag'

# Namespace for AIP identifiers. For UGA, this is the URI for ARCHive.
NAMESPACE = 'INSERT-NAMESPACE'

# Groups in ARCHive for verifying departments.
GROUPS = ['Group1', 'Group2']
