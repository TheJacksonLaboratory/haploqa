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
