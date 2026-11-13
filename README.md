# Nue Event Exposure

UE가 SBI로 이벤트 구독을 받고, 구독된 이벤트를 주기적으로 통지하는 서버와 그 클라이언트를 구현한 프로젝트다. 스펙 원본은 `yaml/Nue_EventExposure.yaml`이고, 서버 스텁은 OpenAPI Generator로 생성했다.

## 구성

| 역할 | 위치 | 주소 |
|---|---|---|
| UE 서버 (SBI producer) | `server/` | `127.0.0.1:8080`, base path `/nue-event-exposure/v1` |
| 클라이언트 (구독 요청 + 통지 수신) | `client.py` | `0.0.0.0:9981`, 콜백 경로 `/eventexpsure` |

서버는 Connexion으로 `POST/GET/PUT/DELETE /subscriptions`를 제공한다. 구독이 만들어지면 스레드가 약 5초마다 콜백 주소로 측정값을 POST한다. 삭제가 오면 그 스레드를 멈춘다.

클라이언트가 보내는 구독 body는 다음 형태다.

```json
{
  "notifId": "1",
  "notifUri": "http://192.168.133.27:9981/eventexpsure",
  "eventSubs": [{ "event": "Location" }, { "event": "GPU_util" }]
}
```

UE가 돌려주는 통지는 스펙 모델과 별도로 맞춘 JSON이다.

```json
{
  "Noti_ID": "1",
  "Event_Info": [{ "Location": [1, 2], "GPU_util": 20 }]
}
```

`Location`과 `GPU_util` 값은 `server/openapi_server/controllers/operationData.py`의 고정 샘플이다. 실측 장비가 붙어 있지 않다. 콜백 경로 철자는 `eventexposure`가 아니라 `eventexpsure`다.

## 테스트

의존성:

```bash
cd server
pip3 install -r requirements.txt
pip3 install flask-restx requests
```

터미널 1에서 UE 서버를 켠다.

```bash
cd /home/boo/Nue_eventexposure/server
python3 -m openapi_server
```

터미널 2에서 클라이언트를 켠다. 클라이언트가 자신의 콜백 주소를 `notifUri`에 넣어 구독을 만든다.

```bash
cd /home/boo/Nue_eventexposure
python3 client.py --host 127.0.0.1 --events Location GPU_util --notif-id 1
```

정상이면 클라이언트에 `subscribed subId=...`가 찍히고, 약 5초마다 `Receive data:`가 이어진다.

중지는 다음 중 하나다.

- 클라이언트 터미널에 `stop`을 입력하고 Enter
- Ctrl+C
- 다른 터미널에서 `python3 client.py stop`

중지 후 `Receive data`가 더 이상 나오지 않으면 구독 삭제가 반영된 것이다. 이 머신에서 다른 주소로 콜백을 받으려면 `--host 192.168.133.27`처럼 도달 가능한 주소를 준다.

Swagger UI는 `http://127.0.0.1:8080/nue-event-exposure/v1/ui/`에서 같은 구독 API를 직접 호출할 때 쓴다. 클라이언트를 쓰면 이 화면은 필요 없다.

## UERANSIM과 연동

UERANSIM은 NGAP/NAS만 처리하고 HTTP SBI는 없다. 연동 지점은 PDU 세션으로 UE IP가 생긴 뒤의 사용자 평면이다. 이 저장소의 UERANSIM은 `/home/boo/UERANSIM` (v3.3.0)이고, 5G 코어는 이 VM에 설치되어 있지 않다. Open5GS처럼 AMF가 `127.0.0.5:38412`, PLMN이 `999/70`인 코어가 먼저 떠 있어야 한다. 가입자 정보는 `UERANSIM/config/open5gs-ue.yaml`의 `imsi-999700000000001`과 같아야 한다.

1. 코어를 켠다.
2. gNB와 UE를 켠다. TUN 생성에 권한이 필요하다.

```bash
cd /home/boo/UERANSIM
sudo build/nr-gnb -c config/open5gs-gnb.yaml
sudo build/nr-ue -c config/open5gs-ue.yaml
```

3. UE 로그에 PDU 세션이 성공한 뒤 IP를 확인한다.

```bash
ip addr show uesimtun0
```

4. 이벤트 노출 서버를 그 UE가 받는 주소에서 연다. 현재 `server/openapi_server/__main__.py`의 `app.run(port=8080)`은 로컬에서만 듣는다. 사용자 평면에서 접속하려면 같은 호출을 `app.run(host="0.0.0.0", port=8080)`으로 바꾼 다음 서버를 다시 시작한다.

5. 클라이언트는 UE IP로 구독한다. 아래 `10.45.0.2`는 `uesimtun0`에 실제로 붙은 주소로 바꾼다. `--host`는 UE가 통지를 돌려보낼 수 있는 데이터 네트워크 주소다.

```bash
python3 client.py --ue http://10.45.0.2:8080/nue-event-exposure/v1/subscriptions --host 192.168.133.27
```

같은 VM 안에서 동작만 확인할 때는 `--ue http://127.0.0.1:8080/nue-event-exposure/v1/subscriptions --host 127.0.0.1`을 쓴다. 이 경로는 5G 사용자 평면을 지나지 않는다. 구독과 통지가 사용자 평면을 지나게 하려면 클라이언트는 데이터 네트워크 쪽에 두고, `--ue`에는 UE의 PDU 주소를 넣는다.

`Location`과 `GPU_util`은 연동 후에도 샘플 값이다. UERANSIM에서 실제로 읽을 수 있는 것은 IMSI, 등록 상태, PDU IP, 설정에 적힌 셀 정보다.
