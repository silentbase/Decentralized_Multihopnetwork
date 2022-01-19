import serial
from time import sleep
import base64
import ReverseEintrag
import RouteEintrag
from threading import Thread


class Lora:
    # FIELDS
    myaddr = 210
    broadAddr = 255
    SequenceNr = 0
    previousMSGAddr = None
    previousErrorAddr = None
    msgId = 0
    reqId = 0
    recievedACK = False
    secondsCount = 0

    modus = ''
    # INIT
    def __init__(self):
        self.serial = serial.Serial(
            port="COM11",
            baudrate=115200,
            bytesize=8,
            stopbits=1,
            parity="N",
            timeout=30,
        )

    # LORA-SETUP
    def setup(self):
        RouteEintrag.addToRouteTable(self.myaddr, self.myaddr, [], 0, 0, True)

        self.send(b"AT+CFG=433920000,5,6,12,4,1,0,0,0,0,3000,8,8", b"AT,OK")
        self.send(b"AT+RX", b"AT,OK")

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
    # SEND
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def send(self, msg, confirm):
       
        received = b""
        self.serial.write(msg + b"\r\n")
        while not (confirm + b"\r\n" in received):
            received += self.serial.readline()
        print("SENDED!\n")

    def sendATCommands(self, msg):

        sendbefehl = "AT+SEND="+str(len(msg))

        self.send(sendbefehl.encode(), b"AT,OK")
        self.send(msg, b"AT,SENDED")

    def sendMessage(self):

            addr = input("Enter Address of destination Node: \n")
            if addr == "":
                return
            msg = input("Enter your Message:\n").encode()

            if self.serial.in_waiting == 0:
                
                
                if RouteEintrag.getDestination(int(addr)) != None:
                    if RouteEintrag.getDestination(int(addr)) == self.myaddr:
                        print('cant send to yourself')
                        return

                    self.msgId = self.msgId + 1
                    self.SequenceNr = self.SequenceNr+1
                    self.sendMSG(48, RouteEintrag.getNextHop(
                        int(addr)), self.myaddr, addr, self.SequenceNr, self.msgId, msg)

                    Thread(target=self.waitForMSG, args=(120, 48, RouteEintrag.getNextHop(
                        int(addr)), self.myaddr, addr, self.SequenceNr, self.msgId, msg)).start()
                else:
                 
                    self.reqId = self.reqId+1
                    ReverseEintrag.addToReverseTable(addr,
                                                     self.myaddr, self.reqId,
                                                     0, None)

                    self.sendRREQ(0, self.broadAddr, self.myaddr, self.reqId,
                                  addr, self.SequenceNr+1, 0, self.myaddr, self.SequenceNr)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
    # RECIEVE
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def recieve(self):
        print("recieve..")

        while True:
            if self.modus == 's':
                return
                
            if self.serial.in_waiting > 0:

                incoming = self.serial.readline()
                

                if incoming.decode()[:2] != 'LR':
                    continue

                stelle = incoming.rfind(b',')+1
                incoming = incoming[stelle:-2]

                

                payload = ''
                if self.isBase64(incoming) == False:

                    payload = incoming[8:]
                    incoming = incoming[0:8]

                length = len(str(bin(self.decodeBase64(incoming)[0])))
                flags = str(bin(self.decodeBase64(incoming)[0]))[length-4:]
                typ = str(bin(self.decodeBase64(incoming)[0]))[2:length-4]
                flags = int(flags, 2)

                if typ == '':
                    typ = '0'
                typ = int(typ, 2)

                if(typ == 0):  # RREQ
                    
                    code = self.decodeBase64(incoming)[0]
                    broadcastAddr = self.decodeBase64(incoming)[1]
                    previousAddr = self.decodeBase64(incoming)[2]
                    req_id = self.decodeBase64(incoming)[3]
                    destinationAddr = self.decodeBase64(incoming)[4]
                    destSequence = self.decodeBase64(incoming)[5]
                    hopCount = self.decodeBase64(incoming)[6]
                    originatorAddr = self.decodeBase64(incoming)[7]
                    originator_sequence = self.decodeBase64(incoming)[8]
                    

                    hopCount = int(hopCount+1)  # hop um 1 hochzaehlen
                    if RouteEintrag.getDestination(destinationAddr) == None:

                        if ReverseEintrag.getSource(originatorAddr) == originatorAddr and ReverseEintrag.getReqID(originatorAddr) == req_id:
                            
                            self.sendRREQ(typ, broadcastAddr, self.myaddr, req_id, destinationAddr, destSequence, hopCount,
                                          originatorAddr, originator_sequence)
                            print('RREQ mit der Id '+str(req_id)+' von '+str(originatorAddr) +
                                  ' für '+str(destinationAddr) + ' weitergeleitet')

                            ReverseEintrag.addToReverseTable(destinationAddr,
                                                             originatorAddr, req_id,
                                                             hopCount, previousAddr)

                    elif RouteEintrag.getDestination(destinationAddr) == self.myaddr:
                        self.SequenceNr = self.SequenceNr+1
                        self.sendRREP(16, previousAddr, self.myaddr, req_id, originatorAddr,  
                                      self.SequenceNr, 0, destinationAddr, 0)  
                        print('RREQ mit der Id '+str(req_id)+' von ' +
                              str(originatorAddr) + ' für mich (' + str(destinationAddr)+')')
                        print('RREP an ' + str(originatorAddr)+' geschickt')

                    else:
                        
                        if ReverseEintrag.getSource(originatorAddr) == originatorAddr and ReverseEintrag.getReqID(originatorAddr) == req_id: 
                            if ReverseEintrag.getHopCount(originatorAddr) > hopCount:
                                ReverseEintrag.update(
                                    originatorAddr, hopCount, previousAddr)
                        else:
                            self.sendRREP(16, previousAddr, self.myaddr, req_id, originatorAddr, 
                                          self.SequenceNr+1, RouteEintrag.getHopCount(
                                              destinationAddr),
                                          destinationAddr, 3)
                            print('RREP mit der Id '+str(req_id)+' von '+str(destinationAddr) +
                                  'für '+str(originatorAddr) + ' gesendet')

                elif(typ == 1):  # RREP

                    code = self.decodeBase64(incoming)[0]
                    hopAddr = self.decodeBase64(incoming)[1]
                    previousAddr = self.decodeBase64(incoming)[2]
                    req_id = self.decodeBase64(incoming)[3]
                    destinationAddr = self.decodeBase64(incoming)[4]
                    destSequence = self.decodeBase64(incoming)[5]
                    hopCount = self.decodeBase64(incoming)[6]
                    originatorAddr = self.decodeBase64(incoming)[7]
                    ttl = self.decodeBase64(incoming)[8]

                    hopAddr = ReverseEintrag.getPreviousAddr(
                        destinationAddr, req_id)

                    precursor = hopAddr
                    hopCount = int(hopCount+1)
                    # check if already in routeTable and maybe update maybe here precursors?
                    if RouteEintrag.getDestination(originatorAddr) == None:
                        
                        RouteEintrag.addToRouteTable(originatorAddr, previousAddr, precursor,
                                                     hopCount, destSequence, True)

                        if destinationAddr != self.myaddr:
                            self.sendRREP(16, hopAddr, self.myaddr, req_id, destinationAddr,
                                          destSequence, hopCount, originatorAddr, ttl)

                            print("Recieved RREP with the id: " + str(req_id) +

                                  " from " + str(originatorAddr))
                            print(" forwarding it to: " + str(destinationAddr))
                        else:
                            print("Recieved RREP for my RREQ with the id: " + str(req_id) +
                                  " from " + str(originatorAddr))
                    else:
                        if RouteEintrag.getHopCount(originatorAddr) > hopCount or RouteEintrag.getSequenceNr(originatorAddr) < destSequence:
                            RouteEintrag.invalidate(originatorAddr)
                            RouteEintrag.addToRouteTable(originatorAddr, previousAddr, precursor,
                                                         hopCount, destSequence, True)
                            if destinationAddr != self.myaddr:
                                self.sendRREP(16, hopAddr, self.myaddr, req_id, destinationAddr,
                                              destSequence, hopCount, originatorAddr, 3)

                            print("Recieved RREP with the id: " + str(req_id) +

                                  " from " + str(originatorAddr))
                            print(" forwarding it to: " + str(destinationAddr))                  

                    print('RREP')
                elif(typ == 2):  # RERR

                    code = self.decodeBase64(incoming)[0]
                    hopAddr = self.decodeBase64(incoming)[1]
                    self.previousErrorAddr = self.decodeBase64(incoming)[2]
                    pathCount = self.decodeBase64(incoming)[3]

                    self.sendACK(64, self.previousErrorAddr, self.myaddr)
                    self.handleForwardError(pathCount, incoming)
                
                    print('Forwarding RERR')
                elif(typ == 3):  # MSG
                    header_ext = incoming[0:8]
                    
                    code = self.decodeBase64(header_ext)[0]
                    hopAddr = self.decodeBase64(header_ext)[1]
                    self.previousMSGAddr = self.decodeBase64(header_ext)[2]
                    destinationAddr = self.decodeBase64(header_ext)[3]
                    originator_sequence = self.decodeBase64(header_ext)[4]
                    msgId = self.decodeBase64(header_ext)[5]

                    if hopAddr == self.myaddr:

                        print(RouteEintrag.getDestination(destinationAddr))
                        if RouteEintrag.getDestination(destinationAddr) == self.myaddr:
                            self.sendACK(64, self.previousMSGAddr, self.myaddr)
                            print("Recieved Message: " + payload.decode())

                        else:
                            hopAddr = RouteEintrag.getNextHop(destinationAddr)
                            self.sendACK(64, self.previousMSGAddr, self.myaddr)
                            self.sendMSG(48, hopAddr,
                                        self.myaddr, destinationAddr, originator_sequence, msgId, payload)
                            print("Forwarded Message: " + payload.decode())            
                            Thread(target=self.waitForMSG, args=(10, 48, hopAddr,
                                        self.myaddr, destinationAddr, originator_sequence, msgId, payload
                             )).start()
                            
                        
                            print('MSG')
                elif(typ == 4):  # ACK
                    self.recievedACK = True
                    code = self.decodeBase64(incoming)[0]
                    hopAddr = self.decodeBase64(incoming)[1]
                    prevAddr = self.decodeBase64(incoming)[2]
                    print(hopAddr)
                    print(self.previousMSGAddr)
                    if hopAddr == self.myaddr and self.previousMSGAddr != None:

                        self.sendACK(64, self.previousMSGAddr, self.myaddr)
                        self.previousMSGAddr = None
                        self.recievedACK = False
                        print('Forwarding ACK')
                    elif  hopAddr == self.myaddr and self.previousErrorAddr != None:   
                          self.sendACK(64, self.previousErrorAddr, self.myaddr)
                          self.previousErrorAddr = None
                          self.recievedACK = False
                          print('Forwarding ACK')
                    else :      
                        print('Recieved ACK')
                        self.recievedACK = False  
            else:
                continue
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
    # SEND ERROR METHODS
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def handleForwardError(self, pathCount, incoming):
        destAddrList = []
        for i in range(pathCount):
            i = i*2
            destAddrList.append(
                destinationAddr=self.decodeBase64(incoming)[4+i])

        RouteEintrag.invalidate(destAddrList)

        destSeqList = []
        for i in range(pathCount):
            i = i*2
            destSeqList.append(
                destSequence=self.decodeBase64(incoming)[5+i])

        precursors = RouteEintrag.getPrecursors(destAddrList)

        for i in range(len(precursors)):
            self.sendRERR(
                32, precursors[i], self.myaddr, pathCount, destAddrList, destSeqList, 0)
            print("Send Error Msg To: "+str(precursors[i]))    
            sleep(1)
        

    def handleSendError(self, destAddrList, d_sequence_List):
            RouteEintrag.invalidate(destAddrList)
            precursors = RouteEintrag.getPrecursors(destAddrList)

            for i in range(len(precursors)):
                self.sendRERR(
                    32, precursors[i], self.myaddr, len(destAddrList), destAddrList, d_sequence_List, 0)
                print("Send Error Msg To: "+str(precursors[i]))  
                sleep(1)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
    # SEND PACKAGE METHODS
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def sendRREQ(self, code, broadcastAddr, previousAddress, req_id, destinationAddr, destSequence, hopCount, originatorAddr, originator_sequence):
        rreq = self.encodeBase64(code, broadcastAddr, previousAddress, req_id, destinationAddr, destSequence,
                                 hopCount, originatorAddr, originator_sequence)
        self.sendATCommands(rreq)

    def sendRREP(self, code, hopAddress, previousAddr, req_id, destinationAddr, destSequence, hopCount, originatorAddr, ttl):
        rreq = self.encodeBase64(code, hopAddress, previousAddr, req_id,
                                 destinationAddr, destSequence, hopCount, originatorAddr, ttl)
        self.sendATCommands(rreq)

    def sendMSG(self, code, hopAddr, prevAddr, destAddr, or_seq, msgId, payload):
        msg = self.encodeBase64(code, hopAddr, prevAddr,
                                destAddr, or_seq, msgId)
        self.sendATCommands(msg+payload)

    def sendRERR(self, code, hopAddr, prevAddr, pathCount, desAdrrList, destSeqList, buffer):
        msg = self.encodeREERbase64(code, hopAddr, prevAddr,
                                    pathCount, desAdrrList, destSeqList, buffer)
        self.sendATCommands(msg)

    def sendACK(self, code, hopAddr, prevAddr):
        msg = self.encodeBase64(code, hopAddr, prevAddr)
        self.sendATCommands(msg)


