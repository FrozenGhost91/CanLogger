from .. import TinyCan as tiny_can
from .. import file_manager as fman

can_driver =None
data_file_name ="dataFile.txt"

can_msg_nr = 0
buffered_can_frames={}
newdata=0

def newData():
    global newdata
    print("read {}".format(can_msg_nr))
    return newdata

def read_buffered_can_frame_dicct_by_nr(nr):
    if nr==can_msg_nr:
        newdata=0

    frame = buffered_can_frames.get(nr)
    if frame:
        print("popped {}".format(nr))
        buffered_can_frames.pop(nr)
    return frame



def save_cached_msgs(nr,can_frame_data):
    global data_file_name
    data_string=""
    s =["tTime", "direction", "format", "dlc", "data","diff" ]
    #print(can_frame_data)    
    #s =[time, Id, direction, data,diff ]
    data_string+=can_frame_data.get("Id")
    #print(data_string)
    for part in s:
        data_string+=";"+str(can_frame_data.get(part))
    fman.general_file_functions.safe_write(data_string,data_file_name,mirror_terminal=0)

    with open(data_file_name ,"a") as loggingFile:
        loggingFile.write(data_string)


#####################
#######calbacks######
#####################

def PnPEventCallback(index, status):
    global can_driver
    if status:
        can_driver.canDeviceOpen(index)
        can_driver.startCanBus(index)
        log("[Device connected]")
    else:
        log("[Device Disconnected]")
        log("[reconnecting...]")
        time.sleep(0.500)
        connect(baudrate)


def StatusEventCallback(index,deviceStatusPointer):
    deviceStatus = deviceStatusPointer.contents
    #log(can_driver.FormatCanDeviceStatus(deviceStatusPointer, deviceStatusPointer.CanStatus,deviceStatusPointer.FIfoStatus))


def can_msg_to_dicct(raw_msg):
     sec = raw_msg.Sec
     usec = raw_msg.USec
     dlc = raw_msg.Flags.FlagBits.DLC
     tTime = sec*1000000+usec

     #frame formatif
     if raw_msg.Flags.FlagBits.RTR and raw_msg.Flags.FlagBits.EFF:
        f_format = "EFF/RTR"
     elif raw_msg.Flags.FlagBits.EFF:
        f_format = "EFF"
     elif raw_msg.Flags.FlagBits.RTR:
        f_format = "STD/RTR"
     else:
        f_format = "STD"

     #data direction
     if raw_msg.Flags.FlagBits.TxD:
        direction = "TX"
     else:
        direction = "RX"

     data =""
     for i in range(dlc):
        d = raw_msg.Data[i]
        hexD = hex(d)[2:]
        if d <16:
            data="0"+hexD+" "+data
        else:
            data=hexD+" "+data 
     Id = hex(raw_msg.Id)[2:]
     cached_msg = {
     "Id" : Id,
     "tTime" : tTime,
     "dlc" :dlc,
     "data":data,
     "format" :f_format,
     "direction":direction,
     "diff":0,
     "time":{
        "Sec":sec,
        "USec":usec}
     }
     return cached_msg 


def RxEventCallback(index, DummyPointer, count):
    global can_msg_nr
    global buffered_can_frames
    global newdata
    newdata=1
    print("-------------------------")
    #log("RxEvent Index{0}".format(index))
    global can_driver
    num_msg, raw_msgs = can_driver.CanReceive(count = 500)
    cached_msgs={} 
    if num_msg>0:       
        msgs = can_driver.FormatMessages(raw_msgs)
        dataArray=[]
        
        for raw_msg in raw_msgs:
            #cached_msg=get_diff_time(Id, cached_msg)
            
            #append new data to dicct and save it 
            new_can_frame_data = can_msg_to_dicct(raw_msg) 
            buffered_can_frames.update({
            can_msg_nr : new_can_frame_data 
            })
            #print(buffered_can_frames)
            save_cached_msgs(can_msg_nr, new_can_frame_data)
            can_msg_nr+=1
    else:
        fman.logFileManager.logEvent(can_driver.FormatError(0, 'CanReceive'))
            #return -1
    #return 0
    print(buffered_can_frames)
    print("---------------------------------------")






###################
##setup############
###################
def connect_api(can_driver,baudrate, snr=None, attempts=5):
    current_attempt=0
    while(current_attempt<attempts):
        status = can_driver.OpenComplete(canSpeed=baudrate, snr=snr)
        #if status is None no error 
        if status:
            current_attempt+=1
        else:
            return 1
    return -1

def connect_tiny_can(baudrate,reconnect_attemps):
    #initalize CanDriver
    global can_driver
    can_driver=tiny_can.mhsTinyCanDriver.MhsTinyCanDriver()
    status = connect_api(can_driver,baudrate,attempts=reconnect_attemps)
    can_driver.CanSetUpEvents(PnPEventCallbackfunc=PnPEventCallback,
                          StatusEventCallbackfunc=StatusEventCallback,
                          RxEventCallbackfunc=RxEventCallback)

