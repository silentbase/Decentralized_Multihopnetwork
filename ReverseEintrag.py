class ReverseEintrag:
    def __init__(self, destination, source, req_id, hop_count, previous_hop):
        self.destination = destination
        self.source = source
        self.req_id = req_id
        self.hop_count = hop_count
        self.previous_hop = previous_hop


reverseRouteTable = []


def addToReverseTable(dest, source, reqId, hopCount, previousHop):
    eintrag = ReverseEintrag(dest, source, reqId, hopCount, previousHop)
    reverseRouteTable.append(eintrag)

def update(addr, hopCount, previousHop):
    for obj in reverseRouteTable:
        if obj.source == addr:
            obj.hopCount == hopCount
            obj.previousHop == previousHop

def getElement(destination):
    for obj in reverseRouteTable:
        if obj.destination == destination:
            print("destination:"+str(obj.destination))
            return obj.destination    

def getPreviousAddr(addr, reqId):
    for obj in reverseRouteTable:
        if obj.source == addr and obj.req_id == reqId:
            print("previous_hop:"+str(obj.previous_hop))
            return obj.previous_hop 
    return None
    
def getSource(addr):
    for obj in reverseRouteTable:
        if obj.source == addr:
            return obj.source

def getReqID(addr, reqId):
    for obj in reverseRouteTable:
        print(str(obj.source)+", "+ str(obj.req_id))
        if obj.source == addr and obj.req_id == reqId:
            return obj.req_id

def getHopCount(addr):
    for obj in reverseRouteTable:
        if obj.source == addr:
            return obj.hop_count