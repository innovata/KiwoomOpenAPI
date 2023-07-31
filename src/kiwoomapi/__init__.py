# -*- coding: utf-8 -*-
import os, sys, subprocess
from datetime import datetime, timedelta
from time import sleep
import re
import math
import importlib


from PyQt5.QtCore import *
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QEventLoop
import pandas as pd


from ipylib.idebug import *
from ipylib import inumber, iparser, idatetime
from ipylib.datacls import BaseDataClass

import trddt
from pyqtclass import QBaseObject


from kiwoomapi._openapi import *
from kiwoomapi import mdb, const  




############################################################
"""General Functions"""
############################################################
def clean_issueCode(code):
    m = re.search('([A-Z]*)(\d+$)|([A-Z]*)(\d+[A-Z]$)', code)
    code = m[2]
    return code





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


def getIssName(code):
    try:
        return getattr(dataapi.IssueCodeName, code)
    except Exception as e:
        logger.error([e, code])
        name = GetMasterCodeName(code)
        setattr(dataapi.IssueCodeName, code, name)
        setattr(dataapi.IssueNameCode, name, code)
        return name


def getIssCode(name):
    try:
        return getattr(dataapi.IssueNameCode, name)
    except Exception as e:
        logger.error(e, name)
        raise


def isscdnm(code):
    name = getIssName(code)
    return f'{name}({code})'


def isMoiServer(): return True if GetServerGubun() == '모의' else False


"""호가단위"""
def callprcunit(prc):
    for d in mdb.CALL_PRICE_UNIT_DATA:
        if d['left'] <= prc < d['right']: return d['unit']
        else: pass

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
def callprcinfo02(code, price, pct):
    r1 = inumber.Percent(pct).to_float
    nextprc = price
    r2 = 0
    while r2 < r1:
        nextprc += callprcunit(nextprc)
        r2 = nextprc/price-1
    return callprcinfo00(code, nextprc)


"""기준가로부터 목표호가%에 해당하는 호가구하기"""
def callprcinfo03(stndprc, pct):
    nextprc = stndprc
    r1 = inumber.Percent(pct).to_float
    r2 = 0
    while r2 < r1:
        nextprc += callprcunit(nextprc)
        r2 = round(nextprc/stndprc-1, 4)
    return nextprc, r2


"""모의투자도 실전투자 기준으로 맞추는게 맞다"""
def get_CostRate(): return round(inumber.Percent(const.Cost).to_float, 4)


"""수익률계산"""
def calc_profit(p1, p2):
    r = round(p2/p1-1, 4)
    c = get_CostRate()
    return r - c


"""목표가계산"""
def calc_goalprc(buyprc, goalpct='0.1%'):
    cost = inumber.Percent(const.Cost, prec=2)
    goal = inumber.Percent(goalpct)
    r = 1 + cost.to_float + goal.to_float
    return int(buyprc * r)


def KiwoomDataParser(k, v, dtype, unit=0):
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
            return idatetime.DatetimeParser(v)
        elif dtype == 'str':
            return None if str(v) == 'nan' else str(v)
        elif dtype in ['boolean','bool']:
            return bool(v)
        else: raise
    except Exception as e:
        logger.error([k, v, dtype, unit])
        raise


class ScreenNumberGenerator(QBaseObject):

    def __init__(self):
        super().__init__()
        self.cnt = 0
    def gen(self):
        self.cnt += 1
        v = math.fmod(self.cnt, 200)
        v = int(5000 + v)
        return str(v).zfill(4)

SNG = ScreenNumberGenerator()

def gen_scrNo(): return SNG.gen()



# 프로세스 자체를 재시작해야 키움증권OpenAPI 32비트 COM 객체를 리셋할 수 있다
@ftracer
def restart():
    filepath = os.environ['RUN_FILE_PATH']
    subprocess.run([sys.executable, os.path.realpath(filepath)] + sys.argv[1:])




############################################################
"""키움OpenAPI"""
############################################################


