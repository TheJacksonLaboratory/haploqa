/**
 * An ordered array of chromosome sizes. This data structure was derived from the data in
 * ftp://hgdownload.cse.ucsc.edu/goldenPath/mm10/database/chromInfo.txt.gz
 * @type Array.<GenoInterval>
 */
var mm10ChrSizes = [
    {
        "chr": "1",
        "size": 195471971,
        "startPos": 0
    },
    {
        "chr": "2",
        "size": 182113224,
        "startPos": 0
    },
    {
        "chr": "3",
        "size": 160039680,
        "startPos": 0
    },
    {
        "chr": "4",
        "size": 156508116,
        "startPos": 0
    },
    {
        "chr": "5",
        "size": 151834684,
        "startPos": 0
    },
    {
        "chr": "6",
        "size": 149736546,
        "startPos": 0
    },
    {
        "chr": "7",
        "size": 145441459,
        "startPos": 0
    },
    {
        "chr": "8",
        "size": 129401213,
        "startPos": 0
    },
    {
        "chr": "9",
        "size": 124595110,
        "startPos": 0
    },
    {
        "chr": "10",
        "size": 130694993,
        "startPos": 0
    },
    {
        "chr": "11",
        "size": 122082543,
        "startPos": 0
    },
    {
        "chr": "12",
        "size": 120129022,
        "startPos": 0
    },
    {
        "chr": "13",
        "size": 120421639,
        "startPos": 0
    },
    {
        "chr": "14",
        "size": 124902244,
        "startPos": 0
    },
    {
        "chr": "15",
        "size": 104043685,
        "startPos": 0
    },
    {
        "chr": "16",
        "size": 98207768,
        "startPos": 0
    },
    {
        "chr": "17",
        "size": 94987271,
        "startPos": 0
    },
    {
        "chr": "18",
        "size": 90702639,
        "startPos": 0
    },
    {
        "chr": "19",
        "size": 61431566,
        "startPos": 0
    },
    {
        "chr": "X",
        "size": 171031299,
        "startPos": 0
    },
    {
        "chr": "Y",
        "size": 91744698,
        "startPos": 0
    },
    {
        "chr": "M",
        "size": 16299,
        "startPos": 0
    }
];

/**
 * An array of cytoband intervals. Note that in addition to the GenoInterval properties each array element has a
 * cytoBandType string property (eg. "gpos66"). This data structure was derived from the data in
 * ftp://hgdownload.cse.ucsc.edu/goldenPath/mm10/database/cytoBand.txt.gz
 * @type Array.<GenoInterval>
 */
