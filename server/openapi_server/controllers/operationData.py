import pandas as pd
import threading

sub_map = [] 
used_scbCIDs =[]
max_subCIDs = 9
state_lock = threading.Lock()
#ee_map = pd.DataFrame(columns=['Sub_ID','Noti_ID','Noti_URI','Event_List' ])
ee_info_list = []

notify_treads = []

eventIndex = 0;
locTrace = [\
[1, 2], \
[2, 3], \
[3, 4], \
[11, 12], \
[12, 23], \
[13, 24], \
[21, 22], \
[22, 23], \
[23, 24],\
[0, 0]]

gpuTrace = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
traceExample = {'Location': locTrace, 'GPU_util': gpuTrace}
