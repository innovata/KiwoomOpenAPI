
------------------------------------------------------------------------------------------------------------------------------------

Q : 실시간 조건검색 종목이 영웅문4와 다르게 나옵니다.

A : 조건검색 실시간으로 편입되는 종목이 순간적으로 편입/이탈을 반복하는 경우
     서버에따라 결과가 일시적으로 다를 수 있습니다.
     하지만 특정종목이 편입되어 머무르는 경우, 그리고 실시간이 아닌 검색 결과는
     서버나 매체에 무관하게 동일해야 맞습니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 영웅문4로 전송한 주문이 OpenAPI로 수신되는데 맞나요?

A : 실시간 주문체결 정보는 동일ID로 접속되어 있는 매체에 모두 전송됩니다.
     따라서 영웅문4나 영웅문S로 발생시킨 주문에대해서
     OpenAPI의 실시간 주문체결 이벤트(OnReceiveChejanData)가 발생됩니다.
     반대로 OpenAPI를 통해 발생시킨 주문을 영웅문4, 영웅문S 의 화면에서 실시간으로 확인하실 수 있습니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 주문을 전송한 뒤에 응답이 없습니다.

A : SendOrder 함수의 리턴값이 0으로 정상적인 주문을 전송한 뒤에도
     해당 주문이 특정한 사유로 서버에서 거부처리 되었을 가능성이 있습니다.
     주문거부 사유를 포함한 서버의 메세지를 OnReceiveMsg() 이벤트에서 확인하실 수 있습니다.
     서버에서 주문거부 발생시 OnReceiveChejanData 이벤트는 발생되지 않습니다.

     정확한 주문 처리내역을 확인하고자 하실때는 접속ID, 주문시간, 주문종목으로 게시판에 문의해주시면
     담당자를 통해 해당 주문 로그를 확인하여 답변드리겠습니다.
     모의투자 서버에서의 주문 처리내역 확인은 위의 정보들로 하여 모의투자 게시판에 문의 부탁드립니다.
     (모의투자 1:1 문의 https://www.kiwoom.com/h/mock/ordinary/VMockTotalNOTICView)

------------------------------------------------------------------------------------------------------------------------------------

Q : 주문가능한 수량으로 주문한거 같은데 시장가 주문일때 증거금 부족 거부가 발생합니다.

A : 시장가 주문의 경우 주문가격이 없기때문에 주문가능 수량을 계산할때 해당 종목의
     상한가를 기준으로 하여 계산됩니다.
     따라서 사용자가 현재가로 계산하여 주문수량을 입력했다면 해당주문이 시장가 주문인 경우
     주문가능수량 초과로 증거금 부족 주문거부가 발생할 수 있습니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 장시작전에 미리 접속할때 오전에 몇시이전은 작동하면 안되는지요?

A : 서버점검시간은 매일 05:00 에 시작되며 보통 1분, 길어지면 5분정도 소요됩니다.
     이 시간에는 접속자체가 불가하며 이전에 접속되어 있는 경우 접속이 단절됩니다.
     조건검색 조회는 07:30 부터 가능합니다.
     따라서 07:30 이후에 접속하시길 권장 드립니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 정정주문, 취소주문시에 OnReceiveChejanData 응답이 이상합니다.

A : 정정이나 취소주문시 마지막 신호로 미체결삭제(미체결클리어) 신호가 한번 더 수신됩니다.
     주문처리 완료시점으로 미체결수량을 0으로 만드는 신호라고 여기시면 되겠습니다.
     해당 신호를 통해 영웅문4나 영웅문S의 주문화면에서 미체결상태의 주문을 클리어 또는 업데이트 합니다.
     이때 FID 913번 값은 원주문의 마지막상태로 수신됩니다.
     즉 취소주문의 원주문 상태가 접수상태에서 취소되었다면 "접수" 값으로 수신되고
     원주문 상태가 일부 체결상태에서 취소되었다면 "체결" 값으로 수신됩니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 시간외 단일가 주문 방법이 어떻게 되나요?

A : 주식 종목의 주문은 모두 SendOrder 함수가 사용됩니다.
     정규장 마감 후 시간외 단일가 주문은 16:00 ~ 18:00 시간동안 가능하며
     거래구분 62, 주문가격 0입력하여 주문하시면 되겠습니다.
     10분 단위로 체결이 이루어지게 됩니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 모의투자 수익율이 이상합니다.

A : opw00004  TR의 "손익율" 데이터는 모의투자와 실서버에서 단위가 다른 값이 수신됩니다.
     모의투자 서버에서는 손익율 데이터가 소숫점으로 수신되고, 실거래 서버에서는 소숫점 없이 수신됩니다.
     실거래 서버에서 수신된 손익율 데이터의 뒤 4자리가 소숫점 데이터로 보시면 되겠습니다. 다른 항목들의 값은 동일합니다.
     프로그램이 모의투자와 실서버 양쪽에서 수익율 값을 처리해야 하는 경우
     접속된 서버를 구분해주시기 바랍니다.
     접속하신 서버가 어디인지 구분하는 방법은
     KOA_Functions("GetServerGubun", "") 함수를 사용하시면 되겠습니다.
     리턴값은 "1" 일때 모의투자 서버에 접송중인 상태이고, 나머지 값은 실서버 접속 중으로 구분하시면 되겠습니다.
     참고로 opw00018 TR서비스의 "수익률%" 항목에 대해서도 위와 동일합니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 조건검색 실시간을 1개가 아닌 2개이상 실행 가능?

A : 실시간 조건검색은 최대 10개까지 동시에 사용이 가능합니다.
     영웅문4에서 [0156] 조건검색실시간 화면을 최대 10개 열어놓으신것과 같습니다.
     OpenAPI에서 A와 B조건식에대해 동일한 화면번호를 사용하게 되면 이전 조건식은 실시간이 중지됩니다.
     각각 다른 화면번호를 사용하시고, 조건검색에서 사용하신 화면번호가
     또 다른 TR이나 주문에서 사용되지 않도록 하시는 경우
     A, B 동시에 실시간 조건검색 사용이 가능합니다.
     OnReceiveRealCondition() 이벤트를 통해 실시간으로 수신되며 수신된 조건식이름으로 구분하시면 되겠습니다.

------------------------------------------------------------------------------------------------------------------------------------

Q : 조건식 불러오기 특정 조건식 못가져 옵니다.

A : HTS와 OpenAPI의 조건검색 버전이 일치하지 않는 경우 특정 조건식을 불러오지 못할 수 있습니다.
     OpenAPI를 자동로그인으로 사용중이시면 수동로그인으로 전환하셔서 버전처리를
     진행하신뒤에 사용해보시기 바랍니다.
     버전처리를 정상적으로 진행한 이후에도 동일한 현상이시면
     사용하신 ID와 해당 조건식이름, GetConditionLoad 하신 시간으로 하여 문의주시면
     서버담당자와 확인해보도록 하겠습니다.

------------------------------------------------------------------------------------------------------------------------------------
