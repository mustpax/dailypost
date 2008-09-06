#!/usr/bin/python
import string
import re

# CONFIGURATION ================================================================
# Default configuration. TODO: read overrides from config file.
Config={}
Config['defaultEditor'] = 'vim' # FTW!
Config['shownEntries'] = 3 # Last X entries shown in the MOTD file
Config['motdFile'] = 'motd' # Usually /etc/motd
Config['archiveDir'] = 'motd_archive/' # Makes sense to create a directory under /etc/ for this too
#Config['entrySeperator'] = '\n\n'
Config['entrySeperator'] = '                              ====================                              \n' # This seperates entries in the combined motd file
# For the MOTD_HEADER: only $update_date and $update_user are allowed in the Template
Config['motdHeader'] = None
Config['motdFooter'] = string.Template('Last updated $update_date\n')
Config['dateFormat'] = '$month/$day/$year' # String template with only three variables: $day, $month, $year
Config['dateRegex'] = re.compile(r'^(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})$')
Config['lineLength'] = 80
Config['headerIndent'] = 4
Config['bodyIndent'] = 10
Config['footerRightIndent'] = 20
# Each list element goes to new line
Config['sig'] = ["The SCCS Staff","<staff@sccs.swarthmore.edu>"]
Config['sig'] = []
Config['alwaysYes'] = False # Do not display confirmation dialogues, destroy data with impunity.
Config['debugMode'] = False # Be more verbose with errors and such.
# ==============================================================================
