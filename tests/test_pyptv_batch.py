from pyptv import pyptv_batch


def test_pyptv_batch():
    # assert cli.cli() == 'CLI template'
    pyptv_batch.main('./tests/test_cavity', 10000, 10004)
