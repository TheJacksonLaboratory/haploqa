import argparse
import csv
from functools import cmp_to_key
import re
import sys

import haploqa.mongods as mds


valid_nonnumeric_chromosome_names = ['X', 'Y', 'M', 'MT']


def normalize_chr(chrom):
    """
    This function attempts to standardize how a chromosome is named.
    Eg.: both chrX and x will be mapped to X
    """
    chrom = str(chrom).upper()
    prefixes_to_remove = ['CHROMOSOME', 'CHR']
    for prefix in prefixes_to_remove:
        if chrom.startswith(prefix):
            chrom = chrom[len(prefix):]

    # make sure that the value is valid
    if not chrom in valid_nonnumeric_chromosome_names:
        # will throw a ValueError if this is not an int
        int(chrom)

    return chrom


def chr_cmp(chrom1, chrom2):
    """
    a comparison function for ordering chromosome names
    """

    chrom1 = normalize_chr(chrom1)
    chrom2 = normalize_chr(chrom2)

    def idx(xs, x):
        return xs.index(x) if x in xs else -1

    chrom1_idx = idx(valid_nonnumeric_chromosome_names, chrom1)
    chrom2_idx = idx(valid_nonnumeric_chromosome_names, chrom2)

    if chrom1_idx == -1 and chrom2_idx == -1:
        return int(chrom1) - int(chrom2)
    elif chrom1_idx == -1:
        return -1
    elif chrom2_idx == -1:
        return 1
    else:
        return chrom1_idx - chrom2_idx


def import_snp_anno(snp_anno_file, platform_id, db):
    with open(snp_anno_file, 'r') as snp_anno_file_handle:
        snp_anno_table = csv.reader(snp_anno_file_handle, delimiter='\t')

        header = next(snp_anno_table)
        header_indexes = {x.lower(): i for i, x in enumerate(header)}

        snp_pattern = re.compile('''^\[(.)/(.)\]$''')
        snps = db.snps
        all_chrs = set()
        for row in snp_anno_table:
            try:
                def get_val(column_name):
                    try:
                        val = row[header_indexes[column_name]]
                    except KeyError:
                        val = None

                    if val == "Unknown":
                        val = None

                    return val

                snp_calls = get_val('snp')
                snp_match = snp_pattern.match(snp_calls)
                if not snp_match:
                    raise Exception('unexpected snp calls format: ' + snp_calls)
                x_probe_call, y_probe_call = snp_match.groups()
                chromosome = get_val('chromosome')
                snps.insert_one({
                    'platform_id': platform_id,
                    'snp_id': get_val('name'),
                    'chromosome': chromosome,
                    'position_bp': int(get_val('position')),
                    'x_probe_call': x_probe_call,
                    'y_probe_call': y_probe_call,
                })
                all_chrs.add(chromosome)
            except:
                print('failed to import row:', row, file=sys.stderr)
                raise

        all_chrs = sorted(all_chrs, key=cmp_to_key(chr_cmp))
        db.platforms.insert_one({
            'platform_id': platform_id,
            'chromosomes': all_chrs,
        })


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import SNP annotations')
    parser.add_argument(
        'platform',
        help='the platform for the data we are importing. eg: MegaMUGA'
    )
    parser.add_argument(
        'snp_annotation_txt',
        help='the tab-delimited snp annotation file. There should be a header row and one row per SNP')
    args = parser.parse_args()

    import_snp_anno(args.snp_annotation_txt, args.platform, mds.init_db())


if __name__ == '__main__':
    main()
