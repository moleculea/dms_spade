# -*- coding: utf-8 -*-
from math import *
from DIGIT import *
from types import *

from dbmodel import * # Reference: getWAP()

idlenessList = [
{20100312: 5, 20100909: 3, 20100311: 8},
{20100312: 4, 20100909: 5, 20100311: 7},
{20100312: 5, 20100909: 4, 20100311: 6},
]

# Success Rate calculated by MSA
successRate = {20100312: 10, 20100909: 12, 20100311: 11}

# Temporary Data Begin
# Host's Daily Period Status within the Meeting Range
dailyPeriod = {
 20100312: 0b1100001111000011, 
 20100909: 0b1100001111100011, 
 20100311: 0b1100001111110011,
}

# Meeting Length
meetingLen = 2

# Preferred Period
preferredPeriod = 0b1000000000000011
# Temporary Data End
"""
getSuccessRate():
Calculate success rate with idlenessDict

idlenessList: list of dicts (idlenessDict)
idlenessDict = { 
Date1 : Idleness1 ,
Date2 : Idleness2 ,
 ...} 
of a single invitee 

"""
def getSuccessRate(idlenessList):
    successRate = {}
    n = len(idlenessList)
    for idlenessDict in idlenessList:
        for key in idlenessDict.keys():
            if successRate.has_key(key):
                successRate[key] *= idlenessDict[key]
            else:
                successRate[key] = idlenessDict[key]
    
    valueList = successRate.values()
    minValue = min(valueList)

    k = 1
    if minValue in range(1,1000):
        k = 1
    elif minValue in range(1000,100000):
        k = 10
    elif minValue in range(100000,1000000):
        k = 100
    else:
        k = 1000

    for key in successRate:
        successRate[key] /= k
    return successRate    

def sortSuccessRate(successRate):
    # Sort dictionary elements by success rate
    return sorted(successRate.iteritems(), key = lambda item:item[1], reverse = True)
    
def sortByDate(dailyPeriod):
    return sorted(dailyPeriod.iteritems(), key = lambda item:item[0], reverse = False)

def genEarlyDate(sortedDailyPeriod):
    return sortedDailyPeriod.pop(0), sortedDailyPeriod
    # Pop the first tuple in the list, and return the remaining sortedDailyPeriod

def genDate(sortedSuccessRate):
    return sortedSuccessRate.pop(0), sortedSuccessRate # Pop the first tuple in the list, and return the remaining sortedSuccessRate
    
"""
filterShortPeriod():
Filter (remove) subperiods shorted than mLen from a period
"""
def filterShortPeriod(dperiod, mLen): # modified from countZero()
    # Convert string arguments into integers
    if isinstance(mLen,str):
        mLen = int(mLen)
    if isinstance(dperiod,str):
        dperiod = int(dperiod)
        
    bitToOne = []
    cZero = 0 # Consecutive number of zeroes temporarily counted
    
    for i in range(0,16):
        if (dperiod | DIGIT[i]) == DIGIT[i]:
            cZero = cZero + 1
            bitToOne.append(i)
            if i == range(0,16)[-1] and cZero != 0:
                if cZero < mLen:
                    for b in bitToOne:
                        dperiod = dperiod | (REVERSE - DIGIT[b]) # filter the bits into one
        else:
            if cZero != 0:
                if cZero < mLen:
                    for b in bitToOne:
                        dperiod = dperiod | (REVERSE - DIGIT[b]) # filter the bits into one
                bitToOne = []
            cZero = 0
    return dperiod
"""
getRecomPeriod(): Get Recommended Period
For HIERARCHICAL
"""    
def getRecomPeriod(dailyPeriodHost, mLen, pPeriod, successRate):
    
    # Convert string arguments into integers
    if isinstance(mLen,str):
        mLen = int(mLen)
    if isinstance(pPeriod,str):
        pPeriod = int(pPeriod)
        
    if len(successRate) > 0:
        # If successRate is a dict, sort it
        if isinstance(successRate, DictType):
            sortedSuccessRate = sortSuccessRate(successRate)
        # If not, it means it is already a sorted list of tuples (remsuccessRate)
        else:
            sortedSuccessRate = successRate
        # genDate returns a tuple () with sortedSuccessRate
        # sSR: (gdate,remsuccessRate) # generated date and remaining success rate after popping
        sSR = genDate(sortedSuccessRate)
        gdate = sSR[0] # Popped date
        print gdate
        print dailyPeriodHost
        remsuccessRate = sSR[1] # Remaining success rate with popped date removed
        
        dailyPeriod = dailyPeriodHost[gdate[0]] # Daily Period of the generated date (gdate[0])
        period = pPeriod | dailyPeriod # OR two periods to get common part (1111101111000011)
        period = filterShortPeriod(period, mLen) # Filter the Consecutive Sub-Periods whose length are smaller than the Meeting Length
        date = gdate[0]
        return date,period,remsuccessRate
    else:
        # If successRate (remaining success rate) is empty:
        date = None
        period = None
        return date,period,[]
