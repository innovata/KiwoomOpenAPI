# -*- coding: utf-8 -*-
import re


from PyQt5.QAxContainer import QAxWidget
import pandas as pd


from ipylib.idebug import *
from ipylib import idatetime




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
