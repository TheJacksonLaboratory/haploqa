import haploqa.mongods as mds


def upgrade_from_0_0_0(db):
    upgrade_to_schema_version = 0, 0, 1

    # We were erroneously referring to sex as "gender" in previous schema.
    # This update corrects that.
    db.samples.update_many(
        {},
        {
            '$rename': {'gender': 'sex'},
        },
    )
    db.samples.drop_index('gender_1')
    db.samples.create_index('sex')
    db.meta.replace_one({}, {'schema_version': upgrade_to_schema_version}, upsert=True)


def upgrade_from_0_0_1(db):
    upgrade_to_schema_version = 0, 0, 2

    # add unique IDs to each sample
    for sample in db.samples.find({}, {'sample_id': 1}):
        db.samples.update_one(
            {'_id': sample['_id']},
            {
                '$set': {
                    'sample_id': mds.gen_unique_id(db),
                    'other_ids': [sample['sample_id']],
                },
            },
        )
    db.samples.drop_index('sample_id_1')
    db.samples.create_index('sample_id', unique=True)
    db.samples.create_index('other_ids')

    db.meta.update_one(
        {},
        {'$set': {'schema_version': upgrade_to_schema_version}},
    )


SCHEMA_UPGRADE_FUNCTIONS = [
    ((0, 0, 0), upgrade_from_0_0_0),
    ((0, 0, 1), upgrade_from_0_0_1),
]


def main():
    db = mds.get_db()
    schema_version = mds.get_schema_version(db)
    if schema_version is not None:
        hit_schema_version = False
        for from_version, conversion_func in SCHEMA_UPGRADE_FUNCTIONS:
            if hit_schema_version or schema_version == from_version:
                hit_schema_version = True
                observed_from_version = mds.get_schema_version(db)
                if observed_from_version != from_version:
                    raise Exception(
                        'Aborting schema upgrade. '
                        'Expected schema version to be {} but observed {}'.format(
                            mds.version_to_str(from_version),
                            mds.version_to_str(observed_from_version),
                        )
                    )

                print('upgrading schema from version:', mds.version_to_str(from_version))
                conversion_func(db)

    mds.init_db(db)
    print(
        'successfully upgraded schema to version:',
        mds.version_to_str(mds.get_schema_version(db)),
    )


# as a convenience we can run this file as a script to
# upgrade or initialize the DB
if __name__ == '__main__':
    main()
