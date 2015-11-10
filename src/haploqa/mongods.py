import pymongo


def get_db():
    client = pymongo.MongoClient('localhost', 27017)
    return client.haploqa


def init_db(db=None):
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
    db.users.create_index('email_address', unique=True)
    db.users.create_index('password_reset_hash')

    return db


def get_snps(platform_id, chromosome, db=None):
    if db is None:
        db = get_db()

    return db.snps.find({'platform_id': platform_id, 'chromosome': chromosome}).sort([
        ('position_bp', pymongo.ASCENDING),
        ('snp_id', pymongo.ASCENDING),
    ])


def post_proc_sample(sample):
    print('post-processing sample: ' + sample['sample_id'])

    sample['homozygous_count'] = 0
    sample['heterozygous_count'] = 0
    sample['no_read_count'] = 0
    sample['contributing_strains'] = []

    for chr_dict in sample['chromosome_data'].values():
        chr_dict['homozygous_count'] = 0
        chr_dict['heterozygous_count'] = 0
        chr_dict['no_read_count'] = 0

        allele1_fwds = chr_dict['allele1_fwds']
        allele2_fwds = chr_dict['allele2_fwds']
        for i in range(len(allele1_fwds)):
            if allele1_fwds[i] == '-' or allele2_fwds[i] == '-':
                chr_dict['no_read_count'] += 1
            elif allele1_fwds[i] == allele2_fwds[i]:
                chr_dict['homozygous_count'] += 1
            else:
                chr_dict['heterozygous_count'] += 1
        sample['homozygous_count'] += chr_dict['homozygous_count']
        sample['heterozygous_count'] += chr_dict['heterozygous_count']
        sample['no_read_count'] += chr_dict['no_read_count']
