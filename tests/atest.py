# -*- coding: utf-8 -*-
from tests._testenv import *
from ipylib.datacls import BaseDataClass
from pyqtclass import *

import kiwoomapi as openapi
from kiwoomapi import KiwoomAPI


class AppTester(QBaseObject):
    finished = pyqtSignal()
    closed = pyqtSignal() # finished 로 통일하라
    stopped = pyqtSignal() # finished 로 통일하라
    started = pyqtSignal() # 가끔 필요한 경우도 있다
    completed = pyqtSignal() # started 로 통일하라
    trigger = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.name = self.__class__.__name__
        self.key = 0
        self.mdb = BaseDataClass('테스트객체MDB')
        self.wmdb = ThreadMDB('테스트스레드MDB')
        """테스트함수리스트"""
        self.testNoList = []
        for a in dir(self):
            m = re.search('(test)(\d+)', a)
            if m is None: pass
            else: self.testNoList.append(m[2])
        print('테스트번호', self.testNoList)
        dbg.set_viewEnvType('logger')
    @ctracer
    def testNo(self, s, e=None, sec=1):
        if e is None: e = s
        else: pass

        def __get(s):
            for k in range(2,5):
                no = str(s).zfill(k)
                if no in self.testNoList: return no
                else: pass

        for i in range(s, e+1):
            sleep(sec)
            no = __get(i)
            try: getattr(self, f"test{no}")()
            except Exception as e:
                logger.error([self, e, i])
    def _autogen_key(self):
        k = str(self.key).zfill(4)
        self.key += 1
        return k
    def run_worker(self, cls):
        k = self._autogen_key()
        self.wmdb.set_n_run(k, cls)
    def set_object(self, obj):
        k = self._autogen_key()
        self.mdb.set(k, obj)


issname = '셀바스AI'
isscode = openapi.getIssCode(issname)


