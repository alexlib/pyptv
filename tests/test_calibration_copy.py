import unittest
import copy
from optv.calibration import Calibration

from pyptv.ptv import clone_calibration

class TestCalibrationCopy(unittest.TestCase):
    def test_clone_calibration(self):
        # Create a Calibration object and set some attributes
        cal = Calibration()
        # Example: set some attributes if possible
        # cal.some_attr = 42
        # cal.other_attr = 'test'
        
        # Clone the calibration
        cal_copy = clone_calibration(cal)
        
        # Check that the copy is not the same object
        self.assertIsNot(cal, cal_copy)
        # Check that the copy is of the same type
        self.assertIsInstance(cal_copy, Calibration)
        # Optionally, check that attributes are equal
        # self.assertEqual(cal.some_attr, cal_copy.some_attr)
        # self.assertEqual(cal.other_attr, cal_copy.other_attr)

if __name__ == "__main__":
    unittest.main()
