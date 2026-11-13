"""
UE Event Exposure client
------------------------
Swagger UI 없이 UE 서버에 구독을 보내고, 통지를 받아 출력하고, 구독을 중지한다.

시작 (콜백 수신 + 구독 요청):
  python3 client.py
  python3 client.py --host 192.168.133.27 --events Location GPU_util

실행 중 중지:
  이 터미널에 stop 입력 후 Enter
  또는 Ctrl+C

다른 터미널에서 중지:
  python3 client.py stop
"""

from flask import Flask, request
from flask_restx import Resource, Api
from werkzeug.serving import make_server

import argparse
import json
import signal
import sys
import threading
import time
from pathlib import Path

import requests


app = Flask(__name__)
api = Api(app)

todos = []
todos_lock = threading.Lock()

STATE_FILE = Path(__file__).with_name(".client_state.json")
STOP_FILE = Path(__file__).with_name(".client_stop")

DEFAULT_UE = "http://127.0.0.1:8080/nue-event-exposure/v1/subscriptions"
DEFAULT_HOST = "192.168.133.27"
DEFAULT_PORT = 9981


@api.route("/eventexpsure")
class EventExposure(Resource):
    def post(self):
        body = request.json or {}
        rcv_data = {
            "Noti_ID": body.get("Noti_ID"),
            "Event_Info": body.get("Event_Info"),
        }
        with todos_lock:
            todos.append(rcv_data)
            count = len(todos)
        print("Receive data:", rcv_data, flush=True)
        print("stored notifications:", count, flush=True)
        return {"message": "received"}, 200


def callback_url(host, port):
    return "http://%s:%s/eventexpsure" % (host, port)


def subscribe(ue_url, notif_uri, events, notif_id):
    payload = {
        "notifId": notif_id,
        "notifUri": notif_uri,
        "eventSubs": [{"event": event} for event in events],
    }
    print("POST", ue_url, flush=True)
    print("payload", json.dumps(payload), flush=True)
    response = requests.post(ue_url, json=payload, timeout=10)
    print("subscribe status", response.status_code, response.text, flush=True)
    response.raise_for_status()
    return parse_sub_id(response)


def parse_sub_id(response):
    location = response.headers.get("Location", "")
    if location:
        sub_id = location.rstrip("/").split("/")[-1]
        if sub_id:
            return sub_id
    text = (response.text or "").strip().strip('"')
    if text.isdigit():
        return text
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, int):
        return str(body)
    if isinstance(body, str) and body.strip().isdigit():
        return body.strip()
    if isinstance(body, dict) and body.get("subId") is not None:
        return str(body["subId"])
    raise RuntimeError("subscription id was not in the UE response: %s" % response.text)


def unsubscribe(ue_url, sub_id):
    url = "%s/%s" % (ue_url.rstrip("/"), sub_id)
    print("DELETE", url, flush=True)
    response = requests.delete(url, timeout=10)
    print("unsubscribe status", response.status_code, response.text, flush=True)
    if response.status_code not in (200, 204, 404):
        response.raise_for_status()


def save_state(ue_url, sub_id):
    STATE_FILE.write_text(json.dumps({"ue": ue_url, "subId": sub_id}))


def load_state():
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text())


def clear_state():
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def stop_running_client():
    """Ask a running client to unsubscribe. If it is already gone, delete directly."""
    STOP_FILE.write_text("stop")
    deadline = time.time() + 3
    while time.time() < deadline:
        if not STATE_FILE.exists():
            if STOP_FILE.exists():
                STOP_FILE.unlink()
            print("client stopped")
            return
        time.sleep(0.2)
    state = load_state()
    if state:
        unsubscribe(state["ue"], state["subId"])
        clear_state()
    if STOP_FILE.exists():
        STOP_FILE.unlink()
    if state:
        print("subscription %s deleted" % state["subId"])
    else:
        print("no active subscription")


def serve(ue_url, host, port, events, notif_id):
    if STOP_FILE.exists():
        STOP_FILE.unlink()

    notif_uri = callback_url(host, port)
    server = make_server("0.0.0.0", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            requests.get(notif_uri, timeout=0.3)
            break
        except requests.ConnectionError:
            time.sleep(0.05)
    else:
        raise RuntimeError("callback server did not start on %s" % notif_uri)
    print("callback listening on", notif_uri, flush=True)

    sub_id = subscribe(ue_url, notif_uri, events, notif_id)
    save_state(ue_url, sub_id)
    print("subscribed subId=%s" % sub_id, flush=True)
    print("type stop and press Enter to unsubscribe", flush=True)

    stop_local = threading.Event()

    def request_stop(signum, frame):
        stop_local.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    def watch_stdin():
        while not stop_local.is_set():
            line = sys.stdin.readline()
            if line == "":
                return
            if line.strip().lower() in ("stop", "quit", "exit"):
                stop_local.set()
                return

    stdin_thread = threading.Thread(target=watch_stdin)
    stdin_thread.daemon = True
    stdin_thread.start()

    try:
        while not stop_local.is_set():
            if STOP_FILE.exists():
                stop_local.set()
                break
            stop_local.wait(0.5)
    finally:
        state = load_state()
        if state:
            try:
                unsubscribe(state["ue"], state["subId"])
            except requests.RequestException as exc:
                print("unsubscribe failed:", exc, flush=True)
            clear_state()
        if STOP_FILE.exists():
            STOP_FILE.unlink()
        server.shutdown()
        print("client stopped", flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_running_client()
        return

    parser = argparse.ArgumentParser(description="Subscribe to UE event exposure and receive notifications")
    parser.add_argument("--ue", default=DEFAULT_UE, help="UE subscriptions URL")
    parser.add_argument("--host", default=DEFAULT_HOST, help="client address written into notifUri")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--notif-id", default="1")
    parser.add_argument("--events", nargs="+", default=["Location", "GPU_util"])
    args = parser.parse_args()
    serve(args.ue, args.host, args.port, args.events, args.notif_id)


if __name__ == "__main__":
    main()
