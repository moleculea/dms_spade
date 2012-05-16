# -*- coding: utf-8 -*-
"""
dbmodel.py
Model program to fetch data from database
"""
import mysql.connector
from dbconfig import Config # dbconfig is for dbconfig.py
config = Config.dbinfo().copy() # Initialization

# Global variables
tb_user_agenda = "user_agenda"      # Table name of user agenda
################################################################
tb_user = "user_spade"              # Table name of user
################################################################
tb_user_invitee = "user_invitee"
fn_daily_period = "daily_period"    # Field name of daily period
fn_preferred_period = "pref_period"
fn_best_period = "best_period"
fn_date = "date"                    # Field name of date
fn_user_id = "user_id"              # Field name of user id
fn_host_id = "host_id"
fn_user_name = "user_name"
fn_invitee_id = "invitee_id"
fn_invitee_status = "invitee_status"

"""
fetchPeriod()

Returns the periods (daily_period, pref_period and best_period) for a single date
"""
def fetchPeriod(date, userID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    """
    tb_user_agenda = "user_agenda"  # Table name of user agenda
    fn_daily_period = "daily_period" # Field name of daily period
    fn_preferred_period = "pref_period"
    fn_best_period = "best_period"
    fn_date = "date" # Field name of date
    fn_user_id = "user_id" # Field name of user id
    """
    """
    SELECT daily_period, pref_period,best_period FROM user_agenda WHERE date = date and user_id = userID
    """

    stdp = "SELECT `%s`,`%s`,`%s` FROM `%s` WHERE `%s`='%s' AND `%s`='%s'"%(fn_daily_period,fn_preferred_period,fn_best_period,tb_user_agenda,fn_date,date,fn_user_id,userID)
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
        
    rows = cursor.fetchall()
    db.close()
    if len(rows) > 0:
        # rows[0]: (daily_period, preferred_period, best_period)
        return rows[0]        
    else:
        # If fetched result is empty,
        # (which means this date does not exists
        # in the table ), return all zero period
        # (which means no agenda is arranged for this date)
        return 0,0,0
    
        #############################################
        # Fetch default pref_period and best_period #
        # from user_config                          #
        # To be implemented in later stage          #
        #############################################

"""
retrieveAgenda():
Generator returns a Daily Period (within the dayRange) at a single time
"""
def retrieveAgenda(dayRange, userID):

    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    """
    tb_user_agenda = "user_agenda"  # Table name of user agenda
    fn_daily_period = "daily_period" # Field name of daily period
    fn_date = "date" # Field name of date
    fn_user_id = "user_id" # Field name of user id
    """
    """
    SELECT daily_period FROM user_agenda WHERE date = date and user_id = userID
    """
    for date in dayRange: 
        stdp = "SELECT `%s` FROM `%s` WHERE `%s`='%s' AND `%s`='%s'"%(fn_daily_period,tb_user_agenda,fn_date,date,fn_user_id,userID)
        cursor.execute(stdp)
        warnings = cursor.fetchwarnings()
        if warnings:
            print warnings
        rows = cursor.fetchall()
        #db.close()
        # If date exists
        if len(rows)>0:
             yield date,rows[0][0] # Yield tuple:(date, daily period)
        # If date does not exist, return all zero period (no agenda arranged)
        else:
            yield date,0
            

    
"""
getAgenda():
Make generator retrieveAgenda()'s return value and its related date into a dictionary

{Date1: Daily_Period1, Date2: Daily_Period2, ...}
"""
def getAgenda(dayRange, userID):
    dailyPeriod = []
    
    for date,dailyperiod in retrieveAgenda(dayRange, userID):
        dailyPeriod.append((date,dailyperiod))
        
    # Convert into dictionary    
    dict(dailyPeriod)
    return dict(dailyPeriod)

"""
retrieveInvitee():
Generator returns a user name at a single time
"""
def retrieveInvitee(userID, sgroup):
    
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    """
    tb_user_invitee = "user_invitee"
    fn_user_id = "user_id"
    fn_host_id = "host_id"
    fn_user_name = "user_name"
    fn_invitee_id = "invitee_id"
    fn_invitee_status = "invitee_status"
    
    
    sgroup=="VIP_INVITEE":
    
    SELECT user_name FROM user INNER JOIN user_invitee ON user.user_id = user_invitee.invitee_id WHERE user_invitee.host_id = userID AND user_invitee.invitee_status = sgroup 
    """
    
    if sgroup=="VIP_INVITEE":
        sgroup = "VIP"
        stiv = "SELECT `%s` FROM `%s` INNER JOIN `%s` ON %s.%s = %s.%s WHERE %s.%s = '%s' AND  %s.%s = '%s'"%(fn_user_name,tb_user,tb_user_invitee,tb_user,fn_user_id,tb_user_invitee,fn_invitee_id,tb_user_invitee,fn_host_id,
        userID,tb_user_invitee,fn_invitee_status,sgroup)
        
    elif sgroup=="ALL_INVITEE":
        stiv = "SELECT `%s` FROM `%s` INNER JOIN `%s` ON %s.%s = %s.%s WHERE %s.%s = '%s'"%(fn_user_name,tb_user,tb_user_invitee,tb_user,fn_user_id,tb_user_invitee,fn_invitee_id,tb_user_invitee,fn_host_id,userID,tb_user_invitee)
        
    elif sgroup=="COMMON_INVITEE":
        sgroup = "VIP"
        stiv = "SELECT `%s` FROM `%s` INNER JOIN `%s` ON %s.%s = %s.%s WHERE %s.%s = '%s' AND  %s.%s <> '%s'"%(fn_user_name,tb_user,tb_user_invitee,tb_user,fn_user_id,tb_user_invitee,fn_invitee_id,tb_user_invitee,fn_host_id,
        userID,tb_user_invitee,fn_invitee_status,sgroup)
    
    cursor.execute(stiv)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    rows = cursor.fetchall()
    #db.close()
    for row in rows:
        yield row[0]

"""
retrieveInviteeList():
Make generator retrieveInvitee()'s return value into a list
"""
def getInviteeList(userID, sgroup):
    inviteeList = []
    # retrieveInvitee() retrieves invitees of this user from database
    for invitee in retrieveInvitee(userID, sgroup):
        inviteeList.append(invitee)
    return inviteeList


# Global variables

tb_meeting = "meeting"
tb_uim = "user_invitee_meeting"
tb_user_invitee = "user_invitee"
tb_meeting_canceled = "meeting_canceled"
tb_meeting_success = "meeting_success"
tb_msa = "msa"
tb_ca = "ca"
tb_user_msa = "user_msa"
tb_user_ca = "user_ca"
tb_message = "message"
tb_meeting_stat = "meeting_stat"
fn_conf_period = "conf_period"
fn_meeting_id = "meeting_id"
fn_host_id = "host_id"
fn_choose_period = "choose_period"
fn_invite = "invite"
fn_accept = "accept"
fn_available = "available"
fn_invitee_id = "invitee_id"
fn_invitee_status = "invitee_status"
fn_stage = "stage"
fn_period = "period"
fn_reason = "reason"
fn_active = "active"
fn_content_id = "content_id"
fn_uri = "uri"
fn_read = "read"
fn_stat_id = "stat_id"
fn_confirm = "confirm"
fn_decline = "decline"
fn_cancel = "cancel"
fn_reschedule = "reschedule"
fn_user_name = "user_name"

"""
Prefix rules:
    * update- : update specific column with value given
    * check- : check and return the value of a single column
    * inspect- : check and return values of multiple columns or the whole table
    * is- : check whether the value of a specific column is True
"""

"""
updateConfPeriod():

Update dms.meeting.conf_period
value: False | period (int)
"""

def updateConfPeriod(meetingID, value):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "UPDATE %s SET %s = '%s' WHERE %s ='%s'"%(tb_meeting, fn_conf_period, 'False', fn_meeting_id, meetingID)
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    db.commit()
    return cursor.rowcount



"""
checkConfPeriod():

Check the value of dms.meeting.conf_period
"""

def checkConfPeriod(meetingID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s FROM %s WHERE %s ='%s'"%(fn_conf_period, tb_meeting, fn_meeting_id, meetingID)
    cursor.execute(stdp)   
    row = cursor.fetchone()
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
            
    if row == None:
        return None
    else:
        return row[0]
    
    
    
"""
updateChoosePeriod()

Update dms.meeting.choose_period to string

"""
    
def updateChoosePeriod(meetingID, value):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "UPDATE %s SET %s = '%s' WHERE %s ='%s'"%(tb_meeting, fn_choose_period, value, fn_meeting_id, meetingID)
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings    
    db.commit()
    return cursor.rowcount

"""
checkInvite():

Check the value of dms.meeting.invite
"""

def checkInvite(meetingID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s FROM %s WHERE %s ='%s'"%(fn_invite, tb_meeting, fn_meeting_id, meetingID)
    cursor.execute(stdp)
    row = cursor.fetchone()
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings    
    if row == None:
        return None
    else:
        return row[0]
    
"""
updateInvite()

Update dms.meeting.invite

"""
    
def updateInvite(meetingID, value):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "UPDATE %s SET %s = '%s' WHERE %s ='%s'"%(tb_meeting, fn_invite, value, fn_meeting_id, meetingID)
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings   
    db.commit()
    return cursor.rowcount



"""
inspectUIM():

Called by MSA.Feedback
Inspect dms.user_invitee_meeting table
"""
def inspectUIM(meetingID, hostID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s,%s FROM %s WHERE %s ='%s' AND %s = '%s' AND %s = '%s'"%(fn_invitee_id,fn_accept,tb_uim,fn_meeting_id,meetingID,fn_host_id,hostID,fn_available,'True')
    #print stdp
    cursor.execute(stdp)
    rows = cursor.fetchall()
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    # List of tuples,e.g. [(invitee_id1,True),(invitee_id2,False),(invitee_id3,NULL)]
    return rows



"""
updateUIMavailable()


"""

def updateUIMavailable(hostID, meetingID, value):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "UPDATE %s SET %s = '%s' WHERE %s ='%s' AND %s ='%s'"%(tb_uim, fn_available, value, fn_meeting_id, meetingID, fn_host_id, hostID )
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings   
    db.commit()
    return cursor.rowcount


"""
isInviteeVIP():

Check whether an Invitee is VIP to a Host
"""   
def isInviteeVIP(hostID,inviteeID): 
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s FROM %s WHERE %s ='%s' AND %s = '%s' "%(fn_invitee_status,tb_user_invitee,fn_host_id,hostID,fn_invitee_id,inviteeID)
    #print stdp
    cursor.execute(stdp)
    row = cursor.fetchone()
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    if row != None:
        if row[0] == "VIP":
            return True
        else:
            return False
    else:
        return None


"""
addMeetingCanceled()

Add a meeting to dms.meeting_canceled
Return number of rows affected
"""    

def addMeetingCanceled(meetingID,hostID,date,period,stage,reason=None):
    if not isMeetingCanceled(meetingID):
        db = mysql.connector.Connect(**config)
        cursor = db.cursor()
        if reason == None:
            stdp = "INSERT INTO %s (%s,%s,%s,%s,%s) VALUES ('%s','%s','%s','%s','%s')"%(tb_meeting_canceled,fn_meeting_id, fn_host_id, fn_date, fn_period, fn_stage, meetingID, hostID, date, period, stage)                                                  
        else:
            stdp = "INSERT INTO %s (%s,%s,%s,%s,%s,%s) VALUES ('%s','%s','%s','%s','%s','%s')"%(tb_meeting_canceled, fn_meeting_id, fn_host_id, fn_date, fn_period, fn_stage, fn_reason, meetingID, hostID, date, period, stage, reason)
        #print stdp
        cursor.execute(stdp)
        warnings = cursor.fetchwarnings()
        if warnings:
            print warnings
        db.commit()
        return cursor.rowcount
    else:
        print "addMeetingCanceled() failed: meeting_id: %s already exists"%(meetingID)
        return None

"""
isMeetingCanceled():

Check whether a meeting is canceled (whether exists in dms.meeting_canceled)
"""   
def isMeetingCanceled(meetingID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT * FROM %s WHERE %s ='%s' "%(tb_meeting_canceled, fn_meeting_id, meetingID)
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    # Return number of rows
    # If meeting exists, return 1
    # else, return 0
    result = cursor.fetchall()
    if len(result)>0:
        return True
    else:
        return False



"""
isMeetingToCancel():

Check whether a meeting is to be canceled (check the value of dms.meeting.cancel)
"""

def checkMeetingToCancel(meetingID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s FROM %s WHERE %s ='%s' "%(fn_cancel, tb_meeting, fn_meeting_id, meetingID)
    cursor.execute(stdp)
    row = cursor.fetchone()
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings    
    if row == None:
        return None
    else:
        return row[0]


"""
addMeetingSuccess()

Add a meeting to dms.meeting_success
Return number of rows affected
"""    

def addMeetingSuccess(meetingID, hostID, confirmDate, confirmPeriod):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "INSERT INTO %s (%s,%s,%s,%s) VALUES ('%s','%s','%s','%s')"%(tb_meeting_success, fn_meeting_id, fn_host_id, fn_date, fn_period, meetingID, hostID, confirmDate, confirmPeriod)         
                                
    cursor.execute(stdp)
    
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
        
    db.commit()
    return cursor.rowcount   



"""
isRescheduled():

Check whether a meeting is rescheduled (whether dms.meeting.reschedule = True)

Called by ALCC

"""   

def isRescheduled(meetingID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s FROM %s WHERE %s ='%s' "%(tb_meeting,fn_reschedule, fn_meeting_id, meetingID)
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    result = cursor.fetchall()
    if len(result) > 0:
        return True
    else:
        return False


"""
refreshMeeting()

Clear important columns into initial default values (those other than initial parameters)

Columns to be cleared:
* conf_period   => NULL
* choose_period => NULL
* invite        => NULL
* cancel        => NULL
* stat_id       => NULL
* reschedule    => NULL

"""

def refreshMeeting(meetingID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    null = 'NULL'
    stdp = "UPDATE %s SET %s = '%s', %s = '%s', %s = '%s', %s = '%s', %s = '%s', %s = '%s' WHERE %s ='%s"%(tb_meeting, fn_conf_period, null, fn_choose_period, null, fn_invite, null, fn_cancel, null, fn_stat_id, null, fn_reschedule, null )
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings   
    db.commit()
    return cursor.rowcount



"""
Add a user to dms.msa

ALCC inspects this table and manipulates the life of agents (register and disregister)
After manipulation ALCC empties table dms.msa, which is normally empty

"""

def addMSA(meetingID,userID,active):
    rowcount = 0
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    # First check whether the userID exists in dms.msa
    stdp = "SELECT * FROM %s WHERE %s ='%s' "%(tb_msa, fn_meeting_id, meetingID)
    #print stdp
    cursor.execute(stdp)
    # If not exists
    result = cursor.fetchall()
    if len(result) == 0:
        stdp = "INSERT INTO %s (%s,%s,%s) VALUES ('%s','%s','%s')"%(tb_msa, fn_meeting_id,  fn_user_id, fn_active, meetingID, userID, active)   
        #print stdp
        cursor.execute(stdp)
        warnings = cursor.fetchwarnings()
        if warnings:
            print warnings
        db.commit()
        rowcount = cursor.rowcount
    return rowcount


"""
checkMSA()

Check dms.msa
For ALCC inspection

"""

def checkMSA():
    
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT * FROM %s "%(tb_msa)
    cursor.execute(stdp)
    
    warnings = cursor.fetchwarnings()   
    if warnings:
        print warnings
        
    result = cursor.fetchall()    
    if len(result) > 0:
        return result
    else:
        return None

"""
emptyMSA()

Empty (truncate) dms.msa
For ALCC inspection

"""

def emptyMSA():
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "TRUNCATE TABLE %s "%(tb_msa)
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()   
    if warnings:
        print warnings
    db.commit()
    #return cursor.rowcount # always 0
"""
checkCA()

Check dms.ca
For ALCC inspection

"""

def checkCA():
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT * FROM %s "%(tb_ca)
    #print stdp
    cursor.execute(stdp)
    
    warnings = cursor.fetchwarnings()   
    if warnings:
        print warnings

    result = cursor.fetchall()    
    if len(result) > 0:
        return result
    else:
        return None
"""
emptyCA()

Empty (truncate) dms.ca
For ALCC inspectionmsa

"""

def emptyCA():
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "TRUNCATE TABLE %s "%(tb_ca)
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()   
    if warnings:
        print warnings
    db.commit()
    #return cursor.rowcount # always 0


"""
updateUserMSA()

Update dms.user_msa.active


"""

def updateUserMSA(userID, active):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "UPDATE %s SET %s = '%s' WHERE %s = '%s'"%(tb_user_msa, fn_active, active, fn_user_id,userID)   
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    db.commit()
    rowcount = cursor.rowcount
    return rowcount



"""
updateUserCA()

Update dms.user_ca.active


"""

def updateUserCA(userID):
    
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "UPDATE %s SET %s = '%s' WHERE %s = '%s'"%(tb_user_ca, fn_active, active, fn_user_id,userID)   
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    db.commit()
    rowcount = cursor.rowcount
    return rowcount


"""
getAcceptUserCA()

Get dms.user_ca.accept of a user, which is the default config for whether accepting invitation

"""


def getAcceptUserCA(userID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s FROM %s WHERE %s = '%s'"%(fn_accept, tb_user_ca, fn_user_id, userID)
    cursor.execute(stdp)
    
    row = cursor.fetchone()
    
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
            
    if row == None:
        return None
    else:
        return row[0]

"""
addMeetingStat():

Add meeting stat to dms.meeting_stat and then add stat_id to dms.meeting.stat_id
"""

def addMeetingStat(meetingID,confirmDate,confirmPeriod, confNum, declNum):
    
    # First add stat to dms.meeting_stat
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "INSERT INTO %s (%s,%s,%s,%s,%s) VALUES ('%s','%s','%s','%s','%s')"%(tb_meeting_stat,fn_meeting_id,fn_date,fn_conf_period,fn_confirm,fn_decline,meetingID,confirmDate,confirmPeriod,confNum,declNum)       
    cursor.execute(stdp)
    db.commit()
    rowcount = cursor.rowcount
    
    if rowcount > 0:
        # Then add stat_id to dms.meeting
        statID = cursor.lastrowid
        stdp = "INSERT INTO %s (%s) VALUES ('%s')"%(tb_meeting,fn_stat_id,statID)
        cursor.execute(stdp)
        db.commit()
        rowcount = cursor.rowcount
        return rowcount
    
    else:
        return 0


"""
getMeeting()

Get the initial paramters and other values of a meeting

result:

* [0] meeting_id 
* [1] host_id
* [2] length
* [3] day_range
* [4] pref
* [5] topic
* [6] location
* [7] search_bias
* [8] delimit
* [9] conf_method

"""

def getMeeting(meetingID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT * FROM %s WHERE %s = '%s'"%(tb_meeting, fn_meeting_id, meetingID )
    cursor.execute(stdp)
    
    result = cursor.fetchone()
    
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
            
    if row == None:
        return None
    else:
        return result



"""
addMessage():

Add a message to dms.message

"""

def addMessage(userID,contentID,uri,read):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "INSERT INTO %s (%s,%s,%s,%s) VALUES ('%s','%s','%s','%s')"%(tb_message, fn_user_id, fn_content_id, fn_uri, fn_read, userID,contentID,uri,read)                                                  
    #print stdp
    cursor.execute(stdp)
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    db.commit()
    rowcount = cursor.rowcount
    return rowcount   


"""
addManyMessage():

Add multiple messages to dms.message

Sequence is a list of 4-tuple
"""
def addManyMessage(sequence):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    st = "INSERT INTO %s (%s,%s,%s,%s) VALUES"%(tb_message, fn_user_id, fn_content_id, fn_uri, fn_read)                                                  
    #print stdp
    cursor.executemany(st+"('%s','%s','%s','%s')",sequence)    
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
    db.commit()
    rowcount = cursor.rowcount
    return rowcount   

"""
getUsername()

Get the user_name with userID

"""

def getUsername(userID):
    
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    stdp = "SELECT %s FROM %s WHERE %s = '%s'"%(fn_user_name, tb_user, fn_user_id, userID)
    cursor.execute(stdp)   
    row = cursor.fetchone()
    warnings = cursor.fetchwarnings()
    if warnings:
        print warnings
            
    if row == None:
        return None
    else:
        return row[0]



if __name__ == "__main__":
    dayRange = [20120603,20120604]
    userID = 1
    #print getAgenda(dayRange,userID)
    #print fetchPeriod(20120601,1)
    #print checkConfPeriod('1')
    #pass
    #print isInviteeVIP('23', '15')
    #addMeetingCanceled('10','2',20120603,541,'INVT')
    #print isMeetingCanceled('1')
    #addMSA('14','26','False')
    #print addMeetingStat(1, 20120304, 431, 3, 4)
    #print emptyCA()
    print updateUserMSA('1',True)