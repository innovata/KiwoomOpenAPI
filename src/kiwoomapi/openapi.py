# -*- coding: utf-8 -*-
import os, sys, subprocess
from datetime import datetime, timedelta
from time import sleep
import re
from copy import copy, deepcopy
import math


from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import *
import pandas as pd


from ipylib.idebug import *
from ipylib import inumber, iparser, idatetime
from ipylib.datacls import BaseDataClass

import trddt
from pyqtclass import *


from kwdataengineer import database
from kwdataengineer import datamodels



############################################################
"""Constants"""
############################################################
"""
# 평가금액 = 현재가 X 수량
# 매입금액 = 매입가 X 수량
# 매수수수료 = 매입금액 X 수수료(모의투자 0.0035. 실거래 0.00015)
# 매도수수료 = 평가금액 X 수수료(모의투자 0.0035. 실거래 0.00015)
# 수수료합 = 매수수수료(원단위절사) + 매도수수료(원단위절사)

# 당사 수수료 징수는 종목별 매수/매도를 기준으로 하며, 동일종목의 분할매매시는 매수별, 매도별 체결합계금액을 기준으로 산정합니다.
# 매매수수료는 10원 미만 절사이며, (ex. 3,000원 X 50주 = 150,000원 체결 시, 온라인 매체 매매수수료는 150,000원 X 0.015% = 22.5원 -> 20원 부과)
# 세금은 원 미만 절사 입니다. (ex. 2,050원 X 50주 = 102,500원 체결 시, 거래세는 102,500원 X 0.23%(코스닥) = 235.75원 -> 235원 부과)
"""


"""거래세"""
Tax = '0.20%'
"""수수료"""
Commission = '0.015%'
"""거래세+매수/도수수료"""
Cost = '0.23%'

"""트레이딩종목 최대개수"""
MAX_REALREG_LIMIT = 100

"""종목당 최대투자금"""
MAX_TRADE_BUDGET = 10*pow(10,4)

"""키움서버 점검시간"""
# 월~토: 05:05~05:10
# 일요일: 04:00~04:30


OpenAPI = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
print({'OpenAPI':OpenAPI})
# pp.pprint(dir(OpenAPI))

def dynamicCall(*args): return OpenAPI.dynamicCall(*args)

# @ftracer
def KOA_Functions(func, param): return dynamicCall('KOA_Functions(QString,QString)', [func, param])

############################################################
"""FunctionalAPIs::로그인-버전처리"""
############################################################

@ftracer
def CommConnect(): return dynamicCall('CommConnect()')

@ftracer
def GetLoginInfo(s): return dynamicCall('GetLoginInfo(QString)', s)

@ftracer
def GetConnectState(): return dynamicCall('GetConnectState()')


############################################################
"""FunctionalAPIs::기타함수"""
############################################################
@ftracer
def GetBranchCodeName():
    s = dynamicCall('GetBranchCodeName()')
    data = re.findall('(\d+)\|([가-힣A-Za-z\s\.]+)', s.strip())
    df = pd.DataFrame(data, columns=['code','name'])
    return df.to_dict('records')

@ftracer
def GetCodeListByMarket(mktcd):
    s = dynamicCall('GetCodeListByMarket(QString)', [mktcd])
    codes = s.strip().split(';')
    codes = [c for c in codes if len(c.strip()) > 0]
    return codes

# @ftracer
def GetMasterCodeName(code): return dynamicCall('GetMasterCodeName(QString)', [code])

# @ftracer
def GetMasterConstruction(code): return dynamicCall('GetMasterConstruction(QString)', [code])

"""전일종가==기준가"""
# @ftracer
def GetMasterLastPrice(code):
    v = dynamicCall('GetMasterLastPrice(QString)', [code])
    return int(v.strip())

"""상장일"""
# @ftracer
def GetMasterListedStockDate(code):
    s = dynamicCall('GetMasterListedStockDate(QString)', [code])
    return idatetime.DatetimeParser(s)

# @ftracer
def GetMasterListedStockCnt(code): return dynamicCall('GetMasterListedStockCnt(QString)', [code])

# @ftracer
def GetMasterStockState(code):
    try:
        s = dynamicCall('GetMasterStockState(QString)', [code])
        s = s.strip()
        _m = re.search('증거금(\d+%)', s)
        # print(_m, _m[1])
        d = {} if _m is None else {'증거금':_m[1]}

        s = re.sub('증거금(\d+%)', repl='', string=s)
        # print(s)
        li = s.split('|')
        li = [e for e in li if len(e.strip()) > 0]
        # print(li)
        if len(li) > 0: d.update({'state1':li})
        else: pass
        return d
    except Exception as e:
        logger.error(e)
        return {}

@ftracer
def GetServerGubun():
    v = KOA_Functions('GetServerGubun', "")
    return '모의' if v == '1' else '실전'

"""업종코드목록"""
@ftracer
def GetUpjongCode(ujcd):
    s = KOA_Functions('GetUpjongCode', ujcd)
    li = s.split('|')
    li = [e.strip() for e in li if len(e.strip()) > 0]
    p = re.compile("(\d),(\d+),(.+)")
    data = []
    for e in li:
        m = p.search(e)
        d = {'mktcd':m[1], 'code':m[2], 'name':m[3].strip()}
        data.append(d)
    return data

"""업종이름"""
@ftracer
def GetUpjongNameByCode(ujcd): return KOA_Functions('GetUpjongNameByCode', ujcd)

"""ETF 투자유의 종목 여부"""
# @ftracer
def IsOrderWarningETF(code):
    v = KOA_Functions('IsOrderWarningETF', code)
    return False if v == '0' else True

"""주식 전종목대상 투자유의 종목 여부"""
# @ftracer
def IsOrderWarningStock(code):
    v = KOA_Functions('IsOrderWarningStock', code)
    return False if v == '0' else True

# @ftracer
def GetMasterStockInfo(code):
    try:
        s = KOA_Functions('GetMasterStockInfo', code)
        info = s.strip().split(';')
        info = [i for i in info if len(i.strip()) > 0]
        # print(len(info), info)
        d = {}
        for i in info:
            li = i.split('|')
            li = [e for e in li if len(e.strip()) > 0]
            # print(li)
            if len(li) == 1: d.update({li[0]:None})
            elif len(li) == 2: d.update({li[0]:li[1]})
            elif len(li) == 3:
                d.update({li[0]:li[1]})
                if li[0] == '시장구분0': d.update({'시장구분2':li[2]})
                elif li[0] == '업종구분': d.update({'업종구분2':li[2]})
        return d
    except Exception as e:
        logger.error(e)
        return {}

@ftracer
def ShowAccountWindow(): return KOA_Functions('ShowAccountWindow', "")


############################################################
"""FunctionalAPIs::조건검색"""
############################################################
@ftracer
def GetConditionLoad(): return dynamicCall('GetConditionLoad()')

@ftracer
def GetConditionNameList():
    v = dynamicCall('GetConditionNameList()')
    conds = v.split(';')
    conds = [e for e in conds if len(e.strip()) > 0]
    conds = [cond.split('^') for cond in conds]
    print(['GetConditionNameList-->', len(conds), conds])
    return conds

@ftracer
def SendCondition(ScrNo, ConditionName, Index, Search):
    v = dynamicCall('SendCondition(QString,QString,int,int)', [ScrNo, ConditionName, Index, Search])
    d = {1:'성공', 0:'실패'}
    print(['SendCondition-->', ScrNo, ConditionName, Index, Search, d[v]])
    return v

@ftracer
def SetRealReg(ScrNo, CodeList, FidList, OptType):
    return dynamicCall('SetRealReg(QString,QString,QString,QString)', [ScrNo, CodeList, FidList, OptType])

@ftracer
def SetRealRemove(ScrNo, DelCode):
    return dynamicCall('SetRealRemove(QString,QString)', [ScrNo, DelCode])

############################################################
"""FunctionalAPIs::조회와-실시간데이터처리"""
############################################################
@ftracer
def CommRqData(RQName, TrCode, PrevNext, ScrNo):
    return dynamicCall('CommRqData(QString,QString,int,QString)', [RQName, TrCode, PrevNext, ScrNo])

# @ftracer
def GetCommData(TrCode, RecordName, Index, ItemName):
    return dynamicCall('GetCommData(QString,QString,int,QString)', [TrCode, RecordName, Index, ItemName])

@ftracer
def GetCommDataEx(TrCode, RecordName):
    return dynamicCall('GetCommDataEx(QString,QString)', [TrCode, RecordName])

# @ftracer
def GetCommRealData(Code, Fid):
    return dynamicCall('GetCommRealData(QString,QString)', [Code, Fid])

@ftracer
def GetRepeatCnt(TrCode, RQName):
    return dynamicCall('GetRepeatCnt(QString,QString)', [TrCode, RQName])

@ftracer
def SetInputValue(ID, Value):
    return dynamicCall('SetInputValue(QString,QString)', [ID, Value])

############################################################
"""FunctionalAPIs::주문과-잔고처리"""
############################################################
# @ftracer
def GetChejanData(Fid):
    return dynamicCall('GetChejanData(int)', [Fid])

