# -*- coding: utf-8 -*-
# User가 직접 셋업하지 않고도 OpenAPI를 사용할 수 있도록
# 최상위 패키지 레벨에서 자동으로 메타데이터를 셋업해줘야한다.


from PyQt5.QtCore import QObject


from kiwoomapi_v3 import meta, api
from kiwoomapi_v3.api import OpenAPI, dynamicCall 
# meta.initialize() 











class KiwoomAPI(QObject):

    def __init__(self):
        super().__init__()

        OpenAPI.OnEventConnection.connect(self.OnEventConnection)

    def CommConnect(self):
        dynamicCall('CommConnect()')

    def OnEventConnection(self, err_code):
        pass 

    def GetLoginInfo(self, s): return dynamicCall('GetLoginInfo(QString)', s)

    def GetConnectState(self): return dynamicCall('GetConnectState()')