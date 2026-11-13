import requests
import json
import time

from openapi_server.controllers.operationData import *
eventIndex = 0
def find_event_info(eventID):
	global eventIndex
	value = traceExample[eventID][eventIndex]
	val ={eventID:value}
	eventIndex = (eventIndex+1)%10
	
	return val

def notify_event (sub_id):
    # find subscription info
    with state_lock:
        if sub_id not in used_scbCIDs:
            print ( sub_id + " Subscription is not registered")
            return
        info = None
        for item in ee_info_list:
            if item['Sub_ID'] == sub_id:
                info = item
                break
        if info is None:
            print ( sub_id + " Subscription is not registered")
            return
        print ("Find Information of " + sub_id + " Subscription")
        print (info)
        notif_id = info['Noti_ID']
        notif_URI = info['Noti_URI']
        event_names = [eventID._event for eventID in info['Event_List']]

    eventInfo = []
    valdic ={}
    for event_name in event_names:
        val = find_event_info(event_name)
        valdic.update(val)
    eventInfo.append(valdic)
	# mesaure event information
    headers = {"Content-Type": "application/json"}
    temp = {'Noti_ID': notif_id, 'Event_Info': eventInfo}
    data = json.dumps(temp)

    try:
        response = requests.post(notif_URI, headers=headers, data=data, timeout=3)
        print (response)
    except requests.RequestException as exc:
        print ("Notification post failed:", exc)

def notiOperation (sub_id, stop_event=None):
    while stop_event is None or not stop_event.is_set():
        notify_event (sub_id)
        if stop_event is None:
            time.sleep(5)
        elif stop_event.wait(5):
            break


