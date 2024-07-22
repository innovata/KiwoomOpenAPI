# -*- coding: utf-8 -*-
# 키움증권 KOA StudioSA 개발가이드 텍스트 문서 파싱



import os
import re

# from ipylib.idebug import *






class ParserTypeA:

    @classmethod
    def parse(self, text):
        pattern='(\d+|[A-Za-z]+)\s*:\s*([가-힣A-Za-z]+)'
        pairs = re.findall(pattern, string=text)
        
        data = []
        for p in pairs:
            data.append({'code':p[0].strip(), 'name':p[1].strip()})
        return data 


class ParserTypeB:

    @classmethod
    def parse(self, text):
        pattern='([\+-]*\d+)\s*//\s*(.+)'
        pairs = re.findall(pattern, string=text)
        
        data = []
        for p in pairs:
            data.append({'code':int(p[0].strip()), 'msg':p[1].strip()})
        return data


"""KOA StudioSA / TR목록"""
class TRList:
    
    def parse(self, text):
        txt_list = self._split_by_TR(text)
        data = []
        for txt in txt_list:
            # 파싱
            trcode, trname = self._get_trcodename(txt)
            outputs = self._get_outputs(txt)
            inputs = self._get_inputs(txt)
            caution = self._get_caution(txt)
            realActive, testActive = self._get_active(caution)
            data.append({
                'trcode':trcode, 'trname':trname,
                'inputs':inputs, 'outputs':outputs,
                'caution':caution, 'realActive':realActive, 'testActive':testActive
            })
        return data
    
    """TR별로 텍스트 나누기"""
    def _split_by_TR(self, text):
        # Split Whole-Text into Each TR-based Text
        p = re.compile('(/[\*]+/)')
        li = p.split(text)
        li = [e.strip() for e in li if len(e.strip()) > 0]
        # 분할패턴도 결과에 포함되어 리턴되므로 삭제해야 한다 --> 쥰내 이해가 안됨
        return [e for e in li if p.search(e) is None]
    
    def _get_trcodename(self, text):
        m = re.search("\[\s*([a-zA-Z0-9]+)\s*:\s*([가-힝A-Z\s0-9\(\)]+)\s*\]", text)
        return m.group(1).strip(), m.group(2).strip()
    
    def _get_outputs(self, text):
        m = re.search('OUTPUT=(.+)', text)
        return None if m is None else m.group(1).strip().split(',')
    
    def _get_inputs(self, text):
        inputs = re.findall('SetInputValue\("(.+)"\s*,', text)
        # print(inputs)
        data = []
        for input in inputs:
            d = {'id':input}
            m = re.search(f'{input}\s*=\s*(.+)\n', text)
            value = None if m is None else m.group(1).strip()
            # print(value)
            d.update({'value':value})
            data.append(d)
        return data
    
    def _get_caution(self, text):
        p = re.compile('\[\s*주의\s*\]')
        m = p.search(text)
        if m is None:
            return None
        else:
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if p.search(line) is not None:
                    break
            return lines[i+1]
    
    def _get_active(self, caution):
        if caution is None:
            real, test = True, True
        else:
            m = re.search('(이 TR은)[.\s]+(모의투자)*', caution)
            if m is None:
                real, test = True, True
            else:
                real, test = (False, False) if m.group(2) is None else (True, False)
        return real, test


"""KOA StudioSA / RT목록"""
class RTList:
    
    def parse(self, text):
        txt_list = self._split_by_realtype(text)
        data = []
        for txt in txt_list:
            realtype = self._get_realtype(txt)
            fid_data = self._get_fid_data(txt)
            data.append({'realtype':realtype, 'fid_data':fid_data})

        return data
    
    def _split_by_realtype(self, text):
        # 전체 텍스트를 26개의 Realtype별로 나눈다
        li = re.split('[\*]+', text)
        return [e.strip() for e in li if len(e.strip()) > 0]
    
    def _get_realtype(self, text):
        m = re.search("Real Type\s*:\s*([가-힝A-Z\s0-9\(\)/]+)", text)
        return m.group(1).strip()
    
    def _get_fid_data(self, text):
        li = re.findall('\[(\d+)\]\s*=\s*(.+)', text)
        data = []
        for t in li:
            data.append({'fid':t[0], 'name':t[1].strip()})
        return data


"""KOA StudioSA / 개발가이드 / 주문과 잔고처리 / 기본설명"""
class ChejanFID:
    # TypeA 인거 같은데?
    def parse(self, text):
        data = []
        pairs = re.findall(pattern='"(\d+)"\s*:\s*"(.+)"', string=text)
        for p in pairs:
            data.append({'fid':p[0].strip(), 'name':p[1].strip()})
        return data


class MarketTime:

    def parse(self, text):
        return text 


"""개별 파서 보유"""
class ParserTypeC:
    TRList = TRList
    RTList = RTList
    ChejanFID = ChejanFID
    MarketTime = MarketTime

    @classmethod
    def get(self, modelName): return getattr(self, modelName)()



MODEL_PARSERS = {
    'ChejanFID': ParserTypeC,
    'ErrorCode': ParserTypeB,
    'HogaGubun': ParserTypeA,
    'MarketGubun': ParserTypeA,
    'MarketOptGubun': ParserTypeA,
    'OrderType': ParserTypeA,
    'RTList': ParserTypeC,
    'TRList': ParserTypeC,
    'MarketTime': ParserTypeC,
}



def get_parser(modelName):
    if modelName in MODEL_PARSERS:
        parser = MODEL_PARSERS[modelName]()
        if isinstance(parser, ParserTypeC):
            parser = parser.get(modelName)
        return parser 
    else:
        # logger.error(['해당모델의 파서는 없다. modelName:', modelName])
        print(['해당모델의 파서는 없다. modelName:', modelName])


# def get_parsed_data(modelName):
#     parser = get_parser(modelName)
#     if parser is None:
#         return None 
#     else:
#         text = read_docs_file(modelName)
#         return parser.parse(text)



# def read_docs_file(modelName):
#     filepath = os.path.join(str(WindowsPath(DatasetPath.DOCS_PATH)), f'{modelName}.txt')
#     with open(filepath, mode='r', encoding='utf-8') as f:
#         text = f.read()
#         f.close()
#     return text.strip()













