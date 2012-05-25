# -*- coding: utf-8 -*-
import sys
sys.path.append('/home/anshichao/spade/')

"""
Agent Life Cycle Control (ALCC)

Main portal
"""
import spade
import time,os
import DMS

from Algorithms.dbmodel import *
from Algorithms.idleness import *

# Global variables
hostname = '127.0.0.1'
password = 'secret'

"""
msaControl()

MSA Life Control

"""

# Global variables
# Instantiated agents living in SPADE
# {username1: instance1, username2: instance2 }
livingMSA = {}
livingCA = {}
# Meetings (id) currently being scheduled
# {username1: meeting_id1, username2: meeting_id2 }
meeting = {}

"""
msaControl()

Check dms.msa and empty it

"""
def msaControl():
    # Fetch result from dms.user_msa
    print "ALCC --> msaControl(): Checking database dms.msa for MSA/meeting request"
    result = checkMSA()

    if result:
        # Analyze and take actions against the fetched result if result is not None
        
        # row = ( id , meeting_id , user_id , active )
        for row in result:
            meetingID = row[1]
            userID = row[2]
            active = row[3]
            
            # If active is True, start MSA with meeting parameters
            if active == 'True':
                
                # user is username
                user = getUsername(userID)
                
                # Check whether this user exists in livingMSA
                if user in livingMSA.keys():
                    print "ALCC --> msaControl(): The MSA of %s is already living in MAS"%(user)
                    break
                
                else:
                    # Instantiate and start MSA
                    msa = startMSA(userID, user, meetingID)
                    
                    # Append the instance to the dictionary
                    livingMSA[user] = msa
                    
                    # Append the meeting id to the dictionary
                    meeting[user] = meetingID
                    
                    # Update dms.user_msa.active of this user to True
                    ### Already True
                    #updateUserMSA(userID, True)
                    
            # If active is False, shutdown MSA 
            if active == 'False': 
                shutdownAgent(user,'MSA')
                
        # Empty dms.user_msa
        emptyMSA()
        
    else:
        print "ALCC --> msaControl(): No request to start/shutdown MSA"
                  

"""
caControl()

Check dms.ca and empty it

"""

def caControl():
    # Fetch result from dms.user_ca
    print "ALCC --> msaControl(): Checking database dms.ca for CA request"
    result = checkCA()
    
    if result:
        # row = ( id , user_id , active )
        for row in result:
            userID = row[1]
            active = row[2]
            
            if active == 'True':
                
                # user is username
                user = getUsername(userID)
                
                # Check this user exists in livingCA
                if user in livingCA.keys():
                    print "ALCC --> caControl(): The CA of %s is already living in MAS"%(user)
                    break
                
                else:

                    # Instantiate and start CA with accept as default config for accepting invitations
                    ca = startCA(userID,user)
                    
                    # Append the instance to the dictionary
                    livingCA[user] = ca
                    
                    # Update dms.user_ca.active of this user to True
                    ### Already True
                    #updateUserCA(userID, True)
                    
            # If active is False, shutdown CA
            if active == 'False': 
                shutdownAgent(user,userID,'CA')

        # Empty dms.user_ca
        emptyCA()
        
    else:
        print "ALCC --> caControl(): No request to start/shutdown CA"
        
"""
reschedule()

For every running MSAs and their meetings:
    Check dms.meeting.reschedule
    If True, shutdown the agent and refresh the table

"""
def reschedule():
    
    if meeting.items():
        # Inspect dms.meeting.reschdule
        # meeting_id in meeting (dictionary)
        for user, meetingID in meeting.items():
            print "ALCC --> reschedule(): Checking dms.meeting.reschedule for reschedule request"
            result = isRescheduled(meetingID)
            print result
            # If dms.meeting.reschedule is True
            if result:
                # Get the instance of this user's MSA
                msa = livingMSA[user]
                
                # Shutdown the MSA
                msa._shutdown()
                
                # Refresh dms.meeting
                refreshMeeting(meetingID)
            else:
                print "ALCC --> reschedule(): No request to reschedule"
                
    else:
        print "ALCC --> reschedule(): No running MSA/meeting; reschedule is needless"
        
    # ***** Finish ****** 
    # (User reinput the initial meeting parameter at Django and
    # import them into dms.meeting)
    # When clicking start, Django add the user to dms.msa, and then ACLL starts MSA

"""
startMSA()

Instantiate MSA, initialize initial parameters and start it

"""    

