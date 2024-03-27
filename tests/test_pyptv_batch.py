from pyptv.pyptv_batch import main


def test_pyptv_batch():
    """ Test pyptv_batch.py """
    main('./tests/test_cavity', first=10000, last=10004)
