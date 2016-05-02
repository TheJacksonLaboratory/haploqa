import haploqa.mongods as mds


def est_gemm_probs(samples):
    #db.getCollection('snps').find({'engineered_target': {'$exists': 1}})

    # find all the SNPs that have been labeled for engineered targets
    db = mds.get_db()
    gemm_snps = db.snps.find({'engineered_target': {'$exists': 1}})
    return gemm_snps


def main():
    import pprint
    for gemm_snp in est_gemm_probs('hi'):
        print('-------------------')
        pprint.pprint(gemm_snp)


if __name__ == '__main__':
    main()
