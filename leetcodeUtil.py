import configparser
import os

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
    driverpath = cp.get('leetcode', 'driverpath')
    rst = dict(
        username=username,
        password=password,
        driverpath=driverpath,
    )
    return rst