"""
getEarlyPeriod(): Get Recommended Period (Earliest Period)
For LINEAR_EARLY
"""    
def getEarlyPeriod(dailyPeriodHost, mLen, pPeriod):
    # Convert string arguments into integers
    if isinstance(mLen,str):
        mLen = int(mLen)
    if isinstance(pPeriod,str):
        pPeriod = int(pPeriod)

    if len(dailyPeriodHost) > 0:
        # If dailyPeriodHost is a dict, sort it
        if isinstance(dailyPeriodHost, DictType):
            sortedDailyPeriod = sortByDate(dailyPeriodHost)
        # If not, it means it is already a sorted list of tuples (remdailyPeriod)
        else:
            sortedDailyPeriod = dailyPeriodHost

        # sDP: (gdate,remdailyPeriod) # generated date and remaining daily period after popping
        sDP = genEarlyDate(sortedDailyPeriod)

        gdate = sDP[0] # Popped date
        remdailyPeriod = sDP[1] # Remaining daily period with popped date removed
        #print remdailyPeriod
        
        # Daily Period of the generated date (gdate[1])
        dailyPeriod = gdate[1]
        
        period = pPeriod | dailyPeriod # OR two periods to get common part (1111101111000011)
        period = filterShortPeriod(period, mLen) # Filter the Consecutive Sub-Periods whose length are smaller than the Meeting Length
        
        date = gdate[0]
        return date,period,remdailyPeriod
    else:
        # If dailyPeriodHost (remaining success rate) is empty:
        date = None
        period = None
        return date,period,[]
        
"""
getAvailablePeriod(): Get Available Period by calculating Common Period with the Recommended Period and a user's period

"""
def getAvailablePeriod(date, userID, recomPeriod, mLen):
    
    # Convert string arguments into integers
    if isinstance(mLen,str):
        mLen = int(mLen)
    if isinstance(recomPeriod,str):
        recomPeriod = int(recomPeriod)

    # dayRange has a single date
    #dayRange = []
    #dayRange.append(date)
    fPeriod = fetchPeriod(date, userID)
    
    # Get daily period of this user on this date
    dailyPeriod = fPeriod[0]

    availablePeriod = dailyPeriod | recomPeriod
    
    # Filter short subperiods than mLen
    availablePeriod = filterShortPeriod(availablePeriod, mLen)
    
    if availablePeriod == REVERSE:
        # No Available Period
        return None
    else:
        return availablePeriod

"""
getWAP(): Get the Weighted Available Period (WAP)
Return every WAP in a dict

"""
def getWAP(date,userID,availablePeriod,mLen):
    
    # Convert string arguments into integers
    if isinstance(mLen,str):
        mLen = int(mLen)
    if isinstance(availablePeriod,str):
        availablePeriod = int(availablePeriod)
         
    # (daily_period, preferred_period, best_period)
    fPeriod = fetchPeriod(date, userID)
    
    pPeriod = fPeriod[1]
    bPeriod = fPeriod[2]
    oPeriod = REVERSE - (fPeriod[1] & fPeriod[2])
    
    weight = setWeight(availablePeriod,oPeriod,pPeriod,bPeriod)
    
    WAP = []
    for i in range(0,16):
        if weight[i] and weight[i+mLen-1]:
            mp = DIGIT[i]
            tw = 0 # tw is Total Weight
            for m in range(i,i+mLen):
                mp &= DIGIT[m] # mp is a mLen-long period
                tw += weight[m]
            gw = tw/mLen # gw is General Weight
            WAP.append((mp,gw))
    WAP = dict(WAP)        
    return date,WAP
    
"""
test for getWAP; to be removed soon

""" 
def test(weight,mLen):
    WAP = []
    for i in range(0,16):
        if weight[i] and weight[i+mLen-1]:
            mp = DIGIT[i]
            print bin(mp)
            tw = 0 # tw is Total Weight
            for m in range(i,i+mLen):
                mp &= DIGIT[m] # mp is a mLen-long period
                tw += weight[m]
            gw = tw/mLen # gw is General Weight
            WAP.append((bin(mp),gw))
    WAP = dict(WAP)  
    return WAP   
    
"""
isSubordinate(): Determine whether a subPeriod is subsidiary to a period 
"""
def isSubordinate(subPeriod, period):
    
    rPeriod = subPeriod | period
    if rPeriod == subPeriod:
        return True
    else:
        return False

