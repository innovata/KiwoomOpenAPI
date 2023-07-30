# -*- coding: utf-8 -*-
from test._testenv import *
from ipylib.datacls import BaseDataClass

from PyQt5.QtCore import QObject, pyqtSlot

import kiwoomapi
from kiwoomapi import OpenAPI


issname, isscode = '삼성전자', '005930'


class MainTester(QObject):

    def __init__(self):  super().__init__()
    def run(self):
        self.login()
    def login(self):
        login = kiwoomapi.LoginAPI()
        login.ConnectSent.connect(self.recv_login)
        login.CommConnect()
    @pyqtSlot(int)
    def recv_login(self, ErrCode): 
        print({'ErrCode':ErrCode})
        for i in [4]:
            func = f'test{str(i).zfill(2)}'
            getattr(self, func)()

    """로그인-버전처리"""
    def test01(self):
        OpenAPI.OnEventConnect.connect(self.OnEventConnect)
        v = kiwoomapi.CommConnect()
        print(['CommConnect', v, type(v)])
    """기타함수"""
    def test02(self):
        v = kiwoomapi.GetBranchCodeName()
        print(['GetBranchCodeName', v, type(v)])
        if not isinstance(v, list): raise

        v = kiwoomapi.GetCodeListByMarket('0')
        print(['GetCodeListByMarket', v, type(v)])
        if not isinstance(v, list): raise

        v = kiwoomapi.GetMasterCodeName(isscode)
        print(['GetMasterCodeName', v, type(v)])
        if not isinstance(v, str): raise

        v = kiwoomapi.GetMasterConstruction(isscode)
        print(['GetMasterConstruction', v, type(v)])
        if not isinstance(v, str): raise

        v = kiwoomapi.GetMasterLastPrice(isscode)
        print(['GetMasterLastPrice', v, type(v)])
        if not isinstance(v, int): raise

        v = kiwoomapi.GetMasterListedStockDate(isscode)
        print(['GetMasterListedStockDate', v, type(v)])
        if not isinstance(v, datetime): raise

        v = kiwoomapi.GetMasterListedStockCnt(isscode)
        print(['GetMasterListedStockCnt', v, type(v)])
        if not isinstance(v, int): raise

        v = kiwoomapi.GetMasterStockState(isscode)
        print(['GetMasterStockState', v, type(v)])
        if not isinstance(v, dict): raise

        # mktcds = db.UpjongMarketCode.distinct('code')
        # for ujcd in mktcds:
        #     v = kiwoomapi.GetUpjongCode(ujcd)
        #     print(['GetUpjongCode', ujcd, v, type(v)])
        #     if not isinstance(v, list): raise

        v = kiwoomapi.GetServerGubun()
        print(['GetServerGubun',v, type(v)])
        if not isinstance(v, str): raise

        v = kiwoomapi.GetUpjongNameByCode('002')
        print(['GetUpjongNameByCode',v, type(v)])
        if not isinstance(v, str): raise

        v = kiwoomapi.IsOrderWarningETF(isscode)
        print(['IsOrderWarningETF',v, type(v)])
        if not isinstance(v, bool): raise

        v = kiwoomapi.IsOrderWarningStock(isscode)
        print(['IsOrderWarningStock',v, type(v)])
        if not isinstance(v, bool): raise

        v = kiwoomapi.GetMasterStockInfo(isscode)
        print(['GetMasterStockInfo',v, type(v)])
        if not isinstance(v, dict): raise

        # kiwoomapi.ShowAccountWindow()
    """TR조회"""
    def test03(self):
        # m = datamodels.TRInput()
        # data = m.load({'trname':'주식기본정보요청'}, {'id':1, 'value':1, '_id':0})
        # for d in data:
        #     try:
        #         v = kiwoomapi.SetInputValue(d['id'], d['value'])
        #         print(['SetInputValue', v, type(v), d])
        #     except Exception as e:
        #         print(['SetInputValue', e, d])

        pretty_title('케이스1')
        v = kiwoomapi.SetInputValue('종목코드', isscode)
        print(['SetInputValue', v, type(v)])

        v = kiwoomapi.CommRqData('요청명','opt10001',0,'8000')
        print(['CommRqData', v, type(v)])

        v = kiwoomapi.GetRepeatCnt('opt10001', '요청명')
        print(['GetRepeatCnt', v, type(v)])

        pretty_title('케이스2::GetRepeatCnt 몇개?')
        sleep(2)
        kiwoomapi.SetInputValue('종목코드', isscode)
        kiwoomapi.SetInputValue('기준일자', '20230210')
        kiwoomapi.SetInputValue('수정주가구분', '1')
        v = kiwoomapi.CommRqData(isscode,'opt10081',0,'8001')
        print(['CommRqData', v, type(v)])
        v = kiwoomapi.GetRepeatCnt('opt10081', isscode)
        print(['GetRepeatCnt', v, type(v)])

        pretty_title('케이스3::인풋없이 요청만 하면 에러')
        sleep(2)
        v = kiwoomapi.CommRqData('요청명','opt10001',0,'8000')
        print(['CommRqData', v, type(v)])
    """실시간데이터처리"""
    def test04(self):
        v = kiwoomapi.SetRealReg('5000', '09', '20;214;215', '1')
        print(['SetRealReg->', v, type(v)])

        v = kiwoomapi.SetRealRemove('ALL', 'ALL')
        print(['SetRealRemove->', v, type(v)])

        v = kiwoomapi.GetCommRealData(isscode, '20')
        print(['GetCommRealData->', v, type(v)])

    """조건검색"""
    def test05(self):
        v = kiwoomapi.GetConditionLoad()
        print(['GetConditionLoad->', v, type(v)])

        v = kiwoomapi.GetConditionNameList()
        print(['GetConditionNameList->', v, type(v)])

        conds = v 
        for i, (Index, ConditionName) in enumerate(conds):
            v = kiwoomapi.SendCondition('9000', ConditionName, Index, 1)
            print(i, ['SendCondition->', v, type(v)])
            sleep(0.2)
            # break

        v = kiwoomapi.SendConditionStop('9000', '0000', '005')
        print(['SendConditionStop->', v, type(v)])
    """주문과-잔고처리"""
    def test06(self):
        v = kiwoomapi.SendOrder('rqname','9000','8041895711',1,isscode,1,2000,'00','')
        print(['SendOrder', v, type(v)])

        v = kiwoomapi.GetChejanData(910)
        print(['GetChejanData', v, type(v)])





MainTester = MainTester()
MainTester.run()


sys.exit(app.exec())
