from pyptv import pyptv_batch


def test_pyptv_batch():
    # assert cli.cli() == 'CLI template'
    pyptv_batch.main('./test_cavity', 10000, 10004)
