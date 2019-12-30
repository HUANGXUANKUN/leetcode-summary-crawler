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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    # NOQA
}

TODAY_T = time.time()

CONFIG = get_config_from_file(CONFIG_FILE)


class Leetcode:

    def __init__(self):
        self.problems = {}
        self.acDict = {}
        self.sort_dict = {}
        self.num_solved = 0
        self.num_total = 0
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.proxies = PROXIES
        self.cookies = None

    def login(self):
        logger = logging.getLogger(__name__)
        logger.info('logging in {}'.format(CONFIG['username']))
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
        btns = driver.find_elements_by_tag_name('button')
        submit_btn = btns[1]
        submit_btn.click()

        time.sleep(2)
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
        time.sleep(3)
        resp = self.session.get(url, timeout=10)

        question_list = json.loads(resp.content.decode('utf-8'))
        self.num_solved = question_list['num_solved']
        self.num_total = question_list['num_total']

        for question in question_list['stat_status_pairs']:
            # only record ac submission
            if question['status'] == 'ac':
                # 'ac', 'notac' or 'none'
                question_info = {}
                question_id = question['stat']['question_id']
                question_info['status'] = question['status']
                question_info['slug'] = question['stat']['question__title_slug']
                question_info['title'] = question['stat']['question__title']
                question_info['id'] = question_id
                # difficulty，1 easy，2 medium，3 hard
                question_info['difficulty'] = question['difficulty']['level']
                self.acDict[question_id] = question_info
        print(self.acDict)

    def get_submissions(self):
        logger = logging.getLogger(__name__)
        for question_id in self.acDict:
            question_slug = self.acDict[question_id]['slug']
            hasUpdated = self._get_timestamp_url(question_slug, question_id)
            if not hasUpdated:
                logger.warning('Fails to get submission of problem: {}'.format(self.acDict[question_id]['title']))
        print(self.acDict)

    def _get_timestamp_url(self, slug, id):
        logger = logging.getLogger(__name__)
        url = "https://leetcode.com/graphql"
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
        headers = {'User-Agent': HEADERS['User-Agent'], 'Connection': 'keep-alive',
                   'Referer': 'https://leetcode.com/accounts/login/',
                   "Content-Type": "application/json"}
        resp = self.session.post(url, data=json_data, headers=headers, timeout=20)
        submissions = resp.json()['data']['submissionList']['submissions']
        hasUpdated = False;
        acCount = 0
        for submission in submissions:
            status = submission['statusDisplay']
            timestamp = submission['timestamp']
            url = submission['url']
            lang = submission['lang']
            if status == 'Accepted':
                acCount += 1
                if not hasUpdated:
                    self.acDict[id]['timestamp'] = timestamp
                    self.acDict[id]['submission_url'] = url
                    self.acDict[id]['lang'] = lang
                    hasUpdated = True
        # update accuracy of all submissions
        self.acDict[id]['accuracy'] = (acCount * 100) / len(submissions)
        if not hasUpdated:
            return False
        return True

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

    def write_readme(self):
        self._sort_by_timestamp()

        pass;

    def _sort_by_timestamp(self):
        DAY_T = 3600 * 24
        WEEK_T = 7 * DAY_T
        TIME_TITLES = ['1w', '2w', '3w', '4w', '8w', '12w', '24w', '48w']
        TIME_LIST = [1 * WEEK_T, 2 * WEEK_T, 3 * WEEK_T, 4 * WEEK_T, 8 * WEEK_T, 12 * WEEK_T, 24 * WEEK_T, 48 * WEEK_T]
        sorted_dict = {}

        # Initialize list in sorted_dict
        for title in TIME_TITLES:
            sorted_dict[title] = []

        # sort the question into sorted_dict by timestamp
        for question in self.acDict:
            timestamp = question['timestamp']
            diff = TODAY_T - timestamp
            print(diff / (24 * 3600))
            less_than_a_year = False
            for i in range(len(TIME_TITLES)):
                print(TIME_TITLES)
                if diff < TIME_LIST[i]:
                    sorted_dict[TIME_TITLES[i]].append(question)
                    less_than_a_year = True
                    break

            if not less_than_a_year:
                sorted_dict['rest'].append(question)

        self.sort_dict = sorted_dict


def todo(leetcode):
    leetcode.login()
    if not leetcode.is_login:
        leetcode.login()
    logging.info('Login successfully!')
    leetcode.get_problems()
    leetcode.get_submissions()
    leetcode.write_readme()


def main():
    logging.basicConfig(filename='log.log', level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Crawler starts')
    leetcode = Leetcode()

    while True:
        todo(leetcode)
        time.sleep(24 * 60 * 60)


if __name__ == '__main__':
    main()
