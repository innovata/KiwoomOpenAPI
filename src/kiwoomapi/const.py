# -*- coding: utf-8 -*-
"""
# 평가금액 = 현재가 X 수량
# 매입금액 = 매입가 X 수량
# 매수수수료 = 매입금액 X 수수료(모의투자 0.0035. 실거래 0.00015)
# 매도수수료 = 평가금액 X 수수료(모의투자 0.0035. 실거래 0.00015)
# 수수료합 = 매수수수료(원단위절사) + 매도수수료(원단위절사)

# 당사 수수료 징수는 종목별 매수/매도를 기준으로 하며, 동일종목의 분할매매시는 매수별, 매도별 체결합계금액을 기준으로 산정합니다.
# 매매수수료는 10원 미만 절사이며, (ex. 3,000원 X 50주 = 150,000원 체결 시, 온라인 매체 매매수수료는 150,000원 X 0.015% = 22.5원 -> 20원 부과)
# 세금은 원 미만 절사 입니다. (ex. 2,050원 X 50주 = 102,500원 체결 시, 거래세는 102,500원 X 0.23%(코스닥) = 235.75원 -> 235원 부과)
"""


"""거래세"""
Tax = '0.20%'

"""수수료"""
Commission = '0.015%'

"""거래세+매수/도수수료"""
Cost = '0.23%'

"""키움서버 점검시간"""
# 월~토: 05:05~05:10
# 일요일: 04:00~04:30




