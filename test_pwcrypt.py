import unittest

import pwcrypt

class TestConfig(unittest.TestCase):
    def testStoreAndGetConfig(self):
        password = "Testpassword"

        salt, hash = pwcrypt.hash_new_password(password=password)

        self.assertTrue(pwcrypt.is_correct_password(salt=salt, pw_hash=hash, password=password), "Serverurl not stored propery")

if __name__ == '__main__':
    unittest.main()