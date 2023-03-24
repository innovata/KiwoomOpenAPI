# -*- coding: utf-8 -*-
from datetime import datetime
from time import sleep
import re
from copy import copy, deepcopy
import math

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
import pandas as pd

from ipylib.idebug import *
from ipylib.iparser import *

import trddt


from kwdataengineer import datamodels


from kiwoomtrader32.pyqtclass import *
from kiwoomtrader32.api.openapi import OpenAPI
from kiwoomtrader32.api import openapi



############################################################
"""데이타수신테스트"""
############################################################
class RealDataTester(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): self.finished.emit()
    @ctracer
    def State(self, *args): pass
    @ctracer
    def run(self):
        OpenAPI.OnReceiveRealData.connect(self.recv)
        self.RealType = '주식체결'
        self.fids = datamodels.RTList().distinct('fids', {'realtype':self.RealType})
    @ctracer
    @pyqtSlot(str, str, str)
    def recv(self, Code, RealType, RealData):
        if RealType == self.RealType:
            for fid in self.fids:
                v = openapi.GetCommRealData(Code, int(fid))
                if isinstance(v, str):
                    if len(v.strip()) == 0: logger.error([self, Code, RealType, fid, v])
                    else: pass
                else: raise
        else: pass


class TrDataTester(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): self.finished.emit()
    @ctracer
    def State(self, *args): pass
    @ctracer
    def run(self):
        OpenAPI.OnReceiveTrData.connect(self.recv)
        self.items = datamodels.TRList().distinct('outputs', {'trname':'주식호가요청'})
    @ctracer
    @pyqtSlot(str, str, str, str, str, int, str, str, str)
    def recv(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        n = openapi.GetRepeatCnt(TrCode, RQName)
        self.State('GetRepeatCnt', n, type(n))
        for i in range(n, n+1, 1):
            for item in self.items:
                v = openapi.GetCommData(TrCode, RQName, i, item)
                if isinstance(v, str):
                    if len(v.strip()) == 0: logger.error([self, TrCode, i, item, v])
                    else: pass
                else: raise


class ChejanDataTester(QBaseObject):

    @ctracer
    def __init__(self): super().__init__()
    @ctracer
    def finish(self, *args): self.finished.emit()
    @ctracer
    def State(self, *args): pass
    @ctracer
    def run(self):
        OpenAPI.OnReceiveChejanData.connect(self.recv)
    @ctracer
    @pyqtSlot(str, int, str)
    def recv(self, Gubun, ItemCnt, FIdList):
        fids = FIdList.split(';')
        fids = [fid.strip() for fid in fids]
        for fid in fids:
            v = openapi.GetChejanData(int(fid))
            print(fid, v, type(v), len(v))
            if isinstance(v, str):
                if len(v.strip()) == 0: logger.error([self, fid, v])
                else: pass
            else: raise
