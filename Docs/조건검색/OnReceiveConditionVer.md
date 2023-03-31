
[OnReceiveConditionVer() 이벤트]

OnReceiveConditionVer(
LONG lRet, // 호출 성공여부, 1: 성공, 나머지 실패
BSTR sMsg  // 호출결과 메시지
)

저장된 사용자 조건식 불러오기 요청에 대한 응답 수신시 발생되는 이벤트입니다.

------------------------------------------------------------------------------------------------------------------------------------

[사용자 조건식 호출결과 수신예시]
OnReceiveConditionVer(long lRet, LPCTSTR sMsg)
{
    if(lRet != 0) return;

    CString		strCondList(m_KOA.GetConditionNameList());
    CString		strOneCond, strItemID, strCondName;
    while(AfxExtractSubString(strOneCond, strCondList, nIndex++, _T(';')))  // 조건식을 하나씩 분리한다.
    {
        if(strOneCond.IsEmpty())	continue;
        AfxExtractSubString(strItemID	, strOneCond, 0, _T('^'));  // 고유번호를 분리한다.
        AfxExtractSubString(strCondName	, strOneCond, 1, _T('^'));  // 조건식 이름을 분리한다.
    }
}

------------------------------------------------------------------------------------------------------------------------------------
