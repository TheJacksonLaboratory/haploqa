# Instructions:
# 1. Make a duplicate of this file and just name it config.py
# 2. Do not make any changes to the template file unless it's adding a configuration
#    parameter that is integral to the working of the app
# 3. Change the values to the parameters that are marked with TODOs; whether you
#    wish to remove the TODOs after you fill in the parameters is entirely up to you
# 4. DO NOT CHECK IN THE CONFIG.PY YOU CREATE (THAT DEFEATS THE PURPOSE OF SOME
#    OF THESE CONFIG PARAMETERS)

HAPLOQA_CONFIG = {
    # this list of characters represents the full range of characters we
    # allow ourselves to use when generating unique IDs. We want our IDs
    # to use all characters used should be easy to visually distinguish (exclude
    # '1', 'L', '0' and 'O', and only use upper-case letters
    'UNIQUE_ID_ALPHABET': sorted(
        set(list(map(str, range(2, 10))) + list(map(chr, range(ord('A'), ord('Z') + 1)))) -
        {'I', 'L', 'O'}
    ),
    'GENERATE_IDS_DEFAULT': True,
    'ON_DUPLICATE_ID_DEFAULT': 'skip',  # 'halt', 'replace'

    'DB_HOST': 'localhost',
    'DB_PORT': 27017,

    'SMTP_HOST': 'smtp.jax.org',
    'SMTP_PORT': 25,

    'MIN_PASSWORD_LENGTH': 8,

    # If running on a server, USE_DEFAULT_TMP should be set to False, as the
    # default tmp/ directory on the VMs doesn't have enough allocated memory
    # to support large import files. In the case of being run on a server,
    # ensure that there is a replacement directory in a location that has ample
    # space for tmp files (they will be removed once the samples are imported)
    # and change 'TMP_DIRECTORY' to the absolute path of that directory. If
    # running locally, it may be easier to set this to True
    # TODO: set 'USE_DEFAULT_TMP' accordingly based on above description
    'USE_DEFAULT_TMP': False,
    'TMP_DIRECTORY': '/data/data_uploads/',

    # TODO: generate a secret key here
    'SECRET': ''
}