#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
    # BASE64 METHODS
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def encodeREERbase64(self, *args):
        values = args[:4]
        destList = args[4]
        seqList = args[5]
        buffer = int(args[6]).to_bytes(1, 'big')
        list = b''

        for i in range(len(seqList)):

            list += (int(destList[i]).to_bytes(1, 'big'))
            list += (int(seqList[i]).to_bytes(1, 'big'))

        bytearray = b''

        for v in values:
            bytearray += int(v).to_bytes(1, 'big')

        res = base64.b64encode(bytearray+list+buffer)
        
        return res

    def encodeBase64(self, *args):
        bytearray = b''
        for arg in args:

            bytearray += int(arg).to_bytes(1, 'big')

        res = base64.b64encode(bytearray)
        
        return res

    def decodeBase64(self, b):
        res = base64.b64decode(b)
        int_values = [x for x in res]
        return int_values

    def isBase64(self, s):
        try:
            return base64.b64encode(base64.b64decode(s)) == s
        except Exception:
            return False
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
    # TIMER
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def waitForMSG(self, seconds,code, nextNode,
                                        myaddr, destinationAddr, originator_sequence, msgId, payload):
        self.secondsCount = seconds

        for j in range(3):
            for i in range(self.secondsCount):
                if self.recievedACK == True:
                    return
                sleep(i)
            self.sendMSG(code, nextNode, myaddr, destinationAddr,
             originator_sequence, msgId, payload) 

        destAddrList = RouteEintrag.getAllDestinations(nextNode)
        d_sequenceList = RouteEintrag.getAllDestinations(nextNode)
        self.handleSendError(destAddrList, d_sequenceList)
        
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#
    # RUN
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------#

    def setModus(self):
        while True:
            self.modus = input("Modus:")
            sleep(10)

    def run(self):
        self.setup()
        Thread(target=self.setModus).start()
        while True:
            if self.modus == 's':
                self.sendMessage()
            else:
                self.recieve()


lora = Lora()
lora.run()