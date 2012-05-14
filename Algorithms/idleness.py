# -*- coding: utf-8 -*-
"""
idleness.py

"""
from math import *
from DIGIT import *

from dbmodel import * # Reference: getAverageIdleness()

def countZero(number):
    tZero = 0 # Total number of zeroes counted
    cZero = 0 # Consecutive number of zeroes temporarily counted
    lenIdlePeriod = []
    for i in range(0,16):
        if (number | DIGIT[i]) == DIGIT[i]:
            tZero = tZero + 1
            cZero = cZero + 1
            if i == range(0,16)[-1] and cZero != 0:
                lenIdlePeriod.append(cZero)
        else:
            if cZero != 0:
                lenIdlePeriod.append(cZero)
            cZero = 0
    #print "Zero(es): ", tZero
    return lenIdlePeriod # list for the length of Idle Period, e.g. [3,2,6] (there are three Idle Periods on this day, the length of each being 3, 2 and 6 respectively)  

def idle(lenIdlePeriod, mLen): 
    idleness = 0
    for length in lenIdlePeriod:
        if (length - mLen + 1) >= 1:
            idleness += length - mLen + 1
        else:
            continue 
    #print "Idleness: ", idleness
    return idleness
        
"""
getIdleness(): Return idleness for a single day

"""
def getIdleness(dailyPeriod, mLen): # Argument: Daily Period and Meeting Length
    
    # Convert string arguments into integers
    if isinstance(dailyPeriod,str):
        dailyPeriod = int(dailyPeriod)
    if isinstance(mLen,str):
        mLen = int(mLen)

    lenIdlePeriod = countZero(dailyPeriod)
    idleness = idle(lenIdlePeriod, mLen) # Calculate idleness with length of Idle Period and Meeting Length
    return idleness

"""
getRangeIdleness()
Return a idlenessDict
idlenessDict = { date1:idleness1 , date2:idleness2 , ...}
"""

def getRangeIdleness(dayRange, mLen, userID):
    idlenessDict = {}
    
    # Convert string arguments into integers
    if isinstance(mLen,str):
        mLen = int(mLen)
    dayRange = listEl2Int(dayRange)

    for dailyperiod in retrieveAgenda(dayRange, userID):
        date = int(dailyperiod[0])
        idleness = getIdleness(dailyperiod[1], mLen)
        idlenessDict[date] = idleness
        
    return idlenessDict
"""
getAverageIdleness(): 
Return average idleness within the dayRange

"""
def getAverageIdleness(dayRange, userID, mlen):
    sumIdleness = 0
    days = len(dayRange) # Number of days in dayRange
    for dailyperiod in retrieveAgenda(dayRange, userID): # retriveAgenda() query database to get this user's Daily Periods within the dayRange
        sumIdleness += getIdleness(dailyperiod[1], mlen) # sumIdleness is the sum of idleness for each day within the dayRange
    averageIdleness = sumIdleness/days # Average Idleness
    return averageIdleness
    
"""
Other global functions for DMS.py

"""

"""
getSearchBias(): Determine the Search Bias with method and delimit specified by Host

"""
def getSearchBias(dayRange, method, delimit=None, averageidle=None): 
# method = DAY_LENGTH | AVERAGE_IDLE
# delimit = delimit_days | delimit_idleness
# averageidle = averageIdleness

    searchBias = "LINEAR_EARLY" # Default search bias
    
    if method == "DAY_LENGTH":
        if delimit == None:
            delimit = 5 # Number of days
        if len(dayRange) < delimit:
            searchBias = "LINEAR_EARLY"
        else:
            searchBias = "HIERARCHICAL"
    elif method == "AVERAGE_IDLE":
        if delimit == None:
            delimit = 5 # Idleness
        if averageidle < delimit:
            searchBias = "LINEAR_EARLY"
        else:
            searchBias = "HIERARCHICAL"
    return searchBias

"""
getStatistics(): For MSA.Invite

stat is a list of 5-tuples: (date, confPeriod, mLen, result, sender)

"""
def getStatistics(stat):
    confNum = 0
    declNum = 0
    for s in stat:
        if s[3] == "confirmed":
            confNum += 1
        elif s[3] == "declined":
            declNum += 1
    numstat = (confNum, declNum)
    
    # (confirmed_number, declined_number)
    return numstat

"""

getStatInvitee(): For MSA.Invite

Return inviteeList (list of invitees who are confirmed to be invited)

"""
def getStatInvitee(stat):
    inviteeList = []
    for s in stat:
        if s[3] == "confirmed":
            inviteeList.append(s[4])
 
    # Return list of invitees
    return inviteeList
    
"""
listEl2Str()
Convert each element of a list into string

e.g.:
[3601,3842] ==> ['3601','3842']
"""
def listEl2Str(list):
    return [str(element) for element in list]

"""
listEl2Int()
Convert each element of a list into integer if it is string numb

e.g.:
['3601','3842'] ==> [3601,3842]
"""
def listEl2Int(list):
    return [int(element) for element in list]

if __name__ == "__main__":
    """
    binaryDailyPeriod = 0b1110001111101000
    intDailyPeriod = int(binaryDailyPeriod)
    print intDailyPeriod
    print getIdleness(intDailyPeriod,3)
    """
    """
    for digit in DIGIT:
        print digit,bin(digit)
        print bin(65535-digit)
    """     
    dayRange = ['20120601', '20120602', '20120603']
    #print getAverageIdleness([20120601,20120602],1,2)
    mLen = '2'
    userID = 2
    #print getAverageIdleness(dayRange, mLen, userID)
    date = 20120601
    result = 'confirmed'
    confPeriod = 232
    sender = 'foobar'
    stat = [(date, confPeriod, mLen, result, sender),(date, confPeriod, mLen, 'declined', sender)]
    print getStatistics(stat)