class RouteEintrag:
    def __init__(self, destination, next_hop, precursor, hop_count, d_sequenceNr, is_valid):
        self.destination = destination
        self.next_hop = next_hop
        self.precursors = precursor
        self.hop_count = hop_count
        self.d_sequenceNr = d_sequenceNr
        self.is_valid = is_valid


routeTable = []


def addToRouteTable(dest, next_hop, precursors, hop_count, d_sequenceNr, is_valid):
    eintrag = RouteEintrag(dest, next_hop, precursors,
                           hop_count, d_sequenceNr, is_valid)                       
    routeTable.append(eintrag)


def getDestination(destination):
    for obj in routeTable:
        if obj.destination == destination and obj.is_valid == True:
            return obj.destination

    return None

def getAllDestinations(nextHop):
    destAddrList = []
    for obj in routeTable:
        if obj.next_hop == nextHop:
            destAddrList.append(obj.destination)
            
    return destAddrList

def getAll_d_sequences(nextHop):
    destSeqList = []
    for obj in routeTable:
        if obj.next_hop == nextHop:
            destSeqList.append(obj.d_sequenceNr)
            
    return destSeqList


def getHopCount(destination):
    for obj in routeTable:
        if obj.destination == destination and obj.is_valid == True:
            return obj.hop_count

    return None    

def getNextHop(destination):
    for obj in routeTable:
        if obj.destination == destination and obj.is_valid == True:
            return obj.next_hop

    return None      

def getSequenceNr(destination):
    for obj in routeTable:
        if obj.destination == destination and obj.is_valid == True:
            return obj.d_sequenceNr

    return None  

def getPrecursors(destinations):
    precursors = []
    for i in range(len(destinations)):
        for obj in routeTable:
            if obj.destination == destinations[i]:
                precursors.append(obj.precursor)
    return precursors

def invalidate(destinations):
    for i in range(len(destinations)):
        for obj in routeTable:
            if obj.destination == destinations[i]:
                obj.is_valid = False

    return None              
