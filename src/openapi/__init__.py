# -*- coding: utf-8 -*-

# [모듈 요구사항]
# 키움OpenAPI 에서 응답하는 데이터를 해당 DataType 에 맞게 변환하여 리턴하도록 한다.
# 데이터베이스 없이 단독으로 사용가능한 API 여야 한다.



import os
# import sys
# import subprocess
# from datetime import datetime, timedelta
# from time import sleep
import re
import math 


from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QEventLoop, QTimer
# import pandas as pd


from ipylib.idebug import *
from ipylib import inumber, idatetime
# from ipylib.datacls import BaseDataClass

import trddt
from pyqtclass import QBaseObject
# from configuration import CONFIG


from openapi.metadata import __TRItem__, __RTList__, __RealFID__





############################################################
"""Parser"""
############################################################


# 키움서버에서 오는 모든 데이타는 기본적으로 스트링이다
def KiwoomDataParser(k, v, dtype, unit=0):
    try:
        if dtype in ['int','int_abs','float']:
            v1 = inumber.iNumberV2(v, prec=4).value
            if math.isnan(v1): 
                return v
            else:
                if dtype == 'int': 
                    v2 = int(v1)
                elif dtype == 'int_abs': 
                    v2 = abs(int(v1))
                else: 
                    v2 = v1
                
                if dtype == 'int_abs' and v2 < 0:
                    logger.error(k, unit, [v, v1, v2])
                return v2
        elif dtype == 'pct':
            return inumber.Percent(v, prec=2).to_float
        elif dtype in ['date','time','datetime']:
            return idatetime.DatetimeParser(v)
        elif dtype == 'str':
            return None if str(v) == 'nan' else str(v)
        elif dtype in ['boolean','bool']:
            return bool(v)
        else:
            logger.error(['정의되지 않은 데이터타입이면, 입력값 그대로 반환한다', k, v, dtype, unit])
            return v
    except Exception as e:
        logger.error(['파싱에 실패하면, None 을 반환한다', k, v, dtype, unit])
        return None



def clean_issueCode(code):
    # A005930 --> 005930 변환
    # A35320K --> 35320K
    if isinstance(code, str):
        m = re.search('([A-Z]*)(\d+$)|([A-Z]*)(\d+[A-Z]$)', code)
        if m is None:
            m = re.search('^\d+$', code)
            if m is None:
                return code
            else:
                logger.error(['Invalid IssueCode', {'code': code}])
                raise
        else:
            return m[2]
    else:
        logger.error(['Invalid IssueCode', {'code': code}])
        raise




############################################################
"""API"""
############################################################




__api__ = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")


# 로그인 버전처리
class __ConnAPI__(QBaseObject):

    LoginSucceeded = pyqtSignal()
    LoginFailed = pyqtSignal()

    @tracer.info
    def __init__(self):
        super().__init__()
        __api__.OnReceiveMsg.connect(self.__recv_msg__)
        __api__.OnEventConnect.connect(self.__recv_login__)
        # Shuts down the ActiveX control.
        self.ConnectState = 0

    @tracer.info
    def finish(self):
        __api__.OnReceiveMsg.disconnect(self.__recv_msg__)
        __api__.OnEventConnect.disconnect(self.__recv_login__)
        self.stop_alltimers()

    @tracer.info
    def login(self, acct_win=False):
        self._acct_win = acct_win
        __api__.CommConnect()
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec()

    @tracer.info
    @pyqtSlot(str, str, str, str)
    def __recv_msg__(self, ScrNo, RQName, TrCode, Msg):
        if re.search('서버가 준비되어 있지 않습니다', Msg) is not None:
            logger.critical([ScrNo, RQName, TrCode, Msg, '-->시스템 재시작'])
            self.LoginFailed.emit()
        else:
            pass

    @tracer.info
    @pyqtSlot(int)
    def __recv_login__(self, ErrCode):
        if ErrCode == 0:
            self._set_login_info()

            pretty_title('로그인/계좌 정보')
            dbg.dict(self)

            # 계좌번호입력창
            if self._acct_win: __api__.KOA_Functions('ShowAccountWindow', '')

            # 서버가 준비된 다음 마지막으로 신호를 보내라
            self.LoginSucceeded.emit()

            # 이벤트루프 종료
            self.login_event_loop.exit()
        else:
            logger.critical([ErrCode, '로그인실패 --> 시스템 재시작'])
            self.LoginFailed.emit()

    @tracer.info
    def get_loginInfo(self):
        d = {'ConnectState': __api__.GetConnectState()}
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            d.update({item: __api__.GetLoginInfo(item).strip()})
        return d

    @tracer.info
    def _set_login_info(self):
        d = self.get_loginInfo()
        for k, v in d.items():
            setattr(self, k, v)

        li = self.ACCLIST.split(';')
        self.AccountList = [elem.strip() for elem in li if len(elem.strip()) > 0]




