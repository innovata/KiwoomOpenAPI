
# 개발 가이드 :: 조회와 실시간데이터처리 :: CommRqData


[CommRqData() 함수]

    CommRqData(
        BSTR sRQName,    // 사용자 구분명 (임의로 지정, 한글지원)
        BSTR sTrCode,    // 조회하려는 TR이름
        long nPrevNext,  // 연속조회여부
        BSTR sScreenNo  // 화면번호 (4자리 숫자 임의로 지정)
    )

조회요청 함수입니다.  
리턴값 0이면 조회요청 정상 나머지는 에러  

예)  
-200 시세과부하
-201 조회전문작성 에러