@ftracer
def SendOrder(RQName,ScrNo,AccNo,OrderType,Code,Qty,Price,HogaGb,OrgOrderNo):
    return dynamicCall(
        'SendOrder(QString,QString,QString,int,QString,int,int,QString,QString)',
        [RQName,ScrNo,AccNo,OrderType,Code,Qty,Price,HogaGb,OrgOrderNo]
    )




############################################################
"""MyFunctionalAPIs"""
############################################################
# @ftracer
def getIssueInfo(code):
    v1 = GetMasterLastPrice(code)
    d = {
        'code': code,
        'name': GetMasterCodeName(code),
        'lst_dt': GetMasterListedStockDate(code),
        'n_shrs': GetMasterListedStockCnt(code),
        'supervision': GetMasterConstruction(code),
        '전일종가': v1,
        '기준가': v1,
        'warningETF': IsOrderWarningETF(code),
        'warningStock': IsOrderWarningStock(code),
        'updated_dt': trddt.today(),
    }
    d3 = GetMasterStockInfo(code)
    d.update(d3)
    d4 = GetMasterStockState(code)
    d.update(d4)
    return d


"""부하를 줄이기 위한 함수API"""
def _setup_IssueMap():
    m = datamodels.Issue()
    data = m.load({}, {'code':1,'name':1})
    o1 = BaseDataClass('종목코드-종목명 매핑')
    o2 = BaseDataClass('종목명-종목코드 매핑')
    for d in data:
        setattr(o1, d['code'], d['name'])
        setattr(o2, d['name'], d['code'])
    return o1, o2

IssueCodeName, IssueNameCode = _setup_IssueMap()

def getIssName(code): return getattr(IssueCodeName, code)

def getIssCode(name): return getattr(IssueNameCode, name)

def isscdnm(code):
    name = getIssName(code)
    return f'{name}({code})'

def clean_issueCode(s): return re.sub('^[A-Z]', repl='', string=s)

@ftracer
def isMoiServer():
    return True if GetServerGubun() == '모의' else False

def trcdnm(s):
    o = datamodels.TRList().select(s)
    return f'{o.trname}({o.trcode})'

"""호가단위"""
def callprcunit(prc):
    if prc < 2000: return 1
    elif 2000 <= prc < 5000: return 5
    elif 5000 <= prc < 2*pow(10,4): return 10
    elif 2*pow(10,4) <= prc < 5*pow(10,4): return 50
    elif 5*pow(10,4) <= prc < 20*pow(10,4): return 100
    elif 20*pow(10,4) <= prc < 50*pow(10,4): return 500
    elif 50*pow(10,4) <= prc: return 1000

"""입력가격의 호가정보"""
def callprcinfo00(code, prc):
    stndprc = GetMasterLastPrice(code)
    if prc > stndprc:
        nextprc = stndprc
        while nextprc < prc:
            nextprc += callprcunit(nextprc)
    else:
        nextprc = stndprc
        while nextprc > prc:
            nextprc -= callprcunit(nextprc)
    r = round(nextprc/stndprc-1, 4)
    return nextprc, r

"""입력퍼센트의 근접 상위호가정보"""
def callprcinfo01(code, pct):
    r1 = inumber.Percent(pct).to_float
    stndprc = GetMasterLastPrice(code)
    # stndprc = 3465
    nextprc = stndprc
    r2 = 0
    while r2 < r1:
        nextprc += callprcunit(nextprc)
        r2 = round(nextprc/stndprc-1, 4)
    return nextprc, r2

"""입력가격에서 몇% 높은 호가정보"""
def callprcinfo02(code, prc, pct):
    r1 = inumber.Percent(pct).to_float
    nextprc = prc
    r2 = 0
    while r2 < r1:
        nextprc += callprcunit(nextprc)
        r2 = nextprc/prc-1
    return callprcinfo00(code, nextprc)

"""모의투자도 실전투자 기준으로 맞추는게 맞다"""
def get_CostRate():
    return round(inumber.Percent(Cost).to_float, 4)

"""수익률계산"""
def calc_profit(p1, p2):
    r = round(p2/p1-1, 4)
    c = get_CostRate()
    return r - c

"""목표가계산"""
def calc_goalprc(buyprc, goalpct='0.1%'):
    cost = inumber.Percent(Cost, prec=2)
    goal = inumber.Percent(goalpct)
    r = 1 + cost.to_float + goal.to_float
    return int(buyprc * r)

def DtypeParser(k, v, dtype, unit=0):
    try:
        if dtype in ['int','int_abs','float']:
            v1 = inumber.iNumberV2(v, prec=4).value
            if math.isnan(v1): return v
            else:
                if dtype == 'int': v2 = int(v1)
                elif dtype == 'int_abs': v2 = abs(int(v1))
                else: v2 = v1
                if dtype == 'int_abs' and v2 < 0:
                    logger.error(k, unit, [v, v1, v2])
                return v2
        elif dtype == 'pct':
            return inumber.Percent(v, prec=2).to_float
        elif dtype in ['date','time','datetime']:
            v = idatetime.DatetimeParser(v)
            v = trddt.systrdday(v)
            t = trddt.now()
            if 0 <= t.hour <=5: v -= timedelta(days=1)
            else: pass
            return v
        elif dtype == 'str':
            return None if str(v) == 'nan' else str(v)
        elif dtype in ['boolean','bool']:
            return bool(v)
        else: raise
    except Exception as e:
        logger.error([k, v, dtype, unit])
        raise

@ftracer
def get_cash():
    if isMoiServer():
        cash = 10*pow(10,4)
    else:
        # data = KiwoomAPI.get_data('예수금')
        # cash = 0 if data is None else data[0]['d+2출금가능금액']
        cash = 0
    return cash


class ScreenNumberGenerator(QBaseObject):

    def __init__(self):
        super().__init__()
        self.cnt = 0
    def gen(self):
        self.cnt += 1
        v = math.fmod(self.cnt, 200)
        v = int(5000 + v)
        return str(v).zfill(4)

sng = ScreenNumberGenerator()

@ftracer
def gen_scrNo(): return sng.gen()



