# -*- coding: utf-8 -*-
"""
dbmodel.py
Model program to fetch data from database
"""
import mysql.connector
from dbconfig import Config # dbconfig is for dbconfig.py
config = Config.dbinfo().copy() # Initialization

"""
fetchPeriod()

Returns the periods (daily_period, pref_period and best_period) for a single date
"""
def fetchPeriod(date, userID):
    db = mysql.connector.Connect(**config)
    cursor = db.cursor()
    
    tb_user_agenda = "user_agenda"  # Table name of user agenda
    fn_daily_period = "daily_period" # Field name of daily period
    fn_preferred_period = "pref_period"
    fn_best_period = "best_period"
    fn_date = "date" # Field name of date
    fn_user_id = "user_id" # Field name of user id
    
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

    tb_user_agenda = "user_agenda"  # Table name of user agenda
    fn_daily_period = "daily_period" # Field name of daily period
    fn_date = "date" # Field name of date
    fn_user_id = "user_id" # Field name of user id
    
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
    
    tb_user_invitee = "user_invitee"
    tb_user = "user"
    fn_user_id = "user_id"
    fn_host_id = "host_id"
    fn_user_name = "user_name"
    fn_invitee_id = "invitee_id"
    fn_invitee_status = "invitee_status"
    
    """
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

if __name__ == "__main__":
    dayRange = [20120603,20120604]
    userID = 1
    print getAgenda(dayRange,userID)
    print fetchPeriod(20120601,1)
    #pass