"""로그인/계좌 정보 API"""
class LoginAPI(QBaseObject):
    ConnectSent = pyqtSignal(int)
    LoginSucceeded = pyqtSignal()

    @ctracer
    def __init__(self):
        super().__init__()
        OpenAPI.OnEventConnect.connect(self.OnEventConnect)
    @ctracer
    def CommConnect(self, acct_win=False):
        self._acct_win = acct_win
        CommConnect()
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec()
    @ctracer
    @pyqtSlot(int)
    def OnEventConnect(self, ErrCode):
        self.ConnectState = GetConnectState()
        if ErrCode == 0:
            self._set_login_info()
            self._save_new_accounts()
            self.select_acct()

            pretty_title('로그인/계좌 정보')
            dbg.dict(self)


            """계좌번호입력창"""
            if self._acct_win: ShowAccountWindow()

            """서버가 준비된 다음 마지막으로 신호를 보내라"""
            self.LoginSucceeded.emit()
            self.login_event_loop.exit()
        else:
            logger.critical(['로그인실패 --> 시스템재시작'])
            restart()
    @ctracer
    def _set_login_info(self):
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            v = GetLoginInfo(item)
            setattr(self, item, v)
    """신규계좌번호 저장"""
    @ctracer
    def _save_new_accounts(self):
        acctList = [e.strip() for e in LoginAPI.ACCLIST.split(';') if len(e.strip()) > 0]

        model = datamodels.Account()
        for acct in acctList:
            d = model.select(acct, type='dict')
            if d is None:
                gubun = '모의' if isMoiServer() else '실전'
                bank = '키움증권모의투자' if isMoiServer() else '새로운은행이름'
                d = {'AccountNo': acct,
                    'AccountGubun': gubun,
                    'AccountBank': bank,
                    'AccountCreatedDate': trddt.today()}
                print(['신규계좌발생-->', d])
                model.insert_one(d)
            else: pass
    """계좌정보 선택&셋업"""
    @ctracer
    def select_acct(self):
        s = '키움증권모의투자' if isMoiServer() else '하나은행'
        model = datamodels.Account()
        d = model.select(s, type='dict')
        for k,v in d.items(): setattr(self, k, v)


LoginAPI = LoginAPI()

@ftracer
def login(acct_win=False): LoginAPI.CommConnect(acct_win)

def account_no(): return LoginAPI.AccountNo




