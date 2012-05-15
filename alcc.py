# -*- coding: utf-8 -*-
"""
Agent Life Cycle Control (ALCC)

Main portal
"""
import spade
import time
import DMS

from Algorithms.dbmodel import *

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
    result = checkMSA()
    # Empty dms.user_msa
    emptyMSA()
    
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
                
                # Check this user exists in livingMSA
                if user in livingMSA.keys():
                    print "The MSA of %s is already living in MAS"%(user)
                    break
                
                else:
                    # Instantiate and start MSA
                    msa = startMSA(userID, meetingID)
                    # Append the instance to the dictionary
                    livingMSA[user] = msa
                    # Append the meeting id to the dictionary
                    meeting[user] = meetingID
                    # Update dms.user_msa.active of this user to True
                    updateUserMSA(userID, True)
                    
                    
"""
caControl()

Check dms.ca and empty it

"""

def caControl():
    # Fetch result from dms.user_ca
    result = checkCA()
    # Empty dms.user_ca
    emptyCA()
    
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
                    print "The CA of %s is already living in MAS"%(user)
                    break
                
                else:

                    # Instantiate and start CA with accept as default config for accepting invitations
                    ca = startCA(userID)
                    # Append the instance to the dictionary
                    livingCA[user] = ca
                    # Update dms.user_msa.active of this user to True
                    updateUserCA(userID,True)

"""
reschedule()

Check dms.meeting.reschedule
If True, shutdown the agent and refresh the table

"""
def reschedule(meetingID):

    # Inspect dms.meeting.reschdule
    # meeting_id in meeting (dictionary)
    for user, meetingID in meeting.items():
        result = isRescheduled(meetingID)
        
        # If dms.meeting.reschedule is True
        if result:
            # Get the instance of this user's MSA
            msa = livingMSA[user]
            
            # Shutdown the MSA
            msa._shutdown()
            
            # Refresh dms.meeting
            refreshMeeting(meetingID)
    
    
    # ***** Finish ****** 
    # (User reinput the initial meeting parameter at Django and
    # import them into dms.meeting)
    # When clicking start, Django add the user to dms.msa, and then ACLL starts MSA
    

def startMSA(userID, meetingID):
    # Structure arguments used in MSA.initialize()
    # user,dayRange,pPeriod,mLen,mt,conf
    user = {}
    dayRange = []
    pPeriod = 0
    mLen = 1
    mt = {}
    conf = {}

    result = getMeeting(meetingID)
    username = getUsername(userID)
    
    # ...
    # ...
    # msa = DMS.MSA(username)
    # msa.initialize(user,dayRange,pPeriod,mLen,mt,conf)
    # msa.start()
    
def startCA(user):
    pass

def shutdownAgent():
    pass


"""
Periodically execute:
  * reschedule()
  * caControl()
  * msaControl()
  
"""
def main():
    counter = 0
    # Periodically execute msaControl() and caControl()
    print "Agent Life Cycle Control (ALCC) starting..."
    print "ALCC running"
    while True:
        
        reschedule()
        caControl()
        msaControl()
        counter += 1
        print "ALCC cycle(s): %s"%(counter)
        time.sleep(1)
        

if __name__ == "__main__":
    pass