### ============================================================
### 개발 가이드 :: 조회와 실시간데이터처리
### ============================================================


[GetCommData() 함수]

GetCommData(
BSTR strTrCode,   // TR 이름
BSTR strRecordName,   // 레코드이름
long nIndex,      // nIndex번째
BSTR strItemName) // TR에서 얻어오려는 출력항목이름

OnReceiveTRData()이벤트가 발생될때 수신한 데이터를 얻어오는 함수입니다.
이 함수는 OnReceiveTRData()이벤트가 발생될때 그 안에서 사용해야 합니다.

------------------------------------------------------------------------------------------------------------------------------------

예)
[OPT10081 : 주식일봉차트조회요청예시]

OnReceiveTrData(...)
{
  if(strRQName == _T("주식일봉차트"))
  {
    int nCnt = OpenAPI.GetRepeatCnt(sTrcode, strRQName);
    for (int nIdx = 0; nIdx < nCnt; nIdx++)
    {
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("거래량"));   strData.Trim();	// nIdx번째의 거래량 데이터 구함
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("시가"));   strData.Trim();
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("고가"));   strData.Trim();
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("저가"));   strData.Trim();
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("현재가"));   strData.Trim();
    }
  }
}

------------------------------------------------------------------------------------------------------------------------------------
