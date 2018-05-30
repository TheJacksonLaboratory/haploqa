import haploqa.mongods as mds
import pymongo
from datetime import datetime, timedelta


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
    db.diplotype_probabilities.create_index([
        ('sample_id',   pymongo.ASCENDING),
        ('chromosome',  pymongo.ASCENDING),
    ])

    db.meta.update_one(
        {},
        {'$set': {'schema_version': upgrade_to_schema_version}},
    )


def upgrade_from_0_0_2(db):
    upgrade_to_schema_version = 0, 0, 3

    # before we start this update we should make sure that all haplotype strains have a standard designation assigned
    # and that colors match
    hap_strain_samples = db.samples.find(
        {'tags': 'haplotype-strain'},
        {
            'sample_id': 1,
            'standard_designation': 1,
            'color': 1,
        },
    )

    strain_colors = {}
    for hap_strain_sample in hap_strain_samples:
        if 'standard_designation' in hap_strain_sample:
            std_desig = hap_strain_sample['standard_designation']
            if 'color' in hap_strain_sample and hap_strain_sample['color']:
                color = hap_strain_sample['color']
                if std_desig not in strain_colors:
                    strain_colors[std_desig] = color
                else:
                    if strain_colors[std_desig] != color:
                        raise Exception(
                            'Found samples with standard designation "{}" that have mismatching color. '
                            'All samples with matching standard designations must also have matching colors '
                            'before the upgrade can proceed. Once this has been addressed you can restart '
                            'the upgrade process.'.format(std_desig)
                        )
            else:
                raise Exception(
                    'Every strain tagged with "haplotype-strain" must be assigned a color before upgrade can '
                    'proceed. Once this has been addressed you can restart the upgrade process.'
                )
        else:
            raise Exception(
                'sample "{}" is marked as a "haplotype-strain" but has not been assigned a '
                'standard designation. It is required that all haplotype strains be assigned '
                'a standard designation before the upgrade can proceed. Once this has been '
                'addressed you can restart the upgrade process.'.format(hap_strain_sample['sample_id'])
            )

    db.standard_designations.create_index('standard_designation')
    db.standard_designations.create_index('contributing_strains')
    for std_desig, color in strain_colors.items():
        db.standard_designations.insert_one({
            'standard_designation': std_desig,
            'color': color,
        })

    db.samples.update_many(
        {'tags': 'haplotype-strain'},
        {'$set': {'haplotype_candidate': True}},
    )
    db.samples.update_many({}, {'$unset': {'color': ''}})

    for sample in db.samples.find({'contributing_strains': {'$gt': []}}, {'contributing_strains': 1, 'sample_id': 1}):
        strain_names = []
        for strain_objid in sample['contributing_strains']:
            strain_sample = db.samples.find_one({'_id': strain_objid}, {'standard_designation': 1})
            strain_name = None
            if strain_sample is None:
                print(
                    'in contributing strains sample {} refers to missing object: {}',
                    sample['sample_id'],
                    strain_objid,
                )
            else:
                strain_name = strain_sample['standard_designation']

            strain_names.append(strain_name)

        db.samples.update_one(
            {'_id': sample['_id']},
            {'$set': {'contributing_strains': strain_names}},
        )

    db.samples.create_index([
            ('investigator',            pymongo.TEXT),
            ('notes',                   pymongo.TEXT),
            ('other_ids',               pymongo.TEXT),
            ('platform_id',             pymongo.TEXT),
            ('project',                 pymongo.TEXT),
            ('sample_id',               pymongo.TEXT),
            ('sex',                     pymongo.TEXT),
            ('standard_designation',    pymongo.TEXT),
            ('tags',                    pymongo.TEXT),
        ],
        name='sample_text_idx',
    )

    # no errors occured. let's make the upgrade official
    db.meta.update_one(
        {},
        {'$set': {'schema_version': upgrade_to_schema_version}},
    )


def upgrade_from_0_0_3(db):
    """
    Adds timestamps for last_update field for samples without the field
    :param db: database
    :return: none
    """

    upgrade_to_schema_version = 0, 0, 4
    # Check if there are any samples that don't have a last_update entry (if not, nothing needs to be done here)
    if db.samples.find({'last_update': {'$exists': False}}).count() > 0:
        oldest_ts = None
        oldest_dt = None

        # Iterate through the samples to find the oldest last_update entry so we can set the default last_update entry
        # to a day prior. If we set the default to datetime.now or something similar, samples might get a notification
        # about contributing strains being updated when they haven't really been updated
        for sample in db.samples.find({'last_update': {'$exists': True}}):
            this_ts = sample['last_update']
            this_dt = datetime.strptime(this_ts.split()[0], '%m/%d/%Y')
            # if the oldest timestamp hasn't been set it, just make this one the oldest
            if not oldest_ts:
                oldest_ts = this_ts
                oldest_dt = this_dt
            else:
                # check if the oldest timestamp should be updated with current
                if this_dt < oldest_dt:
                    oldest_ts = this_ts
                    oldest_dt = this_dt

        update_dt = '{:%m/%d/%Y %H:%M %p} EST'.format(oldest_dt - timedelta(days=1))

        db.samples.update_many(
            {'last_update': {'$exists': False}},
            {'$set': {'last_update': update_dt}}
        )

    # Make the update official up updating the schema version in meta
    db.meta.update_one(
        {},
        {'$set': {'schema_version': upgrade_to_schema_version}},
    )


SCHEMA_UPGRADE_FUNCTIONS = [
    ((0, 0, 0), upgrade_from_0_0_0),
    ((0, 0, 1), upgrade_from_0_0_1),
    ((0, 0, 2), upgrade_from_0_0_2),
    ((0, 0, 3), upgrade_from_0_0_3)
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
