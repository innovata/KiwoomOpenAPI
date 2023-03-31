### ============================================================
### 개발 가이드 :: 조회와 실시간데이터처리 :: OrderResultTrData
### ============================================================



[OrderResultTrData() 이벤트]

void OrderResultTrData(
BSTR sScrNo,       // 화면번호
BSTR sRQName,      // 사용자 구분명
BSTR sTrCode,      // TR이름
BSTR sRecordName,  // 레코드 이름
BSTR sPrevNext,    // 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음
LONG nDataLength,  // 사용안함.
BSTR sErrorCode,   // 사용안함.
BSTR sMessage,     // 사용안함.
BSTR sSplmMsg     // 사용안함.
)

요청했던 조회데이터를 수신했을때 발생됩니다.
수신된 데이터는 이 이벤트내부에서 GetCommData()함수를 이용해서 얻어올 수 있습니다.
