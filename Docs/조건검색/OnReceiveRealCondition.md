
[OnReceiveRealCondition() 이벤트]

OnReceiveRealCondition(
BSTR strCode,   // 종목코드
BSTR strType,   //  이벤트 종류, "I":종목편입, "D", 종목이탈
BSTR strConditionName,    // 조건식 이름
BSTR strConditionIndex    // 조건식 고유번호
)

실시간 조건검색 요청으로 신규종목이 편입되거나 기존 종목이 이탈될때 마다 발생됩니다.
※ 편입되었다가 순간적으로 다시 이탈되는 종목에대한 신호는 조건검색 서버마다 차이가 발생할 수 있습니다.

------------------------------------------------------------------------------------------------------------------------------------

[실시간 조건검색 수신예시]
OnReceiveRealCondition(LPCTSTR sCode, LPCTSTR sType, LPCTSTR strConditionName, LPCTSTR strConditionIndex)
{
    CString strCode(sCode), strCodeName;
    int   nIdx = 0;
    CString strType(sType);
    if(strType == _T("I"))// 종목편입
    {
      strCodeName = OpenAPI.GetMasterCodeName(strCode); // 종목명을 가져온다.
      long lRet = OpenAPI.SetRealReg(strSavedScreenNo, strCode, _T("9001;302;10;11;25;12;13"), "1");// 실시간 시세등록
    }
    else if(strType == _T("D")) // 종목이탈
    {
      OpenAPI.SetRealRemove(strSavedScreenNo, strCode);// 실시간 시세해지
    }
}

------------------------------------------------------------------------------------------------------------------------------------
