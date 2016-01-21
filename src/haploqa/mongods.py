import pymongo


def get_db():
    """
    Gets a reference to the HaploQA database
    :return: the DB
    """
    client = pymongo.MongoClient('localhost', 27017)
    return client.haploqa


def init_db(db=None):
    """
    Initialize the DB indexes. This function is safe to rerun on existing databases
    to make sure that all indexes are generated.
    :param db: will be looked up via get_db() by default
    :return: the database
    """
    if db is None:
        db = get_db()

    db.samples.create_index('sample_id')
    db.samples.create_index('tags')
    db.samples.create_index('standard_designation')
    db.samples.create_index('gender')
    db.platforms.create_index('platform_id')
    db.snps.create_index([
        ('platform_id', pymongo.ASCENDING),
        ('snp_id',      pymongo.ASCENDING),
    ], unique=True)
    db.snps.create_index([
        ('platform_id', pymongo.ASCENDING),
        ('chromosome',  pymongo.ASCENDING),
        ('position_bp', pymongo.ASCENDING),
        ('snp_id',      pymongo.ASCENDING),
    ])
    db.users.create_index('email_address_lowercase', unique=True)
    db.users.create_index('password_reset_hash')

    return db


def get_snps(platform_id, chromosome, db=None):
    """
    Grab the SNP annotations from the DB. These will be returned in order (sorted by position then by ID). This
    is the same ordering used by the SNP arrays in samples
    :param platform_id: the platform to get SNPs for. Eg. "GigaMUGA"
    :param chromosome: the chromosome to grab SNPs for
    :param db: the DB (by default we look up the DB using get_db()
    :return: the SNP annotations from the mongodb
    """
    if db is None:
        db = get_db()

    return db.snps.find({'platform_id': platform_id, 'chromosome': chromosome}).sort([
        ('position_bp', pymongo.ASCENDING),
        ('snp_id', pymongo.ASCENDING),
    ])


def post_proc_sample(sample):
    """
    Post-process a sample dict after it's loaded from a data source but before it's inserted into the DB. This adds some
    default values and performs some simple calculations. This function will modify the sample by adding new attributes.
    :param sample: the sample dict to modify
    """
    print('post-processing sample: ' + sample['sample_id'])

    sample['homozygous_count'] = 0
    sample['heterozygous_count'] = 0
    sample['no_read_count'] = 0
    sample['contributing_strains'] = []

    for chr_dict in sample['chromosome_data'].values():
        chr_dict['homozygous_count'] = 0
        chr_dict['heterozygous_count'] = 0
        chr_dict['no_read_count'] = 0

        try:
            allele1_fwds = chr_dict['allele1_fwds']
            allele2_fwds = chr_dict['allele2_fwds']
            for i in range(len(allele1_fwds)):
                if allele1_fwds[i] == '-' or allele2_fwds[i] == '-':
                    chr_dict['no_read_count'] += 1
                elif allele1_fwds[i] == allele2_fwds[i]:
                    chr_dict['homozygous_count'] += 1
                else:
                    chr_dict['heterozygous_count'] += 1
        except KeyError:
            valid_nucs = {'G', 'A', 'T', 'C'}
            snps = chr_dict['snps']
            for snp in snps:
                if snp in valid_nucs:
                    chr_dict['homozygous_count'] += 1
                elif snp == '-':
                    chr_dict['no_read_count'] += 1
                elif snp == 'H':
                    chr_dict['heterozygous_count'] += 1
                else:
                    raise Exception('unexpected SNP code: {}'.format(snp))

        sample['homozygous_count'] += chr_dict['homozygous_count']
        sample['heterozygous_count'] += chr_dict['heterozygous_count']
        sample['no_read_count'] += chr_dict['no_read_count']


def within_chr_snp_indices(platform_id, db=None):

    if db is None:
        db = get_db()

    platform_obj = db.platforms.find_one({'platform_id': platform_id})
    if platform_obj is None:
        raise Exception('failed to find a platform named "{}".'.format(platform_id))

    platform_chrs = platform_obj['chromosomes']
    snp_chr_indexes = dict()
    snp_count_per_chr = {chr: 0 for chr in platform_chrs}

    prev_chr = None
    snp_index = 0

    chr_snps = db.snps.find({'platform_id': platform_id}).sort([
        ('chromosome', pymongo.ASCENDING),
        ('position_bp', pymongo.ASCENDING),
        ('snp_id', pymongo.ASCENDING),
    ])
    for snp in chr_snps:
        if snp['chromosome'] != prev_chr:
            snp_count_per_chr[prev_chr] = snp_index
            snp_index = 0
            prev_chr = snp['chromosome']
        snp_chr_indexes[snp['snp_id']] = {
            'index': snp_index,
            'chromosome': snp['chromosome'],
        }
        snp_index += 1
    if prev_chr is not None:
        snp_count_per_chr[prev_chr] = snp_index

    return platform_chrs, snp_count_per_chr, snp_chr_indexes


# as a convenience we can run this file as a script to
# rebuild DB indexes
if __name__ == '__main__':
    init_db()
