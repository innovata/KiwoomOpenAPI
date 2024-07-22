# -*- coding: utf-8 -*-
# GitHub-Web 에 있는 데이터를 다운로드해서 메모리-데이터베이스 화 한다.

import os 
import csv 


import requests


from kiwoomapi_v3.meta import parser 




print('os.getcwd():', os.getcwd())
print('__file__:', __file__)


# 데이터구조 : (MetaName, ModelName, DownloadURL)
META_LIST = [
    ('OpenAPI-오류코드', 'ErrorCode', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/Docs/OpenAPI-%EC%98%A4%EB%A5%98%EC%BD%94%EB%93%9C.md",),
    ('RTList', 'RTList', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/data/RTList.txt"),
    ('TRList', 'TRList', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/data/TRList.txt"),
    ('HogaGubun', 'HogaGubun', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/data/HogaGubun.txt"),
    ('MarketGubun', 'MarketGubun', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/data/MarketGubun.txt"),
    ('MarketOptGubun', 'MarketOptGubun', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/data/MarketOptGubun.txt"),
    ('OrderType', 'OrderType', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/data/OrderType.txt"),
    ('ChejanFID', 'ChejanFID', "https://raw.githubusercontent.com/innovata/KiwoomOpenAPI/main/data/ChejanFID.txt"),
]


DOWNLOAD_URLS = {meta_name:url for meta_name, model_name, url in META_LIST}

MODEL_NAMES = {meta_name:model_name for meta_name, model_name, url in META_LIST}





def initialize():
    # 메타데이터 MDB 가 준비되어 있는지 체크
    print("Checking...")
    if False:
        print("메타데이터 MDB 준비완료.")
    else:
        print("Initializing...")

        # 메타데이터 리스트

        # 리스트를 반복하며 하나씩 작업
        for meta_name, model_name, url in META_LIST:
            build_mdb(meta_name)    

        print("Initialized 완료.")


def build_mdb(meta_name):
    # 메타데이터 마다 다운로드해서 TXT파일로 저장
    download_meta(meta_name)
    # 메타데이터 마다 다운로드해서 CSV파일로 저장
    convert_to_mdb(meta_name)
    print(f"{meta_name} mdb 구성완료.")


def MDB_DIR():
    _dir = os.path.dirname(__file__)
    _dir = os.path.join(_dir, 'mdb')
    try:
        os.makedirs(_dir)
    except OSError as e:
        pass 

    return _dir 


def download_meta(meta_name):
    file = f"{meta_name}.txt"
    filepath = os.path.join(MDB_DIR(), file)
    url = DOWNLOAD_URLS[meta_name]
    download_file(url, filepath)
    return filepath 


def download_file(url, local_filename):
    # Send a GET request to the URL
    with requests.get(url, stream=True) as response:
        response.raise_for_status()  # Check for HTTP request errors
        # Open a local file with write-binary mode
        with open(local_filename, 'wb') as file:
            # Write the content of the response in chunks
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    print(f"File downloaded: {local_filename}")


def convert_to_mdb(meta_name):
    # TXT 파일 읽기
    txtfile = os.path.join(MDB_DIR(), f"{meta_name}.txt")
    with open(txtfile, mode='r', encoding='utf-8') as f:
        text = f.read()
        f.close()
        
    # 파싱
    model_name = MODEL_NAMES[meta_name]
    p = parser.get_parser(model_name)
    if p is None:
        print(f"ERROR | {meta_name} 해당 파서가 존재하지 않는다.")
        data = []
    else:
        data = p.parse(text)
    
        # MDB에 저장
        model_name = MODEL_NAMES[meta_name]
        csvfile = os.path.join(MDB_DIR(), f"{model_name}.csv")
        with open(csvfile, mode='w', newline='', encoding='utf-8') as f:
            fieldnames = list(data[0])
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for d in data:
                writer.writerow(d)

        # TXT 파일 삭제
        try:
            os.remove(txtfile)
        except OSError as e:
            pass 

    return 


