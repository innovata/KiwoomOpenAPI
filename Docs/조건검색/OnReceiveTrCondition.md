
[OnReceiveTrCondition() 이벤트]

OnReceiveTrCondition(
BSTR sScrNo,    // 화면번호
BSTR strCodeList,   // 종목코드 리스트
BSTR strConditionName,    // 조건식 이름
int nIndex,   // 조건 고유번호
int nNext   // 연속조회 여부
)

조건검색 요청에대한 서버 응답 수신시 발생하는 이벤트입니다.
종목코드 리스트는 각 종목코드가 ';'로 구분되서 전달됩니다.


------------------------------------------------------------------------------------------------------------------------------------

[조건검색 결과 수신예시]
OnReceiveTrCondition(LPCTSTR sScrNo,LPCTSTR strCodeList, LPCTSTR strConditionName, int nIndex, int nNext)
{
    if(strCodeList == "") return;
    CString strCode, strCodeName;
    int   nIdx = 0;
    while(AfxExtractSubString(strCode, strCodeList, nIdx++, _T(';')))// 하나씩 종목코드를 분리
    {
        if(strCode == _T("")) continue;
        strCodeName = OpenAPI.GetMasterCodeName(strCode); // 종목명을 가져온다.
    }
}

------------------------------------------------------------------------------------------------------------------------------------
