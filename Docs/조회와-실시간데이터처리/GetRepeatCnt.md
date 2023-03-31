### ============================================================
### 개발 가이드 :: 조회와 실시간데이터처리 :: GetRepeatCnt
### ============================================================



[GetRepeatCnt() 함수]

GetRepeatCnt(
BSTR sTrCode, // TR 이름
BSTR sRecordName // 레코드 이름
)

데이터 수신시 멀티데이터의 갯수(반복수)를 얻을수 있습니다.
예를들어 차트조회는 한번에 최대 900개 데이터를 수신할 수 있는데
이렇게 수신한 데이터갯수를 얻을때 사용합니다.
이 함수는 OnReceiveTRData()이벤트가 발생될때 그 안에서 사용해야 합니다.

------------------------------------------------------------------------------------------------------------------------------------

예)
[OPT10081 : 주식일봉차트조회요청예시]

OrderResultTrData(...)
{
  if(strRQName == _T("주식일봉차트"))
  {
    int nCnt = OpenAPI.GetRepeatCnt(sTrcode, strRQName);		// 데이터 반복건수 구함
    for (int nIdx = 0; nIdx < nCnt; nIdx++)
    {
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("거래량"));   strData.Trim();
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("시가"));   strData.Trim();
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("고가"));   strData.Trim();
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("저가"));   strData.Trim();
      strData = OpenAPI.GetCommData(sTrcode, strRQName, nIdx, _T("현재가"));   strData.Trim();
    }
  }
}

------------------------------------------------------------------------------------------------------------------------------------
