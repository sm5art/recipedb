from recipedb.science.matching import parse_and_separate_units

import unittest

class TestMatching(unittest.TestCase):
    def test_parse_and_separate_units_positive_case(self):
        output, text = parse_and_separate_units('1 (16 ounce) can diced tomatoes')
        self.assertEqual(output['qty'], 16.0)
        self.assertEqual(output['unit']['unit_id'], 'ounce')
    
    def test_parse_and_separate_units_negative_case(self):
        output, text = parse_and_separate_units('1 (16 dank ounce) can diced tomatoes')
        self.assertEqual(output['qty'], 16.0)
        self.assertEqual(output['unit']['unit_id'], 'ounce')



if __name__ == '__main__':
    unittest.main()