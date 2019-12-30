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

TODAY_T = time.time()
DAY_T = 3600 * 24
WEEK_T = 7 * DAY_T
TIME_TITLES = ['1w', '2w', '3w', '4w', '8w', '12w', '24w', '48w', 'rest']
TIME_LIST = [1 * WEEK_T, 2 * WEEK_T, 3 * WEEK_T, 4 * WEEK_T, 8 * WEEK_T, 12 * WEEK_T, 24 * WEEK_T, 48 * WEEK_T,
             sys.maxsize]


class Leetcode:

    def __init__(self):
        self.problems = {}
        self.acDict = {}
        self.sort_dict = {}
        self.num_solved = 0
        self.num_total = 0
        self.base_url = 'https://leetcode.com'

    def prepare_data(self):
        self.num_solved = 134
        self.num_total = 1388
        acDict = {}

        acDict[1377] = {'title': 'House Robber III 1',
                        'slug': 'House-Robber-3',
                        'accuracy': 99,
                        'difficulty': 1,
                        'submission_url': '/submissions/detail/288978095',
                        'timestamp': 1575462591,
                        'lang': 'cpp',
                        'id': 1377
                        }

        acDict[2] = {'title': 'two sum',
                     'slug': 'two-sum',
                     'accuracy': 88,
                     'difficulty': 1,
                     'submission_url': '/submissions/detail/288978095',
                     'timestamp': 1578469591,
                     'lang': 'cpp',
                     'id': 2
                     }

        acDict[56] = {'title': 'Diameter of Binary Tree',
                      'slug': 'diameter-of-binary-tree',
                      'accuracy': 45,
                      'difficulty': 1,
                      'submission_url': '/submissions/detail/288978095',
                      'timestamp': 1527462591,
                      'lang': 'java',
                      'id': 56
                      }

        acDict[18] = {'title': 'Three Sum',
                      'slug': 'three-sum',
                      'accuracy': 48,
                      'difficulty': 2,
                      'submission_url': '/submissions/detail/288978095',
                      'timestamp': 1577417591,
                      'id': 18,
                      'lang': 'java'
                      }

        acDict[35] = {'title': 'Subtract the Product and Sum of Digits of an Integer',
                      'slug': 'subtract-the-product',
                      'accuracy': 45,
                      'difficulty': 1,
                      'submission_url': '/submissions/detail/288978095',
                      'timestamp': 1577492591,
                      'id': 35,
                      'lang': 'java'
                      }
        self.acDict = acDict

    def write_readme(self):
        self._sort_by_timestamp()
        """Write Readme to current folder"""
        md = '''# :pencil2: Leetcode Solved Summary
                Update time:  {tm}
                Auto created by [leetcode_generate](https://github.com/HUANGXUANKUN/leetcode-summary-generator)
                I have solved **{num_solved}   /   {num_total}** problems
                If you want to use this tool please follow this [User Guide](https://github.com/HUANGXUANKUN/leetcode-summary-generatorREADME.md)
                If you have any question, please give me an [issue](https://github.com/HUANGXUANKUN/leetcode-summary-generator/issues).
                ''' \
            .format(
            tm=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
            num_solved=self.num_solved,
            num_total=self.num_total,
        )
        md += '\n'
        for title in TIME_TITLES:
            list = self.sort_dict[title]
            if len(list) > 0:
                md += '## {}\n'.format(title)
                md += '| # | Problem Code | Submission | Difficulty | Accuracy |\
                        |:---:|:---:|:---:|:---:|:---:|'
                for problem in list:
                    md += '|{id}|[{title}]({problem_url})|[{lang}]({submission_url})|{difficulty}| {accuracy}|'.format(
                        id=problem['id'],
                        title=problem['title'],
                        lang=problem['lang'].capitalize(),
                        problem_url=self.base_url + '/problems/' + problem['slug'],
                        submission_url=self.base_url + problem['submission_url'],
                        difficulty=problem['difficulty'],
                        accuracy=problem['accuracy']
                    )

        with open('README.md', 'w') as f:
            f.write(md)

    def _sort_by_timestamp(self):
        sorted_dict = {}

        # Initialize list in sorted_dict
        for title in TIME_TITLES:
            sorted_dict[title] = []

        # sort the question into sorted_dict by timestamp
        for question_id in sorted(self.acDict.keys()):
            question = self.acDict[question_id]
            timestamp = question['timestamp']
            diff = TODAY_T - timestamp
            less_than_a_year = False
            for i in range(len(TIME_TITLES)):
                if diff < TIME_LIST[i]:
                    sorted_dict[TIME_TITLES[i]].append(question)
                    less_than_a_year = True
                    break
            if not less_than_a_year:
                sorted_dict['rest'].append(question)
        self.sort_dict = sorted_dict
        print(sorted_dict)


def todo(leetcode):
    logging.info('Login successfully!')
    leetcode.prepare_data()
    leetcode.write_readme()


def main():
    logging.basicConfig(filename='test_log.log', level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('Crawler starts')
    leetcode = Leetcode()
    todo(leetcode)


if __name__ == '__main__':
    main()
