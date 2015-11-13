import argparse
import csv
import re
import sys

import haploqa.mongods as mds

gender_canonical = 'gender'
gender_aliases = {'sex', gender_canonical}

male_canonical = 'male'
female_canonical = 'female'
gender_alias_dict = {
    'm': male_canonical,
    male_canonical: male_canonical,
    'f': female_canonical,
    female_canonical: female_canonical,
}

standard_designation_canonical = 'standard_designation'
standard_designation_aliases = {
    'official_name',
    'standard_name',
    'strain_name',
    'strain',
    standard_designation_canonical,
}

sample_id_canonical = 'sample_id'
sample_id_aliases = {
    'internal_name',
    'id',
    sample_id_canonical,
}

notes_canonical = 'notes'
notes_aliases = {
    'note',
    'comment',
    'comments',
    notes_canonical
}


def normalize_header(header):
    """
    Some headers are just treated as key/value pairs but some headers (such as Gender) have
    special meaning and so we must make sure to convert these headers to their canonical form
    :param header: the header string to normalize
    :return: the normalized string
    """
    # we always want to trim whitespace
    header = header.strip()
    if not header:
        # this is just an empty cell
        return None
    else:
        # convert to lower case and replace spaces with underscores
        simplified_header = header.lower()
        simplified_header = re.sub(r'\s+', '_', simplified_header)
        simplified_header = re.sub(r'_+', '_', simplified_header)

        # here we convert to canonical if needed
        if simplified_header in gender_aliases:
            return gender_canonical
        elif simplified_header in standard_designation_aliases:
            return standard_designation_canonical
        elif simplified_header in sample_id_aliases:
            return sample_id_canonical
        elif simplified_header in notes_aliases:
            return notes_canonical
        else:
            return header


def normalize_value(header, value):
    value = value.strip()
    if value:
        if header == gender_canonical:
            norm_val = gender_alias_dict.get(value.lower(), None)
            if norm_val is not None:
                return norm_val
            else:
                return value
        else:
            return value
    else:
        return None


def import_sample_anno(sample_anno_file, db):
    with open(sample_anno_file, 'r') as sample_anno_file_handle:
        sample_anno_table = csv.reader(sample_anno_file_handle, delimiter='\t')

        header = next(sample_anno_table)
        header = list(map(normalize_header, header))
        missing_id_count = 0
        total_row_count = 0
        for row in sample_anno_table:
            total_row_count += 1

            norm_vals = [normalize_value(h, v) for h, v in zip(header, row)]
            sample_properties = {h: nv for h, nv in zip(header, norm_vals) if nv and nv != '#N/A'}

            sample_id = sample_properties.pop(sample_id_canonical, None)
            if not sample_id:
                missing_id_count += 1
                continue

            set_dict = dict()
            standard_designation = sample_properties.pop(standard_designation_canonical, None)
            if standard_designation:
                set_dict[standard_designation_canonical] = standard_designation

            gender = sample_properties.pop(gender_canonical, None)
            if gender:
                set_dict[gender_canonical] = gender

            set_dict['properties'] = sample_properties

            # TODO change this to upsert when we know it should work
            db.samples.update(
                {sample_id_canonical: sample_id},
                {'$set': set_dict},
            )

        if missing_id_count:
            err_fmt = 'failed to import {} out of {} rows because of missing sample IDs'
            print(
                err_fmt.format(missing_id_count, total_row_count),
                file=sys.stderr)


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import sample annotations')
    parser.add_argument(
        'sample_annotation_txt',
        help='the tab-delimited sample annotation file. There should be a header row and one row per sample')
    args = parser.parse_args()

    import_sample_anno(args.sample_annotation_txt, mds.init_db())


if __name__ == '__main__':
    main()
