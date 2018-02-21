import unittest
import EqualityTest


class TestEqualityTest(unittest.TestCase):
    def setUp(self):
        pass

    @unittest.skip
    def test_all(self):
        master_keys, check_keys = EqualityTest.setup(5)
        test_token = EqualityTest.gen_token(master_keys, [3, 3, 3, 3, 3], 5)
        identifier = 5
        check1 = EqualityTest.encrypt(check_keys[0], identifier, 3)
        check2 = EqualityTest.encrypt(check_keys[1], identifier, 3)
        check3 = EqualityTest.encrypt(check_keys[2], identifier, 3)
        check4 = EqualityTest.encrypt(check_keys[3], identifier, 3)
        check5 = EqualityTest.encrypt(check_keys[4], identifier, 3)
        self.assertTrue(EqualityTest.test(test_token, 5, check1, check2, check3, check4, check5))

    def test_on_curves(self):
        master_keys, check_keys = EqualityTest.setup(1)
        b2 = EqualityTest.pairing.b2
        self.assertTrue(EqualityTest.pairing.is_on_curve(master_keys[0]['alpha_multiplied'], b2))
        self.assertTrue(EqualityTest.pairing.is_on_curve(master_keys[0]['gamma_multiplied'], b2))
        b = EqualityTest.pairing.b
        self.assertTrue(EqualityTest.pairing.is_on_curve(check_keys[0]['alpha_g1'], b))

    def test_wrong_identifier(self):
        master_keys, check_keys = EqualityTest.setup(5)
        test_token = EqualityTest.gen_token(master_keys, [3, 3, 3, 3, 3], 5)
        identifier = 5
        other_identifier = 3
        check1 = EqualityTest.encrypt(check_keys[0], identifier, 3)
        check2 = EqualityTest.encrypt(check_keys[1], identifier, 3)
        check3 = EqualityTest.encrypt(check_keys[2], other_identifier, 3)
        check4 = EqualityTest.encrypt(check_keys[3], identifier, 3)
        check5 = EqualityTest.encrypt(check_keys[4], identifier, 3)
        self.assertFalse(EqualityTest.test(test_token, 5, check1, check2, check3, check4, check5))

    def non_equal_checks(self):
        master_keys, check_keys = EqualityTest.setup(5)
        test_token = EqualityTest.gen_token(master_keys, [3, 3, 3, 3, 3], 5)
        identifier = 5
        check1 = EqualityTest.encrypt(check_keys[0], identifier, 3)
        check2 = EqualityTest.encrypt(check_keys[1], identifier, 3)
        check3 = EqualityTest.encrypt(check_keys[2], identifier, 5)   # check not same as required
        check4 = EqualityTest.encrypt(check_keys[3], identifier, 3)
        check5 = EqualityTest.encrypt(check_keys[4], identifier, 3)
        self.assertFalse(EqualityTest.test(test_token, 5, check1, check2, check3, check4, check5))


if __name__ == '__main__':
    unittest.main()