var mm10CytoBands = [
    {
        "chr": "1",
        "cytoBandType": "gpos100",
        "size": 8840440,
        "startPos": 0
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 3437950,
        "startPos": 8840440
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 7858169,
        "startPos": 12278390
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 1964543,
        "startPos": 20136559
    },
    {
        "chr": "1",
        "cytoBandType": "gpos100",
        "size": 8840441,
        "startPos": 22101102
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 12278390,
        "startPos": 30941543
    },
    {
        "chr": "1",
        "cytoBandType": "gpos66",
        "size": 11296119,
        "startPos": 43219933
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 1473407,
        "startPos": 54516052
    },
    {
        "chr": "1",
        "cytoBandType": "gpos75",
        "size": 3437949,
        "startPos": 55989459
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 5893627,
        "startPos": 59427408
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 9331577,
        "startPos": 65321035
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 5402491,
        "startPos": 74652612
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 7367034,
        "startPos": 80055103
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 12278390,
        "startPos": 87422137
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 2946814,
        "startPos": 99700527
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 982271,
        "startPos": 102647341
    },
    {
        "chr": "1",
        "cytoBandType": "gpos100",
        "size": 8840441,
        "startPos": 103629612
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 1473407,
        "startPos": 112470053
    },
    {
        "chr": "1",
        "cytoBandType": "gpos100",
        "size": 11787255,
        "startPos": 113943460
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 2946813,
        "startPos": 125730715
    },
    {
        "chr": "1",
        "cytoBandType": "gpos66",
        "size": 10804983,
        "startPos": 128677528
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 7858170,
        "startPos": 139482511
    },
    {
        "chr": "1",
        "cytoBandType": "gpos100",
        "size": 4420221,
        "startPos": 147340681
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 982271,
        "startPos": 151760902
    },
    {
        "chr": "1",
        "cytoBandType": "gpos100",
        "size": 4420220,
        "startPos": 152743173
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 2946814,
        "startPos": 157163393
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 3929085,
        "startPos": 160110207
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 1473407,
        "startPos": 164039292
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 4420220,
        "startPos": 165512699
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 5893627,
        "startPos": 169932919
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 5893628,
        "startPos": 175826546
    },
    {
        "chr": "1",
        "cytoBandType": "gneg",
        "size": 6384762,
        "startPos": 181720174
    },
    {
        "chr": "1",
        "cytoBandType": "gpos33",
        "size": 7367035,
        "startPos": 188104936
    },
    {
        "chr": "2",
        "cytoBandType": "gpos100",
        "size": 14080919,
        "startPos": 0
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 2346820,
        "startPos": 14080919
    },
    {
        "chr": "2",
        "cytoBandType": "gpos33",
        "size": 12672827,
        "startPos": 16427739
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 19243923,
        "startPos": 29100566
    },
    {
        "chr": "2",
        "cytoBandType": "gpos100",
        "size": 12203464,
        "startPos": 48344489
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 469364,
        "startPos": 60547953
    },
    {
        "chr": "2",
        "cytoBandType": "gpos100",
        "size": 7509823,
        "startPos": 61017317
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 3285548,
        "startPos": 68527140
    },
    {
        "chr": "2",
        "cytoBandType": "gpos66",
        "size": 9387280,
        "startPos": 71812688
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 7509824,
        "startPos": 81199968
    },
    {
        "chr": "2",
        "cytoBandType": "gpos100",
        "size": 12672827,
        "startPos": 88709792
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 3754912,
        "startPos": 101382619
    },
    {
        "chr": "2",
        "cytoBandType": "gpos33",
        "size": 7979188,
        "startPos": 105137531
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 2816183,
        "startPos": 113116719
    },
    {
        "chr": "2",
        "cytoBandType": "gpos66",
        "size": 7979188,
        "startPos": 115932902
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 7979188,
        "startPos": 123912090
    },
    {
        "chr": "2",
        "cytoBandType": "gpos33",
        "size": 2816184,
        "startPos": 131891278
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 6571095,
        "startPos": 134707462
    },
    {
        "chr": "2",
        "cytoBandType": "gpos100",
        "size": 5632368,
        "startPos": 141278557
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 938728,
        "startPos": 146910925
    },
    {
        "chr": "2",
        "cytoBandType": "gpos100",
        "size": 4693640,
        "startPos": 147849653
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 6571096,
        "startPos": 152543293
    },
    {
        "chr": "2",
        "cytoBandType": "gpos33",
        "size": 4224275,
        "startPos": 159114389
    },
    {
        "chr": "2",
        "cytoBandType": "gneg",
        "size": 10326008,
        "startPos": 163338664
    },
    {
        "chr": "2",
        "cytoBandType": "gpos33",
        "size": 8448552,
        "startPos": 173664672
    },
    {
        "chr": "3",
        "cytoBandType": "gpos100",
        "size": 18541182,
        "startPos": 0
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 1951703,
        "startPos": 18541182
    },
    {
        "chr": "3",
        "cytoBandType": "gpos66",
        "size": 15125702,
        "startPos": 20492885
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 11222294,
        "startPos": 35618587
    },
    {
        "chr": "3",
        "cytoBandType": "gpos100",
        "size": 9758518,
        "startPos": 46840881
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 4391332,
        "startPos": 56599399
    },
    {
        "chr": "3",
        "cytoBandType": "gpos33",
        "size": 8782666,
        "startPos": 60990731
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 2927555,
        "startPos": 69773397
    },
    {
        "chr": "3",
        "cytoBandType": "gpos100",
        "size": 11222294,
        "startPos": 72700952
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 9270592,
        "startPos": 83923246
    },
    {
        "chr": "3",
        "cytoBandType": "gpos33",
        "size": 4391332,
        "startPos": 93193838
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 8782666,
        "startPos": 97585170
    },
    {
        "chr": "3",
        "cytoBandType": "gpos33",
        "size": 1951703,
        "startPos": 106367836
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 6830962,
        "startPos": 108319539
    },
    {
        "chr": "3",
        "cytoBandType": "gpos100",
        "size": 11710220,
        "startPos": 115150501
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 1951704,
        "startPos": 126860721
    },
    {
        "chr": "3",
        "cytoBandType": "gpos66",
        "size": 9758517,
        "startPos": 128812425
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 5367184,
        "startPos": 138570942
    },
    {
        "chr": "3",
        "cytoBandType": "gpos33",
        "size": 4391333,
        "startPos": 143938126
    },
    {
        "chr": "3",
        "cytoBandType": "gneg",
        "size": 5855110,
        "startPos": 148329459
    },
    {
        "chr": "3",
        "cytoBandType": "gpos33",
        "size": 5855111,
        "startPos": 154184569
    },
    {
        "chr": "4",
        "cytoBandType": "gpos100",
        "size": 14882673,
        "startPos": 0
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 2880518,
        "startPos": 14882673
    },
    {
        "chr": "4",
        "cytoBandType": "gpos100",
        "size": 10561897,
        "startPos": 17763191
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 1920345,
        "startPos": 28325088
    },
    {
        "chr": "4",
        "cytoBandType": "gpos66",
        "size": 13442415,
        "startPos": 30245433
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 8161466,
        "startPos": 43687848
    },
    {
        "chr": "4",
        "cytoBandType": "gpos33",
        "size": 3360604,
        "startPos": 51849314
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 8161466,
        "startPos": 55209918
    },
    {
        "chr": "4",
        "cytoBandType": "gpos33",
        "size": 6241121,
        "startPos": 63371384
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 2400431,
        "startPos": 69612505
    },
    {
        "chr": "4",
        "cytoBandType": "gpos100",
        "size": 12002156,
        "startPos": 72012936
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 5761035,
        "startPos": 84015092
    },
    {
        "chr": "4",
        "cytoBandType": "gpos66",
        "size": 7681380,
        "startPos": 89776127
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 8161466,
        "startPos": 97457507
    },
    {
        "chr": "4",
        "cytoBandType": "gpos66",
        "size": 5280949,
        "startPos": 105618973
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 6721208,
        "startPos": 110899922
    },
    {
        "chr": "4",
        "cytoBandType": "gpos33",
        "size": 2880517,
        "startPos": 117621130
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 10561897,
        "startPos": 120501647
    },
    {
        "chr": "4",
        "cytoBandType": "gpos33",
        "size": 2880518,
        "startPos": 131063544
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 7681380,
        "startPos": 133944062
    },
    {
        "chr": "4",
        "cytoBandType": "gpos100",
        "size": 6241121,
        "startPos": 141625442
    },
    {
        "chr": "4",
        "cytoBandType": "gneg",
        "size": 8641553,
        "startPos": 147866563
    },
    {
        "chr": "5",
        "cytoBandType": "gpos100",
        "size": 14895174,
        "startPos": 0
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 1441469,
        "startPos": 14895174
    },
    {
        "chr": "5",
        "cytoBandType": "gpos66",
        "size": 9129300,
        "startPos": 16336643
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 8168322,
        "startPos": 25465943
    },
    {
        "chr": "5",
        "cytoBandType": "gpos33",
        "size": 1921958,
        "startPos": 33634265
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 14895175,
        "startPos": 35556223
    },
    {
        "chr": "5",
        "cytoBandType": "gpos33",
        "size": 8168321,
        "startPos": 50451398
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 2402448,
        "startPos": 58619719
    },
    {
        "chr": "5",
        "cytoBandType": "gpos100",
        "size": 10570769,
        "startPos": 61022167
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 1921958,
        "startPos": 71592936
    },
    {
        "chr": "5",
        "cytoBandType": "gpos66",
        "size": 4324406,
        "startPos": 73514894
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 3843916,
        "startPos": 77839300
    },
    {
        "chr": "5",
        "cytoBandType": "gpos100",
        "size": 9609790,
        "startPos": 81683216
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 2402447,
        "startPos": 91293006
    },
    {
        "chr": "5",
        "cytoBandType": "gpos33",
        "size": 5765874,
        "startPos": 93695453
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 2402448,
        "startPos": 99461327
    },
    {
        "chr": "5",
        "cytoBandType": "gpos33",
        "size": 5765874,
        "startPos": 101863775
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 17297622,
        "startPos": 107629649
    },
    {
        "chr": "5",
        "cytoBandType": "gpos33",
        "size": 1921958,
        "startPos": 124927271
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 960979,
        "startPos": 126849229
    },
    {
        "chr": "5",
        "cytoBandType": "gpos33",
        "size": 2882937,
        "startPos": 127810208
    },
    {
        "chr": "5",
        "cytoBandType": "gneg",
        "size": 15375664,
        "startPos": 130693145
    },
    {
        "chr": "5",
        "cytoBandType": "gpos33",
        "size": 5765875,
        "startPos": 146068809
    },
    {
        "chr": "6",
        "cytoBandType": "gpos100",
        "size": 16637394,
        "startPos": 0
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 4893351,
        "startPos": 16637394
    },
    {
        "chr": "6",
        "cytoBandType": "gpos100",
        "size": 5872021,
        "startPos": 21530745
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 978670,
        "startPos": 27402766
    },
    {
        "chr": "6",
        "cytoBandType": "gpos100",
        "size": 5872022,
        "startPos": 28381436
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 7340027,
        "startPos": 34253458
    },
    {
        "chr": "6",
        "cytoBandType": "gpos66",
        "size": 2936010,
        "startPos": 41593485
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 1468006,
        "startPos": 44529495
    },
    {
        "chr": "6",
        "cytoBandType": "gpos66",
        "size": 4893351,
        "startPos": 45997501
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 11744043,
        "startPos": 50890852
    },
    {
        "chr": "6",
        "cytoBandType": "gpos100",
        "size": 11744042,
        "startPos": 62634895
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 2446676,
        "startPos": 74378937
    },
    {
        "chr": "6",
        "cytoBandType": "gpos66",
        "size": 9297367,
        "startPos": 76825613
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 8318697,
        "startPos": 86122980
    },
    {
        "chr": "6",
        "cytoBandType": "gpos33",
        "size": 1468006,
        "startPos": 94441677
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 7340026,
        "startPos": 95909683
    },
    {
        "chr": "6",
        "cytoBandType": "gpos100",
        "size": 5382687,
        "startPos": 103249709
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 978670,
        "startPos": 108632396
    },
    {
        "chr": "6",
        "cytoBandType": "gpos100",
        "size": 7340027,
        "startPos": 109611066
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 5872021,
        "startPos": 116951093
    },
    {
        "chr": "6",
        "cytoBandType": "gpos33",
        "size": 2446676,
        "startPos": 122823114
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 6850691,
        "startPos": 125269790
    },
    {
        "chr": "6",
        "cytoBandType": "gpos66",
        "size": 7340027,
        "startPos": 132120481
    },
    {
        "chr": "6",
        "cytoBandType": "gneg",
        "size": 3425346,
        "startPos": 139460508
    },
    {
        "chr": "6",
        "cytoBandType": "gpos33",
        "size": 6850692,
        "startPos": 142885854
    },
    {
        "chr": "7",
        "cytoBandType": "gpos100",
        "size": 15202939,
        "startPos": 0
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 3040588,
        "startPos": 15202939
    },
    {
        "chr": "7",
        "cytoBandType": "gpos33",
        "size": 10135294,
        "startPos": 18243527
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 6081176,
        "startPos": 28378821
    },
    {
        "chr": "7",
        "cytoBandType": "gpos33",
        "size": 3040588,
        "startPos": 34459997
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 10135293,
        "startPos": 37500585
    },
    {
        "chr": "7",
        "cytoBandType": "gpos33",
        "size": 6587941,
        "startPos": 47635878
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 6587940,
        "startPos": 54223819
    },
    {
        "chr": "7",
        "cytoBandType": "gpos100",
        "size": 10642058,
        "startPos": 60811759
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 5574412,
        "startPos": 71453817
    },
    {
        "chr": "7",
        "cytoBandType": "gpos66",
        "size": 3547352,
        "startPos": 77028229
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 9628529,
        "startPos": 80575581
    },
    {
        "chr": "7",
        "cytoBandType": "gpos100",
        "size": 9628529,
        "startPos": 90204110
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 2533823,
        "startPos": 99832639
    },
    {
        "chr": "7",
        "cytoBandType": "gpos33",
        "size": 9121764,
        "startPos": 102366462
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 7094705,
        "startPos": 111488226
    },
    {
        "chr": "7",
        "cytoBandType": "gpos33",
        "size": 4560882,
        "startPos": 118582931
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 14189411,
        "startPos": 123143813
    },
    {
        "chr": "7",
        "cytoBandType": "gpos33",
        "size": 3547353,
        "startPos": 137333224
    },
    {
        "chr": "7",
        "cytoBandType": "gneg",
        "size": 4560882,
        "startPos": 140880577
    },
    {
        "chr": "8",
        "cytoBandType": "gpos100",
        "size": 15940729,
        "startPos": 0
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 937690,
        "startPos": 15940729
    },
    {
        "chr": "8",
        "cytoBandType": "gpos33",
        "size": 3281914,
        "startPos": 16878419
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 9376900,
        "startPos": 20160333
    },
    {
        "chr": "8",
        "cytoBandType": "gpos33",
        "size": 4219605,
        "startPos": 29537233
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 10314589,
        "startPos": 33756838
    },
    {
        "chr": "8",
        "cytoBandType": "gpos66",
        "size": 4219605,
        "startPos": 44071427
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 1875380,
        "startPos": 48291032
    },
    {
        "chr": "8",
        "cytoBandType": "gpos66",
        "size": 5626139,
        "startPos": 50166412
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 3750760,
        "startPos": 55792551
    },
    {
        "chr": "8",
        "cytoBandType": "gpos100",
        "size": 7501520,
        "startPos": 59543311
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 937690,
        "startPos": 67044831
    },
    {
        "chr": "8",
        "cytoBandType": "gpos100",
        "size": 6563829,
        "startPos": 67982521
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 5626140,
        "startPos": 74546350
    },
    {
        "chr": "8",
        "cytoBandType": "gpos33",
        "size": 4688450,
        "startPos": 80172490
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 5157295,
        "startPos": 84860940
    },
    {
        "chr": "8",
        "cytoBandType": "gpos33",
        "size": 1406535,
        "startPos": 90018235
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 4219604,
        "startPos": 91424770
    },
    {
        "chr": "8",
        "cytoBandType": "gpos100",
        "size": 7501520,
        "startPos": 95644374
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 937690,
        "startPos": 103145894
    },
    {
        "chr": "8",
        "cytoBandType": "gpos33",
        "size": 6563830,
        "startPos": 104083584
    },
    {
        "chr": "8",
        "cytoBandType": "gneg",
        "size": 13127659,
        "startPos": 110647414
    },
    {
        "chr": "8",
        "cytoBandType": "gpos33",
        "size": 5626140,
        "startPos": 123775073
    },
    {
        "chr": "9",
        "cytoBandType": "gpos100",
        "size": 14412120,
        "startPos": 0
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 5113979,
        "startPos": 14412120
    },
    {
        "chr": "9",
        "cytoBandType": "gpos33",
        "size": 4649071,
        "startPos": 19526099
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 13947214,
        "startPos": 24175170
    },
    {
        "chr": "9",
        "cytoBandType": "gpos66",
        "size": 6043793,
        "startPos": 38122384
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 2324535,
        "startPos": 44166177
    },
    {
        "chr": "9",
        "cytoBandType": "gpos66",
        "size": 8368328,
        "startPos": 46490712
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 8368329,
        "startPos": 54859040
    },
    {
        "chr": "9",
        "cytoBandType": "gpos33",
        "size": 6508700,
        "startPos": 63227369
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 7903421,
        "startPos": 69736069
    },
    {
        "chr": "9",
        "cytoBandType": "gpos33",
        "size": 5113978,
        "startPos": 77639490
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 1859629,
        "startPos": 82753468
    },
    {
        "chr": "9",
        "cytoBandType": "gpos100",
        "size": 6508699,
        "startPos": 84613097
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 464907,
        "startPos": 91121796
    },
    {
        "chr": "9",
        "cytoBandType": "gpos100",
        "size": 9298143,
        "startPos": 91586703
    },
    {
        "chr": "9",
        "cytoBandType": "gpos66",
        "size": 929814,
        "startPos": 100884846
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 6508700,
        "startPos": 101814660
    },
    {
        "chr": "9",
        "cytoBandType": "gpos33",
        "size": 2789443,
        "startPos": 108323360
    },
    {
        "chr": "9",
        "cytoBandType": "gneg",
        "size": 8833235,
        "startPos": 111112803
    },
    {
        "chr": "9",
        "cytoBandType": "gpos33",
        "size": 4649072,
        "startPos": 119946038
    },
    {
        "chr": "10",
        "cytoBandType": "gpos100",
        "size": 12822904,
        "startPos": 0
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 4931887,
        "startPos": 12822904
    },
    {
        "chr": "10",
        "cytoBandType": "gpos33",
        "size": 5918264,
        "startPos": 17754791
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 9863773,
        "startPos": 23673055
    },
    {
        "chr": "10",
        "cytoBandType": "gpos100",
        "size": 7891018,
        "startPos": 33536828
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 6904641,
        "startPos": 41427846
    },
    {
        "chr": "10",
        "cytoBandType": "gpos100",
        "size": 7891019,
        "startPos": 48332487
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 7891018,
        "startPos": 56223506
    },
    {
        "chr": "10",
        "cytoBandType": "gpos100",
        "size": 3945510,
        "startPos": 64114524
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 493188,
        "startPos": 68060034
    },
    {
        "chr": "10",
        "cytoBandType": "gpos100",
        "size": 6411453,
        "startPos": 68553222
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 14302471,
        "startPos": 74964675
    },
    {
        "chr": "10",
        "cytoBandType": "gpos33",
        "size": 6904641,
        "startPos": 89267146
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 2959132,
        "startPos": 96171787
    },
    {
        "chr": "10",
        "cytoBandType": "gpos100",
        "size": 12822905,
        "startPos": 99130919
    },
    {
        "chr": "10",
        "cytoBandType": "gneg",
        "size": 12822905,
        "startPos": 111953824
    },
    {
        "chr": "10",
        "cytoBandType": "gpos33",
        "size": 5918264,
        "startPos": 124776729
    },
    {
        "chr": "11",
        "cytoBandType": "gpos100",
        "size": 13046989,
        "startPos": 0
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 4193675,
        "startPos": 13046989
    },
    {
        "chr": "11",
        "cytoBandType": "gpos100",
        "size": 4659639,
        "startPos": 17240664
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 3727711,
        "startPos": 21900303
    },
    {
        "chr": "11",
        "cytoBandType": "gpos100",
        "size": 4659639,
        "startPos": 25628014
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 6057531,
        "startPos": 30287653
    },
    {
        "chr": "11",
        "cytoBandType": "gpos100",
        "size": 6989459,
        "startPos": 36345184
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 4659639,
        "startPos": 43334643
    },
    {
        "chr": "11",
        "cytoBandType": "gpos33",
        "size": 1863855,
        "startPos": 47994282
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 10251206,
        "startPos": 49858137
    },
    {
        "chr": "11",
        "cytoBandType": "gpos33",
        "size": 2795784,
        "startPos": 60109343
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 7921386,
        "startPos": 62905127
    },
    {
        "chr": "11",
        "cytoBandType": "gpos33",
        "size": 3261747,
        "startPos": 70826513
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 7921387,
        "startPos": 74088260
    },
    {
        "chr": "11",
        "cytoBandType": "gpos100",
        "size": 8387350,
        "startPos": 82009647
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 12115062,
        "startPos": 90396997
    },
    {
        "chr": "11",
        "cytoBandType": "gpos66",
        "size": 7921386,
        "startPos": 102512059
    },
    {
        "chr": "11",
        "cytoBandType": "gneg",
        "size": 11649098,
        "startPos": 110433445
    },
    {
        "chr": "12",
        "cytoBandType": "gpos100",
        "size": 17601321,
        "startPos": 0
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 3520265,
        "startPos": 17601321
    },
    {
        "chr": "12",
        "cytoBandType": "gpos66",
        "size": 4840363,
        "startPos": 21121586
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 5720430,
        "startPos": 25961949
    },
    {
        "chr": "12",
        "cytoBandType": "gpos33",
        "size": 7480562,
        "startPos": 31682379
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 4840363,
        "startPos": 39162941
    },
    {
        "chr": "12",
        "cytoBandType": "gpos33",
        "size": 880066,
        "startPos": 44003304
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 7040529,
        "startPos": 44883370
    },
    {
        "chr": "12",
        "cytoBandType": "gpos100",
        "size": 14081058,
        "startPos": 51923899
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 5280396,
        "startPos": 66004957
    },
    {
        "chr": "12",
        "cytoBandType": "gpos100",
        "size": 9680727,
        "startPos": 71285353
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 4400331,
        "startPos": 80966080
    },
    {
        "chr": "12",
        "cytoBandType": "gpos33",
        "size": 3080231,
        "startPos": 85366411
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 7040529,
        "startPos": 88446642
    },
    {
        "chr": "12",
        "cytoBandType": "gpos100",
        "size": 10560793,
        "startPos": 95487171
    },
    {
        "chr": "12",
        "cytoBandType": "gneg",
        "size": 8360628,
        "startPos": 106047964
    },
    {
        "chr": "12",
        "cytoBandType": "gpos66",
        "size": 5720430,
        "startPos": 114408592
    },
    {
        "chr": "13",
        "cytoBandType": "gpos100",
        "size": 16286533,
        "startPos": 0
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 4935313,
        "startPos": 16286533
    },
    {
        "chr": "13",
        "cytoBandType": "gpos66",
        "size": 8390032,
        "startPos": 21221846
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 3454719,
        "startPos": 29611878
    },
    {
        "chr": "13",
        "cytoBandType": "gpos33",
        "size": 8390032,
        "startPos": 33066597
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 2961188,
        "startPos": 41456629
    },
    {
        "chr": "13",
        "cytoBandType": "gpos33",
        "size": 8390032,
        "startPos": 44417817
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 6415907,
        "startPos": 52807849
    },
    {
        "chr": "13",
        "cytoBandType": "gpos33",
        "size": 2467657,
        "startPos": 59223756
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 7896501,
        "startPos": 61691413
    },
    {
        "chr": "13",
        "cytoBandType": "gpos33",
        "size": 8883563,
        "startPos": 69587914
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 2467657,
        "startPos": 78471477
    },
    {
        "chr": "13",
        "cytoBandType": "gpos100",
        "size": 13818877,
        "startPos": 80939134
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 11844751,
        "startPos": 94758011
    },
    {
        "chr": "13",
        "cytoBandType": "gpos33",
        "size": 3948250,
        "startPos": 106602762
    },
    {
        "chr": "13",
        "cytoBandType": "gneg",
        "size": 5922376,
        "startPos": 110551012
    },
    {
        "chr": "13",
        "cytoBandType": "gpos33",
        "size": 3948251,
        "startPos": 116473388
    },
    {
        "chr": "14",
        "cytoBandType": "gpos100",
        "size": 14988269,
        "startPos": 0
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 4496481,
        "startPos": 14988269
    },
    {
        "chr": "14",
        "cytoBandType": "gpos33",
        "size": 10491788,
        "startPos": 19484750
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 13489442,
        "startPos": 29976538
    },
    {
        "chr": "14",
        "cytoBandType": "gpos100",
        "size": 8493353,
        "startPos": 43465980
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 2997654,
        "startPos": 51959333
    },
    {
        "chr": "14",
        "cytoBandType": "gpos66",
        "size": 4996090,
        "startPos": 54956987
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 8992961,
        "startPos": 59953077
    },
    {
        "chr": "14",
        "cytoBandType": "gpos33",
        "size": 3996872,
        "startPos": 68946038
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 11990615,
        "startPos": 72942910
    },
    {
        "chr": "14",
        "cytoBandType": "gpos66",
        "size": 3996872,
        "startPos": 84933525
    },
    {
        "chr": "14",
        "cytoBandType": "gpos100",
        "size": 9992180,
        "startPos": 88930397
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 999218,
        "startPos": 98922577
    },
    {
        "chr": "14",
        "cytoBandType": "gpos100",
        "size": 7494134,
        "startPos": 99921795
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 3497263,
        "startPos": 107415929
    },
    {
        "chr": "14",
        "cytoBandType": "gpos100",
        "size": 9992180,
        "startPos": 110913192
    },
    {
        "chr": "14",
        "cytoBandType": "gneg",
        "size": 3996872,
        "startPos": 120905372
    },
    {
        "chr": "15",
        "cytoBandType": "gpos100",
        "size": 16500320,
        "startPos": 0
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 7791817,
        "startPos": 16500320
    },
    {
        "chr": "15",
        "cytoBandType": "gpos33",
        "size": 5500107,
        "startPos": 24292137
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 2291711,
        "startPos": 29792244
    },
    {
        "chr": "15",
        "cytoBandType": "gpos100",
        "size": 11000214,
        "startPos": 32083955
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 1833369,
        "startPos": 43084169
    },
    {
        "chr": "15",
        "cytoBandType": "gpos66",
        "size": 5041764,
        "startPos": 44917538
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 3666738,
        "startPos": 49959302
    },
    {
        "chr": "15",
        "cytoBandType": "gpos100",
        "size": 12833582,
        "startPos": 53626040
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 2291711,
        "startPos": 66459622
    },
    {
        "chr": "15",
        "cytoBandType": "gpos66",
        "size": 8708502,
        "startPos": 68751333
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 6416792,
        "startPos": 77459835
    },
    {
        "chr": "15",
        "cytoBandType": "gpos33",
        "size": 3208395,
        "startPos": 83876627
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 8708502,
        "startPos": 87085022
    },
    {
        "chr": "15",
        "cytoBandType": "gpos66",
        "size": 5500107,
        "startPos": 95793524
    },
    {
        "chr": "15",
        "cytoBandType": "gneg",
        "size": 916685,
        "startPos": 101293631
    },
    {
        "chr": "15",
        "cytoBandType": "gpos33",
        "size": 1833369,
        "startPos": 102210316
    },
    {
        "chr": "16",
        "cytoBandType": "gpos100",
        "size": 15432649,
        "startPos": 0
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 935312,
        "startPos": 15432649
    },
    {
        "chr": "16",
        "cytoBandType": "gpos33",
        "size": 4208904,
        "startPos": 16367961
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 5611873,
        "startPos": 20576865
    },
    {
        "chr": "16",
        "cytoBandType": "gpos33",
        "size": 6079528,
        "startPos": 26188738
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 6079529,
        "startPos": 32268266
    },
    {
        "chr": "16",
        "cytoBandType": "gpos33",
        "size": 6547184,
        "startPos": 38347795
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 8885465,
        "startPos": 44894979
    },
    {
        "chr": "16",
        "cytoBandType": "gpos66",
        "size": 4208904,
        "startPos": 53780444
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 935312,
        "startPos": 57989348
    },
    {
        "chr": "16",
        "cytoBandType": "gpos66",
        "size": 7950153,
        "startPos": 58924660
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 3741248,
        "startPos": 66874813
    },
    {
        "chr": "16",
        "cytoBandType": "gpos100",
        "size": 8417809,
        "startPos": 70616061
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 467656,
        "startPos": 79033870
    },
    {
        "chr": "16",
        "cytoBandType": "gpos100",
        "size": 12159057,
        "startPos": 79501526
    },
    {
        "chr": "16",
        "cytoBandType": "gneg",
        "size": 6547185,
        "startPos": 91660583
    },
    {
        "chr": "17",
        "cytoBandType": "gpos100",
        "size": 13943085,
        "startPos": 0
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 2178607,
        "startPos": 13943085
    },
    {
        "chr": "17",
        "cytoBandType": "gpos33",
        "size": 1307165,
        "startPos": 16121692
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 4357214,
        "startPos": 17428857
    },
    {
        "chr": "17",
        "cytoBandType": "gpos66",
        "size": 9585871,
        "startPos": 21786071
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 8714429,
        "startPos": 31371942
    },
    {
        "chr": "17",
        "cytoBandType": "gpos33",
        "size": 1307164,
        "startPos": 40086371
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 4357214,
        "startPos": 41393535
    },
    {
        "chr": "17",
        "cytoBandType": "gpos66",
        "size": 10021593,
        "startPos": 45750749
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 4357214,
        "startPos": 55772342
    },
    {
        "chr": "17",
        "cytoBandType": "gpos100",
        "size": 7842986,
        "startPos": 60129556
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 871443,
        "startPos": 67972542
    },
    {
        "chr": "17",
        "cytoBandType": "gpos100",
        "size": 4357214,
        "startPos": 68843985
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 5228657,
        "startPos": 73201199
    },
    {
        "chr": "17",
        "cytoBandType": "gpos33",
        "size": 4357215,
        "startPos": 78429856
    },
    {
        "chr": "17",
        "cytoBandType": "gneg",
        "size": 6100100,
        "startPos": 82787071
    },
    {
        "chr": "17",
        "cytoBandType": "gpos33",
        "size": 6100100,
        "startPos": 88887171
    },
    {
        "chr": "18",
        "cytoBandType": "gpos100",
        "size": 19406146,
        "startPos": 0
    },
    {
        "chr": "18",
        "cytoBandType": "gneg",
        "size": 10124945,
        "startPos": 19406146
    },
    {
        "chr": "18",
        "cytoBandType": "gpos66",
        "size": 5906219,
        "startPos": 29531091
    },
    {
        "chr": "18",
        "cytoBandType": "gneg",
        "size": 1687491,
        "startPos": 35437310
    },
    {
        "chr": "18",
        "cytoBandType": "gpos100",
        "size": 8437454,
        "startPos": 37124801
    },
    {
        "chr": "18",
        "cytoBandType": "gneg",
        "size": 4218728,
        "startPos": 45562255
    },
    {
        "chr": "18",
        "cytoBandType": "gpos100",
        "size": 4218727,
        "startPos": 49780983
    },
    {
        "chr": "18",
        "cytoBandType": "gneg",
        "size": 421873,
        "startPos": 53999710
    },
    {
        "chr": "18",
        "cytoBandType": "gpos100",
        "size": 6328091,
        "startPos": 54421583
    },
    {
        "chr": "18",
        "cytoBandType": "gneg",
        "size": 7171837,
        "startPos": 60749674
    },
    {
        "chr": "18",
        "cytoBandType": "gpos33",
        "size": 7171836,
        "startPos": 67921511
    },
    {
        "chr": "18",
        "cytoBandType": "gneg",
        "size": 8437455,
        "startPos": 75093347
    },
    {
        "chr": "18",
        "cytoBandType": "gpos33",
        "size": 7171837,
        "startPos": 83530802
    },
    {
        "chr": "19",
        "cytoBandType": "gpos100",
        "size": 16680094,
        "startPos": 0
    },
    {
        "chr": "19",
        "cytoBandType": "gneg",
        "size": 8950294,
        "startPos": 16680094
    },
    {
        "chr": "19",
        "cytoBandType": "gpos66",
        "size": 9357126,
        "startPos": 25630388
    },
    {
        "chr": "19",
        "cytoBandType": "gneg",
        "size": 3254652,
        "startPos": 34987514
    },
    {
        "chr": "19",
        "cytoBandType": "gpos66",
        "size": 9357126,
        "startPos": 38242166
    },
    {
        "chr": "19",
        "cytoBandType": "gneg",
        "size": 4068316,
        "startPos": 47599292
    },
    {
        "chr": "19",
        "cytoBandType": "gpos33",
        "size": 7322968,
        "startPos": 51667608
    },
    {
        "chr": "19",
        "cytoBandType": "gneg",
        "size": 2440990,
        "startPos": 58990576
    },
    {
        "chr": "X",
        "cytoBandType": "gpos100",
        "size": 15772338,
        "startPos": 0
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 2464428,
        "startPos": 15772338
    },
    {
        "chr": "X",
        "cytoBandType": "gpos33",
        "size": 2957314,
        "startPos": 18236766
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 6900398,
        "startPos": 21194080
    },
    {
        "chr": "X",
        "cytoBandType": "gpos66",
        "size": 5421741,
        "startPos": 28094478
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 985772,
        "startPos": 33516219
    },
    {
        "chr": "X",
        "cytoBandType": "gpos66",
        "size": 5421741,
        "startPos": 34501991
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 7886170,
        "startPos": 39923732
    },
    {
        "chr": "X",
        "cytoBandType": "gpos66",
        "size": 8379055,
        "startPos": 47809902
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 6900398,
        "startPos": 56188957
    },
    {
        "chr": "X",
        "cytoBandType": "gpos66",
        "size": 6407512,
        "startPos": 63089355
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 1478657,
        "startPos": 69496867
    },
    {
        "chr": "X",
        "cytoBandType": "gpos66",
        "size": 6407513,
        "startPos": 70975524
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 4928856,
        "startPos": 77383037
    },
    {
        "chr": "X",
        "cytoBandType": "gpos100",
        "size": 8871940,
        "startPos": 82311893
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 985771,
        "startPos": 91183833
    },
    {
        "chr": "X",
        "cytoBandType": "gpos100",
        "size": 8871941,
        "startPos": 92169604
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 8871941,
        "startPos": 101041545
    },
    {
        "chr": "X",
        "cytoBandType": "gpos100",
        "size": 10350597,
        "startPos": 109913486
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 985771,
        "startPos": 120264083
    },
    {
        "chr": "X",
        "cytoBandType": "gpos100",
        "size": 13800797,
        "startPos": 121249854
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 6407512,
        "startPos": 135050651
    },
    {
        "chr": "X",
        "cytoBandType": "gpos33",
        "size": 7393284,
        "startPos": 141458163
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 7393284,
        "startPos": 148851447
    },
    {
        "chr": "X",
        "cytoBandType": "gpos33",
        "size": 7393284,
        "startPos": 156244731
    },
    {
        "chr": "X",
        "cytoBandType": "gneg",
        "size": 7393284,
        "startPos": 163638015
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos100",
        "size": 20642557,
        "startPos": 0
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos66",
        "size": 12041491,
        "startPos": 20642557
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos33",
        "size": 12614896,
        "startPos": 32684048
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos100",
        "size": 9174470,
        "startPos": 45298944
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos33",
        "size": 7454257,
        "startPos": 54473414
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos100",
        "size": 10321278,
        "startPos": 61927671
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos33",
        "size": 10894683,
        "startPos": 72248949
    },
    {
        "chr": "Y",
        "cytoBandType": "gpos66",
        "size": 8601066,
        "startPos": 83143632
    }
];

var mm10ChrBand = [
    {
        "chr": "1",
        "size": 195471971,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "2",
        "size": 182113224,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "3",
        "size": 160039680,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "4",
        "size": 156508116,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "5",
        "size": 151834684,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "6",
        "size": 149736546,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "7",
        "size": 145441459,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "8",
        "size": 129401213,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "9",
        "size": 124595110,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "10",
        "size": 130694993,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "11",
        "size": 122082543,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "12",
        "size": 120129022,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "13",
        "size": 120421639,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "14",
        "size": 124902244,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "15",
        "size": 104043685,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "16",
        "size": 98207768,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "17",
        "size": 94987271,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "18",
        "size": 90702639,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "19",
        "size": 61431566,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "X",
        "size": 171031299,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "Y",
        "size": 91744698,
        "cytoBandType":"gpos",
        "startPos": 0
    },
    {
        "chr": "M",
        "size": 16299,
        "cytoBandType":"gpos",
        "startPos": 0
    }
];
