# -*- coding: utf-8 -*-
def part_gubun(s):
    print()
    print('#'*100)
    print(s)


part_gubun("""파이썬 모듈 로딩""")
import os
import sys
import unittest
from time import sleep
import re
from datetime import datetime, timedelta
from importlib import reload

print({'__file__':os.path.realpath(__file__)})
print({'sys.executable':sys.executable})


part_gubun("""iDevEnv 셋업""")
sys.path.append(os.path.join('C:\pypjts', 'KiwoomOpenAPI', 'src'))
import devpkgpath


part_gubun("""써드파티 패키지 로딩""")
import pandas as pd
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication
from ipylib.idebug import *
import trddt


part_gubun("""디버거 환경설정""")
os.environ['LOG_LEVEL'] = '20'
dbg.set_viewEnvType('jupyter')
dbg.report()
pp.pprint(sorted(sys.path))


part_gubun("""QApplication 실행""")
app = QApplication(sys.argv)
print(app)