############################################################
"""키움서버API"""
############################################################
class KiwoomAPI(QBaseObject):
    MsgSent = pyqtSignal(str, str, str, str)

    ConnectSent = pyqtSignal(int)
    LoginSucceeded = pyqtSignal()

    TrDataSent = pyqtSignal(str, str, str, str, str, list)
    OrdNoSent = pyqtSignal(str, str, str)
    TrJangoSent = pyqtSignal(list)

    RealDataSent = pyqtSignal(str, str, dict)
    ChegeolSent = pyqtSignal(str, str, dict)
    RealJangoSent = pyqtSignal(str, dict)

    ConditionVerSent = pyqtSignal(int, str)
    TrConditionSent = pyqtSignal(str, list, str, int, int)
    RealConditionSent = pyqtSignal(str, str, str, str)

    @ctracer
    def __init__(self):
        super().__init__()

        OpenAPI.OnReceiveMsg.connect(self.OnReceiveMsg)
        OpenAPI.OnEventConnect.connect(self.OnEventConnect)
        OpenAPI.OnReceiveTrData.connect(self.OnReceiveTrData)
        OpenAPI.OnReceiveRealData.connect(self.OnReceiveRealData)
        OpenAPI.OnReceiveChejanData.connect(self.OnReceiveChejanData)
        OpenAPI.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
        OpenAPI.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)
        OpenAPI.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)

        self.ConnectState = 0

        self.TrServer = TrServer()
        self.RealServer = RealServer()
        self.HoldServer = HoldServer()
    @ctracer
    def State(self, *args): pass

    @ctracer
    @pyqtSlot(str)
    def restart(self, filepath):
        subprocess.run([sys.executable, os.path.realpath(filepath)] + sys.argv[1:])

    """#################### 메시지서버 ####################"""
    @ctracer
    @pyqtSlot(str, str, str, str)
    def OnReceiveMsg(self, ScrNo, RQName, TrCode, Msg):
        # self.MsgSent.emit(ScrNo, RQName, TrCode, Msg)
        if re.search('서버가 준비되어 있지 않습니다', Msg) is not None:
            logger.critical(f'{Msg} --> 시스템재시작')
            KiwoomAPI.restart()
        else: pass

    """#################### 로그인서버 ####################"""
    @ctracer
    def CommConnect(self, acct_win=False):
        self.acct_win = acct_win
        CommConnect()
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec()
    @ctracer
    @pyqtSlot(int)
    def OnEventConnect(self, ErrCode):
        self.ConnectState = OpenAPI.GetConnectState()
        if ErrCode == 0:
            self._set_login_info()
            self._set_account_info()
            pretty_title('로그인성공')
            dbg.dict(self)

            """계좌번호입력창"""
            if self.acct_win:
                ShowAccountWindow()
                # self.window_event_loop = QEventLoop()
                # self.window_event_loop.exec()
                # self.window_event_loop.exit()
            else: pass

            self.RealServer.InitRealReg()
            GetConditionLoad()

            """서버가 준비된 다음 마지막으로 신호를 보내라"""
            self.LoginSucceeded.emit()

            """시스템재시작테스트"""
            # for i in range(10):
            #     print(i)
            #     sleep(1)
            # self.restart()
        else:
            logger.critical(['로그인실패 --> 시스템재시작'])
            self.restart()
        self.login_event_loop.exit()
    @ctracer
    def _set_login_info(self):
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            v = OpenAPI.GetLoginInfo(item)
            setattr(self, item, v)
    @ctracer
    def _set_account_info(self):
        m = datamodels.Account()

        """신규계좌번호 저장"""
        acct_list = [e.strip() for e in self.ACCLIST.split(';') if len(e.strip()) > 0]
        for acct in acct_list:
            d = m.select(acct, type='dict')
            if d is None:
                gubun = '모의' if self.GetServerGubun == '1' else '실전'
                bank = '키움증권모의투자' if self.GetServerGubun == '1' else '무슨은행'
                d = {'AccountNo':acct,
                    'AccountGubun':gubun,
                    'AccountBank':bank,
                    'AccountCreatedDate':trddt.today()}
                m.insert_one(d)
            else: pass
        """계좌정보셋업"""
        s = '8041895711' if self.GetServerGubun == '1' else '하나은행'
        d = m.select(s, type='dict')
        for k,v in d.items(): setattr(self, k, v)

    """#################### TR데이타서버 ####################"""
    @ctracer
    def SetTrReg(self, inputs, rqname, trcode, prevnext, screen_no):
        self.TrServer.SetTrReg(inputs, rqname, trcode, prevnext, screen_no)
    @pyqtSlot(str, str, str, str, str, int, str, str, str)
    def OnReceiveTrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        if re.search('^KOA.+', TrCode) is not None:
            """주문번호처리"""
            ordNo = GetCommData(TrCode, RQName, 0, '주문번호').strip()
            self.OrdNoSent.emit(TrCode, RQName, ordNo)
        else:
            """일반데이타처리"""
            Data = self.TrServer._build_trdata(TrCode, RQName, self.AccountNo)

            if TrCode == 'opw00018':
                self.HoldServer.set(self.TrServer.storage.get('보유종목'))

            Data = [] if Data is None else Data
            self.TrDataSent.emit(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)

    """#################### 실시간데이타서버 ####################"""
    @ctracer
    def SetRealReg(self, code): self.RealServer.SetRealReg(code)
    @ctracer
    def SetRealRemove(self, code): self.RealServer.SetRealRemove(code)
    @pyqtSlot(str, str, str)
    def OnReceiveRealData(self, Code, RealType, RealData):
        def __emit__():
            d = self.RealServer._build_realdatum(Code, RealType)
            if isinstance(d, dict): self.RealDataSent.emit(Code, RealType, d)
            else: pass

        if RealType in ['장시작시간','VI발동/해제']: __emit__()
        else:
            if Code in self.RealServer.codes: __emit__()
            else:
                # 해제가 안된다......
                # SetRealRemove('ALL', Code)
                pass
    @pyqtSlot(str, int, str)
    def OnReceiveChejanData(self, Gubun, ItemCnt, FIdList):
        d = self.RealServer._build_chejandatum(FIdList)
        code = clean_issueCode(d['종목코드,업종코드'])
        if Gubun == '0':
            self.ChegeolSent.emit(code, d['주문번호'], d)
            # 신규매수/도 체결이 완료될 때 계좌잔고를 재요청한다
            if d['미체결수량'] == 0: self._refresh_trjango({'종목명':d['종목명'], '미체결수량':0})
        elif Gubun == '1':
            self.HoldServer.add(d['종목명'])

            self.RealServer.storage.set(code, d)
            self.RealJangoSent.emit(code, d)
    @ctracer
    def _refresh_trjango(self, *args):
        self.trapi01 = TrAPI('계좌평가잔고내역요청', maxLoop=None, timeout=10)
        self.trapi01.req()

    """#################### 조건검색서버 ####################"""
    @pyqtSlot(int, str)
    def OnReceiveConditionVer(self, Ret, Msg):
        self.ConditionVerSent.emit(Ret, Msg)
    @pyqtSlot(str, str, str, int, int)
    def OnReceiveTrCondition(self, ScrNo, CodeList, ConditionName, Index, Next):
        CodeList = CodeList.split(';')
        CodeList = [c for c in CodeList if len(c.strip()) > 0]
        self.TrConditionSent.emit(ScrNo, CodeList, ConditionName, Index, Next)
    @pyqtSlot(str, str, str, str)
    def OnReceiveRealCondition(self, Code, Type, ConditionName, ConditionIndex):
        self.RealConditionSent.emit(Code, Type, ConditionName, ConditionIndex)

    """#################### 데이타스토리지 ####################"""
    @ctracer
    def get_data(self, k):
        v = self.TrServer.storage.get(k)
        if v is None: logger.warning([self, f"요청한 '{k}' 정보는 가지고 있지 않다"])
        else: return v
    @ctracer
    def get_value(self, k):
        try:
            if k == 'd+2출금가능금액':
                v = self.TrServer.storage.get('예수금')[0][k]
                return 0 if v is None else v
            elif k == '종목최대투자금': return MAX_TRADE_BUDGET
            elif k == '보유종목': return self.HoldServer.holds
            else: return None
        except Exception as e:
            return None
    @ctracer
    def get_realjango(self, code): return self.RealServer.storage.get(code)


class RealServer(QBaseObject):

    @ctracer
    def __init__(self):
        super().__init__()
        self._setup_RealFID()

        self.codes = []
        self.start_timer('실시간등록FID일괄변경타이머', self._autochange_realreg, 60)

        self.storage = BaseDataClass('실시간잔고스토리지')

    """#################### 실시간데이타처리 ####################"""
    @ctracer
    def _setup_RealFID(self):
        m = datamodels.RealFID()
        f = {'useful':True}
        f.update({'dtype':{'$ne':None}})
        data = m.load(f)
        for d in data:
            if 'unit' not in d: d.update({'unit':0})
            o = BaseDataClass(**d)
            setattr(self, o.fid, o)

        self.realtypes = m.distinct('realtype', f)
        for realtype in self.realtypes:
            f.update({'realtype':realtype})
            fids = m.distinct('fid', f)
            setattr(self, realtype, fids)
    def _get_fids(self, realtype): return getattr(self, realtype)
    def _get_name(self, fid):
        try: return getattr(self, fid).name
        except Exception as e: return fid
    def _parse_value(self, fid, value):
        try: o = getattr(self, fid)
        except Exception as e: return value
        else: return DtypeParser(o.name, value, o.dtype, o.unit)
    def _build_realdatum(self, Code, RealType):
        if RealType in self.realtypes:
            d = {}
            fids = self._get_fids(RealType)
            for fid in fids:
                v = GetCommRealData(Code, int(fid)).strip()
                if len(v) > 0:
                    v = self._parse_value(fid, v)
                    name = self._get_name(fid)
                    d.update({name:v})
                else: pass

            if len(d) > 0: d.update({'dt':trddt.now()})
            else: pass
            return d
        else: return None
    def _build_chejandatum(self, FIdList):
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
                    v = self._parse_value(fid, v)
                    d.update({name: v})
        if len(d) == 0: raise
        else: d.update({'dt':trddt.now()})
        return d

    """#################### 레지스터 ####################"""
    @ctracer
    def InitRealReg(self):
        SetRealRemove('ALL', 'ALL')
        SetRealReg('5000', '09', '20;214;215', '1')
    @ctracer
    def SetRealReg(self, code):
        if len(self.codes) >= MAX_REALREG_LIMIT:
            logger.warning([self, '실시간등록최대종목수 초과하여 등록하지 않음', isscdnm(code)])
        else:
            if code in self.codes: pass
            else:
                tpls = self._autogen_param()
                for screen_no, fidList in tpls:
                    print([screen_no, code, fidList, '1'])
                    try:
                        v = SetRealReg(screen_no, code, fidList, '1')
                    except Exception as e:
                        logger.error(e)
                    else:
                        if v == 0: self.codes.append(code)
                        else: logger.error([self, {'리턴값':v}])
            self._report()
    # @ctracer
    def SetRealRemove(self, code):
        try: self.codes.remove(code)
        except Exception as e: pass
        else: SetRealRemove('ALL', code)
        finally: self._report()
    # @ctracer
    def _report(self):
        names = [getIssName(c) for c in self.codes]
        # self.State('실시간등록종목', len(names), names)
        print('실시간등록종목리스트', trddt.logtime(), [len(names), names])
    # @ctracer
    def _autogen_param(self):
        try:
            def __intime(s, e):
                t1, t2 = trddt.systrdday(s), trddt.systrdday(e)
                return True if t1 <= trddt.now() < t2 else False
            def __gen(realtypes):
                f = {'realtype': {'$regex': realtypes}, 'useful':True}
                fids = m.distinct('fid', f)
                fidList = ";".join(fids)
                screen_no = m.distinct('screen_no', f)[0]
                params.append((screen_no, fidList))

            m = datamodels.RealFID()
            params = []
            if __intime('08:40', '09:00'):
                __gen('주식예상체결|주식체결')
            elif __intime('09:00', '15:20'):
                __gen('주식체결|주식우선호가|주식호가잔량')
                # __gen('종목프로그램매매|주식당일거래원')
            elif __intime('15:20', '15:30'):
                __gen('주식예상체결|주식체결')
            elif __intime('16:00', '23:59'):
                __gen('주식시간외호가')
            else:
                __gen('주식체결')
            return params
        except Exception as e:
            logger.error([self, e])
            raise
    # @ctracer
    def _autochange_realreg(self):
        def __autochange__():
            SetRealRemove('ALL', 'ALL')
            codeList = ";".join(self.codes)
            tpls = self._autogen_param()
            for screen_no, fidList in tpls:
                p = (screen_no, codeList, fidList, '1')
                v = SetRealReg(*p)
                print(trddt.logtime(), ['실시간레지변경', {'리턴값':v, '파라미터':p}])

        t = trddt.now()
        t1 = trddt.systrdday('15:20')
        t2 = trddt.systrdday('15:30')
        t3 = trddt.systrdday('16:00')
        t4 = trddt.systrdday('16:10')
        if t1 <= t <= t2: __autochange__()
        elif t3 <= t <= t4: __autochange__()
        else: pass


