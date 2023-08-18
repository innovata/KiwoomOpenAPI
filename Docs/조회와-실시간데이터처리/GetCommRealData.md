
# 개발 가이드 :: 조회와 실시간데이터처리 :: GetCommRealData




[GetCommRealData() 함수]

    GetCommRealData(
        BSTR strCode,   // 종목코드
        long nFid   // 실시간 타입에 포함된FID (Feild ID)
    )

실시간시세 데이터 수신 이벤트인 OnReceiveRealData() 가 발생될때 실시간데이터를 얻어오는 함수입니다.  
이 함수는 OnReceiveRealData()이벤트가 발생될때 그 안에서 사용해야 합니다.  
FID 값은 "실시간목록"에서 확인할 수 있습니다.

-------------------------------------------------------------------------------------

예)
[주식체결 실시간 데이터 예시]

    if(strRealType == _T("주식체결"))	// OnReceiveRealData 이벤트로 수신된 실시간타입이 "주식체결" 이면
    {
        strRealData = OpenAPI.GetCommRealData(strCode, 10);   // 현재가
        strRealData = OpenAPI.GetCommRealData(strCode, 13);   // 누적거래량
        strRealData = OpenAPI.GetCommRealData(strCode, 228);    // 체결강도
        strRealData = OpenAPI.GetCommRealData(strCode, 20);  // 체결시간
    }

-------------------------------------------------------------------------------------
