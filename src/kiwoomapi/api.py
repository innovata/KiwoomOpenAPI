# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import re 


from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


import trddt


from kiwoomapi.core import *





@ftracer
def restart():
    filepath = os.environ['RUN_FILE_PATH']
    subprocess.run([sys.executable, os.path.realpath(filepath)] + sys.argv[1:])


class LoginInfo(QObject):

    def __init__(self):
        super().__init__()
        self._set_login_info()

    @ctracer
    def _set_login_info(self):
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            v = GetLoginInfo(item)
            setattr(self, item, v)

        pretty_title('로그인/계좌 정보')
        dbg.dict(self)



class TrDataBuilder(object):

    def __init__(self): pass 

    def build(self, TrCode, RQName):
        n = GetRepeatCnt(TrCode, RQName)
        _now = trddt.now()
        _day = trddt.date()
        items = getattr(self, TrCode)
        Data = []
        for i in range(0, n+1, 1):
            d = {}
            for item in items:
                v = GetCommData(TrCode, RQName, i, item)
                if len(v) == 0: 
                    pass
                else:
                    d.update({item: v})
            if len(d) > 0: 
                d.update({'dt': _now, 'date': _day})
                Data.append(d)
            else: pass
        return Data


class KiwoomAPI(QObject):

    ConnectSent = pyqtSignal(int)
    LoginSucceeded = pyqtSignal()

    TrDataSent = pyqtSignal(str, str, str, str, str, list)
    OrdNoSent = pyqtSignal(str, str, str)
    TrJangoSent = pyqtSignal(list)

    @ctracer
    def __init__(self):
        super().__init__()
        OpenAPI.OnEventConnect.connect(self.__recv_login__)
        OpenAPI.OnReceiveTrData.connect(self.__recv_trdata__)

    @ctracer
    def CommConnect(self, acct_win=False):
        self._acct_win = acct_win
        CommConnect()
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec()
    
    @ctracer
    @pyqtSlot(int)
    def __recv_login__(self, ErrCode):
        self.ConnectState = GetConnectState()
        if ErrCode == 0:
            self.LoginInfo = LoginInfo()

            """계좌번호입력창"""
            if self._acct_win: ShowAccountWindow()

            """서버가 준비된 다음 마지막으로 신호를 보내라"""
            self.LoginSucceeded.emit()
            self.login_event_loop.exit()
        else:
            logger.critical(['로그인실패 --> 시스템재시작'])
            restart()

    @pyqtSlot(str, str, str, str, str, int, str, str, str)
    def __recv_trdata__(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        if re.search('^KOA.+', TrCode) is not None:
            """주문번호처리"""
            ordNo = GetCommData(TrCode, RQName, 0, '주문번호').strip()
            self.OrdNoSent.emit(TrCode, RQName, ordNo)
        else:
            """일반데이타처리"""
            Data = self._build_trdata(TrCode, RQName)
            Data = self.preprocess_data(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
            self.TrDataSent.emit(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)