import haploqa.haploqa as hqa


def test_get_platforms():
    platforms = hqa.get_platforms()
    assert platforms == ['MegaMUGA']


def test_get_sample():
    sample = hqa.get_sample('2014-1')
    assert sample == {'notes': None, 'platform': 'MegaMUGA', 'diet': None, 'sex': None, 'sample_id': '2014-1'}


def test_get_sample_ids():
    sample_ids = hqa.get_sample_ids()
    for id in sample_ids:
        assert id is not None
        assert type(id) is str
    assert len(sample_ids) == len(set(sample_ids))
    con = hqa.connect_db()
    c = con.cursor()
    c.execute('''SELECT DISTINCT sample_id FROM probe_intensities''')
    probe_sample_ids = [x for x, in c]
    assert set(sample_ids) == set(probe_sample_ids)


def test_get_valid_chromosomes():
    valid_chrs = hqa.get_valid_chromosomes('MegaMUGA')
    assert len(valid_chrs) == len(set(valid_chrs))
    assert set(valid_chrs) == set(map(str, range(1, 20))).union(['X', 'Y', 'M'])


def test_probe_data():
    sample_ids = hqa.get_sample_ids()
    assert len(sample_ids) > 0
    for sample_index, sample_id in enumerate(sample_ids):
        sample = hqa.get_sample(sample_id)
        assert sample['platform'] == 'MegaMUGA'
        valid_chrs = hqa.get_valid_chromosomes(sample['platform'])
        assert set(valid_chrs) == set(map(str, range(1, 20))).union(['X', 'Y', 'M'])

        # skip the probe data checks for most samples (it just takes too long)
        if sample_index % 10 == 0:
            for chromosome in valid_chrs:
                probe_data = hqa.get_sample_probe_data(sample_id, chromosome)

                prev_position = None
                good_intensity_count = 0
                for probe_row in probe_data:
                    probeset_id = probe_row['probeset_id']
                    position_bp = probe_row['position_bp']
                    assert position_bp is None or position_bp > 0
                    if prev_position is not None:
                        assert position_bp >= prev_position
                    prev_position = position_bp

                    assert len(probeset_id) > 0
                    if probe_row['probe_a_norm'] is not None and probe_row['probe_b_norm'] is not None:
                        good_intensity_count += 1
                        assert \
                            (probe_row['probe_a_norm'] is None and probe_row['probe_b_norm'] is None) or \
                            (probe_row['probe_a_norm'] >= 0 and probe_row['probe_b_norm'] >= 0)
                        assert probe_row['chromosome'] == chromosome

                # make sure that the good ratio is greater than 90%
                assert good_intensity_count / len(probe_data) > 0.9
