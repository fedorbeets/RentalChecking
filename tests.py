import unittest
import equality_test


class TestEqualityTest(unittest.TestCase):
    def setUp(self):
        pass

    @unittest.skip
    def test_all(self):
        master_keys, check_keys = equality_test.setup(5)
        test_token = equality_test.gen_token(master_keys, [3, 3, 3, 3, 3], 5)
        identifier = 5
        check1 = equality_test.encrypt(check_keys[0], identifier, 3)
        check2 = equality_test.encrypt(check_keys[1], identifier, 3)
        check3 = equality_test.encrypt(check_keys[2], identifier, 3)
        check4 = equality_test.encrypt(check_keys[3], identifier, 3)
        check5 = equality_test.encrypt(check_keys[4], identifier, 3)
        self.assertTrue(equality_test.test(test_token, 5, check1, check2, check3, check4, check5))

    def test_on_curves(self):
        master_keys, check_keys = equality_test.setup(1)
        b2 = equality_test.pairing.b2
        self.assertTrue(equality_test.pairing.is_on_curve(master_keys[0]['alpha_multiplied'], b2))
        self.assertTrue(equality_test.pairing.is_on_curve(master_keys[0]['gamma_multiplied'], b2))
        b = equality_test.pairing.b
        self.assertTrue(equality_test.pairing.is_on_curve(check_keys[0]['alpha_g1'], b))

    def test_wrong_identifier(self):
        master_keys, check_keys = equality_test.setup(5)
        test_token = equality_test.gen_token(master_keys, [3, 3, 3, 3, 3], 5)
        identifier = 5
        other_identifier = 3
        check1 = equality_test.encrypt(check_keys[0], identifier, 3)
        check2 = equality_test.encrypt(check_keys[1], identifier, 3)
        check3 = equality_test.encrypt(check_keys[2], other_identifier, 3)
        check4 = equality_test.encrypt(check_keys[3], identifier, 3)
        check5 = equality_test.encrypt(check_keys[4], identifier, 3)
        self.assertFalse(equality_test.test(test_token, 5, check1, check2, check3, check4, check5))

    def non_equal_checks(self):
        master_keys, check_keys = equality_test.setup(5)
        test_token = equality_test.gen_token(master_keys, [3, 3, 3, 3, 3], 5)
        identifier = 5
        check1 = equality_test.encrypt(check_keys[0], identifier, 3)
        check2 = equality_test.encrypt(check_keys[1], identifier, 3)
        check3 = equality_test.encrypt(check_keys[2], identifier, 5)   # check not same as required
        check4 = equality_test.encrypt(check_keys[3], identifier, 3)
        check5 = equality_test.encrypt(check_keys[4], identifier, 3)
        self.assertFalse(equality_test.test(test_token, 5, check1, check2, check3, check4, check5))


if __name__ == '__main__':
    unittest.main()