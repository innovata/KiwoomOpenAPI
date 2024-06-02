# KiwoomOpenAPI

Windows COM 기반으로 파이썬 32비트로만 동작하는 키움증권 오픈API 패키지.

KiwoomTraderV2 프로젝트 패키지의 내부 모듈을 독립적인 패키지로 분리하는 작업 완료.




## 사용법

데이터 요청할 때는 패키지의 함수들을 사용해야 한다.

    import kiwoomapi as api
    api.CommConnect()

데이터 수신할 때는 PyQt-QAxWidget 객체인 'OpenAPI'의 pyqtSinal 을 사용해야 한다.

키움증권으로부터 메시지를 수신하기 위해서는 아래와 같이 코드를 작성해야 한다. 

    from kiwoomapi import OpenAPI
    OpenAPI.OnReceiveMessage.connect(YOUR_METHOD) 


로그인 객체 구현 예시:

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QEventLoop
    import kiwoomapi as api
    from kiwoomapi import OpenAPI
    
    class LoginAPI(QObject):

        LoginSucceeded = pyqtSignal()

        def __init__(self):
            super().__init__()
            OpenAPI.OnReceiveMessage.connect(self.__recv_msg__)
            OpenAPI.OnEventConnect.connect(self.__recv_login__)

        @pyqtSlot(str, str, str, str)
        def __recv_msg__(self, ScrNo, RQName, TrCode, Msg):
            print([ScrNo, RQName, TrCode, Msg])
        
        @pyqtSlot(int)
        def __recv_login__(self, ErrCode):
            print(ErrCode)
            if ErrCode == 0:
                self.LoginSucceeded.emit()
            else:
                print('로그인 실패)
            self._event_loop.exit()

        def login(self):
            api.CommConnect()
            self._event_loop = QEventLoop()
            self._event_loop.exec()


    app = QApplication(sys.argv)
    
    LoginAPI = LoginAPI()
    LoginAPI.login()

    sys.exit(app.exec())





## 개발 가이드 문서

[로그인-버전처리\기본설명](/Docs/로그인-버전처리/기본설명.md)

[모의투자](Docs\모의투자.md)

[로그인-버전처리](Docs\로그인-버전처리\기본설명.md)

[조건검색](Docs\조건검색\기본설명.md)

[조회와-실시간데이터처리](Docs\조회와-실시간데이터처리\기본설명.md)

[주문과-잔고처리](Docs\주문과-잔고처리\기본설명.md)

[OpenAPI-오류코드](Docs\OpenAPI-오류코드.md)

[OpenAPI-사용제한](Docs\OpenAPI-사용제한.md)



