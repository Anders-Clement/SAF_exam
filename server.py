import socket
from xml.dom import minidom
import csv
import sys
import signal
from time import gmtime, strftime

HOST =  'localhost' # '172.20.66.83'
PORT = 11333
logFile = open("log.txt", 'w')

def writeLog(stringToWrite):
    currentTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    s =  currentTime + ": " + stringToWrite + "\n"
    logFile.write(s)

def main():
    ###### Load CSV file into a list, assumes time_table is in same directory 
    carrier_station_arr = []

    with open('procssing_times_table.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for count, row in enumerate(reader):
            rowList = []
            if count == 0:  
                for i in range(1,17):
                    rowList.append(i)
            else:
                for data in row:
                    if data.isdigit():
                        rowList.append(int(data))
                    else:
                        rowList.append(count)

            carrier_station_arr.append(rowList)

        print("Processing time table loaded")

    ######## ready socket, and go into loop waiting for clients
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))

        print("Server ready")
        writeLog("Server ready")
        while True:
            s.listen()
            conn, addr = s.accept()
            msg = ""    
            with conn:
                print('Connected to', addr)
                reading = False
                while True:
                    data = conn.recv(1)
                    #print('got data', data)
                    a = data.decode("utf-8")

                    if a == ';' or data == b'':
                        break
                    if reading:
                        msg = msg + a
                    if a == ':':
                        reading = True

                #example msg:
                #<station id="12"><carrier id="5"/></station>
                try:
                    doc = minidom.parseString(msg)
                except Exception:
                    conn.close()
                    continue

                stationNode = doc.childNodes[0]
                stationID = int(stationNode.getAttribute("id"))
                carriers = stationNode.getElementsByTagName("carrier")
                if carriers.length != 1:
                    print("malformed XML, too many carriers?")
                    conn.close()
                    continue
                
                carrierID = int(carriers[0].getAttribute("id"))

                print("Current carrier ID: " + str(carrierID) + ", at station: " + str(stationID))

                if carrierID < 17 and carrierID > 0 and stationID < 17 and stationID > 0:
                    processingTime = carrier_station_arr[carrierID][stationID]
                else:
                    print("Out of range station or carrier ids!")
                    processingTime = 0

                conn.sendall(str(processingTime).encode("utf-8"))
                conn.close()
                print("Carrier served, processing time: " + str(processingTime) + ", closing connection\n")

                logString = "Station " + str(stationID) + " has carrier " + str(carrierID) + ", processing time is: " + processingTime + "ms \n"
                logFile.write(logString)


def exitServer(signal_received, frame):
    print("Server exiting, saving log")
    writeLog("Server exiting")
    logFile.close()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exitServer)
    main()


