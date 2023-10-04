# -*- coding: utf-8 -*-
# Author  : xiayouran
# Email   : youran.xia@foxmail.com
# Datetime: 2023/10/1 20:29
# Filename: build_kg.py
import os
import json
from py2neo import Graph, Node, Relationship, NodeMatcher


class WOTKG(object):
    def __init__(self, clean_kg=True):
        self.clean_kg = clean_kg
        self.entity_tank = []
        self.entity_price = []
        self.entity_firepower = []
        self.entity_mobility = []
        self.entity_survivability = []
        self.entity_spotting = []
        self.data_path = '../data/tank_list_detail.json'

        self.graph = Graph('neo4j://172.20.203.172:7687', auth=('neo4j', 'lyp123456'))  # use your ip 172.20.197.99
        self.matcher = NodeMatcher(self.graph)
        if self.clean_kg:
            self.graph.delete_all()

    def build_KG(self):
        self.collect_entity()
        self.create_all_node()
        self.create_relation()

    def check_zero(self, v_str):
        if not v_str:
            return True
        elif len(v_str) == 2 and v_str[0] == '0' and v_str[1] in ['秒', '米', '%', '度']:
            return True
        else:
            return False

    def add_entity(self, entity_name, v_item: dict):
        for k_, v_ in v_item.items():
            if self.check_zero(v_):
                continue
            if entity_name == 'Price':
                self.entity_price.append(('Price', k_, v_))
            elif entity_name == 'Firepower':
                self.entity_firepower.append(('Firepower', k_, v_))
            elif entity_name == 'Mobility':
                self.entity_mobility.append(('Mobility', k_, v_))
            elif entity_name == 'Survivability':
                self.entity_survivability.append(('Survivability', k_, v_))
            elif entity_name == 'Spotting':
                self.entity_spotting.append(('Spotting', k_, v_))

    def collect_entity(self):
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        for tank_item in data_json.values():
            tank_name = tank_item['tank_name']
            for k, v in tank_item.items():
                if k[0] == 't' or not v:
                    continue
                if k == '价格':
                    if isinstance(v, str):
                        self.entity_price.append(('Price', '金币', v))
                    else:
                        self.add_entity('Price', v)
                elif k == '火力':
                    self.add_entity('Firepower', v)
                elif k == '机动性':
                    self.add_entity('Mobility', v)
                elif k == '防护':
                    self.add_entity('Survivability', v)
                elif k == '侦察':
                    self.add_entity('Spotting', v)
                else:
                    self.entity_tank.append((tank_name, k, v))

            self.entity_tank.append((tank_name, '价格', 'Price'))
            self.entity_tank.append((tank_name, '火力', 'Firepower'))
            self.entity_tank.append((tank_name, '机动性', 'Mobility'))
            self.entity_tank.append((tank_name, '防护', 'Survivability'))
            self.entity_tank.append((tank_name, '侦察', 'Spotting'))

    def create_node(self, entity_list, entity_name='Tank'):
        head_nodes = []
        tail_nodes = []

        for (head, rela, tail) in entity_list:
            if head not in head_nodes:
                head_nodes.append(head)
                node = Node(entity_name, name=head)
                self.graph.create(node)
            if tail not in tail_nodes:
                tail_nodes.append(tail)
                node = Node("{}Value".format(entity_name), name=tail)
                self.graph.create(node)

    def create_all_node(self):
        self.create_node(self.entity_tank, entity_name='Tank')
        self.create_node(self.entity_price, entity_name='Price')
        self.create_node(self.entity_firepower, entity_name='Firepower')
        self.create_node(self.entity_mobility, entity_name='Mobility')
        self.create_node(self.entity_survivability, entity_name='Survivability')
        self.create_node(self.entity_spotting, entity_name='Spotting')

    def create_relation(self):
        all_entity = self.entity_tank + self.entity_price + self.entity_firepower + self.entity_mobility + self.entity_survivability + self.entity_spotting
        for (head, rela, tail) in all_entity:
            if head in ['Price', 'Firepower', 'Mobility', 'Survivability', 'Spotting']:
                node_head = self.matcher.match(head).where(name=head).first()
                node_tail = self.matcher.match('{}Value'.format(head)).where(name=tail).first()
            elif tail in ['Price', 'Firepower', 'Mobility', 'Survivability', 'Spotting']:
                node_head = self.matcher.match('Tank').where(name=head).first()
                node_tail = self.matcher.match(tail).where(name=tail).first()
            else:
                node_head = self.matcher.match('Tank').where(name=head).first()
                node_tail = self.matcher.match('TankValue').where(name=tail).first()
            rela_node = Relationship(node_head, rela, node_tail)
            self.graph.create(rela_node)


