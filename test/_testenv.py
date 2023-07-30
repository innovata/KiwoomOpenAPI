# -*- coding: utf-8 -*-
"""파이썬 모듈 로딩"""
import os
import sys
import unittest
from time import sleep
import re
from datetime import datetime, timedelta
from importlib import reload

print({'__file__':os.path.realpath(__file__)})
print({'sys.executable':sys.executable})


"""프로젝트 패키지 경로 셋업"""
sys.path.append(os.path.join('C:\pypjts', 'KiwoomOpenAPI', 'src'))


"""My 3rd 패키지 경로 셋업"""
# sys.path.append(os.path.join('C:\pypjts', 'iPyLibrary', 'src'))
# sys.path.append(os.path.join('C:\pypjts', 'TradeDatetime', 'src'))
# sys.path.append(os.path.join('C:\pypjts', 'PyQtClasses', 'src'))
# sys.path.append(os.path.join('C:\pypjts', 'KiwoomDataEngineer', 'src'))
for s in sorted(sys.path): print(s)


"""써드파티 패키지 로딩"""
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication
from ipylib.idebug import *


"""디버거 환경설정"""
os.environ['LOG_LEVEL'] = '20'
dbg.set_viewEnvType('jupyter')
dbg.report()


"""QApplication 실행"""
app = QApplication(sys.argv)
print(app)
