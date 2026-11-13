import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.nue_event_exposure import NueEventExposure  # noqa: E501
from openapi_server.models.problem_details import ProblemDetails  # noqa: E501
from openapi_server.models.redirect_response import RedirectResponse  # noqa: E501
from openapi_server import util

from openapi_server.controllers.operationData import *
import pandas as pd
import json

def delete_individual_subcription(sub_id):  # noqa: E501
    with state_lock:
        if sub_id not in used_scbCIDs:
            print ( sub_id + " Subscription is not registered")
            return "Subscription is not registered", 404
        used_scbCIDs.remove(sub_id)
        for index, info in enumerate(ee_info_list):
            if info['Sub_ID'] == sub_id:
                del ee_info_list[index]
                break
        thread_entry = None
        for index, info in enumerate(notify_treads):
            if info['Sub_ID'] == sub_id:
                thread_entry = notify_treads.pop(index)
                break
        print ("Delete Information of " + sub_id + " Subscription")
        print (ee_info_list)
        print ("Used Subscription Correlation IDs:", used_scbCIDs)
    if thread_entry is not None:
        thread_entry["stop"].set()
        thread_entry["thread"].join(timeout=2)
        print ("Delete Notification Thread of " + sub_id + " Subscription")
    return "deleted", 200

def get_individual_subcription(sub_id):  # noqa: E501
    print ("Recive the get request for" + sub_id + " Subscription")
    if sub_id in used_scbCIDs:
    	index_subid = 0
    	for info in ee_info_list:
    		if info['Sub_ID'] == sub_id:
    			break	
    		index_subid += 1
	# replay tpye should be generated but this version uses our type
    		
    	print ("Find event exposure information of " + sub_id + " Subscription")
    	print (ee_info_list[index_subid])
    	temp = ee_info_list[index_subid]
    	data = json.dumps(temp, default=str)
    	return data
    else: 
    	print ( sub_id + " Subscription is not registered")
    	return "Subscription is not registered"


def replace_individual_subcription(sub_id):  # noqa: E501
    if connexion.request.is_json:
        nue_event_exposure = NueEventExposure.from_dict(connexion.request.get_json()) 
        print ("Recived Service Request")
        noti_id = nue_event_exposure._notif_id
        noti_uri= nue_event_exposure._notif_uri
        ee_list = nue_event_exposure._event_subs
        print ("Recived Service Request with:")
        print ("-Notification Target Address: "+ noti_uri) 
        print ("-Notification Correlation ID: "+ noti_id) 
        print ("-Reqeusted Event ID: ", ee_list)

        if sub_id in used_scbCIDs:
            index_subid = 0
        for info in ee_info_list:
            if info['Sub_ID'] == sub_id:
                break	
            index_subid += 1
        print ("Current event exposure information of " + sub_id + " Subscription")
        print (ee_info_list[index_subid])

        ee_info_list[index_subid] = {'Sub_ID' : str(sub_id),'Noti_ID': noti_id, 'Noti_URI': noti_uri, 'Event_List': ee_list}

        print ("Change event exposure information of " + sub_id + " Subscription")
        print (ee_info_list[index_subid])
        print ("All event exposure information of " + sub_id + " Subscription")
        print (ee_info_list)  
        return 'do some magic!'

    else: 
        print ( sub_id + " Subscription is not registered")

        return "Subscription is not registered"

