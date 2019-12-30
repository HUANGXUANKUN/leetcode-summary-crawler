import configparser
import logging
import os
import re


def get_config_from_file(config_file):
    cp = configparser.ConfigParser()
    cp.read(config_file)
    if 'leetcode' not in list(cp.sections()):
        raise Exception('Please create config.cfg first.')

    username = cp.get('leetcode', 'username')
    if os.getenv('leetcode_username'):
        username = os.getenv('leetcode_username')
    password = cp.get('leetcode', 'password')
    if os.getenv('leetcode_password'):
        password = os.getenv('leetcode_password')
    if not username or not password:  # username and password not none
        raise Exception(
            'Please input your username and password in config.cfg.'
        )

    language = cp.get('leetcode', 'language')
    if not language:
        language = 'python'  # language default python
    repo = cp.get('leetcode', 'repo')
    if not repo:
        raise Exception('Please input your Github repo address')

    driverpath = cp.get('leetcode', 'driverpath')
    rst = dict(
        username=username,
        password=password,
        language=language.lower(),
        repo=repo,
        driverpath=driverpath,
    )
    return rst

def rep_unicode_in_code(code):
    """
    Replace unicode to str in the code
    like '\u003D' to '='
    :param code: type str
    :return: type str
    """
    pattern = re.compile('(\\\\u[0-9a-zA-Z]{4})')
    m = pattern.findall(code)
    for item in set(m):
        code = code.replace(item, chr(int(item[2:], 16)))  # item[2:]去掉\u

    return code