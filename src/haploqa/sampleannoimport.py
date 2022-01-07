import argparse
import csv
import re
import sys

import haploqa.mongods as mds

sex_canonical = 'sex'
sex_aliases = {'gender', sex_canonical}

male_canonical = 'male'
female_canonical = 'female'
sex_alias_dict = {
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

color_canonical = 'color'


def normalize_header(header):
    """
    Some headers are just treated as key/value pairs but some headers (such as sex) have
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
        if simplified_header in sex_aliases:
            return sex_canonical
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
        if header == sex_canonical:
            norm_val = sex_alias_dict.get(value.lower(), None)
            if norm_val is not None:
                return norm_val
            else:
                return value
        else:
            return value
    else:
        return None


def merge_dicts(dict1, dict2):
    def merge_rec_gen(dict1, dict2):
        for k in set(dict1.keys()).union(dict2.keys()):
            val1 = dict1.get(k, None)
            val2 = dict2.get(k, None)
            if val1 is not None and val2 is not None:
                if isinstance(val1, dict) and isinstance(val2, dict):
                    yield k, dict(merge_rec_gen(val1, val2))
                else:
                    yield k, val1
            elif val1 is None:
                yield k, val2
            else:
                yield k, val1

    return dict(merge_rec_gen(dict1, dict2))


def sample_anno_dicts(sample_anno_file):
    with open(sample_anno_file, 'r') as sample_anno_file_handle:
        sample_properties_dicts = dict()
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

            sample_dict = {sample_id_canonical: sample_id}
            standard_designation = sample_properties.pop(standard_designation_canonical, None)
            if standard_designation:
                sample_dict[standard_designation_canonical] = standard_designation

            sex = sample_properties.pop(sex_canonical, None)
            if sex:
                sample_dict[sex_canonical] = sex

            color = sample_properties.pop(color_canonical, None)
            if color:
                sample_dict[color_canonical] = color

            sample_dict['properties'] = sample_properties
            sample_properties_dicts[sample_id] = sample_dict

        if missing_id_count:
            err_fmt = 'failed to import {} out of {} rows because of missing sample IDs'
            print(
                err_fmt.format(missing_id_count, total_row_count),
                file=sys.stderr)

        print(sample_properties_dicts)
        return sample_properties_dicts


def minimuga_sample_anno_dict(genotype_file):
    with open(genotype_file, 'r') as file_handle:
        table = csv.reader(file_handle, delimiter='\t')
        header = next(table)
        header = list(map(normalize_header, header))
        first_row = [normalize_value(h, v) for h, v in zip(header, next(table))]

        return {
            'sample_id': first_row[0],
            'sex': 'Unknown',
            'properties': {
                'Index': 'NA',
                'Name': first_row[0],
                'Plate': 'NA',
                'Well': 'NA',
                'SentrixPosition': 'NA'
            }
        }