"""
setWeight(): Set the weight to a period according to periods of different weights
Return a 16-element list (indicating a period), each element being weight
"""
def setWeight(period,oPeriod,pPeriod,bPeriod):
    # Weight value defined
    ORD = 1 # Ordinary
    PRE = 3 # Preferred
    BES = 5 # Best
    weight = []
    for i in range(0,16):
        if (period | DIGIT[i]) == DIGIT[i]:
            if isSubordinate(DIGIT[i], oPeriod):
                weight.append(ORD)
            elif isSubordinate(DIGIT[i], pPeriod):    
                weight.append(PRE) 
            elif isSubordinate(DIGIT[i], bPeriod):    
                weight.append(BES)  
        else:
            weight.append(0) 
    return weight


#WAPList = [{51:1,52:1,53:1,54:1,55:1},{51:1,52:1,53:1,55:1},{51:1,52:1,54:1,55:1}]
"""
getConfirmPeriod()

WAPList is a list of WAPDict
method is conf variables to determine whether the agent asks host to generate Period Confirmation
CONFIRM_METHOD:
method:  PROMPT | AUTO
if method == PROMPT, the agent will call Interact.confirmPeriod
Interact is the class responsible for interacting with host, implemented as a class
"""

def getConfirmPeriod(WAPList, method):
    commonPeriod = getCommonPeriod(WAPList)
    if commonPeriod:
        # If only one Common Period exists
        if len(commonPeriod) == 1:
            return commonPeriod[0]
        # If multiple Common Period exist
        else:
            wap = {}
            
            # Intialize wap with Common Periods and their weight to 1
            # {common1 : 1, common2 : 2}
            for period in commonPeriod:
                wap[period] = 1
            
            # Multiple weight of Common Period in the WAPList (of each agent)
            for period in commonPeriod:
                for waps in WAPList:
                    wap[period] *= waps[period]
            # Sort the wap using sortSuccessRate()
            # into a list tuple
            wap = sortSuccessRate(wap)
                
            if method == "AUTO":    
                # No matter the weight, return the first element
                return wap[0][0]
                
            elif method == "PROMPT":
                # [(period1,weight1),(period1,weight2),...]
                return wap
                
    # If no Common Period exists
    else:
        return None

"""
getCommonPeriod()

WAPList is a list of WAPDict
"""

def getCommonPeriod(WAPList):
    plist = [] # Temporary List
    clist = [] # Temporary List for Common Periods
    cnt = 0 # Counter
    for WAPDict in WAPList:
        for period in WAPDict.keys():
            if cnt == 0:
                plist.append(period)
            elif cnt == 1:
                for p in plist:
                    if p == period:
                        clist.append(period)
            else:
                for p in plist:
                    if p == period:
                        clist.append(period)
        if cnt > 0:
            plist = clist
            clist = []
            
        cnt += 1
    return plist        


if __name__ == "__main__":    
    #resultPeriod = getRecomPeriod(dailyPeriod, 3, preferredPeriod, successRate)
    """
    resultPeriod,rem = getRecomPeriod(dailyPeriod, 2, preferredPeriod, successRate)
    print bin(resultPeriod)
    resultPeriod,rem = getRecomPeriod(dailyPeriod, 2, preferredPeriod, rem)
    print bin(resultPeriod)
    resultPeriod,rem = getRecomPeriod(dailyPeriod, 2, preferredPeriod, rem)
    print bin(resultPeriod)
    print rem
    """
    """
    print sortByDate(dailyPeriod)
    
    resultPeriod,rem = getEarlyPeriod(dailyPeriod, 2, preferredPeriod)
    print bin(resultPeriod)
    resultPeriod,rem = getEarlyPeriod(rem, 2, preferredPeriod)
    print bin(resultPeriod)
    resultPeriod,rem = getEarlyPeriod(rem, 2, preferredPeriod)
    print bin(resultPeriod)
    """
    #print getSuccessRate(idlenessList)
    #WAPList = [{51:2,52:3,53:1,54:1,55:2},{51:3,52:1,53:1,55:2},{51:1,52:3,54:1,55:2}]
    WAPList = [{51:1,52:1,53:1,54:1,55:1},{51:1,52:1,53:1,55:1},{51:1,52:1,54:1,55:1}]
    #WAPList = [{51:1,52:1,53:1,54:1,55:1}]
    #print getCommonPeriod(WAPList)
    #print getCommonPeriod(WAPList)
    #print getConfirmPeriod(WAPList,"AUTO")
    print "ap:",bin(getAvailablePeriod(20120603, 2, 33731, 2))
    print "rp:",bin(33731)
    print "dp:",bin(33075)
    #20120603 33731 2 host
    print getConfirmPeriod(WAPList,'PROMPT')