from typing import Tuple
import os
import hashlib
import hmac
import base64

"""
Generate randomly a salt and hash the provided password. Return the salt and hash to store in the database.
"""
def hash_new_password(password: str) -> Tuple[str, str]:
    salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt).decode('utf-8'), base64.b64encode(pw_hash).decode('utf-8')

"""
Given a previously-stored salt and hash, and a password provided by a user trying to log in, check whether the password is correct.
"""
def is_correct_password(salt: str, pw_hash: str, password: str) -> bool:
    return hmac.compare_digest(base64.b64decode(pw_hash), hashlib.pbkdf2_hmac('sha256', password.encode(), base64.b64decode(salt), 100000))

"""
Prompt the user to input a password, generates a salt and hashed password using the 'hash_new_password' function. 
Prints the salt and hashed password.
"""
if __name__ == '__main__':
    pw = input("Insert Password to hash: ")
    salt, pw_hash = hash_new_password(pw)
    #print("Salt: " + str(list(salt)))
    print("Salt: " +  salt)
    print("Password hash: " + pw_hash)

    pw2 = input("Insert Password to check with generated salt and hash: ")
    print(is_correct_password(salt, pw_hash, pw2))