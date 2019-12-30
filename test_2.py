# coding:utf-8
#
# Author: BONFY<foreverbonfy@163.com>
# Github: https://github.com/bonfy
# Repo:   https://github.com/bonfy/leetcode
# Usage:  Leetcode solution downloader and auto generate readme
#
import requests
import os
import configparser
import json
import time
import datetime
import re
import sys
import html
import logging

from pathlib import Path
from selenium import webdriver
from collections import namedtuple, OrderedDict
from leetcodeUtil import *

HOME = Path.cwd()
CONFIG_FILE = Path.joinpath(HOME, 'config.cfg')
COOKIE_PATH = Path.joinpath(HOME, 'cookies.json')
BASE_URL = 'https://leetcode.com'
# If you have proxy, change PROXIES below
PROXIES = None
HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'leetcode.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36',
    # NOQA
}
CONFIG = get_config_from_file(CONFIG_FILE)


class Leetcode:

    def __init__(self):
        self.problems = {}
        self.acDict = {}
        self.submissions = []
        self.num_solved = 0
        self.num_total = 0
        self.num_lock = 0
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.proxies = PROXIES
        self.cookies = None

    def login(self):
        logging.info('logging in {}'.format(CONFIG['username']))
        LOGIN_URL = self.base_url + '/accounts/login/'  # NOQA
        if not CONFIG['username'] or not CONFIG['password']:
            raise Exception(
                'Leetcode - Please input your username and password in config.cfg.'
            )

        usr = CONFIG['username']
        pwd = CONFIG['password']
        # driver = webdriver.PhantomJS()
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('--disable-gpu')
        executable_path = CONFIG.get('driverpath')
        # driver = webdriver.Chrome(
        #     chrome_options=options, executable_path=executable_path
        # )
        driver = webdriver.Chrome(
            executable_path=executable_path
        )
        driver.get(LOGIN_URL)

        # Wait for update
        time.sleep(10)

        driver.find_element_by_name('login').send_keys(usr)
        driver.find_element_by_name('password').send_keys(pwd)
        # driver.find_element_by_id('id_remember').click()
        btns = driver.find_elements_by_tag_name('button')
        # print(btns)
        submit_btn = btns[1]
        submit_btn.click()

        time.sleep(5)
        webdriver_cookies = driver.get_cookies()
        driver.close()
        if 'LEETCODE_SESSION' not in [
            cookie['name'] for cookie in webdriver_cookies
        ]:
            raise Exception('Please check your config or your network.')

        with open(COOKIE_PATH, 'w') as f:
            json.dump(webdriver_cookies, f, indent=2)
        self.cookies = {
            str(cookie['name']): str(cookie['value'])
            for cookie in webdriver_cookies
        }
        self.session.cookies.update(self.cookies)

    def get_problems(self):
        url = self.base_url + "/api/problems/all/"
        time.sleep(5)
        resp = self.session.get(url, timeout=10)

        question_list = json.loads(resp.content.decode('utf-8'))
        for question in question_list['stat_status_pairs']:
            # 'ac', 'notac' or 'none'
            question_info = {}
            question_id = question['stat']['question_id']
            question_info['status'] = question['status']
            question_info['slug'] = question['stat']['question__title_slug']
            question_info['title'] = question['stat']['question_title']
            # difficulty，1 easy，2 medium，3 hard
            question_info['difficulty'] = question['difficulty']['level']
            # only record ac submission
            if question_info['status'] == 'ac':
                self.acDict[question_id] = question_info

        print(self.acDict)

    def get_timestamp(self):
        for question_id in self.acDict:
            question_slug = self.acDict[question_id]
            timestamp = self.get_submission(question_slug)
            self.acDict[question_id][timestamp] = timestamp

        print(self.acDict)

    def get_submission(self, slug):
        url = self.base_url + "/graphql"
        params = {'operationName': "Submissions",
                  'variables': {"offset": 0, "limit": 20, "lastKey": '', "questionSlug": slug},
                  'query': '''query Submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!) {
                    submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug) {
                    lastKey
                    hasNext
                    submissions {
                        id
                        statusDisplay
                        lang
                        runtime
                        timestamp
                        url
                        isPending
                        __typename
                    }
                    __typename
                }
            }'''
                  }

        json_data = json.dumps(params).encode('utf8')
        # headers = {'User-Agent': HEADERS['User-Agent'], 'Connection': 'keep-alive',
        #            'Referer': 'https://leetcode.com/accounts/login/',
        #            "Content-Type": "application/json"}
        resp = self.session.post(url, data=json_data, timeout=10)
        print(resp)
        content = resp.json()
        for submission in content['data']['submissionList']['submissions']:
            status = submission['status_display']
            print(status)
            timestamp = submission['timestamp']
            if status == 'Accepted':
                return timestamp
        return 1

    @property
    def is_login(self):
        """ validate if the cookie exists and not overtime """
        api_url = self.base_url + '/api/problems/algorithms/'  # NOQA
        if not COOKIE_PATH.exists():
            return False

        with open(COOKIE_PATH, 'r') as f:
            webdriver_cookies = json.load(f)
        self.cookies = {
            str(cookie['name']): str(cookie['value'])
            for cookie in webdriver_cookies
        }
        self.session.cookies.update(self.cookies)
        r = self.session.get(api_url, proxies=PROXIES)
        if r.status_code != 200:
            return False

        data = json.loads(r.text)
        return 'user_name' in data and data['user_name'] != ''

def todo(leetcode):
    leetcode.login()
    if not leetcode.is_login:
        leetcode.login()
    logging.info('Login successfully!')
    leetcode.get_problems()
    leetcode.get_timestamp()


def main():
    logging.basicConfig(filename='log.log', level=logging.INFO)
    logger = logging.getLogger("main")
    logger.info('Master runs')
    leetcode = Leetcode()
    todo(leetcode)


if __name__ == '__main__':
    main()
