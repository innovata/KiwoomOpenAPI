
# [OnReceiveChejanData() 이벤트]

    OnReceiveChejanData(
        BSTR sGubun, // 체결구분. 접수와 체결시 '0'값, 국내주식 잔고변경은 '1'값, 파생잔고변경은 '4'
        LONG nItemCnt,
        BSTR sFIdList
    )

주문전송 후 주문접수, 체결통보, 잔고통보를 수신할 때 마다 발생됩니다.  
GetChejanData()함수를 이용해서 FID항목별 값을 얻을수 있습니다.
