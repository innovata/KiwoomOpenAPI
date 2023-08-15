
# [GetChejanData() 함수]

    GetChejanData(
        long nFid   // 실시간 타입에 포함된 FID(Field ID)
    )

OnReceiveChejan()이벤트가 발생될때 FID에 해당되는 값을 구하는 함수입니다.  
이 함수는 OnReceiveChejan() 이벤트 안에서 사용해야 합니다.  
예) 체결가 = GetChejanData(910)