class kiwoomapi_openapi(AppTester):

    def __init__(self): super().__init__()
    def run(self):
        self.testNo(501)
        self.testNo(201)

    """#################### OpenAPI ####################"""
    """로그인-버전처리"""
    def test01(self):
        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for k in items:
            v = openapi.GetLoginInfo(k)
            print([k, v, type(v), len(v)])

        v = openapi.GetConnectState()
        print(['GetConnectState', v, type(v)])
    """기타함수"""
    def test02(self):
        v = openapi.GetBranchCodeName()
        print(['GetBranchCodeName', v, type(v)])
        if not isinstance(v, list): raise

        v = openapi.GetCodeListByMarket('0')
        print(['GetCodeListByMarket', v, type(v)])
        if not isinstance(v, list): raise

        v = openapi.GetMasterCodeName(isscode)
        print(['GetMasterCodeName', v, type(v)])
        if not isinstance(v, str): raise

        v = openapi.GetMasterConstruction(isscode)
        print(['GetMasterConstruction', v, type(v)])
        if not isinstance(v, str): raise

        v = openapi.GetMasterLastPrice(isscode)
        print(['GetMasterLastPrice', v, type(v)])
        if not isinstance(v, int): raise

        v = openapi.GetMasterListedStockDate(isscode)
        print(['GetMasterListedStockDate', v, type(v)])
        if not isinstance(v, datetime): raise

        v = openapi.GetMasterListedStockCnt(isscode)
        print(['GetMasterListedStockCnt', v, type(v)])
        if not isinstance(v, int): raise

        v = openapi.GetMasterStockState(isscode)
        print(['GetMasterStockState', v, type(v)])
        if not isinstance(v, dict): raise

        mktcds = db.UpjongMarketCode.distinct('code')
        for ujcd in mktcds:
            v = openapi.GetUpjongCode(ujcd)
            print(['GetUpjongCode', ujcd, v, type(v)])
            if not isinstance(v, list): raise

        v = openapi.GetServerGubun()
        print(['GetServerGubun',v, type(v)])
        if not isinstance(v, str): raise

        v = openapi.GetUpjongNameByCode('002')
        print(['GetUpjongNameByCode',v, type(v)])
        if not isinstance(v, str): raise

        v = openapi.IsOrderWarningETF(isscode)
        print(['IsOrderWarningETF',v, type(v)])
        if not isinstance(v, bool): raise

        v = openapi.IsOrderWarningStock(isscode)
        print(['IsOrderWarningStock',v, type(v)])
        if not isinstance(v, bool): raise

        v = openapi.GetMasterStockInfo(isscode)
        print(['GetMasterStockInfo',v, type(v)])
        if not isinstance(v, dict): raise

        # openapi.ShowAccountWindow()
    """조회와-실시간데이터처리"""
    def test03(self):
        # m = datamodels.TRInput()
        # data = m.load({'trname':'주식기본정보요청'}, {'id':1, 'value':1, '_id':0})
        # for d in data:
        #     try:
        #         v = openapi.SetInputValue(d['id'], d['value'])
        #         print(['SetInputValue', v, type(v), d])
        #     except Exception as e:
        #         print(['SetInputValue', e, d])

        pretty_title('케이스1')
        v = openapi.SetInputValue('종목코드', isscode)
        print(['SetInputValue', v, type(v)])

        v = openapi.CommRqData('요청명','opt10001',0,'8000')
        print(['CommRqData', v, type(v)])

        v = openapi.GetRepeatCnt('opt10001', '요청명')
        print(['GetRepeatCnt', v, type(v)])

        pretty_title('케이스2::GetRepeatCnt 몇개?')
        sleep(2)
        openapi.SetInputValue('종목코드', isscode)
        openapi.SetInputValue('기준일자', '20230210')
        openapi.SetInputValue('수정주가구분', '1')
        v = openapi.CommRqData(isscode,'opt10081',0,'8001')
        print(['CommRqData', v, type(v)])
        v = openapi.GetRepeatCnt('opt10081', isscode)
        print(['GetRepeatCnt', v, type(v)])

        pretty_title('케이스3::인풋없이 요청만 하면 에러')
        sleep(2)
        v = openapi.CommRqData('요청명','opt10001',0,'8000')
        print(['CommRqData', v, type(v)])

        v = openapi.SetRealReg('5000', '09', '20;214;215', '1')
        print(['SetRealReg', v, type(v)])

        v = openapi.SetRealRemove('ALL', 'ALL')
        print(['SetRealRemove', v, type(v)])
    """조건검색"""
    def test04(self):
        v = openapi.GetConditionLoad()
        print(['GetConditionLoad->', v, type(v)])

        v = openapi.GetConditionNameList()
        print(['GetConditionNameList->', v, type(v)])

        v = openapi.SendCondition('9000', '0000', int('005'), 1)
        print(['SendCondition->', v, type(v)])
        v = openapi.SendCondition('9000', '0001', int('004'), 1)
        v = openapi.SendCondition('9000', '0002', int('001'), 1)
        v = openapi.SendCondition('9000', '0003', int('003'), 1)
        print(['SendCondition->', v, type(v)])

        # v = openapi.SendConditionStop('9000', '0000', int('005'))
        # print(['SendConditionStop->', v, type(v)])
    """주문과-잔고처리"""
    def test05(self):
        v = openapi.SendOrder('rqname','9000','8041895711',1,isscode,1,2000,'00','')
        print(['SendOrder', v, type(v)])

        v = openapi.GetChejanData(910)
        print(['GetChejanData', v, type(v)])

    """#################### KiwoomAPI ####################"""
    def test20(self):
        for i in range(10):
            print(i)
            sleep(1)
        KiwoomAPI.restart()
    """실시간등록종목수 100개 제한"""
    def test21(self):
        data = datamodels.Issue().load({'banned':False}, sort=[('lst_dt',-1)], limit=110)
        codes = [d['code'] for d in data]
        print([len(codes), codes])
        for c in codes:
            KiwoomAPI.SetRealReg(c)
            sleep(0.5)
    def test22(self):
        for i in range(10):
            sleep(1)
            v = KiwoomAPI.get('예수금')
            print(v)
    def test23(self):
        o = openapi.RealServer
        @ctracer
        @pyqtSlot(str, str, dict)
        def __recv__(Code, RealType, d): pass
        o.RealDataSent.connect(__recv__)
        o.SetRealReg(isscode)
        # sleep(10)
        # o.SetRealRemove(isscode)
    """Real데이타모니터링"""
    def test24(self):
        KiwoomAPI.SetRealReg(isscode)

    """#################### IssueAPI ####################"""
    def test101(self):
        o = openapi.IssueAPI(issname)
        self.set_object(o)
        o.set_sellcallprc02('4%')

        api = openapi.TrAPI('계좌평가잔고내역요청')
        self.set_object(api)
        api.req()
    """대량생성테스트"""
    def test102(self):
        m = datamodels.TRModel('전일대비등락률상위요청')
        data = m.load({'dt':finder.lastdt(m)}, sort=[('등락률',-1)], limit=10)
        names = [d['종목명'] for d in data]
        print([len(names), names])

        self.trapi = openapi.TrAPI('계좌평가잔고내역요청')
        self.trapi.req()

        self.it = iter(names)
        @pyqtSlot()
        def __run__():
            try: name = next(self.it)
            except Exception as e: self.stop_timer('타이머')
            else:
                o = openapi.IssueAPI(name)
                self.set_object(o)

        self.start_timer('타이머', __run__, 1)

    def test103(self):
        o = datamodels.TRList().select('주식일봉차트조회요청')
        tpls = [('종목코드',isscode), ('기준일자','20230127'), ('수정주가구분','1')]
        for id, val in tpls: openapi.SetInputValue(id, val)
        openapi.CommRqData(isscode, o.trcode, 0, o.screen_no)
    def test104(self):
        o = openapi.TrAPI('당일거래량상위요청')
        inputs = o.get()
        KiwoomAPI.SetTrReg(inputs, o.trname, o.trcode, 0, o.screen_no)
        for i in range(10):
            KiwoomAPI.SetTrReg(inputs, o.trname, o.trcode, 2, o.screen_no)
    def test105(self):
        o = openapi.TrAPI('시가대비등락률요청', maxLoop=1, 정렬구분='4')
        self.set_object(o)
        o.req()
    def test106(self):
        o = openapi.TrAPI('예상체결등락률상위요청', maxLoop=1)
        self.set_object(o)
        o.req()

    """#################### TrAPI ####################"""
    """extParam:0"""
    def test201(self):
        # o = openapi.TrAPI('주식기본정보요청')
        # self.set_object(o)
        # o.req()

        def __view__(): print(pd.DataFrame(o.cumData))
        o = openapi.TrAPI('계좌평가잔고내역요청', maxLoop=None, timeout=10)
        self.set_object(o)
        o.finished.connect(__view__)
        o.req()

    """extParam:1"""
    def test202(self):
        # o = openapi.TrAPI('체결정보요청', 종목코드=isscode)
        # self.set_object(o)
        # o.req()
        # sleep(1)
        # o = openapi.TrAPI('주식분봉차트조회요청', 종목코드=isscode)
        # self.set_object(o)
        # o.req()
        # sleep(1)
        o = openapi.TrAPI('일별주가요청',종목코드=isscode)
        self.set_object(o)
        o.req()
    def test203(self):
        o = openapi.TrAPI('테마그룹별요청', 종목코드='', 검색구분='2')
        o.req()
    def test204(self):
        # P10101 -> 30
        # P10102 -> 30
        # '' -> 50
        o = openapi.TrAPI('투자자별일별매매종목요청', 시장구분='102')
        o.req()
        self.set_object(o)
    def test205(self):
        trname = '투자자별일별매매종목요청'
        o = openapi.TrAPI(trname)
        o.req()
        self.set_object(o)

        o = openapi.TrAPI(trname, 시장구분='001')
        o.req()
        self.set_object(o)

        o = openapi.TrAPI(trname, 시장구분='101')
        o.req()
        self.set_object(o)
    def test206(self):
        # trname = '프로그램순매수상위50요청'
        trname = '종목별프로그램매매현황요청'
        """
        위의 두TR은 3가지케이스 모두 동일 데이타수신
        """
        o = openapi.TrAPI(trname, 시장구분='')
        o.req()
        self.set_object(o)
        sleep(2)
        o = openapi.TrAPI(trname, 시장구분='P00101')
        o.req()
        self.set_object(o)
        sleep(2)
        o = openapi.TrAPI(trname, 시장구분='P00102')
        o.req()
        self.set_object(o)
    def test207(self):
        trname = '프로그램매매추이차트요청'

        # 입력값 에러케이스
        # o = openapi.TrAPI(trname, 종목코드='')
        # o.req()
        # self.set_object(o)
        # sleep(2)

        # 둘다 같은 데이타 케이스
        o = openapi.TrAPI(trname, 종목코드='P10101')
        o.req()
        self.set_object(o)
        sleep(2)
        o = openapi.TrAPI(trname, 종목코드='P10102')
        o.req()
        self.set_object(o)
    def test208(self):
        """
        투자자별일별매매종목요청, 투자자별일별매매종목요청 --> 3가지케이스 모두 동일 데이타수신
        호가잔량상위요청 --> 'P00102'일 경우 다른 데이타수신
        """
        # trname = '투자자별일별매매종목요청'
        # trname = '호가잔량급증요청'
        trname = '호가잔량상위요청'
        o = openapi.TrAPI(trname, 시장구분='')
        o.req()
        self.set_object(o)
        sleep(2)
        o = openapi.TrAPI(trname, 시장구분='P00101')
        o.req()
        self.set_object(o)
        sleep(2)
        o = openapi.TrAPI(trname, 시장구분='P00102')
        o.req()
        self.set_object(o)
    def test209(self):

        o = openapi.TrAPI('가격급등락요청')
        o.req()
        self.set_object(o)

    """#################### OrderAPI ####################"""
    """신규매수::성공"""
    def test301(self):
        o = openapi.OrderAPI(issname,'신규매수','지정가',23900,1, timeout=2)
        self.set_object(o)

        @ctracer
        @pyqtSlot()
        def __completed__(): o.info()
        @ctracer
        @pyqtSlot(str)
        def __terminated__(org_key): print({'객체ID':org_key})

        def __order__(): o.order()
        o.completed.connect(__completed__)
        o.terminated.connect(__terminated__)
        self.timer = QTimer()
        self.timer.timeout.connect(__order__)
        self.timer.start(1000*10)
    """신규매수::실패"""
    def test302(self):
        o = openapi.OrderAPI(issname,'신규매수','지정가',23000,1, timeout=2)
        self.set_object(o)

        @ctracer
        @pyqtSlot(str)
        def __terminated__(org_key): print({'객체ID':org_key})
        @ctracer
        @pyqtSlot()
        def __cancelled(): o.info()
        def __order__(): o.order()

        o.cancelled.connect(__cancelled)
        o.terminated.connect(__terminated__)
        self.timer = QTimer()
        self.timer.timeout.connect(__order__)
        self.timer.start(1000*10)
    """신규매도::성공"""
    def test303(self):
        o = openapi.OrderAPI(issname,'신규매도','지정가',23000,1, timeout=10)
        self.set_object(o)

        @ctracer
        @pyqtSlot()
        def __completed__(): o.info()
        @ctracer
        @pyqtSlot(str)
        def __terminated__(org_key): print({'객체ID':org_key})

        def __order__(): o.order()
        o.completed.connect(__completed__)
        o.terminated.connect(__terminated__)
        self.timer = QTimer()
        self.timer.timeout.connect(__order__)
        self.timer.start(1000*2)
    """신규매도::실패"""
    def test304(self):
        o = openapi.OrderAPI(issname,'신규매도','지정가',24000,1, timeout=2)
        self.set_object(o)

        @ctracer
        @pyqtSlot()
        def __cancelled__(): o.info()
        @ctracer
        @pyqtSlot(str)
        def __terminated__(org_key): print({'객체ID':org_key})
        def __order__(): o.order()

        o.cancelled.connect(__cancelled__)
        o.terminated.connect(__terminated__)
        self.timer = QTimer()
        self.timer.timeout.connect(__order__)
        self.timer.start(1000*10)
    """신규매수::오류"""
    def test305(self):
        o = openapi.OrderAPI(issname,'신규매수','지정가',23000,1, timeout=10)
        self.set_object(o)

        @ctracer
        @pyqtSlot()
        def __errored__(): o.info()
        @ctracer
        @pyqtSlot(str)
        def __terminated__(org_key): print({'객체ID':org_key})

        o.errored.connect(__errored__)
        o.terminated.connect(__terminated__)
        # 가격오류
        o.prc = 0
        o.order()

    """#################### MyFunctionalAPIs ####################"""
    def test401(self):
        v = openapi.getIssueInfo('121850')
        pp.pprint(v)
        if not isinstance(v, dict): raise

        v = openapi.isMoiServer()
        print(['isMoiServer', v, type(v)])
        if not isinstance(v, bool): raise

        v = openapi.get_cash()
        print(['get_cash', v, type(v)])
        if not isinstance(v, int): raise

    """#################### BackendServer ####################"""
    def test501(self): self.run_worker(openapi.BackendServer)
    def test502(self): self.run_worker(openapi.RawDataServer)



KiwoomAPI.CommConnect()


MainTester = kiwoomapi_openapi()
MainTester.run()


sys.exit(app.exec())
