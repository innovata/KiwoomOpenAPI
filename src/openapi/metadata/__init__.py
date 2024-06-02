# -*- coding: utf-8 -*-


import os
import csv 


from ipylib.idebug import *




# 데이터 객체
class __TRItem__():

    # Item 파싱을 위한 자료구조 셋업. 파일을 읽어들여서 객체로 저장.
    @tracer.info
    def __init__(self):
        _dir = os.path.dirname(__file__)
        filepath = os.path.join(_dir, 'TRItem.csv')
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self._TRItemStructure = object()
            self._trcodes = []
            for d in reader:
                # 기본값 재조정
                if len(d['unit']) == 0: d.update({'unit':0})
                if len(d['var']) == 0: d.update({'var':None})

                # Document 별로 저장
                id = d['trcode'] + '_' + d['item']
                setattr(self, id, d)

                # TrCode별 item 리스트 생성
                if hasattr(self, d['trcode']): 
                    pass 
                else:
                    setattr(self, d['trcode'], [])
                items = getattr(self, d['trcode'])
                if d['item'] in items:
                    pass 
                else:
                    items.append(d['item'])

                # TrCode 리스트 저장
                if d['trcode'] not in self._trcodes:
                    self._trcodes.append(d['trcode'])

    def get_items(self, trcode):
        try:
            d = getattr(self, trcode)
        except Exception as e:
            logger.error(['정의되지 않은 TR코드에 대한 값은 Empty List 를 반환한다', trcode])
            return []
        else:
            return d
        
    def get_doc(self, trcode, item):
        try:
            return getattr(self, f'{trcode}_{item}')
        except Exception as e:
            logger.error([e, trcode, item])
            return None
        
    def get_value(self, trcode, item, key):
        try:
            d = self.get_doc(trcode, item)
            return d[key]
        except Exception as e:
            logger.error([e, trcode, item, key])
            return None
    


# 데이터 객체
class __RTList__():

    def __init__(self):
        _dir = os.path.dirname(__file__)
        modelName = self.__class__.__name__.replace('_', '')
        filepath = os.path.join(_dir, f'{modelName}.csv')
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self._data = []
            self._realtypeList = []
            for d in reader:
                self._data.append(d)
                setattr(self, d['realtype'], d)
                self._realtypeList.append(d['realtype'])

    @property
    def realtypes(self): return self._realtypeList

    def get_fids(self, realtype):
        return getattr(self, realtype)['fids']


# 데이터 객체
class __RealFID__():

    def __init__(self):
        _dir = os.path.dirname(__file__)
        filepath = os.path.join(_dir, f'{self.__class__.__name__}.csv')
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self._data = []
            self._fidList = []
            for d in reader:
                if 'unit' not in d: d.update({'unit':0})

                self._data.append(d)
                self._fidList.append(d['fid'])
                setattr(self, d['fid'], d)

            self._fidList = list(set(self._fidList))

    def get_doc(self, fid):
        try:
            return getattr(self, fid)
        except Exception as e:
            return None 
    
    def get_value(self, fid, key):
        try:
            return getattr(self, fid)[key]
        except Exception as e:
            return None 

    @property
    def fids(self): return self._fidList