class WOTKGPRO(object):
    def __init__(self, clean_kg=True):
        self.clean_kg = clean_kg
        self.entity_tank = []
        self.entity_price = []
        self.entity_firepower = []
        self.entity_mobility = []
        self.entity_survivability = []
        self.entity_spotting = []
        self.all_entity = []
        self.data_path = '../data/tank_list_detail.json'

        self.graph = Graph('neo4j://172.20.203.172:7687', auth=('neo4j', 'lyp123456'))  # use your ip 172.20.197.99
        self.matcher = NodeMatcher(self.graph)
        if self.clean_kg:
            self.graph.delete_all()

    def build_KG(self):
        self.collect_entity()
        self.create_all_node()
        self.create_relation()

    def check_zero(self, v_str):
        if not v_str:
            return True
        elif len(v_str) == 2 and v_str[0] == '0' and v_str[1] in ['秒', '米', '%', '度']:
            return True
        else:
            return False

    def add_entity(self, tank_name, entity_name, v_item: dict):
        for k_, v_ in v_item.items():
            if self.check_zero(v_):
                continue
            if entity_name == 'Price':
                self.entity_price.append(('Price', k_, v_))
            elif entity_name == 'Firepower':
                self.entity_firepower.append(('Firepower', k_, v_))
            elif entity_name == 'Mobility':
                self.entity_mobility.append(('Mobility', k_, v_))
            elif entity_name == 'Survivability':
                self.entity_survivability.append(('Survivability', k_, v_))
            elif entity_name == 'Spotting':
                self.entity_spotting.append(('Spotting', k_, v_))
            self.all_entity.append((tank_name, entity_name, k_, v_))

    def collect_entity(self):
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        for tank_item in data_json.values():
            tank_name = tank_item['tank_name']
            for k, v in tank_item.items():
                if k[0] == 't' or not v:
                    continue
                if k == '价格':
                    if isinstance(v, str):
                        self.entity_price.append(('Price', '金币', v))
                        self.all_entity.append((tank_name, 'Price', '金币', v))
                    else:
                        self.add_entity(tank_name, 'Price', v)
                elif k == '火力':
                    self.add_entity(tank_name, 'Firepower', v)
                elif k == '机动性':
                    self.add_entity(tank_name, 'Mobility', v)
                elif k == '防护':
                    self.add_entity(tank_name, 'Survivability', v)
                elif k == '侦察':
                    self.add_entity(tank_name, 'Spotting', v)
                else:
                    self.entity_tank.append((tank_name, k, v))
                    self.all_entity.append((tank_name, 'Tank', k, v))

    def create_node(self, entity_list, entity_name='Tank'):
        head_nodes = []
        tail_nodes = []

        for (head, rela, tail) in entity_list:
            if head not in head_nodes and head not in ['Price', 'Firepower', 'Mobility', 'Survivability', 'Spotting']:
                head_nodes.append(head)
                node = Node(entity_name, name=head)
                self.graph.create(node)
            if tail not in tail_nodes:
                tail_nodes.append(tail)
                node = Node("{}Value".format(entity_name), name=tail)
                self.graph.create(node)

    def create_all_node(self):
        self.create_node(self.entity_tank, entity_name='Tank')
        self.create_node(self.entity_price, entity_name='Price')
        self.create_node(self.entity_firepower, entity_name='Firepower')
        self.create_node(self.entity_mobility, entity_name='Mobility')
        self.create_node(self.entity_survivability, entity_name='Survivability')
        self.create_node(self.entity_spotting, entity_name='Spotting')

    def create_relation(self):
        for (head, flag_str, rela, tail) in self.all_entity:
            node_head = self.matcher.match('Tank').where(name=head).first()
            node_tail = self.matcher.match('{}Value'.format(flag_str)).where(name=tail).first()
            rela_node = Relationship(node_head, rela, node_tail)
            self.graph.create(rela_node)


if __name__ == '__main__':
    wot_kg = WOTKGPRO(clean_kg=True)
    wot_kg.build_KG()
