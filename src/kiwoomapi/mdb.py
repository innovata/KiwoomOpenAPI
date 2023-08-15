# -*- coding: utf-8 -*-
"""
API 내부에서 사용하는 Memory DB
"""
import os 
import sqlite3


import pandas as pd


from ipylib.idebug import *
from ipylib.ifile import FileReader, FileWriter



DB_FILE_PATH = os.path.join(os.path.dirname(__file__), 'mdb.db')
conn = sqlite3.connect(DB_FILE_PATH)





class MemoryDB(object):

    def __init__(self, modelName):
        self.modelName = modelName
        self._setup_model()

    def _load_file(self, modelName):
        current_path = os.path.dirname(__file__)
        file = f'{modelName}.json'
        filepath = os.path.join(current_path, 'metadata', file)
        filepath = os.path.abspath(filepath)
        print(filepath)

        data = FileReader.read_json(filepath)
        # pp.pprint(data)
        return data
    
    def _setup_model(self):
        data = self._load_file(self.modelName)
        df = pd.DataFrame(data)
        dic = df.to_dict('tight')
        self.schemaCols = dic['columns']
    
    def _create_model(self):
        data = self._load_file(self.modelName)
        df = pd.DataFrame(data)
        dic = df.to_dict('tight')
        # pp.pprint(dic)
        # pp.pprint(dic['data'])
        q_cols = ", ".join(self.schemaCols)
        # print({'q_cols': q_cols})
        data = dic['data']
    
        cur = conn.cursor()

        # 테이블 삭제 후 생성
        query = f"DROP TABLE IF EXISTS {self.modelName};"
        cur.execute(query)
        query = f"CREATE TABLE {self.modelName}({q_cols});"
        cur.execute(query)

        # 데이터 저장
        q_values = ", ".join(['?'] * len(self.schemaCols))
        query = f"INSERT INTO {self.modelName}({q_cols}) VALUES({q_values})"
        # print({'query': query})
        cur.executemany(query, data)
        conn.commit()

    def select_all(self):
        cur = conn.cursor()
        res = cur.execute(f"SELECT * FROM {self.modelName}")
        data = res.fetchall()
        # pp.pprint(data)
        df = pd.DataFrame(data, columns=self.schemaCols)
        return df.to_dict('records')
    
    def select(self, filter):
        for k, v in filter.items(): break 
        query = f"SELECT * FROM {self.modelName} WHERE {k} == '{v}'"
        # print({'query': query})
        cur = conn.cursor()
        res = cur.execute(query)
        tpls = res.fetchone()
        # print(self.schemaCols)
        print(tpls)
        
        # d = {}
        # for col, val in zip(self.schemaCols, tpls):
        #     d.update({col: val})
        # return d
        
        data = [tpls]
        df = pd.DataFrame(data, columns=self.schemaCols)
        return df.to_dict('records')[0]
    
    def view(self):
        data = self.select_all()
        return pd.DataFrame(data)




CALL_PRICE_UNIT_DATA = [
    {"unit": 1, "left": 0, "right": 2000,},
    {"unit": 5, "left": 2000, "right": 5000},
    {"unit": 10, "left": 5000, "right": 20000},
    {"unit": 50, "left": 20000, "right": 50000},
    {"unit": 100, "left": 50000, "right": 200000},
    {"unit": 500, "left": 200000, "right": 500000},
    {"unit": 1000, "left": 500000, "right": 10000000},
]


from kiwoomapi.metadata import ErrorCode


ErrorCodeMDB = {}
for d in ErrorCode.data:
    key = str(d['code'])
    ErrorCodeMDB.update({key: d['msg']})