class TrServer(QBaseObject):

    @ctracer
    def __init__(self):
        super().__init__()

        self._setup_TrItem()

        self.queue = []
        """1초안에 최대 5번 요청할 수 있다"""
        self.start_timer('TrReqTimer', self.__req__, 0.3)

        self.storage = BaseDataClass('데이타스토리지', 보유종목=[])

    """#################### 레지스터 ####################"""
    # @ctracer
    def SetTrReg(self, inputs, rqname, trcode, prevnext, screen_no):
        if trcode == 'opw00018':
            if prevnext == 0: self.storage.set('TR계좌잔고', [])
        else: pass

        p = [inputs, rqname, trcode, prevnext, screen_no]
        if p in self.queue: pass
        else: self.queue.append(p)
    # @ctracer
    def __req__(self):
        try:
            inputs, rqname, trcode, prevnext, screen_no = self.queue.pop(0)
        except Exception as e: pass
        else:
            for id, val in inputs: SetInputValue(id, val)
            CommRqData(rqname, trcode, prevnext, screen_no)
    def _report(self):
        df = pd.DataFrame(self.queue, columns=['inputs','rqname','trcode','prevnext','screen_no'])
        print(df.T)

    """#################### TR데이타처리 ####################"""
    @ctracer
    def _setup_TrItem(self):
        m = datamodels.TRItem()
        c = m.find()
        for d in list(c):
            if 'unit' not in d: d.update({'unit':0})
            o = BaseDataClass(**d)
            id = o.trcode + '_' + o.item
            setattr(self, id, o)

        self.trcodes = m.distinct('trcode')
        for trcode in self.trcodes:
            setattr(self, trcode, m.distinct('item', {'trcode':trcode}))
    def _parse_value(self, trcode, item, value):
        try: o = getattr(self, f'{trcode}_{item}')
        except Exception as e: return value
        else: return DtypeParser(o.item, value, o.dtype, o.unit)
    def _build_trdata(self, TrCode, RQName, AccountNo):
        if TrCode in self.trcodes:
            n = GetRepeatCnt(TrCode, RQName)
            dt = trddt.now()
            items = getattr(self, TrCode)
            Data = []
            for i in range(0, n+1, 1):
                d = {'dt': dt}
                for item in items:
                    v = GetCommData(TrCode, RQName, i, item).strip()
                    if len(v) == 0: pass
                    else:
                        v = self._parse_value(TrCode, item, v)
                        d.update({item: v})
                if len(d) > 1: Data.append(d)
                else: pass

            try: Data = getattr(self, f'_process_{TrCode}')(Data, AccountNo)
            except Exception as e: pass
            return Data

        else: return None
    """예수금상세현황요청"""
    # @ctracer
    def _process_opw00001(self, Data, AccountNo):
        for d in Data: d.update({'계좌번호':AccountNo})
        self.storage.set('예수금', Data)
        return Data
    """계좌평가잔고내역요청"""
    # @ctracer
    def _process_opw00018(self, Data, AccountNo):
        if len(Data) > 0:
            for d in Data: d.update({'계좌번호':AccountNo})

            # 기존잔고에 신규잔고를 합산
            li = self.storage.get('TR계좌잔고')
            li += Data
            for d in li: d.update({'dt':trddt.now()})
            df = pd.DataFrame(li).sort_values('평가손익', ascending=False).reset_index(drop=True)
            l1 = len(df)
            df = df.drop_duplicates(keep='first', subset=['종목명'])
            l2 = len(df)
            print('TR계좌잔고합산', [l1, l2])
            self.storage.set('TR계좌잔고', df.to_dict('records'))
            self.storage.set('보유종목', list(df.종목명))

            """뷰어"""
            _df = df.loc[:, ['종목명','평가손익','수익률(%)']]
            print('-'*100)
            print(_df[:60])
            if len(df) > 60:
                print('-'*100)
                print(_df[60:])
        else: pass
        return Data


class HoldServer(QBaseObject):

    @ctracer
    def __init__(self):
        super().__init__()
        self.holds = []
    @ctracer
    def set(self, li):
        self.holds = li
        self._report()
    @ctracer
    def add(self, name):
        if name not in self.holds: self.holds.append(name)
        self._report()
    def _report(self): print('보유종목리스트', [len(self.holds), self.holds])


KiwoomAPI = KiwoomAPI()




############################################################
"""키움백엔드서버"""
############################################################
RAW_DATA_MONITOR_ON = 0
TR_DATA_MONITOR_ON = 1
REAL_DATA_MONITOR_ON = 0
CHEJAN_DATA_MONITOR_ON = 1
COND_DATA_MONITOR_ON = 0

class BackendServer(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): super().finish()
    @ctracer
    def run(self):
        workers = [
            RawDataServer,
            TrDataServer,
            RealDataServer,
            ChejanDataServer,
            CondDataServer,
        ]
        self.wmdb = ThreadMDB('백엔드서버MDB')
        for w in workers: self.wmdb.set_n_run(w.__name__, w)
        dbg.dict(self.wmdb)


