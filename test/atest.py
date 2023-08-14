# -*- coding: utf-8 -*-
from test._testenv import *
from ipylib.datacls import BaseDataClass


from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QEventLoop


from kiwoomapi import *


issname, isscode = '삼성전자', '005930'




class MainTester(QObject):

    def __init__(self):  
        super().__init__()
        OpenAPI.OnEventConnect.connect(self.__recv_login__)
        OpenAPI.OnReceiveMsg.connect(self.__recv_msg__)
        OpenAPI.OnReceiveTrData.connect(self.__recv_trdata__)
        OpenAPI.OnReceiveRealData.connect(self.__recv_realdata__)
        OpenAPI.OnReceiveConditionVer.connect(self.__recv_condver__)
        OpenAPI.OnReceiveTrCondition.connect(self.__recv_trcond__)
        OpenAPI.OnReceiveRealCondition.connect(self.__recv_realcond__)
        OpenAPI.OnReceiveChejanData.connect(self.__recv_chejan__)
   
    def run(self):
        self.login()
   
    @ctracer
    @pyqtSlot(str, str, str, str)
    def __recv_msg__(self, ScrNo, RQName, TrCode, Msg):
        pass 
   
    @ctracer
    def login(self):
        v = CommConnect()
        print(['CommConnect-->', v, type(v)])
        self._event_loop = QEventLoop()
        self._event_loop.exec()
   
    @ctracer
    @pyqtSlot(int)
    def __recv_login__(self, ErrCode): 
        print({'ErrCode':ErrCode})
        self._event_loop.exit()
        
        self.test41()
        # self.__run_many__()

    def __run_many__(self):
        for i in range(1, 40):
            func = f'test{str(i).zfill(2)}'
            try:
                testFunc = getattr(self, func)
            except Exception as e:
                logger.debug(e)
            else:
                testFunc()
                sleep(2)

    """로그인-버전처리"""
    def test01(self):
        pretty_title("""로그인-버전처리""")

        v = GetConnectState()
        print(['GetConnectState-->', v, type(v)])

        items = ['GetServerGubun','ACCLIST','ACCOUNT_CNT','USER_ID','USER_NAME','KEY_BSECGB','FIREW_SECGB']
        for item in items:
            v = GetLoginInfo(item)
            print(['GetLoginInfo-->', v, type(v)])


    ############################################################
    """FunctionalAPIs::기타함수"""
    ############################################################

    """기타함수::dynamicCall"""
    def test02(self):
        pretty_title("""기타함수::dynamicCall""")

        v = GetBranchCodeName()
        print(['GetBranchCodeName', v, type(v)])
        if not isinstance(v, list): raise

        v = GetCodeListByMarket('0')
        print(['GetCodeListByMarket', v, type(v)])
        if not isinstance(v, list): raise

        v = GetMasterCodeName(isscode)
        print(['GetMasterCodeName', v, type(v)])
        if not isinstance(v, str): raise

        v = GetMasterConstruction(isscode)
        print(['GetMasterConstruction', v, type(v)])
        if not isinstance(v, str): raise

        v = GetMasterLastPrice(isscode)
        print(['GetMasterLastPrice', v, type(v)])
        if not isinstance(v, int): raise

        v = GetMasterListedStockDate(isscode)
        print(['GetMasterListedStockDate', v, type(v)])
        if not isinstance(v, datetime): raise

        v = GetMasterListedStockCnt(isscode)
        print(['GetMasterListedStockCnt', v, type(v)])
        if not isinstance(v, int): raise

        v = GetMasterStockState(isscode)
        print(['GetMasterStockState', v, type(v)])
        if not isinstance(v, dict): raise

        # mktcds = db.UpjongMarketCode.distinct('code')
        # for ujcd in mktcds:
        #     v = kiwoomapi.GetUpjongCode(ujcd)
        #     print(['GetUpjongCode', ujcd, v, type(v)])
        #     if not isinstance(v, list): raise

    """기타함수::KOA_Functions"""
    def test03(self):
        pretty_title("""기타함수::KOA_Functions""")

        v = GetServerGubun()
        print(['GetServerGubun',v, type(v)])
        if not isinstance(v, str): raise

        v = GetUpjongNameByCode('002')
        print(['GetUpjongNameByCode',v, type(v)])
        if not isinstance(v, str): raise

        v = IsOrderWarningETF(isscode)
        print(['IsOrderWarningETF',v, type(v)])
        if not isinstance(v, bool): raise

        v = IsOrderWarningStock(isscode)
        print(['IsOrderWarningStock',v, type(v)])
        if not isinstance(v, bool): raise

        v = GetMasterStockInfo(isscode)
        print(['GetMasterStockInfo',v, type(v)])
        if not isinstance(v, dict): raise

        # ShowAccountWindow()
   
    ############################################################
    """FunctionalAPIs::조회와-실시간데이터처리"""
    ############################################################
    
    """TR조회"""
    @ctracer
    def __recv_trdata__(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        if hasattr(self, '_trcode') and TrCode == self._trcode:
            v = GetRepeatCnt(self._trcode, '요청명')
            print(['GetRepeatCnt', v, type(v)])
            if not isinstance(v, int): raise
            index = v

            v = GetCommData(self._trcode, '요청명', index, '종목명')
            print(['GetCommData', v, type(v)])
    
    """TR조회::정상케이스"""
    def test10(self):
        pretty_title("""TR조회::정상케이스""")
        v = SetInputValue('종목코드', isscode)
        print(['SetInputValue', v, type(v)])

        self._trcode = 'opt10001'
        v = CommRqData('요청명', self._trcode, 0, '8000')
        print(['CommRqData', v, type(v)])
        if not isinstance(v, int): raise
        if v != 0: raise

    """TR조회::2개 이상의 데이타"""
    def test11(self):
        pretty_title("""TR조회::2개 이상의 데이타""")
        SetInputValue('종목코드', isscode)
        SetInputValue('기준일자', '20230210')
        SetInputValue('수정주가구분', '1')
        
        self._trcode = 'opt10081'
        v = CommRqData(isscode, self._trcode, 0, '8001')
        print(['CommRqData', v, type(v)])

    """TR조회::에러::인풋없이 요청만 하면 에러"""
    def test12(self):
        pretty_title("""TR조회::에러::인풋없이 요청만 하면 에러""")
        v = CommRqData('요청명','opt10001',0,'8000')
        print(['CommRqData', v, type(v)])
        if not isinstance(v, int): raise
        if v != -300: raise 
   

    @ctracer
    @pyqtSlot(str, str, str)
    def __recv_realdata__(self, Code, RealType, RealData):

        def __action__(code, fid):
            for i in range(10):
                v = GetCommRealData(code, fid)
                print(i, ['GetCommRealData->', v, type(v)])
                sleep(1)
            
            # 테스트가 끝나면 연결을 해제해야 다른 테스트 결과를 보기 편하다
            OpenAPI.OnReceiveRealData.disconnect(self.__recv_realdata__)

        if Code == '09': __action__('09', '20')
        elif Code == isscode: __action__(isscode, '10')

    """실시간데이터처리"""
    def test20(self):
        pretty_title("""실시간데이터처리""")

        v = SetRealReg('5000', '09', '20;214;215', '1')
        print(['SetRealReg->', v, type(v)])
        if not isinstance(v, int): raise
        if v != 0: raise

        v = SetRealRemove('ALL', 'ALL')
        print(['SetRealRemove->', v, type(v)])

    """실시간데이터처리::종목실시간데이타 가져오기"""
    def test21(self):
        pretty_title("""실시간데이터처리::종목실시간데이타 가져오기""")

        SetRealReg('5000', isscode, '10;20', '1')

    ############################################################
    """FunctionalAPIs::조건검색"""
    ############################################################

    @ctracer
    @pyqtSlot(int, str)
    def __recv_condver__(self, Ret, Msg):
        v = GetConditionNameList()
        print(['GetConditionNameList->', v, type(v)])
        if not isinstance(v, list): raise
        if len(v) == 0: raise 

        # 최대허용개수 10개
        conds = v[:10]
        for i, (Index, ConditionName) in enumerate(conds):
            v = SendCondition('9000', ConditionName, Index, 1)
            print(i, ['SendCondition->', v, type(v)])
            sleep(0.2)
            # break

    @ctracer 
    @pyqtSlot(str, str, str, int, int)
    def __recv_trcond__(self, ScrNo, CodeList, ConditionName, Index, Next):
        pass

    @ctracer 
    @pyqtSlot(str, str, str, str)
    def __recv_realcond__(self, Code, Type, ConditionName, ConditionIndex):
        pass 
        
    """조건검색"""
    def test30(self):
        pretty_title("""조건검색""")

        v = GetConditionLoad()
        print(['GetConditionLoad->', v, type(v)])
        if not isinstance(v, int): raise
        if v != 1: raise

    """조건검색::정지"""
    def test31(self):
        pretty_title("""조건검색::정지""")

        v = SendConditionStop('9000', '0000', '005')
        print(['SendConditionStop->', v, type(v)])
   

   ############################################################
    """주문과-잔고처리 -----> 모의투자 환경에서만 테스트해라!!!"""
    ############################################################
    
    @ctracer
    @pyqtSlot(str, int, str)
    def __recv_chejan__(self, Gubun, ItemCnt, FIdList):
        pass 

    """주문과-잔고처리::모의투자 환경"""
    def test40(self):
        pretty_title("""주문과-잔고처리::모의투자 환경""")

        if GetServerGubun() == '모의':
            v = SendOrder('rqname','9000','8041895711',1,isscode,1,2000,'00','')
            print(['SendOrder', v, type(v)])

            v = GetChejanData(910)
            print(['GetChejanData', v, type(v)])
        else:
            print("주문과-잔고처리 -----> 모의투자 환경에서만 테스트해라!!!")

    """주문과-잔고처리::실전투자 환경"""
    def test41(self):
        pretty_title("""주문과-잔고처리::실전투자 환경""")

        self._trcode = 'KOA_NORMAL_BUY_KP_ORD'
        v = SendOrder('테스트_0개_주문','9000','5063318011',1,isscode,0,70000,'00','')
        print(['SendOrder', v, type(v)])
        if not isinstance(v, int): raise 
        if v != 0: raise 




MainTester = MainTester()
MainTester.run()


sys.exit(app.exec())