class __ScreenNumberGenerator__(QBaseObject):

    def __init__(self):
        super().__init__()

        # 실시간, 조건검색
        self._set_group(1, 5000)
        # 주문요청화면
        self._set_group(2, 6000)
        # TR요청화면
        self._set_group(3, 7000)

    def _set_group(self, group_no, start):
        if group_no == 3:
            li = [start, 9999, start]
        else:
            li = [start, start+999, start]
        setattr(self, f'group{group_no}', li)

    def gen(self, group_no):
        start, end, count = getattr(self, f'group{group_no}')
        # print([start, end, count])
        count += 1
        if start <= count <= end:
            # 증가된 신규번호 업데이트
            getattr(self, f'group{group_no}')[-1] = count
        else:
            logger.warning(f"""
                신규 할당된 화면번호 : {count}
                {type} 요청 등록화면이 할당된 범위({start}~{end})를 넘어섰다.
                초기값부터 다시 시작하므로 기존 등록된 요청화면은 더이상 유효하지 않다.
            """)
            # 초기화
            self._set_group(group_no, start)

        return str(count).zfill(4)

__ScrNoGen__ = __ScreenNumberGenerator__()

# type: 실시간|조건검색|TR요청|주문요청
def generate_screenNo(type='실시간'):
    if type in ['실시간', '조건검색']:
        return __ScrNoGen__.gen(1)
    elif type == 'TR요청':
        return __ScrNoGen__.gen(2)
    elif type == '주문요청':
        return __ScrNoGen__.gen(3)
    else:
        logger.error('"실시간|조건검색|TR요청|주문요청" 중에 하나만 입력하시오')