class TrAPI(QBaseObject):
    TrDataSent = pyqtSignal(str, str, str, str, str, list)
    OrdNoSent = pyqtSignal(str, str, str)
    TrJangoSent = pyqtSignal(list)

    @ctracer
    def __init__(self):
        super().__init__()
        OpenAPI.OnReceiveTrData.connect(self.OnReceiveTrData)

        self._setup_TrItem()

        self._reset_TrJango()

        LoginAPI.LoginSucceeded.connect(self.WhenLoginSucceeded)

        self.queue = []
        """1초안에 최대 5번 요청할 수 있다"""
        self.start_timer('TR요청타이머', self.__req__, 0.3)

    """#################### 레지스터 ####################"""
    @pyqtSlot()
    def WhenLoginSucceeded(self):
        print('\n로그인성공 후 계좌관련TR을 요청한다\n')
        # self.trapi01 = TrReq('계좌평가잔고내역요청', maxLoop=None, timeout=10)
        # self.trapi01.req()

        # self.trapi02 = TrReq('예수금상세현황요청', timeout=10)
        # self.trapi02.req()
    @ctracer
    def SetTrReg(self, inputs, rqname, trcode, prevnext, screen_no):
        p = [inputs, rqname, trcode, prevnext, screen_no]
        if p in self.queue: pass
        else: self.queue.append(p)
        # 계좌잔고평가요청이면 TR계좌잔고를 리셋한다
        if trcode == 'opw00018' and prevnext == 0: self._reset_TrJango()
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
    @pyqtSlot(str, str, str, str, str, int, str, str, str)
    def OnReceiveTrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        if re.search('^KOA.+', TrCode) is not None:
            """주문번호처리"""
            ordNo = GetCommData(TrCode, RQName, 0, '주문번호').strip()
            self.OrdNoSent.emit(TrCode, RQName, ordNo)
        else:
            """일반데이타처리"""
            Data = self._build_trdata(TrCode, RQName)
            Data = self.preprocess_data(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
            self._monitor_TrData(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
            self.TrDataSent.emit(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
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
        else: return KiwoomDataParser(o.item, value, o.dtype, o.unit)
    def _build_trdata(self, TrCode, RQName):
        if TrCode in self.trcodes:
            n = GetRepeatCnt(TrCode, RQName)
            _now = trddt.now()
            _day = _now.replace(hour=0, minute=0, second=0, microsecond=0)
            items = getattr(self, TrCode)
            Data = []
            for i in range(0, n+1, 1):
                d = {'dt': _now, 'date': _day}
                for item in items:
                    v = GetCommData(TrCode, RQName, i, item).strip()
                    if len(v) == 0: pass
                    else:
                        v = self._parse_value(TrCode, item, v)
                        d.update({item: v})
                if len(d) > 2: Data.append(d)
                else: pass
            return Data
        else: return []

    # TR별로 필요한 데이타를 추가한다
    # @ctracer
    def preprocess_data(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        if re.search('opt10080|opt10081', TrCode) is not None:
            Data = self._process_charts(RQName, TrCode, Data)
        elif re.search('^opw', TrCode) is not None:
            Data = self._process_account_related(TrCode, Data)
        else:
            try: f = getattr(self, f'_process_{TrCode}')
            except Exception as e: pass
            else: Data = f(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
        return Data

    """주식[분/일]봉차트조회요청"""
    def _process_charts(self, RQName, TrCode, Data):
        try:
            if TrCode == 'opt10080':
                for d in Data:
                    t = d['체결시간'].astimezone().strftime('%Y-%m-%d')
                    d.update({'일자': idatetime.DatetimeParser(t)})
        except Exception as e:
            logger.error(e)
            raise
        return Data
    """계좌번호 관련 요청"""
    def _process_account_related(self, TrCode, Data):
        for d in Data:
            d['계좌번호'] = account_no()
        if TrCode == 'opw00018': self._setup_TrJango(Data)
        elif TrCode == 'opw00001': self._setup_Yesugeum(Data)
        return Data
    """예상체결등락률상위요청"""
    def _process_OPT10029(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        for d in Data:
            d['일자'] = d['dt'].replace(hour=0, minute=0, second=0, microsecond=0)
            try: d['예상체결액'] = d['예상체결가'] * d['예상체결량']
            except Exception as e: pass
        return Data
    """전일대비등락률상위요청"""
    def _process_opt10027(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        for d in Data:
            d['현재거래액'] = d['현재가'] * d['현재거래량']
            d['일자'] = d['dt'].replace(hour=0, minute=0, second=0, microsecond=0)
        return Data
    """시가대비등락률요청"""
    def _process_opt10028(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        for d in Data:
            stndprc = d['현재가'] - d['전일대비']
            d['전일종가'] = stndprc
            d['일자'] = d['dt'].replace(hour=0, minute=0, second=0, microsecond=0)
            for e in ['시가','고가','저가']:
                d[f'{e}변화율'] = round(d[e]/stndprc-1, 4)
        return Data

    def _monitor_TrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        def __clean__(df):
            try: df = df.drop(columns=['dt'])
            except Exception as e: pass

            for c in list(df.columns):
                if re.search('시간$|일자$|날짜$', c) is None: pass
                else:
                    df = df.set_index(c).sort_index()
                    break
            return df.dropna(axis=1, how='all').\
                    reset_index(drop=True).fillna('_')
        def __monitor01__():
            if len(Data) > 0:
                title = f'{dataapi.trcdnm(TrCode)} {[ScrNo, RQName, TrCode, PrevNext]}'
                pretty_title(title)
                df = pd.DataFrame(Data)
                df = __clean__(df)
                # df.info()
                print(df)
            else: pass
        def __monitor02__():
            print(
                trddt.logtime(), 'TR데이타모니터링',
                [ScrNo, RQName, dataapi.trcdnm(TrCode), RecordName, PrevNext, len(Data)]
            )

        __monitor02__()


    """#################### 계좌잔고관리 ####################"""
    def _reset_TrJango(self):
        setattr(self, 'TR계좌잔고', [])
    # @ctracer
    def _setup_TrJango(self, Data):
        if len(Data) == 0: pass
        else:
            try:
                """기존잔고에 신규잔고를 합산"""
                li = getattr(self, 'TR계좌잔고')
                for d in Data: d['종목번호'] = clean_issueCode(d['종목번호'])
                li += Data
                df = pd.DataFrame(li).\
                    drop_duplicates(keep='first', subset=['종목명']).\
                    sort_values('평가손익', ascending=False).\
                    reset_index(drop=True)

                setattr(self, 'TR계좌잔고', df.to_dict('records'))
                self._holdCodes = list(df['종목번호'])
                self._holdNames = list(df['종목명'])
            except Exception as e:
                logger.error(e)
            else:
                """뷰어"""
                self._view_TrJango(df)
                self.TrJangoSent.emit(df.to_dict('records'))
    # @ctracer
    def _view_TrJango(self, df):
        _df = df.loc[:, ['종목명','종목번호','평가손익','수익률(%)']].\
                sort_values('수익률(%)', ascending=False).\
                reset_index(drop=True)
        pretty_title('계좌평가잔고내역(누적)')
        print(_df[:60])
        if len(df) > 60:
            print('-'*100)
            print(_df[60:])
    def get_TrJango(self): return getattr(self, 'TR계좌잔고').copy()
    def get_HoldCodes(self): return self._holdCodes.copy()
    def get_HoldNames(self): return self._holdNames.copy()

    # @ctracer
    def _setup_Yesugeum(self, Data):
        setattr(self, '예수금', Data[0])
    def get_Yesugeum(self): return getattr(self, '예수금')

TrAPI = TrAPI()




class RealAPI(QBaseObject):
    RealDataSent = pyqtSignal(str, str, dict)
    ChegeolSent = pyqtSignal(str, str, dict)
    RealJangoSent = pyqtSignal(str, dict)

    @ctracer
    def __init__(self):
        super().__init__()
        OpenAPI.OnReceiveRealData.connect(self.OnReceiveRealData)
        OpenAPI.OnReceiveChejanData.connect(self.OnReceiveChejanData)

        self._setup_RealFID()

        self.codes = []

        LoginAPI.LoginSucceeded.connect(self.WhenLoginSucceeded)


    """#################### 레지스터 ####################"""
    @pyqtSlot()
    def WhenLoginSucceeded(self):
        print('\n로그인성공 후 실시간레지를 초기화한다\n')
        self.InitRealReg()
        self.SetRealVIReg()
        self._autochange_realreg()
        self.start_timer('실시간등록자동변경타이머', self._autochange_realreg, 60)
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
        print(trddt.logtime(), '실시간등록종목리스트', [len(names), names])
    # @ctracer
    def _autogen_param(self):
        m = datamodels.RealFID()
        fidLists = m.autogen_fidLists()
        params = []
        for fidList in fidLists:
            params.append((gen_scrNo(), fidList))
        return params
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
        t1 = trddt.date('15:20')
        t2 = trddt.date('15:30')
        t3 = trddt.date('16:00')
        t4 = trddt.date('16:10')
        if t1 <= t <= t2: __autochange__()
        elif t3 <= t <= t4: __autochange__()
        else: pass
    """변동성완화장치발동종목요청"""
    @ctracer
    def SetRealVIReg(self):
        desc = """\nOpenAPI에서 변동성완화장치는 OPT10054 : 변동성완화장치발동종목요청 조회로 구하실수 있으며
        조회 TR의 "종목코드" 입력값에 따라 결과가 다르게 됩니다.
        공백으로 설정하면 "시장구분"입력값으로 설정한 전체(000) 코스피(001), 코스닥(101) 구분으로 조회되며
        변동성완화장치 실시간 데이터를 수신할수 있습니다.
        정리해서 답변드리면 TR 조회후 VI발생한 종목은 실시간타입 "VI발동/해제"으로 수신됩니다.
        영웅문4 [0193]변동성완화장치(VI)발동종목현황 화면 참고 바랍니다.\n"""
        print(desc)
        self.TrApiVI = TrReq('변동성완화장치발동종목요청', maxLoop=None, timeout=10)
        self.TrApiVI.req()

    """#################### 실시간데이타처리 ####################"""
    # @ctracer
    @pyqtSlot(str, str, str)
    def OnReceiveRealData(self, Code, RealType, RealData):
        def __emit__():
            d = self._build_RealDatum(Code, RealType)
            if isinstance(d, dict): self.RealDataSent.emit(Code, RealType, d)
            else: pass

        if RealType in ['장시작시간','VI발동/해제']: __emit__()
        else:
            if Code in self.codes: __emit__()
            else:
                # 해제가 안된다......
                # SetRealRemove('ALL', Code)
                pass
    @ctracer
    @pyqtSlot(str, int, str)
    def OnReceiveChejanData(self, Gubun, ItemCnt, FIdList):
        d = self._build_ChejanDatum(FIdList)
        code = clean_issueCode(d['종목코드,업종코드'])
        if Gubun == '0':
            self.ChegeolSent.emit(code, d['주문번호'], d)
        elif Gubun == '1':
            self.RealJangoSent.emit(code, d)

    # 서버쪽에서는 모든 FID 를 가지고 있어야 한다.
    # 클라이언트쪽에서 무슨 FID를 등록할지 모르니까.
    # @ctracer
    def _setup_RealFID(self):
        f = {'dtype': {'$ne': None}}
        model = datamodels.RealFID()
        data = model.load(f)
        for d in data:
            if 'unit' not in d: d.update({'unit':0})
            o = BaseDataClass(**d)
            setattr(self, o.fid, o)

        self.realtypes = model.distinct('realtype', f)
        for realtype in self.realtypes:
            f.update({'realtype':realtype})
            fids = model.distinct('fid', f)
            setattr(self, realtype, fids)
    # @ctracer
    def _get_fids(self, realtype): return getattr(self, realtype)
    # @ctracer
    def _get_name(self, fid):
        try: return getattr(self, fid).name
        except Exception as e: return fid
    # @ctracer
    def _parse_value(self, fid, value):
        try: o = getattr(self, fid)
        except Exception as e: return value
        else: return KiwoomDataParser(o.name, value, o.dtype, o.unit)
    # @ctracer
    def _build_RealDatum(self, Code, RealType):
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
    # @ctracer
    def _build_ChejanDatum(self, FIdList):
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
        else: d.update({'dt': trddt.now()})
        return d

RealAPI = RealAPI()





class ConditionAPI(QBaseObject):
    ConditionListSent = pyqtSignal(list)
    TrConditionSent = pyqtSignal(str, list, str, int, int)
    RealConditionSent = pyqtSignal(str, str, str, str)

    @ctracer
    def __init__(self):
        super().__init__()
        OpenAPI.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
        OpenAPI.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)
        OpenAPI.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)

        LoginAPI.LoginSucceeded.connect(self.WhenLoginSucceeded)
    @pyqtSlot()
    def WhenLoginSucceeded(self):
        print('\n로그인성공 후 영웅문에 등록된 모든 조건을 요청한다\n')
        GetConditionLoad()
    @ctracer
    @pyqtSlot(int, str)
    def OnReceiveConditionVer(self, Ret, Msg):
        conds = GetConditionNameList()
        self.SendConditions(conds)
        self.ConditionListSent.emit(conds)
    @pyqtSlot(str, str, str, int, int)
    def OnReceiveTrCondition(self, ScrNo, CodeList, ConditionName, Index, Next):
        CodeList = CodeList.split(';')
        CodeList = [c for c in CodeList if len(c.strip()) > 0]
        self.TrConditionSent.emit(ScrNo, CodeList, ConditionName, Index, Next)
    @pyqtSlot(str, str, str, str)
    def OnReceiveRealCondition(self, Code, Type, ConditionName, ConditionIndex):
        self.RealConditionSent.emit(Code, Type, ConditionName, ConditionIndex)
    @ctracer
    def SendConditions(self, conds):
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

ConditionAPI = ConditionAPI()




############################################################
"""ClientAPIs"""
############################################################
class TrReq(QBaseObject):

    @ctracer
    def __init__(self, trcdnm, maxLoop=1, timeout=5, monitor=False, **kw):
        super().__init__()
        TrAPI.TrDataSent.connect(self._recv_TrData)

        d = datamodels.TRList().select(trcdnm, type='dict')
        del d['inputs']
        for k,v in d.items(): setattr(self, k, v)

        self.screen_no = gen_scrNo()

        self._setup_TrInput()
        for k,v in kw.items(): self.set(k, v)

        self.maxLoop = maxLoop
        self.curLoop = 0
        self.timeout = timeout
        self._monitor = monitor
        self.queue = []

        self.data = []
        self.cumData = []
    @ctracer
    def finish(self, *args):
        try:
            TrAPI.TrDataSent.disconnect(self._recv_TrData)
        except Exception as e: pass
        self.stop_alltimers()
        super().finish()
    @ctracer
    def _finish_timeout(self): self.finish(self.trname, '키움서버로부터 데이타가 안온다')

    @ctracer
    def _setup_TrInput(self):
        def __autoset_dttype(id, val, trcode, fmt):
            if isinstance(val, str):
                dt = trddt.date(val) if len(val) > 0 else trddt.date()
                if re.search('종료', id) is not None: pass
                elif re.search('시작', id) is not None:
                    if trcode in ['OPT10072']: pass
                    else: dt -= timedelta(days=30)
                elif id == '기준일자':
                    dt = trddt.date()
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
            if id == '계좌번호': d.update({'value': account_no()})
            elif id == '비밀번호': d.update({'value': ''})
            elif id == '비밀번호입력매체구분': d.update({'value': '00'})
            else:
                try: fmt = d['fmt']
                except Exception as e: pass
                else: d.update({'value': __autoset_dttype(id, val, self.trcode, fmt)})

            """RQName초기값자동셋업"""
            if id == '계좌번호': self.rqname = account_no()
            elif id == '종목코드': self.rqname = val
            else: self.rqname = self.trname
    def set(self, k, v):
        for d in self._inputs:
            if d['id'] == k: d.update({'value':v})
            """RQName자동셋업"""
            if k == '계좌번호': self.rqname = account_no()
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
        self.start_timer('TR요청타이머', self.__req__, 0.5)
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
            TrAPI.SetTrReg(inputs, rqname, trcode, prevnext, screen_no)
            self.start_timer('TR요청한계타이머', self._finish_timeout, self.timeout)

    # @ctracer
    @pyqtSlot(str, str, str, str, str, list)
    def _recv_TrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        c1 = True if TrCode == self.trcode else False
        c2 = True if RQName == self.rqname else False
        if c1 and c2:
            self.stop_timer('TR요청한계타이머')

            self._save_TrData(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)

            self.data = Data
            self.cumData += Data
            if self.maxLoop is None:
                if PrevNext == '2': self._next_loop(int(PrevNext))
                else: self.finish('더이상요청할데이타없음', {'PrevNext':PrevNext})
            elif isinstance(self.maxLoop, int):
                self.curLoop += 1
                if self.curLoop < self.maxLoop: self._next_loop(int(PrevNext))
                else: self.finish('최대반복수도달', {'maxLoop':self.maxLoop})
        else: pass
    """데이타저장"""
    # @ctracer
    def _save_TrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, Data):
        if len(Data) > 0:
            model = datamodels.TRModel(TrCode, RQName)
            model.save_data(ScrNo, RQName, TrCode, RecordName, PrevNext, Data)
        else: pass



class Order(QBaseObject):
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
        RealAPI.RealJangoSent.connect(self._recv_RealJango)
        RealAPI.ChegeolSent.connect(self._recv_Chegeol)
        TrAPI.OrdNoSent.connect(self._recv_ordNo)

        """파라미터 셋업"""
        self.rqname = trddt.logtime()
        self.acct_no = account_no()
        self.screen_no = gen_scrNo()
        o = datamodels.Issue().select(isscdnm)
        self.code = o.code
        self.cdnm = o.cdnm
        self.amt = int(inumber.iNumber(amt))
        self.orgOrderNo = orgOrderNo
        self.timeout = int(timeout)

        OrderType = datamodels.DataModel('OrderType').select({'name':{'$regex':otype}})
        self.ordertype = int(OrderType.code)
        self._ordertype = OrderType.name

        HogaGubun = datamodels.DataModel('HogaGubun').select({'name':{'$regex':hoga}})
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
            RealAPI.RealJangoSent.disconnect(self._recv_RealJango)
            RealAPI.ChegeolSent.disconnect(self._recv_Chegeol)
            TrAPI.OrdNoSent.disconnect(self._recv_ordNo)
        except Exception as e: pass
        self.stop_alltimers()
        super().finish()
        try: self.terminated.emit(self.org_key)
        except Exception as e: logger.error([self.code, e])
    @ctracer
    def _finish_completed(self, *args):
        self.completed.emit()
        self.finish(self.cdnm, f'{self._ordertype}완료', *args)
    @ctracer
    def _finish_cancelled(self, *args):
        self.cancelled.emit()
        self.finish(self.cdnm, f'{self._ordertype}완료', *args)
    @ctracer
    def _finish_errored(self, *args):
        self.errored.emit()
        self.finish(self.cdnm, f'{self._ordertype}실패', *args)
    @ctracer
    def State(self, *args): pass

    """#################### 주문요청 ####################"""
    @ctracer
    def _SendOrder(self):
        params = ['rqname','screen_no','acct_no','ordertype','code','amt','prc','hoga','orgOrderNo']
        args = [getattr(self, p) for p in params]
        kwargs = {p:getattr(self, p) for p in params}
        print(trddt.logtime(), [self.cdnm, self._ordertype, kwargs])
        v = SendOrder(*args)
        if v == 0: pass
        else:
            self.ApiErrorSent.emit(v)
            kwargs.update({'에러코드':v})
            self._finish_errored(self.cdnm, '주문오류', kwargs)

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
            logger.critical([self.cdnm, self._ordertype, msg])
        else:
            self.stop_timer('OrderLimitTimer')
            self.rqname = trddt.logtime()
            v = 3 if self.ordertype == 1 else 4
            o = datamodels.DataModel('OrderType').select({'code':v})
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
    @ctracer
    @pyqtSlot(str, str, str)
    def _recv_ordNo(self, TrCode, RQName, ordNo):
        if RQName == self.rqname:
            d = {'주문ID':RQName, '주문번호':ordNo}
            if len(ordNo) == 0:
                logger.warning([self.cdnm, f'{self._ordertype}/주문번호없음', d])
                self.ordNo = '없음'
            else:
                self.ordNo = ordNo
                setattr(self, '주문번호', ordNo)
                self.State(self.cdnm, f'{self._ordertype}주문번호수신', d)
        else: pass
    @ctracer
    @pyqtSlot(str, str, dict)
    def _recv_Chegeol(self, code, ordNo, d):
        if code == self.code:
            for k,v in d.items(): setattr(self, k, v)
            _ordNo = getattr(self, '주문번호')

            if _ordNo == ordNo:
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
            else:
                logger.error([code, ordNo, d])
        else: pass
    @pyqtSlot(str, dict)
    def _recv_RealJango(self, code, d):
        if code == self.code:
            for k,v in d.items(): setattr(self, k, v)
        else: pass



