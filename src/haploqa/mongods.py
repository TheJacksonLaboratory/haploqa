import pymongo


def get_db():
    client = pymongo.MongoClient('localhost', 27017)
    return client.haploqa


def init_db(db=None):
    if db is None:
        db = get_db()

    db.samples.create_index('sample_id')
    db.samples.create_index('tags')
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

    return db


def get_snps(platform_id, chromosome, db=None):
    if db is None:
        db = get_db()

    return db.snps.find({'platform_id': platform_id, 'chromosome': chromosome}).sort([
        ('position_bp', pymongo.ASCENDING),
        ('snp_id', pymongo.ASCENDING),
    ])


def _post_proc_sample(samples, sample):
    print('post-processing sample: ' + sample['sample_id'])

    hom_total_count = 0
    het_total_count = 0
    n_total_count = 0

    for chr_name, chr_dict in sample['chromosome_data'].items():
        hom_chr_count = 0
        het_chr_count = 0
        n_chr_count = 0

        allele1_fwds = chr_dict['allele1_fwds']
        allele2_fwds = chr_dict['allele2_fwds']
        for i in range(len(allele1_fwds)):
            if allele1_fwds[i] == '-' or allele2_fwds[i] == '-':
                n_chr_count += 1
            elif allele1_fwds[i] == allele2_fwds[i]:
                hom_chr_count += 1
            else:
                het_chr_count += 1
        hom_total_count += hom_chr_count
        het_total_count += het_chr_count
        n_total_count += n_chr_count

        samples.update_one(
            {'sample_id': sample['sample_id']},
            {
                '$set': {
                    'chromosome_data.' + chr_name + '.homozygous_count': hom_chr_count,
                    'chromosome_data.' + chr_name + '.heterozygous_count': het_chr_count,
                    'chromosome_data.' + chr_name + '.no_read_count': n_chr_count,
                }
            }
        )

    samples.update_one(
        {'sample_id': sample['sample_id']},
        {
            '$set': {
                'homozygous_count': hom_total_count,
                'heterozygous_count': het_total_count,
                'no_read_count': n_total_count,
            }
        }
    )


def post_proc_samples(sample_ids=None, db=None):
    if db is None:
        db = get_db()

    if sample_ids is None:
        for sample in db.samples.find({}):
            _post_proc_sample(db.samples, sample)

    else:
        for sample_id in sample_ids:
            for sample in db.samples.find({'sample_id': sample_id}):
                _post_proc_sample(db.samples, sample)
