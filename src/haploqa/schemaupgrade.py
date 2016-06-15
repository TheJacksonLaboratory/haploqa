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


SCHEMA_UPGRADE_FUNCTIONS = [
    ((0, 0, 0), upgrade_from_0_0_0),
]


def main():
    db = mds.get_db()
    schema_version = mds.get_schema_version(db)
    if schema_version is not None:
        hit_schema_version = False
        for from_version, conversion_func in SCHEMA_UPGRADE_FUNCTIONS:
            if hit_schema_version or schema_version == from_version:
                hit_schema_version = True
                conversion_func(db)

    mds.init_db(db)


# as a convenience we can run this file as a script to
# upgrade or initialize the DB
if __name__ == '__main__':
    main()
