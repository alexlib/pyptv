import os
import sys
import traceback

par_dir_prefix = 'parameters'


def printException():
    print('=' * 50)
    print('Exception:', sys.exc_info()[1])
    print("getcwd()=%s;curdir=%s" % (os.getcwd(), os.curdir))
    print('Traceback:')
    traceback.print_tb(sys.exc_info()[2])
    print('=' * 50)
