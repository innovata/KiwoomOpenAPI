### ============================================================
### 개발 가이드 :: 조회와 실시간데이터처리 :: GetCommDataEx
### ============================================================



[GetCommDataEx() 함수]

GetCommDataEx(
BSTR strTrCode,   // TR 이름
BSTR strRecordName  // 레코드이름
)

조회 수신데이터 크기가 큰 차트데이터를 한번에 가져올 목적으로 만든 차트조회 전용함수입니다.

------------------------------------------------------------------------------------------------------------------------------------

예)
[차트일봉데이터 예시]

OrderResultTrDataKhopenapictrl(...)
{
  if(strRQName == _T("주식일봉차트"))
  {
    VARIANT   vTemp = OpenAPI.GetCommDataEx(strTrCode, strRQName);
    long	lURows, lUCols;
    long	nIndex[2]
    COleSafeArray saMatrix(vTemp);
    VARIANT vDummy;
    VariantInit(&vDummy);
    saMatrix.GetUBound(1, &lURows); // 데이터 전체갯수(데이터 반복횟수)
    saMatrix.GetUBound(2, &lUCols); // 출력항목갯수

    for(int nRow = 0; nRow <= lURows; nRow ++)
    {
      for(int nCol = 0; nCol <= lUCols; nCol ++)
      {
        nIndex[0] = lURows;
        nIndex[1] = lUCols;
        saMatrix.GetElement(nIndex, &vDummy);
        ::SysFreeString(vDummy.bstrVal);
      }
    }
    saMatrix.Clear();
    VariantClear(&vTemp);
  }
}

------------------------------------------------------------------------------------------------------------------------------------
