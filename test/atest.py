# -*- coding: utf-8 -*-
from test._testenv import *
from ipylib.datacls import BaseDataClass


from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QEventLoop


import kiwoomapi._openapi as _openapi
from kiwoomapi._openapi import *


issname, isscode = '삼성전자', '005930'



class LoginAPI(QObject):
    ConnectSent = pyqtSignal(int)
    LoginSucceeded = pyqtSignal()
    LoginFailed = pyqtSignal()

    @ctracer
    def __init__(self):
        super().__init__()
        OpenAPI.OnEventConnect.connect(self.OnEventConnect)
    @ctracer
    def CommConnect(self, acct_win=False):
        self._acct_win = acct_win
        v = CommConnect()
        self.CommConnectReturn = (v, type(v))
        self._event_loop = QEventLoop()
        self._event_loop.exec()
    @ctracer
    @pyqtSlot(int)
    def OnEventConnect(self, ErrCode):
        self.ErrCode = ErrCode
        self.ConnectState = GetConnectState()
        if ErrCode == 0:
            self._set_login_info()

            pretty_title('로그인/계좌 정보')
            pp.pprint(self.__dict__)

            """계좌번호입력창"""
            if self._acct_win: ShowAccountWindow()

            """서버가 준비된 다음 마지막으로 신호를 보내라"""
            self.LoginSucceeded.emit()
        else:
            logger.critical(['로그인실패 --> 시스템재시작'])
            self.LoginFailed.emit()
        
        self.ConnectSent.emit(ErrCode)
        self._event_loop.exit()
    @ctracer
    def _set_login_info(self):
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            v = GetLoginInfo(item)
            setattr(self, item, v)


class MainTester(QObject):

    def __init__(self):  super().__init__()
    def run(self):
        self.login()
    def login(self):
        OpenAPI.OnEventConnect.connect(self.recv_login)
        v = CommConnect()
        print(['CommConnect-->', v, type(v)])
        self._event_loop = QEventLoop()
        self._event_loop.exec()
    @pyqtSlot(int)
    def recv_login(self, ErrCode): 
        print({'ErrCode':ErrCode})
        self._event_loop.exit()
        self.__run__()
    
    def __run__(self):
        for i in [1,2]:
            func = f'test{str(i).zfill(2)}'
            getattr(self, func)()

    """로그인-버전처리"""
    def test01(self):
        v = GetConnectState()
        print(['GetConnectState-->', v, type(v)])
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            v = GetLoginInfo(item)
            print(['GetLoginInfo-->', v, type(v)])

    """기타함수"""
    def test02(self):
        v = _openapi.GetBranchCodeName()
        print(['GetBranchCodeName', v, type(v)])
        if not isinstance(v, list): raise

        v = _openapi.GetCodeListByMarket('0')
        print(['GetCodeListByMarket', v, type(v)])
        if not isinstance(v, list): raise

        v = _openapi.GetMasterCodeName(isscode)
        print(['GetMasterCodeName', v, type(v)])
        if not isinstance(v, str): raise

        v = _openapi.GetMasterConstruction(isscode)
        print(['GetMasterConstruction', v, type(v)])
        if not isinstance(v, str): raise

        v = _openapi.GetMasterLastPrice(isscode)
        print(['GetMasterLastPrice', v, type(v)])
        if not isinstance(v, int): raise

        v = _openapi.GetMasterListedStockDate(isscode)
        print(['GetMasterListedStockDate', v, type(v)])
        if not isinstance(v, datetime): raise

        v = _openapi.GetMasterListedStockCnt(isscode)
        print(['GetMasterListedStockCnt', v, type(v)])
        if not isinstance(v, int): raise

        v = _openapi.GetMasterStockState(isscode)
        print(['GetMasterStockState', v, type(v)])
        if not isinstance(v, dict): raise

        # mktcds = db.UpjongMarketCode.distinct('code')
        # for ujcd in mktcds:
        #     v = kiwoomapi.GetUpjongCode(ujcd)
        #     print(['GetUpjongCode', ujcd, v, type(v)])
        #     if not isinstance(v, list): raise

        v = _openapi.GetServerGubun()
        print(['GetServerGubun',v, type(v)])
        if not isinstance(v, str): raise

        v = _openapi.GetUpjongNameByCode('002')
        print(['GetUpjongNameByCode',v, type(v)])
        if not isinstance(v, str): raise

        v = _openapi.IsOrderWarningETF(isscode)
        print(['IsOrderWarningETF',v, type(v)])
        if not isinstance(v, bool): raise

        v = _openapi.IsOrderWarningStock(isscode)
        print(['IsOrderWarningStock',v, type(v)])
        if not isinstance(v, bool): raise

        v = _openapi.GetMasterStockInfo(isscode)
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
        v = _openapi.SetInputValue('종목코드', isscode)
        print(['SetInputValue', v, type(v)])

        v = _openapi.CommRqData('요청명','opt10001',0,'8000')
        print(['CommRqData', v, type(v)])

        v = _openapi.GetRepeatCnt('opt10001', '요청명')
        print(['GetRepeatCnt', v, type(v)])

        pretty_title('케이스2::GetRepeatCnt 몇개?')
        sleep(2)
        _openapi.SetInputValue('종목코드', isscode)
        _openapi.SetInputValue('기준일자', '20230210')
        _openapi.SetInputValue('수정주가구분', '1')
        v = _openapi.CommRqData(isscode,'opt10081',0,'8001')
        print(['CommRqData', v, type(v)])
        v = _openapi.GetRepeatCnt('opt10081', isscode)
        print(['GetRepeatCnt', v, type(v)])

        pretty_title('케이스3::인풋없이 요청만 하면 에러')
        sleep(2)
        v = _openapi.CommRqData('요청명','opt10001',0,'8000')
        print(['CommRqData', v, type(v)])
    """실시간데이터처리"""
    def test04(self):
        v = _openapi.SetRealReg('5000', '09', '20;214;215', '1')
        print(['SetRealReg->', v, type(v)])

        v = _openapi.SetRealRemove('ALL', 'ALL')
        print(['SetRealRemove->', v, type(v)])

        v = _openapi.GetCommRealData(isscode, '20')
        print(['GetCommRealData->', v, type(v)])

    """조건검색"""
    def test05(self):
        v = _openapi.GetConditionLoad()
        print(['GetConditionLoad->', v, type(v)])

        v = _openapi.GetConditionNameList()
        print(['GetConditionNameList->', v, type(v)])

        conds = v 
        for i, (Index, ConditionName) in enumerate(conds):
            v = _openapi.SendCondition('9000', ConditionName, Index, 1)
            print(i, ['SendCondition->', v, type(v)])
            sleep(0.2)
            # break

        v = _openapi.SendConditionStop('9000', '0000', '005')
        print(['SendConditionStop->', v, type(v)])
    """주문과-잔고처리"""
    def test06(self):
        v = _openapi.SendOrder('rqname','9000','8041895711',1,isscode,1,2000,'00','')
        print(['SendOrder', v, type(v)])

        v = _openapi.GetChejanData(910)
        print(['GetChejanData', v, type(v)])





MainTester = MainTester()
MainTester.run()


sys.exit(app.exec())
