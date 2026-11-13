import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.nue_event_exposure import NueEventExposure  # noqa: E501
from openapi_server.models.problem_details import ProblemDetails  # noqa: E501
from openapi_server import util

import random
from openapi_server.controllers.operationData import *
import pandas as pd
import threading
from openapi_server.controllers.notification_operation import *
 
def create_individual_subcription():  	
	if connexion.request.is_json:
		nue_event_exposure = NueEventExposure.from_dict(connexion.request.get_json())  # noqa: E501
		print ("Recived Service Request")
		noti_id = nue_event_exposure._notif_id
		noti_uri= nue_event_exposure._notif_uri
		ee_list = nue_event_exposure._event_subs
		print ("Recived Service Request with:")
		print ("-Notification Target Address: "+ noti_uri) 
		print ("-Notification Correlation ID: "+ noti_id) 
		print ("-Reqeusted Event ID: ", ee_list) 

		# Whe the subsciprtion is accepted: Subscription Correlation ID is reported to the consumer
		with state_lock:
			if len(used_scbCIDs) > max_subCIDs:
				return "no subscription id available", 503
			while True:
				sub_id = random.randint(0,max_subCIDs)
				if str(sub_id) not in used_scbCIDs:
					used_scbCIDs.append(str(sub_id))
					break
			print ("Allocate the Subscription Correlation ID " + str(sub_id)) 
			print ("Used Subscription Correlation IDs:", used_scbCIDs)
			print ("Create Notification Map:", )
			ee_info_list.append({'Sub_ID' : str(sub_id),'Noti_ID': noti_id, 'Noti_URI': noti_uri, 'Event_List': ee_list})

			print ("Create Notification Thread")
			stop_event = threading.Event()
			notifTread = threading.Thread(target = notiOperation, args = (str(sub_id), stop_event))
			notifTread.daemon = True
			notifTread.start()
			notify_treads.append({"Sub_ID" : str(sub_id), "thread" : notifTread, "stop" : stop_event})

		location = "/nue-event-exposure/v1/subscriptions/" + str(sub_id)
		return str(sub_id), 201, {"Location": location}
