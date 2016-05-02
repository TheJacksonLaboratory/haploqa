import argparse
import csv

import haploqa.mongods as mds


def import_gemm_anno(anno_file, platform, db):
    with open(anno_file, 'r') as anno_file_handle:
        anno_table = csv.reader(anno_file_handle, delimiter='\t')

        header = next(anno_table)
        header_indexes = {x.lower(): i for i, x in enumerate(header)}

        snps = db.snps

        target_col_idx = None
        marker_col_idx = None
        informative_axis_col_idx = None
        try:
            target_col_idx = header_indexes['target']
            marker_col_idx = header_indexes['marker']
            informative_axis_col_idx = header_indexes['informative axis']
        except KeyError:
            raise Exception(
                'Invalid header. Was expecting "Target", "Marker" and "Informative axis" (tab-separated). '
                'but observed: "{}"'.format(', '.format(header))
            )

        for row in anno_table:
            target = row[target_col_idx].strip()
            marker = row[marker_col_idx].strip()
            inf_axis = row[informative_axis_col_idx].strip().upper()

            if not marker:
                raise Exception('marker missing from row')

            if inf_axis not in {'X', 'Y'}:
                raise Exception('Informative axis should be "X" or "Y", but we observed {} instead.'.format(inf_axis))

            snps.update_one(
                {'platform_id': platform, 'snp_id': marker},
                {'$set': {'engineered_target': target, 'informative_axis': inf_axis}},
            )


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description='import annotations for genetically-engineered constructs')
    parser.add_argument(
        'platform',
        help='the platform for the data we are importing. eg: MegaMUGA or GigaMUGA'
    )
    parser.add_argument(
        'annotation_txt',
        help='the tab-delimited file with header columns: "Target", "Marker" and "Informative axis". '
             'The target column contains an identifiers for the genetically-engineered construct being '
             'targeted by the marker. Informative axis will be "x" or "y" and indicates which axis '
             'is informative for performing a presence/absence call for the genetically-engineered '
             'constructs (the non-informative axis will be ignored)')
    args = parser.parse_args()

    import_gemm_anno(args.annotation_txt, args.platform, mds.init_db())


if __name__ == '__main__':
    main()
