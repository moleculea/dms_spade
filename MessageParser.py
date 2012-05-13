# -*- coding: utf-8 -*-
"""
MessageParser
"""
import sys
sys.path.append('/home/anshichao/spade/')

from spade.SL0Parser import *

"""
SL0ParseIdleness(): For MSA

content:
    "((idleness 
        :value (set
            (20120304 5)
            (20120305 6)
            (20120306 3)
        )
    ))"
"""
def SL0ParseIdleness(content):
    p = SL0Parser()
    msg = p.parse(content)
    idlenessDict = []
    
    for element in msg.idleness.value.set:
        idlenessDict.append((int(element[0]),int(element[1][0])))
    idlenessDict = dict(idlenessDict)
    return idlenessDict
    # {20120304:5, 20120305:6, 20120306:3}


"""
SL0ParseWAP(): For MSA

content:
    "((wap 
		:date 20120311
        :value (set
            (548 3)
            (468 2)
            (421 4)
        )
    ))"

""" 
def SL0ParseWAP(content):
    p = SL0Parser()
    msg = p.parse(content)
    date = msg.wap.date
    WAPDict = []
    if msg.wap.value[0] != 'none':
        for element in msg.wap.value.set:
            WAPDict.append((int(element[0]),int(element[1][0])))
        WAPDict = dict(WAPDict)    
        return int(date[0]),WAPDict
        # {Period1 : 2, Period2 :3, Period3: 1, ...}
    else:
        return int(date[0]),None

        
"""
SL0ParseIdleReq(): For CA
:content
    "((day_range
        :value (set 20120311 20120312)
        :mlen 3
        :sender msa_username
    ))"

"""
def SL0ParseIdleReq(content):
    p = SL0Parser()
    msg = p.parse(content)
    sender = msg.day_range.sender
    mLen = msg.day_range.mlen
    dayRange = []

    for element in msg.day_range.value.set:
        dayRange.append(int(element))
        
    # (['20120601','20120602'],'2','msa_username')
    return dayRange,int(mLen[0]),sender[0]

    
"""
SL0ParseRecPeriod(): For CA
Parse Recommended Period
:content
        "((period
            :date 20120311
            :value 548
            :mlen 3
            :sender username_foo
         ))
        "
"""
def SL0ParseRecPeriod(content):
    p = SL0Parser()
    msg = p.parse(content)
    date = msg.period.date
    recomPeriod = msg.period.value
    mLen = msg.period.mlen
    sender = msg.period.sender
    
    return (int(date[0]), int(recomPeriod[0]), int(mLen[0]), sender[0])
    
    
"""
SL0ParseConfPeriod(): For CA
Parse Confirmed Period
:content
        "((period
            :date 20120311
            :value 548
            :mlen 3
            :sender username_foo
         ))
        "
"""    
def SL0ParseConfPeriod(content):
    p = SL0Parser()
    msg = p.parse(content)
    date = msg.period.date
    confPeriod = msg.period.value
    mLen = msg.period.mlen
    sender = msg.period.sender
    
    return (int(date[0]), int(confPeriod[0]), int(mLen[0]), sender[0])
"""
SL0ParseStat(): For MSA

Parse Replies to Confirmed Period (REPLY_CONF_PERIOD content)
                        
:content
    "((period 
        :date 20120311
        :value 501
        :mlen 3
        :result declined
        :sender ca_username
    ))"

"""
def SL0ParseStat(content):
    p = SL0Parser()
    msg = p.parse(content)
    date = msg.period.date
    confPeriod = msg.period.value
    mLen = msg.period.mlen
    result = msg.period.result
    sender = msg.period.sender
    #print mLen
    return (int(date[0]), int(confPeriod[0]), int(mLen[0]), result[0], sender[0])

if __name__ == "__main__":
    content ="""
((period :date 20120603 :value 62463 :mLen 2 :result confirmed :sender vip1))     
"""

    print content
    print SL0ParseStat(content)