"""쌩데이타 수집기"""
class RawDataServer(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def run(self):
        self._monitorOn = bool(RAW_DATA_MONITOR_ON)

        OpenAPI.OnEventConnect.connect(self.OnEventConnect)
        OpenAPI.OnReceiveMsg.connect(self.OnReceiveMsg)
        OpenAPI.OnReceiveTrData.connect(self.OnReceiveTrData)
        OpenAPI.OnReceiveRealData.connect(self.OnReceiveRealData)
        OpenAPI.OnReceiveChejanData.connect(self.OnReceiveChejanData)

        self.conn = database.DataModel('OnEventConnect')
        self.msg = database.DataModel('OnReceiveMsg')
        self.tr = database.DataModel('OnReceiveTrData')
        self.real = database.DataModel('OnReceiveRealData')
        self.che = database.DataModel('OnReceiveChejanData')

    def _monitoring(self, *args):
        if self._monitorOn: print('쌩데이타모니터링', trddt.logtime(), args)
        else: pass

    @pyqtSlot(int)
    def OnEventConnect(self, ErrCode):
        d = {'dt':trddt.now(), 'ErrCode':ErrCode}
        self._monitoring(d)
        self.conn.insert_one(d)
    @pyqtSlot(str, str, str, str)
    def OnReceiveMsg(self, ScrNo, RQName, TrCode, Msg):
        d = { 'dt':trddt.now(), 'ScrNo':ScrNo, 'RQName':RQName, 'TrCode':TrCode, 'Msg':Msg}
        self._monitoring(d)
        self.msg.insert_one(d)
    @pyqtSlot(str, str, str, str, str, int, str, str, str)
    def OnReceiveTrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        d = {
            'dt':trddt.now(),
            'ScrNo':ScrNo, 'RQName':RQName, 'TrCode':TrCode, 'RecordName':RecordName, 'PrevNext':PrevNext,
            'DataLength':DataLength, 'ErrorCode':ErrorCode, 'Message':Message, 'SplmMsg':SplmMsg
        }
        self._monitoring(d)
        self.tr.insert_one(d)
    @pyqtSlot(str, str, str)
    def OnReceiveRealData(self, Code, RealType, RealData):
        d = {'dt':trddt.now(), 'Code':Code, 'RealType':RealType, 'RealData':RealData}
        self._monitoring(d)
        self.real.insert_one(d)
    @pyqtSlot(str, int, str)
    def OnReceiveChejanData(self, Gubun, ItemCnt, FIdList):
        d = {'dt':trddt.now(), 'Gubun':Gubun, 'ItemCnt':ItemCnt, 'FIdList':FIdList}
        self._monitoring(d)
        self.che.insert_one(d)


"""TR데이타 수집기"""
class TrDataServer(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): self.finished.emit()
    @ctracer
    def run(self):
        self._monitorOn = bool(TR_DATA_MONITOR_ON)
        KiwoomAPI.TrDataSent.connect(self._recv_trdata)

    @pyqtSlot(str, str, str, str, str, list)
    def _recv_trdata(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        """모니터링"""
        self.view01(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
        # if TrCode == 'opw00018':
        #     self.view02(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)

        """데이타처리"""
        try:
            f = getattr(self, f'_process_{TrCode}')
            Data = f(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
        except Exception as e: pass

        o = datamodels.TRList().select(TrCode)

        if re.search('봉차트조회요청$', o.trname) is None: pass
        else: self._process_charts(o.trname, RQName, Data)

        if o.modelExt == 0: extParam = None
        elif o.modelExt == 1: extParam = RQName
        m = datamodels.TRModel(TrCode, extParam)
        m.save_data(Data)

    def view01(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        print('TR데이타모니터링', [ScrNo, RQName, trcdnm(TrCode), RecordName, PrevNext, len(Data)])
    def view02(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        # if TrCode == 'opt10080':
        df = pd.DataFrame(Data)
        if len(Data) > 0: df = self._clean_df(df)
        else: pass

        title = f'{trcdnm(TrCode)} {[ScrNo, RQName, TrCode, PrevNext]}'
        pretty_title(title)
        # df.info()
        print(df)
    def _clean_df(self, df):
        try: df = df.drop(columns=['dt'])
        except Exception as e: pass

        for c in list(df.columns):
            if re.search('시간$|일자$|날짜$', c) is None: pass
            else:
                df = df.set_index(c)
                break
        df = df.dropna(axis=1, how='all')
        return df.fillna('_')

    def _process_OPT10029(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        for d in Data: d.update({'예상체결액':d['예상체결가'] * d['예상체결량']})
        return Data
    def _process_opt10027(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        for d in Data: d.update({'현재거래액':d['현재가'] * d['현재거래량']})
        return Data
    def _process_opt10001(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        m = datamodels.Issue()
        for d in Data: m.update_one({'code':d['종목코드']}, {'$set':d})
        return Data
    def _process_opt10028(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        for d in Data:
            stndprc = d['현재가'] - d['전일대비']
            d.update({'전일종가':stndprc})
            for e in ['시가','고가','저가']:
                d.update({f'{e}변화율':round(d[e]/stndprc-1, 4)})
        return Data
    def _process_charts(self, TrName, RQName, Data):
        t = trddt.now()
        c1 = True if t.hour >= 16 else False
        c2 = True if len(Data) > 0 else False
        name = getIssName(RQName)
        c3 = False if name is None else True
        if c1 and c2:
            m = database.DataModel('ChartDataSaveChecklist')
            f = {'name':name, 'code':RQName}
            d = f.copy()
            d.update({TrName:trddt.systrdday()})
            m.update_one(f, {'$set':d}, True)
        else: pass


"""실시간데이타 수집기"""
class RealDataServer(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): self.finished.emit()
    @ctracer
    def State(self, *args): pass
    @ctracer
    def run(self):
        self._monitorOn = bool(REAL_DATA_MONITOR_ON)
        OpenAPI.OnReceiveRealData.connect(self.OnReceiveRealData)
        KiwoomAPI.RealDataSent.connect(self._recv_realdata)
        self.mdb = BaseDataClass('RealModelsMDB')
        self.Company = datamodels.Issue()

    @pyqtSlot(str, str, str)
    def OnReceiveRealData(self, Code, RealType, RealData):
        if RealType in ['장시작시간','VI발동/해제','주식시간외호가']:
            print(trddt.logtime(), Code, RealType, RealData)
        else: pass
    @pyqtSlot(str, str, dict)
    def _recv_realdata(self, Code, RealType, Datum):
        """모니터링"""
        if self._monitorOn:
            d = Datum.copy()
            if RealType == '장시작시간':
                t1 = d['체결시간'].strftime('%H:%M:%S')
                t2 = d['장시작예상잔여시간']
                data = [d['장운영구분'], t1, t2]
                print('Real데이타모니터링', trddt.logtime(), [Code, RealType, data])
            elif RealType == 'VI발동/해제':
                t1 = d['매매체결처리시각'].strftime('%H:%M:%S')
                t2 = d['VI 해제시각'].strftime('%H:%M:%S')
                data = [d['VI 적용구분'], d['괴리율 정적'], t1, t2, d['VI 발동가격']]
                print('Real데이타모니터링', trddt.logtime(), [RealType, isscdnm(Code), data])
            elif RealType == '주식시간외호가':
                print('Real데이타모니터링', trddt.logtime(), [RealType, isscdnm(Code), Datum])
            else:
                del d['dt']
                print('Real데이타모니터링', trddt.logtime(), [RealType, isscdnm(Code), d])
        else: pass

        """데이타처리"""
        try:
            d1, d2, d3 = [Datum.copy() for i in range(3)]
            self._save01(Code, RealType, d1)
            self._save02(Code, RealType, d2)
        except Exception as e:
            logger.error([self, e, Code, RealType, Datum])
            raise

    """RealModelV1수집"""
    def _save01(self, Code, RealType, Datum):
        if RealType in ['장시작시간','VI발동/해제','업종지수','업종등락']:
            extParam, k = None, RealType
        else:
            extParam, k = Code, RealType+Code
        try:
            m = getattr(self, k)
        except Exception as e:
            m = datamodels.RealModelV1(RealType, extParam)
            setattr(self, k, m)
        finally:
            m.insert_one(Datum)
    """RealModelV2수집"""
    def _save02(self, Code, RealType, Datum):
        if RealType in ['장시작시간','VI발동/해제','업종지수','업종등락']: extParam = 'Market'
        else: extParam = Code
        k = 'RealData'+extParam
        try:
            m = getattr(self, k)
        except Exception as e:
            m = database.DataModel('RealData', extParam)
            setattr(self, k, m)
        finally:
            m.insert_one(Datum)

"""체결잔고데이타 수집기"""
class ChejanDataServer(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): self.finished.emit()
    @ctracer
    def run(self):
        self._monitorOn = bool(CHEJAN_DATA_MONITOR_ON)
        KiwoomAPI.ChegeolSent.connect(self._recv_chegeol)
        KiwoomAPI.RealJangoSent.connect(self._recv_realjango)
        self.start_timer('LoginCheckTimer', self._setup_after_login, 1)

    @pyqtSlot()
    def _setup_after_login(self):
        try: v = KiwoomAPI.AccountNo
        except Exception as e: pass
        else:
            self.stop_timer('LoginCheckTimer')
            self.Chegeol = datamodels.RealModelV1('주문체결', v)
            self.Jango = datamodels.RealModelV1('잔고', v)
            self.Company = datamodels.Issue()
    @pyqtSlot(str, str, dict)
    def _recv_chegeol(self, code, ordNo, d):
        """모니터링"""
        if self._monitorOn:
            _d = d.copy()
            del _d['dt']
            """방법.1"""
            print('-'*200)
            print('체결데이타모니터링', trddt.logtime(), [isscdnm(code), ordNo, _d])

            """방법.2"""
            # cols = ['종목명','주문구분','주문상태','주문번호','원주문번호','주문수량','미체결수량','주문/체결시간']
            # _d = {k:v for k,v in d.items() if k in cols}
            # _d.update({'주문/체결시간': d['주문/체결시간'].strftime('%H:%M:%S')})
            # print('-'*200)
            # print(_d)

        """데이타처리"""
        try: self.Chegeol.insert_one(d)
        except Exception as e: pass
    @pyqtSlot(str, dict)
    def _recv_realjango(self, code, d):
        """모니터링"""
        if self._monitorOn:
            _d = d.copy()
            try: del _d['dt']
            except Exception as e: print(e)
            print('-'*200)
            print('잔고데이타모니터링', trddt.logtime(), [isscdnm(code), _d])

        """데이타처리"""
        try: self.Jango.insert_one(d)
        except Exception as e: pass


"""조건검색 수집기"""
class CondDataServer(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): self.finished.emit()
    @ctracer
    def State(self, *args): pass
    @ctracer
    def run(self):
        self._monitorOn = bool(COND_DATA_MONITOR_ON)

        KiwoomAPI.ConditionVerSent.connect(self._recv_condver)
        KiwoomAPI.TrConditionSent.connect(self._recv_trcondition)
        KiwoomAPI.RealConditionSent.connect(self._recv_realcondition)

        self.screen_no = gen_scrNo()
        self.model = datamodels.ConditionSearchHistory()
        """조건식명-조건식설명 매핑"""
        m = database.DataModel('ConditionSearchInfo')
        data = m.load({'desc':{'$ne':None}})
        for d in data: setattr(self, d['name'], d['desc'])
    @ctracer
    @pyqtSlot(int, str)
    def _recv_condver(self, Ret, Msg):
        conds = GetConditionNameList()

        # DB저장
        m = database.DataModel('ConditionSearchInfo')
        for idx, name in conds:
            m.update_one({'name':name}, {'$set':{'idx':idx, 'name':name}}, True)

        # 한번에 최대 10개만 등록가능하다
        def __send__(conds):
            for idx, name in conds:
                SendCondition(self.screen_no, name, int(idx), 1)

        __send__(conds[:4])
        sleep(1)
        __send__(conds[4:8])
        sleep(1)
        __send__(conds[8:10])
    @pyqtSlot(str, list, str, int, int)
    def _recv_trcondition(self, ScrNo, CodeList, ConditionName, Index, Next):
        """모니터링"""
        if self._monitorOn:
            desc = getattr(self, ConditionName)
            print('TR조건검색모니터링', trddt.logtime(), [ConditionName, desc, {'종목수':len(CodeList)}])

        """데이타처리"""
        for Code in CodeList: self._record(ConditionName, 'I', Code)
    @pyqtSlot(str, str, str, str)
    def _recv_realcondition(self, Code, Type, ConditionName, ConditionIndex):
        """모니터링"""
        if self._monitorOn:
            if Type == 'I':
                desc = getattr(self, ConditionName)
                print('Real조건검색모니터링', trddt.logtime(), [ConditionName, desc, isscdnm(Code)])
            else: pass

        """데이타처리"""
        if Type == 'I': self._record(ConditionName, Type, Code)
        else: pass
    def _record(self, ConditionName, Type, Code):
        Name = getIssName(Code)
        self.model.record(ConditionName, Type, Code, Name)





############################################################
"""ObjectAPIs"""
############################################################
class TrAPI(QBaseObject):

    @ctracer
    def __init__(self, trcdnm, maxLoop=1, timeout=5, **kw):
        super().__init__()
        KiwoomAPI.TrDataSent.connect(self._recv_trdata)

        d = datamodels.TRList().select(trcdnm, type='dict')
        del d['inputs']
        for k,v in d.items(): setattr(self, k, v)

        self.screen_no = gen_scrNo()

        self._setup_TrInput()
        for k,v in kw.items(): self.set(k, v)

        self.maxLoop = maxLoop
        self.curLoop = 0
        self.timeout = timeout
        self.queue = []

        self.data = []
        self.cumData = []
    @ctracer
    def finish(self, *args):
        try:
            KiwoomAPI.TrDataSent.disconnect(self._recv_trdata)
        except Exception as e: pass
        self.stop_alltimers()
        super().finish()
    @ctracer
    def _finish_timeout(self): self.finish(self.trname, '키움서버로부터 데이타가 안온다')

    @ctracer
    def _setup_TrInput(self):
        def __autoset_dttype(id, val, trcode, fmt):
            if isinstance(val, str):
                dt = trddt.systrdday(val) if len(val) > 0 else trddt.systrdday()
                if re.search('종료', id) is not None: pass
                elif re.search('시작', id) is not None:
                    if trcode in ['OPT10072']: pass
                    else: dt -= timedelta(days=30)
                elif id == '기준일자':
                    dt = trddt.systrdday()
                else: pass

                try:
                    return dt.strftime(fmt)
                except Exception as e:
                    logger.error([self, e, id, val, trcode, fmt])
                    raise
            else: raise


        """초기값자동셋업"""
        m = datamodels.TRInput()
        c = m.find({'trcode':self.trcode})
        self._inputs = list(c)
        for d in self._inputs:
            # 초기값이 없으면 공백처리
            try: d['value']
            except Exception as e: d.update({'value':''})
            val = d['value']

            id = d['id']
            if id == '계좌번호': d.update({'value': KiwoomAPI.AccountNo})
            elif id == '비밀번호': d.update({'value': ''})
            else:
                try: fmt = d['fmt']
                except Exception as e: pass
                else: d.update({'value': __autoset_dttype(id, val, self.trcode, fmt)})

            """RQName초기값자동셋업"""
            if id == '계좌번호': self.rqname = KiwoomAPI.AccountNo
            elif id == '종목코드': self.rqname = val
            else: self.rqname = self.trname
    def set(self, k, v):
        for d in self._inputs:
            if d['id'] == k: d.update({'value':v})
            """RQName자동셋업"""
            if k == '계좌번호': self.rqname = KiwoomAPI.AccountNo
            elif k == '종목코드': self.rqname = v
            else: self.rqname = self.trname
    @property
    def inputs(self): return [(d['id'], d['value']) for d in self._inputs]
    def idvalueinfo(self):
        for i,d in enumerate(self._inputs, start=1):
            li = [d[c] for c in ['id','value','value_info']]
            li = ['None' if c is None else c for c in li]
            print(self.trname, i, " | ".join(li))

    @ctracer
    def req(self):
        self.start_timer('TrReqTimer', self.__req__, 0.5)
        self._next_loop(0)
    @ctracer
    def _next_loop(self, prevnext):
        try:
            self.queue.append([self.inputs, self.rqname, self.trcode, prevnext, self.screen_no])
        except Exception as e:
            logger.error(e)
            raise
    @ctracer
    def __req__(self):
        try: inputs, rqname, trcode, prevnext, screen_no = self.queue.pop(0)
        except Exception as e: pass
        else:
            KiwoomAPI.SetTrReg(inputs, rqname, trcode, prevnext, screen_no)
            self.start_timer('TrReqLimitTimer', self._finish_timeout, self.timeout)
    @pyqtSlot(str, str, str, str, str, list)
    def _recv_trdata(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        c1 = True if TrCode == self.trcode else False
        c2 = True if RQName == self.rqname else False
        if c1 and c2:
            self.stop_timer('TrReqLimitTimer')
            self.data = Data
            self.cumData += Data
            if self.maxLoop is None:
                if PrevNext == '2': self._next_loop(int(PrevNext))
                else: self.finish('더이상요청할데이타없음',{'PrevNext':PrevNext})
            elif isinstance(self.maxLoop, int):
                self.curLoop += 1
                if self.curLoop < self.maxLoop: self._next_loop(int(PrevNext))
                else: self.finish('최대반복수도달', {'maxLoop':self.maxLoop})
        else: pass


class IssueAPI(QBaseObject):
    refreshed = pyqtSignal()
    vi_occurred = pyqtSignal()
    soldOut = pyqtSignal()
    onSale = pyqtSignal()
    onBuy = pyqtSignal()
    SendSellSig = pyqtSignal(int, int)

    @ctracer
    def __init__(self, cdnm):
        super().__init__()

        d = datamodels.Issue().select(cdnm, type='dict')
        if d is None:
            logger.error(['존재하지않는 종목', {'cdnm':cdnm}])
            raise
        else:
            for k,v in d.items(): setattr(self, k, v)

            KiwoomAPI.TrDataSent.connect(self._recv_trdata)
            KiwoomAPI.RealDataSent.connect(self._recv_realdata)
            KiwoomAPI.RealJangoSent.connect(self._recv_realjango)
            KiwoomAPI.SetRealReg(self.code)
            self._set_coreInfo()
            self.req_basicInfo()
            self._setup_preprices()
            self._set_buycallprc()

            self.start_timer('PrePriceRateTimer', self._setup_preprices, 10)
            self.start_timer('TrJangoReadTimer', self._read_trjango, 5)
            self._read_trjango()
            self.start_timer('ValuateTimer', self._calc_CurProfitPct, 1)
            self.start_timer('VICalculateTimer', self._calc_vi, 10)

            # self.start_timer('SelfDebugTimer', self._debug01, 10)
            # self.start_timer('PrePriceRateReport', self._debug02, 10)
            # self.start_timer('VIDebugTimer', self._debug03, 10)
            self.start_timer('CurProfitDebugTimer', self._debug04, 10)
    @ctracer
    def finish(self, *args):
        try:
            KiwoomAPI.SetRealRemove(self.code)
            KiwoomAPI.TrDataSent.disconnect(self._recv_trdata)
            KiwoomAPI.RealDataSent.disconnect(self._recv_realdata)
            KiwoomAPI.RealJangoSent.disconnect(self._recv_realjango)
        except Exception as e: pass
        self.stop_alltimers()
        super().finish()

    @ctracer
    def _set_coreInfo(self):
        d = getIssueInfo(self.code)
        for k,v in d.items(): setattr(self, k, v)
    """주식기본정보요청"""
    @ctracer
    def req_basicInfo(self):
        self.trapi01 = TrAPI('주식기본정보요청', 종목코드=self.code)
        self.trapi01.req()

    """입력가격의 호가정보"""
    # @ctracer
    def callprcinfo00(self, prc):
        try: stndprc = getattr(self, '기준가')
        except Exception as e: pass
        else:
            if prc > stndprc:
                nextprc = stndprc
                while nextprc < prc:
                    nextprc += callprcunit(nextprc)
            else:
                nextprc = stndprc
                while nextprc > prc:
                    nextprc -= callprcunit(nextprc)
            r = round(nextprc/stndprc-1, 4)
            return nextprc, r
    """입력퍼센트의 근접 상위호가정보"""
    # @ctracer
    def callprcinfo01(self, pct):
        try: stndprc = getattr(self, '기준가')
        except Exception as e: pass
        else:
            r1 = inumber.Percent(pct).to_float
            nextprc = stndprc
            r2 = 0
            while r2 < r1:
                nextprc += callprcunit(nextprc)
                r2 = round(nextprc/stndprc-1, 4)
            return nextprc, r2
    """입력가격에서 몇% 높은 호가정보"""
    # @ctracer
    def callprcinfo02(self, prc, pct):
        try: stndprc = getattr(self, '기준가')
        except Exception as e: pass
        else:
            r1 = inumber.Percent(pct).to_float
            nextprc = prc
            r2 = 0
            while r2 < r1:
                nextprc += callprcunit(nextprc)
                r2 = nextprc/prc-1
            r = round(nextprc/stndprc-1, 4)
            return nextprc, r

    @pyqtSlot(str, str, str, str, str, list)
    def _recv_trdata(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        if TrCode == 'opt10001':
            if RQName == self.code:
                for k,v in Data[0].items(): setattr(self, k, v)
                self._calc_vi()
                self._calc_preprc_rch()
                self.refreshed.emit()
                self._update_IssueModel(Data[0])
            else: pass
        elif TrCode == 'opw00018':
            for d in Data:
                if d['종목명'] == self.name:
                    self._attributize(d)
                    self._set_buycallprc()
        else: pass
    @pyqtSlot(str, str, dict)
    def _recv_realdata(self, Code, RealType, Datum):
        if Code == self.code:
            for k,v in Datum.items(): setattr(self, k, v)
            if RealType == 'VI발동/해제':
                self._calc_vi()
                self.vi_occurred.emit()
            self._calc_preprc_rch()
        else: pass
    @pyqtSlot(str, dict)
    def _recv_realjango(self, code, d):
        if code == self.code:
            for k,v in d.items(): setattr(self, k, v)
            self._set_buycallprc()
            if d['보유수량'] == 0: self.soldOut.emit()
            else: self.onSale.emit()
        else: pass
    @ctracer
    def _read_trjango(self):
        data = KiwoomAPI.get_data('TR계좌잔고')
        if data is None: pass
        else:
            _data = [d for d in data if d['종목명'] == self.name]
            if len(_data) == 1:
                d = _data[0]
                self._attributize(d)
                self._set_buycallprc()
                if d['보유수량'] == 0: self.soldOut.emit()
                else: self.onSale.emit()
            else:
                self.onBuy.emit()
            self.stop_timer('TrJangoReadTimer')

    # @ctracer
    def _attributize(self, d):
        for k,v in d.items():
            if k == '(최우선)매도호가': k = '매도호가1'
            elif k == '(최우선)매수호가': k = '매수호가1'
            # 실시간잔고 필드명 기준으로 통일시킨다
            elif k == '매매가능수량': k = '주문가능수량'
            elif k == '매입가': k = '매입단가'
            setattr(self, k, v)
    # @ctracer
    def _update_IssueModel(self, d):
        m = datamodels.Issue()
        m.update_one({'code':self.code}, {'$set':d})
    # @ctracer
    def _calc_vi(self):
        def __calc_n_save(p):
            p = int(p)
            if p == 0: logger.warning([self.cdnm, {'p':0}, 'VI계산기준가는 0이 될 수 없다'])
            else:
                p, r = self.callprcinfo00(p)
                setattr(self, 'VI상기준가격', p)
                setattr(self, 'VI상기준가격R', r)

                # 상한가를 넘어서도 그냥 저장한다
                p2, r2 = self.callprcinfo02(p, '10%')
                setattr(self, 'VI상발동예상가격', p2)
                setattr(self, 'VI상발동예상가격R', r2)

                # 상한가를 넘어서면, 상한가 바로 밑 호가를 채택한다
                p3, r3 = self.callprcinfo02(p, '9%')
                try: top = getattr(self, '상한가')
                except Exception as e: pass
                else:
                    if p3 > top:
                        p3 = top - callprcunit(p3)
                        p3, r3 = self.callprcinfo00(p3)
                    else: pass
                setattr(self, 'VI상발동예상매도적정가격', p3)
                setattr(self, 'VI상발동예상매도적정가격R', r3)

                m = database.DataModel('IssueGoalProfitPct')
                f = {'name':self.name}
                d = f.copy()
                pct2 = inumber.Percent(r2*100, prec=2)
                pct3 = inumber.Percent(r3*100, prec=2)
                d.update({
                    'VI호가':p2, 'VI호가R':r2,
                    'VI매도호가':p3, 'VI매도호가R':r3,
                })
                m.update_one(f, {'$set':d}, True)

        try:
            t = trddt.now()
            t1 = trddt.systrdday('09:00')
            if t < t1:
                # 전일종가 기준으로 계산한다
                pass
            else:
                # VI발동해제 이력을 뒤져서 가져온다
                # 없다면 시가를 기준으로 계산한다
                m = datamodels.RealModelV1('VI발동/해제')
                f,s = {}, [('매매체결처리시각',-1)]
                f.update({'dt':{'$gte':trddt.systrdday()}})
                f.update({'종목명':self.name})
                data = m.load(f,sort=s, limit=1)
                if len(data) == 1:
                    for k,v in data[0].items(): setattr(self, k, v)
                    p = int(getattr(self, '기준가격 정적'))
                    __calc_n_save(p)
                else:
                    m = datamodels.TRModel('변동성완화장치발동종목요청')
                    f,s = {}, [('매매체결처리시각',-1)]
                    f.update({'dt':{'$gte':trddt.systrdday()}})
                    f.update({'종목명':self.name})
                    data = m.load(f,sort=s, limit=1)
                    if len(data) == 1:
                        for k,v in data[0].items(): setattr(self, k, v)
                        p = int(getattr(self, '발동가격'))
                        __calc_n_save(p)
                    else:
                        try: p = getattr(self, '시가')
                        except Exception as e: pass
                        else: __calc_n_save(p)
        except Exception as e:
            logger.error([self.cdnm, self, e])
            dbg.dict(self)
            raise

    # @ctracer
    def _setup_preprices(self):
        # [1] 단기급등(다음 사항에 모두 해당)                                     |
        # ① 판단일(T)의 종가가 5일 전날(T-5)의 종가보다 60% 이상 상승           |
        # ② 판단일(T)의 종가가 당일을 포함한 최근 15일 종가중 가장 높은 가격    |
        # ③ 5일 전날(T-5)을 기준으로 한 해당종목의 주가상승률이                 |
        #    같은 기간 종합주가지수 상승률의 5배 이상                            |
        #                                                                        |
        # [2] 중장기급등(다음 사항에 모두 해당)                                   |
        # ① 판단일(T)의 종가가 15일 전날(T-15)의 종가보다 100% 이상 상승        |
        # ② 판단일(T)의 종가가 당일을 포함한 최근 15일 종가중 가장 높은 가격    |
        # ③ 15일 전날(T-15)을 기준으로 한 해당종목의 주가상승률이               |
        #    같은 기간 종합주가지수 상승률의 3배 이상
        try:
            m = datamodels.IssueDailyData(self.name)
            for n in [5,10,15]:
                t = trddt.systrddaydelta(delta=n*-1)
                try: p = m.distinct('현재가', {'일자':t})[0]
                except Exception as e: pass
                else:
                    setattr(self, f'{n}일전종가', p)
                    self.stop_timer('PrePriceRateTimer')
        except Exception as e:
            logger.error([self, e])
            raise
    """몇일전 대비 변화율"""
    # @ctracer
    def _calc_preprc_rch(self):
        try: p0 = getattr(self, '현재가')
        except Exception as e: pass
        else:
            for n in [5,10,15]:
                try: p1 = getattr(self, f'{n}일전종가')
                except Exception as e: pass
                else:
                    r = round(p0/p1 -1, 4)
                    setattr(self, f'{n}일전종가대비변화율', r)
    """매입호가"""
    # @ctracer
    def _set_buycallprc(self):
        try:
            stndprc = getattr(self, '기준가')
            prc = getattr(self, '매입단가')
        except Exception as e: pass
        else:
            if prc > stndprc:
                nextprc = stndprc
                while nextprc < prc:
                    nextprc += callprcunit(nextprc)
            else:
                nextprc = stndprc
                while nextprc > prc:
                    nextprc -= callprcunit(nextprc)
            r = round(nextprc/stndprc-1, 4)
            setattr(self, '매입호가', nextprc)
            setattr(self, '매입호가R', r)
    """목표매도호가1::목표수익률%로 호가찾기"""
    # @ctracer
    def _set_GoalProfitPct(self, pct='1%'):
        # 매입단가 기준으로 목표수익률 적용한 호가구하기
        try:
            p0 = getattr(self, '기준가')
            p1 = getattr(self, '매입단가')
        except Exception as e: pass
        else:
            r = inumber.Percent(pct).to_float
            setattr(self, '목표수익률R', r)
            # v = r + get_CostRate()
            # # 목표호가 찾기
            # p = p1
            # r1 = v
            # r2 = 0
            # while r2 < r1:
            #     p += callprcunit(p)
            #     r2 = p/p1-1
            # # 해당호가는 기준가로부터 몇%인가
            # r = round(p/p0-1, 4)
            #
            # setattr(self, '목표매도호가', p)
            # setattr(self, '목표매도호가R', r)
            # print([self.cdnm, p0, p1, p, r])
    """목표매도호가2::목표호가%로 호가찾기"""
    # @ctracer
    def _set_GoalCallPct(self, pct='4%'):
        # 기준가로부터 목표호가%에 해당하는 호가구하기
        try:
            p0 = getattr(self, '기준가')
        except Exception as e: pass
        else:
            r1 = inumber.Percent(pct).to_float
            p = p0
            r = 0
            while r < r1:
                p += callprcunit(p)
                r = round(p/p0-1, 4)
            setattr(self, '목표매도호가', p)
            setattr(self, '목표매도호가R', r)
            # print([self.cdnm, p0, p, r])

    """현수익률&매도신호"""
    # @ctracer
    def _calc_CurProfitPct(self):
        def __sell__(p1):
            print([self.cdnm, '팔아라'])
            self._debug04()
            amt = self._get_sellable_amt()
            if amt > 0: self.SendSellSig.emit(p1, amt)
            else: pass

        try:
            p0 = getattr(self, '매입단가')
            p1 = getattr(self, '매수호가1')
        except Exception as e: pass
        else:
            r1 = round(p1/p0-1, 4)
            r1 -= get_CostRate()
            setattr(self, '현수익률R', round(r1,4))

            """METHOD-1::목표매도호가R 로 매도판단"""
            try: p2 = getattr(self, '목표매도호가')
            except Exception as e: pass
            else:
                if p1 >= p2 and r1 > 0: __sell__(p1)

            """METHOD-2::목표수익률R 로 매도판단"""
            try: r0 = getattr(self, '목표수익률R')
            except Exception as e: pass
            else:
                if r1 >= r0: __sell__(p1)
    # @ctracer
    def _get_sellable_amt(self):
        try:
            a1 = getattr(self, '보유수량')
            a2 = getattr(self, '주문가능수량')
            a3 = getattr(self, '매수호가수량1')
        except Exception as e: return 0
        else:
            if a1 > 0:
                if a2 > a3: return a3
                else: return a2
            else:
                return 0

    def _debug01(self):
        # print('-'*100)
        # print(self.cdnm, sorted(self.__dict__))
        print(trddt.logtime(), [self.cdnm, '데이타개수:', len(self.__dict__)])
    def _debug02(self):
        cols = ['목표수익률R','목표매도호가R']
        cols += [f'{n}일전종가대비변화율' for n in [5,10,15]]
        d = self.__get_attrs(cols)
        print([self.cdnm, d])
    def _debug03(self):
        cols = ['VI상기준가격','VI상발동예상가격','VI상발동예상매도적정가격']
        cols += [c+'R' for c in cols]
        d = self.__get_attrs(cols)
        print([self.cdnm, d])
    def _debug04(self):
        cols = ['현수익률R','목표수익률R','목표매도호가R','목표매도호가','매수호가1','매입단가','기준가','주문가능수량']
        d = self.__get_attrs(cols)
        print('수익률모니터링', self.cdnm, trddt.logtime(), d)
    def __get_attrs(self, cols):
        d = {}
        for c in cols:
            try: v = getattr(self, c)
            except Exception as e: pass
            else: d.update({c:v})
        return d


class OrderAPI(QBaseObject):
    # 주문량체결완료시
    completed = pyqtSignal()
    # 취소주문완료시
    cancelled = pyqtSignal()
    errored = pyqtSignal()
    # 완전종료시 rqname을 리턴해서 객체를 삭제하도록 한다
    terminated = pyqtSignal(str)
    # 에러발생시 [오류코드 음수값:OpenAPISendOrder오류 | -999:주문번호 없음]
    ApiErrorSent = pyqtSignal(int)
    OrderImpossibleTime = pyqtSignal()
    onSale = pyqtSignal()
    soldOut = pyqtSignal()
    stillBuying = pyqtSignal()
    stillSelling = pyqtSignal()

    @ctracer
    def __init__(self, isscdnm, otype, hoga, prc, amt, orgOrderNo='', timeout=60*10):
        super().__init__()
        OpenAPI.OnReceiveMsg.connect(self.OnReceiveMsg)
        KiwoomAPI.RealJangoSent.connect(self._recv_realjango)
        KiwoomAPI.ChegeolSent.connect(self._recv_chegeol)
        KiwoomAPI.OrdNoSent.connect(self._recv_ordNo)

        """파라미터 셋업"""
        self.rqname = trddt.logtime()
        self.acct_no = KiwoomAPI.AccountNo
        self.screen_no = gen_scrNo()
        self.Issue = datamodels.Issue().select(isscdnm)
        self.code = self.Issue.code
        self.amt = int(inumber.iNumber(amt))
        self.orgOrderNo = orgOrderNo
        self.timeout = int(timeout)

        OrderType = database.DataModel('OrderType').select({'name':{'$regex':otype}})
        self.ordertype = int(OrderType.code)
        self._ordertype = OrderType.name

        HogaGubun = database.DataModel('HogaGubun').select({'name':{'$regex':hoga}})
        self.hoga = str(HogaGubun.code)
        self._hoga = HogaGubun.name

        """가격재조정"""
        prc = int(inumber.iNumber(prc))
        if OrderType.name in ['신규매수','신규매도']:
            if HogaGubun.name == '지정가':
                if prc == 0: raise
                else: self.prc = prc
            elif HogaGubun.name == '시장가':
                self.prc = 0
            else: raise
        elif OrderType.name in ['매수취소','매도취소']:
            self.prc = 0
            if len(orgOrderNo) == 0: raise
            else: pass
        else: raise

        # 객체종료시 전송할 ID
        self.org_key = self.rqname
    @ctracer
    def finish(self, *args):
        try:
            OpenAPI.OnReceiveMsg.disconnect(self.OnReceiveMsg)
            KiwoomAPI.RealJangoSent.disconnect(self._recv_realjango)
            KiwoomAPI.ChegeolSent.disconnect(self._recv_chegeol)
            KiwoomAPI.OrdNoSent.disconnect(self._recv_ordNo)
        except Exception as e: pass
        self.stop_alltimers()
        super().finish()
        try: self.terminated.emit(self.org_key)
        except Exception as e: logger.error([self.code, e])
    @ctracer
    def _finish_completed(self, *args):
        self.completed.emit()
        self.finish(self.Issue.cdnm, f'{self._ordertype}완료', *args)
    @ctracer
    def _finish_cancelled(self, *args):
        self.cancelled.emit()
        self.finish(self.Issue.cdnm, f'{self._ordertype}완료', *args)
    @ctracer
    def _finish_errored(self, *args):
        self.errored.emit()
        self.finish(self.Issue.cdnm, f'{self._ordertype}실패', *args)
    @ctracer
    def State(self, *args): pass

    """#################### 주문요청 ####################"""
    @ctracer
    def _SendOrder(self):
        params = ['rqname','screen_no','acct_no','ordertype','code','amt','prc','hoga','orgOrderNo']
        args = [getattr(self, p) for p in params]
        kwargs = {p:getattr(self, p) for p in params}
        print(trddt.logtime(), [self.Issue.cdnm, self._ordertype, kwargs])
        v = SendOrder(*args)
        if v == 0: pass
        else:
            self.ApiErrorSent.emit(v)
            kwargs.update({'에러코드':v})
            self._finish_errored(self.Issue.cdnm, '주문오류', kwargs)

    """신규매수,신규매도,매수취소,매도취소"""
    @ctracer
    def order(self):
        self.start_timer('OrderLimitTimer', self._cancel, self.timeout)
        self._SendOrder()
    """타이머주문취소"""
    @ctracer
    def _cancel(self):
        try:
            ordNo = getattr(self, '주문번호')
            amt = getattr(self, '미체결수량')
        except Exception as e:
            msg = {'경고':'타이머주문취소실패', '주문ID':self.rqname, '에러':e}
            logger.critical([self.Issue.cdnm, self._ordertype, msg])
        else:
            self.stop_timer('OrderLimitTimer')
            self.rqname = trddt.logtime()
            v = 3 if self.ordertype == 1 else 4
            o = database.DataModel('OrderType').select({'code':v})
            self.ordertype = int(o.code)
            self._ordertype = o.name
            self.prc = 0
            self.amt = amt
            self.orgOrderNo = ordNo
            self._SendOrder()

    """#################### 데이타수신 ####################"""
    # @ctracer
    @pyqtSlot(str, str, str, str)
    def OnReceiveMsg(self, ScrNo, RQName, TrCode, Msg):
        if re.search('장종료되었습니다|장종료$|영업일이 아닙니다', Msg) is not None:
            self._finish_errored(Msg)
        elif re.search('오류', Msg) is not None:
            self._finish_errored(Msg)
        else: pass
    # @ctracer
    @pyqtSlot(str, str, str)
    def _recv_ordNo(self, TrCode, RQName, ordNo):
        if RQName == self.rqname:
            d = {'주문ID':RQName, '주문번호':ordNo}
            if len(ordNo) == 0:
                logger.warning([self.Issue.cdnm, f'{self._ordertype}/주문번호없음', d])
            else:
                self.State(self.Issue.cdnm, f'{self._ordertype}주문번호수신', d)
                self.ordNo = ordNo
                setattr(self, '주문번호', ordNo)
        else: pass
    # @ctracer
    @pyqtSlot(str, str, dict)
    def _recv_chegeol(self, code, ordNo, d):
        if code == self.Issue.code:
            for k,v in d.items(): setattr(self, k, v)
            self.ordNo = ordNo

            msg = {'주문ID':self.rqname,'주문번호':ordNo}
            #################### 주문접수 ####################
            if d['주문상태'] == '접수': pass
            #################### 매수매도 ####################
            elif d['주문상태'] == '체결':
                if '체결량' in d:
                    if d['주문수량'] == d['체결량']: self._finish_completed(msg)
                    else:
                        if d['주문구분'] == '+매수': self.stillBuying.emit()
                        elif d['주문구분'] == '-매도': self.stillSelling.emit()
                else:
                    logger.error(['체결량없음', d])
                    raise
            #################### 주문취소 ####################
            elif d['주문상태'] == '확인':
                if d['주문구분'] == '매수취소':
                    if '보유수량' in d:
                        print('부분매수상태 --> 추가매수없이 매도모드 바로전환')
                    else:
                        print('매수실패상태--> 매수모드 다시실행')
                elif d['주문구분'] == '매도취소': pass
                self._finish_cancelled(msg)
        else: pass
    @pyqtSlot(str, dict)
    def _recv_realjango(self, code, d):
        if code == self.Issue.code:
            for k,v in d.items(): setattr(self, k, v)
        else: pass
