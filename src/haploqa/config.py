HAPLOQA_CONFIG = {
    # this list of characters represents the full range of characters we
    # allow ourselves to use when generating unique IDs. We want our IDs
    # to have two properties:
    #
    # 1) all characters used should be easy to visually distinguish. For this reason we exclude
    #    '1', 'L', '0' and 'O'. We also limit ourselves to upper-case.
    # 2) they should be short so that they're easy to remember and don't take up too much space.
    #    Using almost all of the upper-case alphanumeric characters in our alphabet helps us
    #    generate short IDs
    #
    # The full alphabet we use is [0-9] + [A-H] + [J-K] + [M, N] + [P-Z] for a total of 32 characters
    'UNIQUE_ID_ALPHABET': sorted(
        set(list(map(str, range(2, 10))) + list(map(chr, range(ord('A'), ord('Z') + 1)))) -
        {'I', 'L', 'O'}
    ),
    'UNIQUE_ID_PREFIX_SEP': ':',
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
    'USE_DEFAULT_TMP': True,
    'TMP_DIRECTORY': '/data/data_upload/'
}
