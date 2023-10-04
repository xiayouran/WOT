# -*- coding: utf-8 -*-
# Author  : xiayouran
# Email   : youran.xia@foxmail.com
# Datetime: 2023/9/29 22:43
# Filename: spider_wot.py
import os
import time
import copy
import json
import glob
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class WOTSpider:
    def __init__(self):
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/117.0.0.0 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.post_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Length': '135',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.from_data = {
            'filter[nation]': '',
            'filter[type]': 'lightTank',
            'filter[role]': '',
            'filter[tier]': '',
            'filter[language]': 'zh-cn',
            'filter[premium]': '0,1'
        }

        self.tank_info = {
            '系别': '',
            '类型': '',
            '等级': '',
            '角色': '',
            '性质': '',
            '历史背景': '',
            '价格': {
                '银币': '',
                '经验': ''
            },
            '火力': {
                '损伤': '',
                '装甲穿透力': '',
                '火炮装填时间': '',
                '最小弹震持续时间': '',
                '最大弹震持续时间': '',
                '射速': '',
                '平均每分钟损伤': '',
                '瞄准时间': '',
                '100米精度': '',
                '弹药容量': ''
            },
            '机动性': {
                '重量/最大载重量': '',
                '发动机功率': '',
                '单位功率': '',
                '最大速度': '',
                '旋转速度': '',
                '炮塔旋转速度': ''
            },
            '防护': {
                '生命值': '',
                '车体装甲': '',
                '炮塔装甲': '',
                '悬挂装置维修时间': ''
            },
            '侦察': {
                '观察范围': '',
                '通信距离': ''
            }
        }

        self.data_path = '../data'
        self.tank_list_url = 'https://wotgame.cn/wotpbe/tankopedia/api/vehicles/by_filters/'
        self.tank_url = 'https://wotgame.cn/zh-cn/tankopedia/'
        self.tank_label = ['lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG']
        self.tanks = {}

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片，提升速度
        chrome_options.add_argument('--headless')  # 关闭界面
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, timeout=100)

    def get_html(self, url, method='GET', from_data=None):
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.base_headers)
            else:
                response = requests.post(url, from_data, headers=self.base_headers | self.post_headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as err:
            print(err)
            return ''

    def is_span_with_value(self, driver):
        try:
            element = driver.find_element(By.XPATH, "//span[@data-bind=\"text: ttc().getFormattedBestParam('maxHealth', 'gt')\"]")
            data = element.text.strip()
            if data:
                return True
        except:
            return False

    def get_html_driver(self, url):
        self.driver.get(url)
        self.wait.until(self.is_span_with_value)
        page_source = self.driver.page_source

        return page_source

    def parser_tanklist_html(self, html_text):
        json_data = json.loads(html_text)
        for data in json_data['data']['data']:
            self.tanks[data[0] + '_' + data[4]] = {
                'tank_nation': data[0],
                'tank_type': data[1],
                'tank_rank': data[3],
                'tank_name': data[4],
                'tank_name_s': data[5],
                'tank_url': data[6],
                'tank_id': data[7]
            }

    def parser_tankinfo_html(self, html_text):
        tank_info = copy.deepcopy(self.tank_info)
        soup = BeautifulSoup(html_text, 'lxml')
        # tank_name = soup.find(name='h1', attrs={'class': 'garage_title garage_title__inline js-tank-title'}).strip()
        tank_statistic = soup.find_all(name='div', attrs={'class': 'tank-statistic_item'})
        for ts in tank_statistic:
            ts_text = [t for t in ts.get_text().split('\n') if t]
            if len(ts_text) == 5:
                tank_info['价格'] = {
                    '银币': ts_text[-3],
                    '经验': ts_text[-1]
                }
            else:
                tank_info[ts_text[0]] = ts_text[-1]

        tank_property1 = soup.find(name='p', attrs='garage_objection')
        tank_property2 = soup.find(name='p', attrs='garage_objection garage_objection__collector')
        if tank_property1:
            tank_info['性质'] = tank_property1.text
        elif tank_property2:
            tank_info['性质'] = tank_property2.text
        else:
            tank_info['性质'] = '银币坦克'

        tank_desc_tag = soup.find(name='p', attrs='tank-description_notification')
        if tank_desc_tag:
            tank_info['历史背景'] = tank_desc_tag.text

        tank_parameter = soup.find_all(name='div', attrs={'class': 'specification_block'})
        for tp_tag in tank_parameter:
            param_text = tp_tag.find_next(name='h2', attrs={'class': 'specification_title specification_title__sub'}).get_text()
            # spec_param = tp_tag.find_all_next(name='div', attrs={'class': 'specification_item'})
            spec_param = [tag for tag in tp_tag.contents if isinstance(tag, Tag) and tag.attrs['class'] == ['specification_item']]
            spec_info = {}
            for tp in spec_param:
                tp_text = [t for t in tp.get_text().replace(' ', '').split('\n') if t]
                if not tp_text or not tp_text[0][0].isdigit():
                    continue
                spec_info[tp_text[-1]] = ' '.join(tp_text[:-1])
            tank_info[param_text] = spec_info

        return tank_info

    def save_json(self, file_path, json_data):
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

    def load_json(self, json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        return json_data

    def merge_json(self):
        file_list = glob.glob(os.path.join(self.data_path, '*.json'))
        tanks = {}
        for file in file_list:
            if 'tank_list' in file:
                continue
            with open(file, 'r', encoding='utf-8') as f:
                data_json = json.load(f)
            tank_name = data_json['tank_nation'] + '_' + data_json['tank_name']
            tanks[tank_name] = data_json

        with open(os.path.join(self.data_path, 'tank_list_detail.json'), 'w', encoding='utf-8') as f:
            json.dump(tanks, f, indent=4, ensure_ascii=False)

    def run(self):
        for label in self.tank_label:
            self.from_data['filter[type]'] = label
            html_text = self.get_html(self.tank_list_url, method='POST', from_data=self.from_data)
            if not html_text:
                print('[{}] error'.format(label))
                continue
            self.parser_tanklist_html(html_text)
            time.sleep(3)
        self.save_json(os.path.join(self.data_path, 'tank_list.json'), self.tanks)

        # self.tanks = self.load_json(os.path.join(self.data_path, 'tank_list.json'))
        file_list = [os.path.basename(file)[:-5] for file in glob.glob(os.path.join(self.data_path, '*.json'))]

        for k, item in tqdm(self.tanks.items(), desc='Crawling'):
            file_name = k.replace('"', '').replace('“', '').replace('”', '').replace('/', '-').replace('\\', '').replace('*', '+')
            if file_name in file_list:
                continue
            tank_url = self.tank_url + str(item['tank_id']) + '-' + item['tank_url']
            html_text = self.get_html_driver(tank_url)
            # html_text = self.get_html(tank_url, method='GET')
            tank_info = self.parser_tankinfo_html(html_text)
            self.tanks[k].update(tank_info)
            self.save_json(os.path.join(self.data_path, '{}.json'.format(file_name)), self.tanks[k])
            time.sleep(1.5)
        self.save_json(os.path.join(self.data_path, 'tank_list_detail.json'), self.tanks)


if __name__ == '__main__':
    tank_spider = WOTSpider()
    tank_spider.run()