# TR요청은 1초안에 최대 5번 요청할 수 있다
class __TrAPI__(QBaseObject):

    frequency = 0.3
    SysRestart = pyqtSignal()

    DataSent = pyqtSignal(str, str, str, str, str, list)
    OrdNoSent = pyqtSignal(str, str, str)

    @tracer.info
    def __init__(self):
        super().__init__()

        # TR요청 처리 셋업
        # 클라이언트의 TR요청을 받아 큐에 넣고 최대 1초간 5번 요청하는 역할
        self.queue = []
        # 모든 Request의 누적 횟수
        self._req_cum_cnt = 0
        self.start_timer('TR요청타이머', self.__req__, self.frequency)
        
        # TR데이터 처리 셋업
        self.data = __TRItem__()
        __api__.OnReceiveTrData.connect(self.__recv_trdata__)

    @tracer.info
    def finish(self):
        __api__.OnReceiveTrData.disconnect(self.__recv_trdata__)
        # self.stop_alltimers()

    """#################### TR요청 처리 ####################"""

    @tracer.debug
    def set_trreq(self, inputs, rqname, trcode, prevnext, screen_no):
        self._req_cum_cnt += 1
        logger.info(f"TR요청 누적횟수: {self._req_cum_cnt}")

        # 키움증권 숨겨진 TR요청 제한조건에 대한 처리
        if self._req_cum_cnt > 200:
            logger.info('TR요청 200회를 초과하면 OpenAPI를 재시작해야한다')
            self.SysRestart.emit()
        else:
            self.queue.append([inputs, rqname, trcode, prevnext, screen_no])

    # 키움서버로 TR요청
    @tracer.debug
    def __req__(self):
        if len(self.queue) > 0:
            inputs, rqname, trcode, prevnext, screen_no = self.queue.pop(0)
            for id, val in inputs:
                __api__.SetInputValue(id, val)

            rv = __api__.CommRqData(rqname, trcode, prevnext, screen_no)
            logger.debug([rqname, trcode, prevnext, screen_no, type(rv), rv])
        else:
            pass 


    """#################### TR데이터 처리 ####################"""

    @tracer.debug
    @pyqtSlot(str, str, str, str, str, int, str, str, str)
    def __recv_trdata__(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        if re.search('^KOA.+', TrCode) is not None:
            # 주문번호처리
            ordNo = __api__.GetCommData(TrCode, RQName, 0, '주문번호').strip()
            self.OrdNoSent.emit(TrCode, RQName, ordNo)
        else:
            # 일반데이타처리
            Data = self.build_data(TrCode, RQName)
            pp.pprint(Data)
            logger.debug([ScrNo, RQName, TrCode, RecordName, PrevNext, len(Data)])
            self.DataSent.emit(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)

    def _parse_item(self, trcode, item, value):
        d = self.data.get_doc(trcode, item)
        if d is None:
            logger.error(['정의되지 않은 TR코드/Item에 대한 값은 파싱없이 None 을 반환한다', (trcode, item, value)])
            return None
        else:
            return KiwoomDataParser(d['item'], value, d['dtype'], d['unit'])
        
    @tracer.debug
    def build_data(self, TrCode, RQName):
        _now = trddt.now()
        _day = trddt.date()
        n = __api__.GetRepeatCnt(TrCode, RQName)
        items = self.data.get_items(TrCode)
        Data = []
        for i in range(0, n+1, 1):
            d = {}
            for item in items:
                v = __api__.GetCommData(TrCode, RQName, i, item).strip()
                if len(v) == 0:
                    pass
                else:
                    v = self._parse_item(TrCode, item, v)
                    if v is None:
                        pass 
                    else:
                        # if item == '종목번호':
                            # v = clean_issueCode(v)
                        d.update({item: v})
            if len(d) > 0:
                d.update({'dt': _now, 'date': _day})
                Data.append(d)
            else: 
                pass
        return Data

    

class __RealAPI__(QBaseObject):

    RealDataSent = pyqtSignal(str, str, dict)
    ChegeolSent = pyqtSignal(str, str, dict)
    RealJangoSent = pyqtSignal(str, dict)

    @tracer.info
    def __init__(self):
        super().__init__()

        # 실시간등록 처리부
        # 실시간등록 완료된 종목코드리스트
        self.codes = []

        # 실시간데이터 처리부
        # 서버쪽에서는 모든 FID 를 가지고 있어야 한다.
        # 클라이언트쪽에서 무슨 FID를 등록할지 모르니까.
        self.RTList = __RTList__()
        self.RealFID = __RealFID__()
        __api__.OnReceiveRealData.connect(self.__recv_realdata__)
        __api__.OnReceiveChejanData.connect(self.__recv_chejandata__)

    @tracer.info
    def finish(self):
        __api__.OnReceiveRealData.disconnect(self.__recv_realdata__)
        __api__.OnReceiveChejanData.disconnect(self.__recv_chejandata__)

    
    """#################### 실시간등록 처리 ####################"""

    @tracer.debug
    def SetRealReg(self, codes, fids, optType):
        if isinstance(codes, str):
            codes = [codes]
        elif isinstance(codes, list):
            pass 
        else:
            logger.error("실시간등록 코드를 string 또는 list 로 입력하시오.")
            codes = []

        # 등록되지 않은 종목코드만 남긴다
        codes = [code for code in codes if code not in self.codes]

        fidList = ";".join(fids)

        
        if len(codes) == 0:
            logger.info("실시간등록할 종목코드가 없다")
        else:
            params = self.autogen_params(codes)
            for screen_no, codeList, fidList, optType in params:
                rv = __api__.SetRealReg(screen_no, codeList, fidList, optType)
                if rv == 0:
                    self.codes += codes
                else:
                    pass 

            self.report_registered_list()

    @tracer.debug
    def SetRealRemove(self, codes):
        if isinstance(codes, str):
            codes = [codes]
        elif isinstance(codes, list):
            pass 
        else:
            logger.error("실시간등록 코드를 string 또는 list 로 입력하시오.")
            codes = []

        # 기등록된 종목코드만 남긴다
        codes = [code for code in codes if code in self.codes]

        for code in codes:
            self.codes.remove(code)
            __api__.SetRealRemove('ALL', code)
        
        self.report_registered_list()

    @tracer.debug
    def SetRealRemoveAll(self):
        __api__.SetRealRemove('ALL', 'ALL')
        self.codes = []

    @tracer.info
    def InitRealReg(self):
        self.SetRealRemoveAll()
        __api__.SetRealReg('5000', '09', '20;214;215', '1')
    
    # 변동성완화장치발동종목요청
    @tracer.info
    def SetRealVI(self):
        logger.info("""
            OpenAPI에서 변동성완화장치는 OPT10054 :
            변동성완화장치발동종목요청 조회로 구하실수 있으며 조회 TR의 "종목코드" 입력값에 따라 결과가 다르게 됩니다.
            공백으로 설정하면 "시장구분"입력값으로 설정한 전체(000) 코스피(001), 코스닥(101) 구분으로 조회되며
            변동성완화장치 실시간 데이터를 수신할수 있습니다.
            정리해서 답변드리면 TR 조회후 VI발생한 종목은 실시간타입 "VI발동/해제"으로 수신됩니다.
            영웅문4 [0193]변동성완화장치(VI)발동종목현황 화면 참고 바랍니다.
        """)
        req = TrReq('변동성완화장치발동종목요청', 종목코드='005930')
        TrAPI.SetTrReg(req)


    """#################### 실시간데이터 처리 ####################"""

    # @tracer.debug
    @pyqtSlot(str, str, str)
    def __recv_realdata__(self, Code, RealType, RealData):
        def __emit__():
            d = self._build_realdata(Code, RealType)
            if isinstance(d, dict):
                self.RealDataSent.emit(Code, RealType, d)
            else:
                pass

        if RealType in ['장시작시간','VI발동/해제','주식시간외호가']:
            __emit__()
        else:
            if Code in self.codes:
                __emit__()
            else:
                # 자동으로 등록처리되는 종목코드는 실시간해지 --> 해제가 안된다???
                self.SetRealRemove(Code)

    # @tracer.debug
    @pyqtSlot(str, int, str)
    def __recv_chejandata__(self, Gubun, ItemCnt, FIdList):
        d = self._build_chejandata(FIdList)
        code = d['종목코드,업종코드']
        if Gubun == '0':
            self.ChegeolSent.emit(code, d['주문번호'], d)
            
        elif Gubun == '1':
            self.RealJangoSent.emit(code, d)

    def _parse_fid(self, fid, value):
        d = self.RealFID.get_doc(fid)
        if d is None:
            logger.warning(['정의되지 않은 FID에 대한 값은 파싱없이 그대로 반환한다', (fid, value)])
            return value
        else:
            return KiwoomDataParser(d['name'], value, d['dtype'], d['unit'])

    # @tracer.debug
    def _build_realdata(self, Code, RealType):
        if RealType in self.data.realtypes:
            d = {}
            fids = self.RTList.get_fids(RealType)
            for fid in fids:
                v = __api__.GetCommRealData(Code, int(fid)).strip()
                # print([Code, RealType, fid, v])
                if len(v) > 0:
                    v = self._parse_fid(fid, v)
                    if v is None:
                        pass 
                    else:
                        name = self._get_name(fid)
                        d.update({name: v})
                else:
                    pass

            if len(d) > 0:
                d.update({'dt': trddt.now()})
            else:
                pass
            return d
        else:
            return None

    @tracer.debug
    def _build_chejandata(self, FIdList):
        fids = FIdList.split(';')
        fids = [fid.strip() for fid in fids if len(fid.strip()) > 0]
        d = {}
        for fid in fids:
            name = self.RealFID.get_value(fid, 'name')
            if name is None:
                logger.error(locals())
            else:
                v = __api__.GetChejanData(int(fid)).strip()
                if len(v) > 0:
                    v = self._parse_fid(fid, v)
                    if v is None:
                        pass 
                    else:
                        if name == '종목코드,업종코드':
                            v = clean_issueCode(v)
                        d.update({name: v})
                else:
                    pass

        if len(d) == 0:
            raise
        else:
            d.update({'dt': trddt.now()})
        return d
 


# 개발중....설계 미정 상태
# 주문은 1초당 5회로 제한 됩니다. (조회횟수와는 별개로 카운트 됩니다.)
class __OrderAPI__(QBaseObject):

    frequency = 0.3
    OrderResponse = pyqtSignal(int)
    # RealDataSent = pyqtSignal(str, str, dict)
    # ChegeolSent = pyqtSignal(str, str, dict)
    # RealJangoSent = pyqtSignal(str, dict)

    @tracer.info
    def __init__(self):
        super().__init__()
        self.start_timer('주문요청타이머', self.__send_order__, self.frequency)
        self.queue = []

    def SendOrder(self, rqname, screen_no, acct_no, ordertype, code, amt, prc, hoga, orgOrderNo):
        self.queue.append([rqname, screen_no, acct_no, ordertype, code, amt, prc, hoga, orgOrderNo])

    def __send_order__(self):
        if len(self.queue) > 0:
            args = self.queue.pop(0)
            rv = __api__.SendOrder(*args)
            logger.info([rv, type(rv), args])
            self.OrderResponse.emit(rv)
        else:
            pass 


# 조건등록 & 조건검색데이타 가공/제공
# 한번에 최대 10개만 등록가능하다
# 조건검색 요청은 1초당 5회 조회횟수 제한
class __ConditionAPI__(QBaseObject):

    ConditionListSent = pyqtSignal(list)
    TrConditionSent = pyqtSignal(str, list, str, int, int)
    RealConditionSent = pyqtSignal(str, str, str, str)

    @tracer.info
    def __init__(self):
        super().__init__()
        self.start_timer('조건검색타이머', self.__send_condition__, 0.3)
        __api__.OnReceiveConditionVer.connect(self.__recv_condver__)
        __api__.OnReceiveTrCondition.connect(self.__recv_trcond__)
        __api__.OnReceiveRealCondition.connect(self.__recv_realcond__)

    @tracer.info
    def finish(self):
        __api__.OnReceiveConditionVer.disconnect(self.__recv_condver__)
        __api__.OnReceiveTrCondition.disconnect(self.__recv_trcond__)
        __api__.OnReceiveRealCondition.disconnect(self.__recv_realcond__)

        self.stop_alltimers()

    @tracer.debug 
    def GetConditionLoad(self):
        __api__.GetConditionLoad()

    @tracer.debug
    @pyqtSlot(int, str)
    def __recv_condver__(self, Ret, Msg):
        nameList = __api__.GetConditionNameList().strip()
        conds = nameList.split(';')
        conds = [e.strip() for e in conds if len(e.strip()) > 0]
        conds = [cond.split('^') for cond in conds]
        self.conditions = conds

        self.SendCondition(conds)
        self.ConditionListSent.emit(conds)

    @tracer.debug
    def SendCondition(self, screen_no, name, idx, search=1):
        self.queue.append([screen_no, name, int(idx), int(search)])

    def __send_condition__(self):
        if len(self.queue) > 0:
            args = self.queue.pop(0)
            __api__.SendCondition(*args)
        else:
            pass 

    @pyqtSlot(str, str, str, int, int)
    def __recv_trcond__(self, ScrNo, CodeList, ConditionName, Index, Next):
        codes = CodeList.split(';')
        codes = [c.strip() for c in codes if len(c.strip()) > 0]
        self.TrConditionSent.emit(ScrNo, codes, ConditionName, Index, Next)

    @pyqtSlot(str, str, str, str)
    def __recv_realcond__(self, Code, Type, ConditionName, ConditionIndex):
        self.RealConditionSent.emit(Code, Type, ConditionName, ConditionIndex)

    




"""
[사용법-1]

api = KiwoomAPI()
api.conn.login()
api.tr.DataSent.connect()
api.real.DataSent.connect()
api.cond.ConditionListSent.connect()
api.acct.TrJangoSent.connect()
api.iss.DatumSent.connect()
api.invest.prepared.connect()


[사용법-2]
api = KiwoomAPI()

api.login()
api.LoginInfoSent.connect()

api.TrDataSent.connect()
api.OrdNoSent.connect()
api.RealDataSent.connect()
api.ConditionListSent.connect()
api.TrJangoSent.connect()

"""
class KiwoomAPI(QBaseObject):

    TrDataSent = pyqtSignal(str, str, str, str, str, list)

    @tracer.info
    def __init__(self):
        super().__init__()
        self.conn = __ConnAPI__()
        
        self.tr = __TrAPI__()
        self.tr.DataSent.connect(self.__emit_trdata__)
        self.tr.SysRestart.connect(self.restart)

        self.real = __RealAPI__()

        self.cond = __ConditionAPI__()

    @tracer.info
    @pyqtSlot()
    def restart(self):
        # 기본API 정리/종료
        self.conn.finish()
        self.tr_reg.finish()
        self.tr.finish()

        # 오픈API 정리
        __api__.clear()

        # 프로세스 재시작
        filepath = os.environ['RUN_FILE_PATH']
        params = [sys.executable, os.path.realpath(filepath)] + sys.argv[1:]
        logger.info(params)
        subprocess.run(params)


    """#################### 로그인 관련 함수들 ####################"""

    @tracer.info
    def login(self, acct_win=False):
        self._acct_win = acct_win
        __api__.CommConnect()
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec()

    @tracer.info
    @pyqtSlot(str, str, str, str)
    def __recv_msg__(self, ScrNo, RQName, TrCode, Msg):
        if re.search('서버가 준비되어 있지 않습니다', Msg) is not None:
            logger.critical([ScrNo, RQName, TrCode, Msg, '-->시스템 재시작'])
            self.LoginFailed.emit()
        else:
            pass

    @tracer.info
    @pyqtSlot(int)
    def __recv_login__(self, ErrCode):
        if ErrCode == 0:
            self._set_login_info()

            pretty_title('로그인/계좌 정보')
            dbg.dict(self)

            # 계좌번호입력창
            if self._acct_win: __api__.KOA_Functions('ShowAccountWindow', '')

            # 서버가 준비된 다음 마지막으로 신호를 보내라
            self.LoginSucceeded.emit()

            # 이벤트루프 종료
            self.login_event_loop.exit()
        else:
            logger.critical([ErrCode, '로그인실패 --> 시스템 재시작'])
            self.LoginFailed.emit()

    @tracer.info
    def get_loginInfo(self):
        d = {'ConnectState': __api__.GetConnectState()}
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            d.update({item: __api__.GetLoginInfo(item).strip()})
        return d

    @tracer.info
    def _set_login_info(self):
        d = self.get_loginInfo()
        for k, v in d.items():
            setattr(self, k, v)

        li = self.ACCLIST.split(';')
        self.AccountList = [elem.strip() for elem in li if len(elem.strip()) > 0]



    """#################### TR 관련 함수들 ####################"""

    # TR요청 등록
    @tracer.debug
    def SetTrReq(self, inputs, rqname, trcode, prevnext, screen_no):
        self.tr_reg.add(inputs, rqname, trcode, prevnext, screen_no)

    @pyqtSlot(str, str, str, str, str, list)
    def __emit_trdata__(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        self.TrDataSent.emit(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)


    """#################### 실시간 관련 함수들 ####################"""


    """#################### 주문 관련 함수들 ####################"""
    def SendOrder(self, *args):
        # 방법1 : 직접 API함수를 호출하고 리턴받는다
        return __api__.SendOrder(*args)
        # 방법2 : 오더객체로 처리 

    """#################### 조건검색 관련 함수들 ####################"""

    def GetConditionLoad(self):
        self.cond.GetConditionLoad()

    def SendCondition(self, conds):
        self.cond.SendCondition(conds)


    """#################### MyFunctionalAPIs ####################"""

    def account_no(self): return self.conn.AccountNo

    def isMoiServer(self):
        return True if __api__.GetLoginInfo('GetServerGubun') == '1' else False
    

    """#################### FunctionalAPIs ####################"""

    def GetMasterStockInfo(self, code):
        s = __api__.KOA_Functions('GetMasterStockInfo', code)
        info = s.strip().split(';')
        info = [i for i in info if len(i.strip()) > 0]
        d = {}
        for i in info:
            li = i.split('|')
            li = [e for e in li if len(e.strip()) > 0]
            # print(li)
            if len(li) == 1:
                d.update({li[0]:None})
            elif len(li) == 2:
                d.update({li[0]:li[1]})
            elif len(li) == 3:
                d.update({li[0]:li[1]})
                if li[0] == '시장구분0':
                    d.update({'시장구분2':li[2]})
                elif li[0] == '업종구분':
                    d.update({'업종구분2':li[2]})
        return d
    
    def GetMasterStockState(self, code):
        s = __api__.GetMasterStockState(code)
        s = s.strip()
        _m = re.search('증거금(\d+%)', s)
        # print(_m, _m[1])
        d = {} if _m is None else {'증거금':_m[1]}

        s = re.sub('증거금(\d+%)', repl='', string=s)
        # print(s)
        li = s.split('|')
        li = [e for e in li if len(e.strip()) > 0]
        # print(li)
        if len(li) > 0:
            d.update({'state1': li})
        else:
            pass
        return d
    
    @tracer.info
    def GetBranchCodeName(self):
        s = __api__.GetBranchCodeName()
        tpls = re.findall('(\d+)\|([가-힣A-Za-z\s\.]+)', s.strip())
        data = []
        for code, name in tpls:
            data.append({'code': code, 'name': name})
        return data
    
    @tracer.info
    def GetCodeListByMarket(self, mktcd):
        s = __api__.GetCodeListByMarket(mktcd)
        codes = s.strip().split(';')
        codes = [c for c in codes if len(c.strip()) > 0]
        return codes
    
    # 업종코드목록
    @tracer.info
    def GetUpjongCode(self, ujcd):
        s = __api__.KOA_Functions('GetUpjongCode', ujcd)
        li = s.split('|')
        li = [e.strip() for e in li if len(e.strip()) > 0]
        p = re.compile("(\d),(\d+),(.+)")
        data = []
        for e in li:
            m = p.search(e)
            d = {'mktcd':m[1], 'code':m[2], 'name':m[3].strip()}
            data.append(d)
        return data
    
    # @tracer.info
    def getIssueInfo(self, code):

        price = int(__api__.GetMasterLastPrice(code).strip())
        lst_dt = __api__.GetMasterListedStockDate(code).strip()
        d = {
            'code': code,
            'name': __api__.GetMasterCodeName(code).strip(),
            'lst_dt': idatetime.DatetimeParser(lst_dt),
            'n_shrs': __api__.GetMasterListedStockCnt(code),
            'supervision': __api__.GetMasterConstruction(code),
            '전일종가': price,
            '기준가': price,
            'warningETF': bool(__api__.KOA_Functions('IsOrderWarningETF', code)),
            'warningStock': bool(__api__.KOA_Functions('IsOrderWarningStock', code)),
            'updated_dt': trddt.today(),
        }

        d.update(self.GetMasterStockInfo(code))
        d.update(self.GetMasterStockState(code))
        return d
