def startMSA(userID, username, meetingID):
    print "ACLL: --> startMSA(): Ready to start MSA for " + username
    # Structure arguments used in MSA.initialize()
    # user,dayRange,pPeriod,mLen,mt,conf
    user = {}
    dayRange = []
    pPeriod = 0
    mLen = 1
    mt = {}
    conf = {}
    
    result = getMeeting(meetingID)
    #print result
    """
    result:
    
    * [0] meeting_id 
    * [1] host_id
    * [2] length
    * [3] day_range ("date1;date2;date3;...")
    * [4] pref
    * [5] topic
    * [6] location
    * [7] search_bias
    * [8] delimit
    * [9] conf_method
    
    """
    # Structure user
    user['NAME'] = username
    user['ID'] = userID
    
    # Struct dayRange
    dayRange = result[3].split(';')
    # Convert element into integer
    dayRange = listEl2Int(dayRange)
    
    # Struct length
    mLen = int(result[2])
    
    # Struct pref
    pPeriod = int(result[4])
    
    # Struct mt
    mt['ID'] = meetingID
    
    # Struct conf
    conf = {}
    conf['SEARCH_BIAS'] = {}
    conf['CONFIRM_METHOD'] = {}
    
    conf['SEARCH_BIAS']['METHOD'] = result[7]
    conf['SEARCH_BIAS']['DELIMIT'] = result[8]
    conf['CONFIRM_METHOD']['METHOD_NAME'] = result[9]
    print conf
    # Instantiate MSA
    #print "%s.msa@%s"%(user, hostname)
    
    msa = DMS.MSA("%s.msa@%s"%(username, hostname), password) 
    #print msa
    # Initialize parameters
    msa.initialize(user,dayRange,pPeriod,mLen,mt,conf)
    msa.start()
    print "ACLL: --> startMSA(): MSA for %s started"%(username)
    
"""
startCA()

Instantiate CA, initialize initial parameters and start it

"""        
def startCA(userID,username):
    
    print "ACLL: --> startMSA(): Ready to start CA for " + username
    # Instantiate CA
    ca = DMS.CA("%s.ca@%s"%(username, hostname), password) 
    user = {'NAME':username,'ID':userID}
    
    # Initialize parameters
    ca.initialize(user)
    ca.start()
    print "ACLL: --> startMSA(): CA for %s started"%(username)
    
"""
shutdownAgent()

Shutdown an agent; type is MSA | CA

"""        
def shutdownAgent(user,userID,type):
    
    if type == 'MSA':

        if user not in livingMSA.keys():
            print "ACLL: --> shutdownAgent(): This user %s' MSA is not running in MAS"%(user)
            
        else:
            # Getting the MSA instance of this user saved earlier in livingMSA dict
            # msa is an instance of MSA running in MAS
            
            msa = livingMSA[user]
            msa._shutdown()
            
            # Delete this user's MSA from livingMSA
            del livingMSA[user]
            # Delete this user's meeting meeting
            del meeting[user]

            # Update dms.user_ca.active of this user to False
            updateUserMSA(userID,False)
            
    if type == 'CA':
        if user not in livingCA.keys():
            print "ACLL: --> shutdownAgent(): This user %s' CA is not running in MAS"%(user)
            
        else:
            # Getting the MSA instance of this user saved earlier in livingMSA dict
            # ca is an instance of CA running in MAS
            ca = livingCA[user]
            ca._shutdown()
            # Delete this user's CA from livingCA
            del livingCA[user]
            
            # Update dms.user_msa.active of this user to False
            updateUserCA(userID,False)
"""
main()

Periodically execute:

  * reschedule()
  * caControl()
  * msaControl()
  
"""
def main(interval):
    counter = 0
    # Periodically execute msaControl() and caControl()
    print "Agent Life Cycle Control (ALCC) starting..."
    print "ALCC --> main(): Running"
    

    while True:
        
        reschedule()
        caControl()
        msaControl()
        
        counter += 1
        print "ALCC --> main(): Cycle(s): %s"%(counter)
        
        msaList = ', '.join(livingMSA.keys())
        caList = ', '.join(livingCA.keys())
        
        print "ALCC --> main(): Running MSA(s): %s"%(msaList)
        print "ALCC --> main(): Running CA(s): %s"%(caList)
        
        time.sleep(interval)
        
"""
Main portal of DMS

"""
if __name__ == "__main__":
    
    # Interval of loop
    interval = 2
    try:
        main(interval)
    # Control-C to exit
    except KeyboardInterrupt:
        exit()
    