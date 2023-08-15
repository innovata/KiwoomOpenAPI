# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import re 
from time import sleep


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


"""Item 기반 데이타 빌드업"""
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


"""캐싱할 필요가 있는 TR데이타를 관리한다"""
class TrDataManager(object):

    def __init__(self): pass 

    def manage(self, TrCode, RQName, Data):
        # 보유종목 관리
        # 계좌잔고 관리
        pass 

    def add(self, key, value):
        setattr(self, key, value)

    def get(self, key):
        return getattr(self, key).copy()


"""FID 기반 데이터 빌드업"""
class RealDataBuilder(object):

    def __init__(self): pass 

    def build_realdata(self, Code, RealType):
        if RealType in self.realtypes:
            d = {}
            fids = self._get_fids(RealType)
            for fid in fids:
                v = GetCommRealData(Code, int(fid)).strip()
                if len(v) > 0:
                    # v = self._parse_value(fid, v)
                    name = self._get_name(fid)
                    d.update({name:v})
                else: pass

            if len(d) > 0: d.update({'dt':trddt.now()})
            else: pass
            return d
        else: return None

    def build_chejandata(self, FIdList):
        fids = FIdList.split(';')
        fids = [fid.strip() for fid in fids if len(fid.strip()) > 0]
        d = {}
        for fid in fids:
            name = self._get_name(fid)
            if name is None: pass
            else:
                v = GetChejanData(int(fid)).strip()
                if len(v) == 0: pass
                else:
                    # v = self._parse_value(fid, v)
                    d.update({name: v})
        if len(d) == 0: raise
        else: d.update({'dt': trddt.now()})
        return d


class RealRegManager(object):

    def __init__(self): pass 


class KiwoomAPI(QObject):

    ConnectSent = pyqtSignal(int)
    LoginSucceeded = pyqtSignal()

    TrDataSent = pyqtSignal(str, str, str, str, str, list)
    OrdNoSent = pyqtSignal(str, str, str)
    TrJangoSent = pyqtSignal(list)

    RealDataSent = pyqtSignal(str, str, dict)
    ChegeolSent = pyqtSignal(str, str, dict)
    RealJangoSent = pyqtSignal(str, dict)

    ConditionListSent = pyqtSignal(list)
    TrConditionSent = pyqtSignal(str, list, str, int, int)
    RealConditionSent = pyqtSignal(str, str, str, str)

    @ctracer
    def __init__(self):
        super().__init__()
        OpenAPI.OnEventConnect.connect(self.__recv_login__)

        OpenAPI.OnReceiveTrData.connect(self.__recv_trdata__)
        
        OpenAPI.OnReceiveRealData.connect(self.__recv_realdata__)
        OpenAPI.OnReceiveChejanData.connect(self.__recv_chejandata__)
        
        OpenAPI.OnReceiveConditionVer.connect(self.__recv_condver__)
        OpenAPI.OnReceiveTrCondition.connect(self.__recv_trcond__)
        OpenAPI.OnReceiveRealCondition.connect(self.__recv_realcond__)

        self.TrDataBuilder = TrDataBuilder()
        self.RealDataBuilder = RealDataBuilder()

    ############################################################
    """로그인"""
    ############################################################

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

    ############################################################
    """TR요청"""
    ############################################################

    @pyqtSlot(str, str, str, str, str, int, str, str, str)
    def __recv_trdata__(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        if re.search('^KOA.+', TrCode) is not None:
            """주문번호처리"""
            ordNo = GetCommData(TrCode, RQName, 0, '주문번호').strip()
            self.OrdNoSent.emit(TrCode, RQName, ordNo)
        else:
            """일반데이타처리"""
            Data = self.TrDataBuilder.build(TrCode, RQName)
            self.TrDataSent.emit(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)

    ############################################################
    """실시간요청"""
    ############################################################

    @pyqtSlot(str, str, str)
    def __recv_realdata__(self, Code, RealType, RealData):
        def __emit__():
            d = self.RealDataBuilder.build_realdata(Code, RealType)
            if isinstance(d, dict): self.RealDataSent.emit(Code, RealType, d)
            else: pass

        if RealType in ['장시작시간','VI발동/해제']: __emit__()
        else:
            if Code in self.codes: __emit__()
            else:
                # 해제가 안된다......
                # SetRealRemove('ALL', Code)
                pass
    
    @pyqtSlot(str, int, str)
    def __recv_chejandata__(self, Gubun, ItemCnt, FIdList):
        d = self.RealDataBuilder.build_chejandata(FIdList)
        code = dataapi.clean_issueCode(d['종목코드,업종코드'])
        if Gubun == '0':
            self.ChegeolSent.emit(code, d['주문번호'], d)
        elif Gubun == '1':
            self.RealJangoSent.emit(code, d)

    @ctracer
    def InitRealReg(self):
        SetRealRemove('ALL', 'ALL')
        SetRealReg('5000', '09', '20;214;215', '1')
    
    @ctracer
    def SetRealReg(self, code):
        if code in self.codes: pass
        else:
            tpls = self._autogen_param()

            for screen_no, fidList in tpls:
                try:
                    v = SetRealReg(screen_no, code, fidList, '1')
                except Exception as e:
                    logger.error(e)
                else:
                    if v == 0: self.codes.append(code)
                    else: logger.error([self, {'리턴값':v}])
        self._report()
    
    @ctracer
    def SetRealRemove(self, code):
        try: self.codes.remove(code)
        except Exception as e: pass
        else: SetRealRemove('ALL', code)
        finally: self._report()

    ############################################################
    """조건검색"""
    ############################################################

    @pyqtSlot(int, str)
    def __recv_condver__(self, Ret, Msg):
        conds = GetConditionNameList()
        self.ConditionListSent.emit(conds)

        """조건들을 키움서버로 요청"""   
        screen_no = gen_scrNo()

        def __send__(conds):
            for idx, name in conds:
                SendCondition(screen_no, name, int(idx), 1)

        # 한번에 최대 10개만 등록가능하다
        conds = conds[:10]
        __send__(conds[:4])
        sleep(1)
        __send__(conds[4:8])
        sleep(1)
        __send__(conds[8:10])

    @pyqtSlot(str, str, str, int, int)
    def __recv_trcond__(self, ScrNo, CodeList, ConditionName, Index, Next):
        CodeList = CodeList.split(';')
        CodeList = [c for c in CodeList if len(c.strip()) > 0]
        self.TrConditionSent.emit(ScrNo, CodeList, ConditionName, Index, Next)
    
    @pyqtSlot(str, str, str, str)
    def __recv_realcond__(self, Code, Type, ConditionName, ConditionIndex):
        self.RealConditionSent.emit(Code, Type, ConditionName, ConditionIndex)



