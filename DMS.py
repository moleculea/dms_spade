# -*- coding: utf-8 -*-
import sys
sys.path.append('/home/anshichao/spade/')

import spade
import time
import types
from spade.logic import * 
from MessageParser import * 

# Algorithms
from Algorithms.period import *
from Algorithms.idleness import *
from Algorithms.dbmodel import *
from Algorithms.DIGIT import *

# DEBUG
import pdb

# Global variables
hostname = "127.0.0.1"

"""
class MSA:
(Agent Class)
Meeting Scheduling Agent (MSA) classes:

"""
class MSA(spade.bdi.BDIAgent):

    """
    initialize() initializes variables for this agent to avoid overwriting __init__()
    initialize() can be called before the built-in MSA._setup()
    """
    def initialize(self,user,dayRange,pPeriod,mLen,mt,conf):
            
            # Agent-wide variables
            # Variables that can be accessed through self.myAgent.var
            
            self.user = user         # User data (dict) {'ID':'USER_ID','NAME':'USER_NAME'}
            self.dayRange = dayRange # Day Range (list) list of dates [20120314,20120315]
            self.pPeriod = pPeriod   # Preferred Period (specified by Host)
            self.mLen = mLen         # Meeting Length (int) hours of meeting period
            self.mt = mt             # Meeting data (dict) {'ID':'MEETING_ID'}
            self.conf = conf         # Configuration variables (dict) passed from django view level specification
            
            # Other variables used AMONG behaviours
            self.allInviteeNum = 0
            self.vipInviteeNum = 0
    """
    Overwrite askBelieve() so that it returns True instead of {} (no substitution for true query)   
    """
    def askBelieve(self, sentence): 
        if isinstance(sentence,types.StringType): 
            r = self.kb.ask(expr(sentence)) 
        else: 
            r = self.kb.ask(sentence) 
        if r == {}:
            return True
        else:
            return r
  
    def setReceiverList(self,inviteeList):
        receivers = []
        for invitee in inviteeList:
            #print "%s.ca"%invitee
            receiver = spade.AID.aid(name="%s.ca@%s"%(invitee,hostname),addresses=["xmpp://%s.ca@%s"%(invitee,hostname)])
            receivers.append(receiver)
        return receivers
    
    """
    MSA.scheduleFailed()
    Called when a schedule fails
    """
    def scheduleFailed(self):
        
        # Shut down the agent (disregister agent from AMS)
        #self.myAgent.stop()## ALCC is responsible for agent's life
        # Call interact.failed to wait for user's decision
        meetingID = self.myAgent.mt['ID']
        userID = self.myAgent.user['ID']
        print "000000000000000000000000"
        print meetingID
        interact = Interact(meetingID)
        print "%%%%%%%%%%%%%%%"
        interact.failed()
        print "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    
    def toConfirmPeriod(self,value):
        meetingID = self.myAgent.mt['ID']
        interact = Interact(meetingID)
        # Call Interact.toConfirmPeriod()
        confirmPeriod = interact.toConfirmPeriod(value)
        return confirmPeriod
    
    """
    ### Behaviour
    
    MSA.Config
    
    """
    class Config(spade.Behaviour.OneShotBehaviour):

        def onStart(self):
            print self.myAgent.getName(),"-->MSA.Config.onStart(): starting MSA Configuration"
            
            self.userID = self.myAgent.user['ID']
            self.dayRange = self.myAgent.dayRange
            self.conf = self.myAgent.conf
            self.mLen = self.myAgent.mLen
            """ 
            conf:
            {
            'SEARCH_BIAS': 
                {
                'METHOD': 'METHOD_NAME', # (AVERAGE_IDLE | DAY_LENGTH)
                'DELIMIT': 'DELIMIT_VALUE',
                },
                
            'CONFIRM_METHOD': 'METHOD_NAME', # (PROMPT | AUTO)
            }
            """
            time.sleep(2)
        def _process(self):

            # method is an element in conf for deciding search bias
            method = self.conf['SEARCH_BIAS']['METHOD']
            delimit = self.conf['SEARCH_BIAS']['DELIMIT']
            userID = self.userID
            mLen = self.mLen
            dayRange = self.dayRange
            
            searchBias = "LINEAR_EARLY" # Default search bias
            #print self.myAgent.askBelieve("REQUEST_IDLENESS")
            
            #print searchBias
            print self.myAgent.getName(),"-->MSA.Config._process(): Search bias decision method => %s"%(method)
            
            # Search bias decision method: AVERAGE_IDLE
            if method == 'AVERAGE_IDLE':
                ##### VALIDATED BRANCH #####
                averageIdleness = getAverageIdleness(dayRange, userID, mLen) 
                searchBias = getSearchBias(dayRange, method, delimit, averageidle=averageIdleness)
                
            # Search bias decision method: DAY_LENGTH
            elif method == 'DAY_LENGTH':
                ##### VALIDATED BRANCH #####
                searchBias = getSearchBias(dayRange, method, delimit, averageidle=None) 
            
            print self.myAgent.getName(),"-->MSA.Config._process(): searchBias => %s"%(searchBias)
                
            # Search bias: LINEAR_EARLY | HIERARCHICAL
            ############################################
            # Once search bias is determined,          #
            # it will NOT be changed for the whole     #
            # scheduling process unless reschedule,    #
            # because MSA.Config is OneShotBehaviour   #
            ############################################
            if searchBias == 'LINEAR_EARLY':
                # Get dailyPeriodHost for initial usage in LINEAR_EARLY
                # dailyPeriodHost is a dict of Daily Periods within the dayRange
                self.myAgent.dailyPeriodHost = getAgenda(dayRange, userID)
                print self.myAgent.getName(),"-->MSA.Config._process(): getting dailyPeriodHost (LINEAR_EARLY) for the first time"
                
                self.myAgent.addBelieve("LINEAR_EARLY")
                print self.myAgent.getName(),"-->MSA.Config._process(): addBeilieve => LINEAR_EARLY"
                self.myAgent.addBelieve("YIELD_PERIOD")
                # Unblock GeneratePeriod behaviour
                # Then the process goes to ( LINEAR_EARLY && YIELD_PERIOD ) branch
                print self.myAgent.getName(),"-->MSA.Config._process(): addBeilieve => YIELD_PERIOD"
                
            elif searchBias == 'HIERARCHICAL':
                ##### VALIDATED BRANCH #####
                self.myAgent.addBelieve("HIERARCHICAL")
                print self.myAgent.getName(),"-->MSA.Config._process(): addBeilieve => HIERARCHICAL"
                self.myAgent.addBelieve("REQUEST_IDLENESS")
                # Unblock RequestIdleness behaviour
                print self.myAgent.getName(),"-->MSA.Config._process(): addBeilieve => REQUEST_IDLENESS"
                
        def onEnd(self):
            
            # Agent configuration finished
            print self.myAgent.getName(),"-->MSA.Config.onEnd(): MSA configuration complete"
    """
    ### Behaviour
    
    MSA.RequestIdleness
    
    Branches:
        * REQUEST_IDLENESS (send):
            ==>: WAITING_FOR_IDLENESS
    
    """        

    class RequestIdleness(spade.Behaviour.Behaviour):
    
        def onStart(self):
            print self.myAgent.getName(),"-->MSA.RequestIdleness.onStart(): starting RequestIdleness"
            
            # Interval of loop (seconds)
            self.sleep = 1
            
            userID = self.myAgent.user['ID']
            # sgroup (status group): ALL_INVITEE | VIP_INVITEE | COMMON_INVITEE
            sgroup = "ALL_INVITEE"
            
            # Initialize inviteeList as a list to get invitee name from generator retrieveInvitee()


            inviteeList = getInviteeList(userID, sgroup)
            #inviteeList = ['vip1','vip2','vip3','ci1','ci2','ci3']
            
            # allInviteeNum is the number of invitees in "ALL_INVITEE"
            # self.myAgent.allInviteeNum is number of all invitees in host's invitee list
            self.myAgent.allInviteeNum = len(inviteeList)
            print self.myAgent.getName(),"-->MSA.RequestIdleness.onStart(): MSA.allInviteeNum set"
             
            # setReceiverList sets receiver list for this agent
            # setReceiverList() returns a list of spade.AID.aid

            self.receiverList = self.myAgent.setReceiverList(inviteeList)

            # Save dayRange,username into self from myAgent
            self.dayRange = self.myAgent.dayRange
            self.username = self.myAgent.user['NAME']
            self.mLen = self.myAgent.mLen
            
            print self.myAgent.getName(),"-->MSA.RequestIdleness.onStart(): RequestIdleness started"
            
        def _process(self):

            # HIERARCHICAL
            if self.myAgent.askBelieve("REQUEST_IDLENESS"): 
                ##### VALIDATED BRANCH #####
                
                print self.myAgent.getName(),"-->MSA.RequestIdleness._process(): REQUEST_IDLENESS"
                
                # Instantiate request message
                self.request_msg = spade.ACLMessage.ACLMessage() 
                
                # Create message structure and content
                self.request_msg.setPerformative("inform")
                self.request_msg.setOntology("REQUEST_IDLENESS")
                self.request_msg.setLanguage("fipa-sl")
                
                # days = "DATE1 DATE2 DATE3 ...", separated by space

                # Convert every elemnt in days into string
                days = listEl2Str(self.dayRange)
                days = " ".join(days)

                sender = self.username
                mLen = self.mLen
                """
                   "((day_range
                        :value (set 20120311 20120312)
                        :mlen 3
                        :sender msa_username
                    ))"
                """
                
                content = "((day_range :value (set %s) :mlen %s :sender %s))"%(days,mLen,sender)
                print self.myAgent.getName(),"-->MSA.RequestIdleness._process(): REQUEST_IDLENESS message content: \n %s"%(content)
                self.request_msg.setContent(content) 
                
                # Add all invitees to receivers for this message
                self.request_msg.receivers = self.receiverList 
                receiverNum = len(self.receiverList )
                
                # Send the request message
                self.myAgent.send(self.request_msg) 
                print self.myAgent.getName(),"-->MSA.RequestIdleness._process(): Sending REQUEST_IDLENESS message to %s invitees"%(receiverNum)
                
                # Unblock WAITING_FOR_IDLENESS branch in GeneratePeriod
                self.myAgent.addBelieve("WAITING_FOR_IDLENESS")
                print self.myAgent.getName(),"-->MSA.RequestIdleness._process(): addBeilieve => WAITING_FOR_IDLENESS"
                
                # Remove HIERARCHICAL so that this branch of _process() will not be executed
                self.myAgent.removeBelieve("REQUEST_IDLENESS") 
                print self.myAgent.getName(),"-->MSA.RequestIdleness._process(): removeBelieve => REQUEST_IDLENESS"
                
            # Interval of loop
            time.sleep(self.sleep)
    """
    ### Behaviour
    
    MSA.GeneratePeriod
    
    Branches:
        * WAITING_FOR_IDLENESS (receive): an implicit HIERARCHICAL branch
            ==>: HIERARCHICAL && YIELD_PERIOD
            
        * LINEAR_EARLY && YIELD_PERIOD (send):
            ==>: LINEAR_EARLY && YIELD_PERIOD | WAITING_FOR_WAP | scheduleFailed()
            
        * HIERARCHICAL && YIELD_PERIOD (send):
            ==>: HIERARCHICAL && YIELD_PERIOD | WAITING_FOR_WAP | scheduleFailed()
            
    """
    class GeneratePeriod(spade.Behaviour.Behaviour):

        def onStart(self):
            print self.myAgent.getName(),"-->MSA.GeneratePeriod.onStart(): starting GeneratePeriod"
            
            # Interval of loop (seconds)
            self.sleep = 1
            self.mLen = self.myAgent.mLen
            self.dayRange = self.myAgent.dayRange
            self.userID = self.myAgent.user['ID']
            self.pPeriod = self.myAgent.pPeriod
            
            userID = self.myAgent.user['ID']
            sgroup = "VIP_INVITEE"
    
            inviteeList = getInviteeList(userID, sgroup)
            #inviteeList = ['vip1','vip2','vip3']
            
            # Set receiver list to only VIP invitees
            self.receiverList = self.myAgent.setReceiverList(inviteeList) 
            
            # self.myAgent.vipInviteeNum is number of VIP invitees in host's invitee list
            self.myAgent.vipInviteeNum = len(self.receiverList)
            print self.myAgent.getName(),"-->MSA.GeneratePeriod.onStart(): MSA.vipInviteeNum set"
            
        def _process(self):

            #print "MSA.GeneratePeriod"
            # Receive REPLY_IDLENESS messages
            # HIERARCHICAL
            if self.myAgent.askBelieve("WAITING_FOR_IDLENESS"):
                ##### VALIDATED BRANCH #####
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): WAITING_FOR_IDLENESS"
                
                # Receiving block time
                BLOCK_TIME = 5
                
                # senderNum is the number of senders
                # which is the number of messages to receive
                self.senderNum = self.myAgent.allInviteeNum
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): getting allInviteeNum"
                self.idlenessList = []
                
                # Initialize number of messages received
                self.receivedNum = 0
                self.receive_msg = None
                
                # Receive the first message
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): ready to receive first REPLY_IDLENESS message"
                # if the no message is received for 5 seconds, message receiving will stop
                self.receive_msg = self._receive(True, BLOCK_TIME)
                if self.receive_msg:
                    self.receivedNum += 1
                else:
                    if self.receivedNum == 0:
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): no message received in %s seconds, seems all invitees are not active"%(BLOCK_TIME)

                # While there is an incoming message
                # Wait until all messages under this template (ontology: REPLY_IDLENESS) have been received

                while self.receive_msg: 

                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): receiving REPLY_IDLENESS message, message number: " + str(self.receivedNum)
                    
                    ######## Processing message in the loop: START ########
                    
                    # Single message's content received
                    single_content = self.receive_msg.content 

                    # Use SPADE's SL0 parser to parse the message content (date and idleness) into a dict
                    # idlenessDict = { 
                    # Date1 : Idleness1 ,
                    # Date2 : Idleness2 ,
                    # ...}
                    idlenessDict = SL0ParseIdleness(single_content) 
                    #DEBUG#print idlenessDict
                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): processing REPLY_IDLENESS message, message number: " + str(self.receivedNum)
                    
                    # Get all invitees's idlenessDict and
                    # save in string[] self.idleness
                    self.idlenessList.append(idlenessDict) 
                    ######## Processing message in the loop: END ########
     
                    if self.receivedNum == self.senderNum:
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): having received sufficient messages, number of messages received: " + str(self.receivedNum)
                        break
                    else:
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): having received only %s messages; there are still %s messages to receive"%(self.receivedNum,self.senderNum-self.receivedNum)
                    
                    self.receive_msg = self._receive(True, BLOCK_TIME)
                    
                    if self.receive_msg:
                        self.receivedNum += 1 # Self incrementing by 1
                
                # If number of received messages is less than senders
                """
                #######################
                # IGNORE THIS CASE!!! #
                #######################
                """
                if self.receivedNum < self.senderNum:
                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): receiving only %s REPLY_IDLENESS messages, less than number of senders: %s"%(self.receivedNum,self.senderNum)
                    
                # If there is no message left (means all idleness have been received)
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): receiving REPLY_IDLENESS messages complete"
                
                # Calculate success rate using getSuccessRate() with idlenessList as argument
                # successRate at this time is a dictionary unsorted
                successRate = getSuccessRate(self.idlenessList)
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): calculating success rate"
                
                dayRange = self.dayRange
                userID = self.userID

                # dailyPeriodHost is a dict of Daily Periods within the dayRange
                dailyPeriodHost = getAgenda(dayRange, userID)
                
                # Save dailyPeriodHost for (HIERARCHICAL & YIELD_PERIOD) branch
                self.dailyPeriodHost = dailyPeriodHost

                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): getting host's dailyPeriodHost (HIERARCHICAL) for the first time"
                mLen = self.mLen
                pPeriod = self.pPeriod
                
                # Get Recommended Period for the first time
                # Then process goes to YIELD_PERIOD under HIERARCHICAL
                self.recomDate,self.recomPeriod,self.sortedSuccessRate = getRecomPeriod(dailyPeriodHost, mLen, pPeriod, successRate)
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): getting Recommended Period (HIERARCHICAL) for the first time"
                
                # Block idleness receiving
                self.myAgent.removeBelieve("WAITING_FOR_IDLENESS")
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): removeBelieve => WAITING_FOR_IDLENESS"
                
                # Ready to yield Recommended Period
                # Then the process goes to ( HIERARCHICAL && YIELD_PERIOD ) branch
                self.myAgent.addBelieve("YIELD_PERIOD") 
                print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): addBelieve => YIELD_PERIOD"
                
            """
            # LINEAR_EARLY
            # LINEAR_EARLY && YIELD_PERIOD
            
            # This branch gets dailyPeriodHost for the first from MSA.Config: LINEAR_EARLY, which is saved in self.myAgent.dailyPeriodHost
            # This branch gets dailyPeriodHost from self.myAgent.dailyPeriodHost in every loop
            # This branch pops dailyPeriodHost in every loop and saves dailyPeriodHost into self.myAgent.dailyPeriodHost for the next loop
            # This branch gets self.recomPeriod in every loop by calculating using getEarlyPeriod(dailyPeriodHost, mLen, pPeriod)
            # This branch gets variables mLen and pPeriod from self.myAgent in every loop
            
            """
            
            if self.myAgent.askBelieve("LINEAR_EARLY"):
                if self.myAgent.askBelieve("YIELD_PERIOD"):
                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY && YIELD_PERIOD"
                    
                    # Initialize dailyPeriodHost from self.myAgent
                    dailyPeriodHost = self.myAgent.dailyPeriodHost
                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: re-assign dailyPeriodHost (LINEAR_EARLY) for the first time"
                    
                    # Initialize other variables from agent
                    mLen = self.myAgent.mLen
                    pPeriod = self.myAgent.pPeriod
                    
                    # Get Recommended Period (Early Period) 
                    self.recomDate,self.recomPeriod,sortedDailyPeriod = getEarlyPeriod(dailyPeriodHost, mLen, pPeriod)
                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: getting Recommended Period via getEarlyPeriod()"
                    
                    # Overwrite dailyPeriodHost with the remaining sorted Daily Period for next loop
                    self.myAgent.dailyPeriodHost = sortedDailyPeriod
                    # Save self.recomDate into self.myAgent for MSA.ConfirmPeriod
                    self.myAgent.recomDate = self.recomDate
                    
                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: overwriting dailyPeriodHost with remaining sortedDailyPeriodHost"
                    
                    # If Recommended Period (Early Period) exists 
                    # (this means dailyPeriodHost(sortedDailyPeriod) is not empty)
                    if self.recomPeriod:
                        ##### VALIDATED BRANCH #####
                        if self.recomPeriod != REVERSE:
                            # Instantiate message
                            self.msg = spade.ACLMessage.ACLMessage()
                            
                            # Add VIP invitee to receivers
                            self.msg.receivers = self.receiverList 
                            # create message structure and content
                            
                            sender = self.myAgent.user['NAME']
                            mLen = self.mLen
                            
                             # Create Recommended Period in FIPA-SL0 format
                            recom_period_content = "((period :date %s :value %s :mlen %s :sender %s))"%(self.recomDate,self.recomPeriod,mLen,sender)
                            
                            self.msg.setPerformative("inform")   
                            self.msg.setOntology("RECOMMEND_PERIOD")
                            self.msg.setLanguage("fipa-sl") 
                            self.msg.setContent(recom_period_content)
                            
                            # Send the message                        
                            self.myAgent.send(self.msg)
                            print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: sending RECOMMEND_PERIOD message"
                        else:
                            print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: Recommended Period is invalid (REVERSE), going directly to the next loop for another date"
                            #DEBUG#print self.recomDate
                            #DEBUG#print bin(self.recomPeriod)

                    # If self.recomPeriod = None 
                    # (means dailyPeriodHost(sortedDailyPeriod) is already empty)
                    else: 
                        ##### VALIDATED BRANCH #####
                        # This time of schedule failed
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: schedule failed"
                        self.myAgent.removeBelieve("YIELD_PERIOD")
                        self.myAgent.scheduleFailed()
                        """
                        Shutdown the agent (testing stage)
                        """
                        
                        #print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: shutting down the agent"
                        #self.myAgent._shutdown()

                    """
                    # self.recomPeriod != REVERSE, block this branch (LINEAR_EARLY && YIELD_PERIOD)
                    # self.recomPeriod == REVERSE, directly goes to the next loop of this branch
                    """
                    if self.recomPeriod and self.recomPeriod != REVERSE:  
                        ##### VALIDATED BRANCH #####
                        # Block yielding Recommended Period
                        self.myAgent.removeBelieve("YIELD_PERIOD")    
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: removeBelieve => YIELD_PERIOD"
                        # Unblock WAITING_FOR_WAP
                        self.myAgent.addBelieve("WAITING_FOR_WAP")
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): LINEAR_EARLY: addBelieve => WAITING_FOR_WAP"
                    
            """
            # HIERARCHICAL        
            # HIERARCHICAL && YIELD_PERIOD
            
            # This branch gets self.recomPeriod for the first time (first loop) from WAITING_FOR_IDLENESS branch
            # This branch gets self.dailyPeriodHost for the first time from WAITING_FOR_IDLENESS branch, and uses self.dailyPeriodHost in the rest loops
            # This branch saves self.recomPeriod for the next loop by calculating in the end of every loop
            # This branch pops self.sortedSuccessRate in every loop and keeps the dailyPeriodHost unchanged
             
            
            """
            if self.myAgent.askBelieve("HIERARCHICAL"):
                if self.myAgent.askBelieve("YIELD_PERIOD"):
                    ##### VALIDATED BRANCH #####
                    
                    print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL && YIELD_PERIOD"
                    
                    # If Recommended Period exists 
                    # (this means successRate(sortedSuccessRate) is not empty)
                    if self.recomPeriod: 
                        """
                        if self.recomPeriod == REVERSE # (ALL ONE)
                        # It means even though there is still remaining days to be processed, 
                        # the current day is not available for the host himself.
                        # The behaviour (_process()) should continue to the next loop of this branch 
                        
                        """
                        # If self.recomPeriod != REVERSE
                        # This means valid self.recomPeriod (Recommended Period) exists
                        #DEBUG#print bin(self.recomPeriod)
                        if self.recomPeriod != REVERSE:
                            ##### VALIDATED BRANCH #####
                            print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL: valid Recommended Period exists"
                            self.msg = spade.ACLMessage.ACLMessage() # instantiate message
                            
                            # Add VIP invitee to receivers
                            self.msg.receivers = self.receiverList 
                            mLen = self.mLen
                            
                            sender = self.myAgent.user['NAME']
                            
                             # Create Recommended Period in FIPA-SL0 format
                            recom_period_content = "((period :date %s :value %s :mlen %s :sender %s))"%(self.recomDate, self.recomPeriod, mLen, sender)
                            
                            #DEBUG#print recom_period_content
                            # Save the current recomDate into self.myAgent for MSA.ConfirmPeriod
                            self.myAgent.recomDate = self.recomDate

                            self.msg.setPerformative("inform")   
                            self.msg.setOntology("RECOMMEND_PERIOD")
                            self.msg.setLanguage("fipa-sl") 
                            self.msg.setContent(recom_period_content)
                            
                            # Send the message                        
                            self.myAgent.send(self.msg)
                            print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL: sending RECOMMEND_PERIOD message"
                            
                        else:
                            print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL: Recommended Period is invalid (REVERSE), going directly to the next loop for another date"
                    
                    
                    # If self.recomPeriod = None 
                    # (means sortedSuccessRate is already empty)
                    else:
                        
                        ##### VALIDATED BRANCH ##### 
                        # This time of schedule failed
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL: schedule failed"

                        self.myAgent.removeBelieve("YIELD_PERIOD")
                        self.myAgent.scheduleFailed()

                        """
                        Shutdown the agent (testing stage)
                        """
                        #print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL: shutting down the agent"
                        #self.myAgent._shutdown()
                        
                    """
                    # self.recomPeriod must not be None
                    # self.recomPeriod != REVERSE, block this branch (HIERARCHICAL && YIELD_PERIOD)
                    # self.recomPeriod == REVERSE, directly goes to the next loop of this branch
                    """
                    if self.recomPeriod and self.recomPeriod != REVERSE:  
                        ##### VALIDATED BRANCH #####  
                        # Block yielding Recommended Period
                        self.myAgent.removeBelieve("YIELD_PERIOD") 
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL: removeBelieve => YIELD_PERIOD"
                        
                        # Unblock WAITING_FOR_WAP
                        self.myAgent.addBelieve("WAITING_FOR_WAP")     
                        print self.myAgent.getName(),"-->MSA.GeneratePeriod._process(): HIERARCHICAL: addBelieve => WAITING_FOR_WAP"
                        
                    """
                    Preparing for the next loop
                    """
                    sortedSuccessRate = self.sortedSuccessRate

                    #DEBUG#print self.recomDate,self.recomPeriod,self.sortedSuccessRate
                    # Get and save recomPeriod for the next loop
                    self.recomDate,self.recomPeriod,self.sortedSuccessRate = getRecomPeriod(self.dailyPeriodHost, self.mLen, self.pPeriod, sortedSuccessRate)

            time.sleep(self.sleep)
    """
    ### Behaviour
    
    MSA.ConfirmPeriod
    
    Branches:
        * WAITING_FOR_WAP (receive): 
            ==>: YIELD_PERIOD | CONFIRM_PERIOD
        * CONFIRM_PERIOD (send):
            ==>: YIELD_PERIOD | STATISTICS
        
    """       
    class ConfirmPeriod(spade.Behaviour.Behaviour):
    
        def onStart(self):
            
            print self.myAgent.getName(),"-->MSA.ConfirmPeriod.onStart(): starting ConfirmPeriod"
            
            # Interval of loop (seconds)
            self.sleep = 1
            userID = self.myAgent.user['ID']
            sgroup = "ALL_INVITEE"
            
            """
            FST : ALL_INVITEE
            """
            inviteeList = getInviteeList(userID, sgroup)
            #inviteeList = ['vip1','vip2','vip3','ci1','ci2','ci3']
            
            # Set receiver list to all invitees
            self.receiverList = self.myAgent.setReceiverList(inviteeList) 
            
        def _process(self):
            
            """
            # WAITING_FOR_WAP
            """

            if self.myAgent.askBelieve("WAITING_FOR_WAP"):
                ##### VALIDATED BRANCH #####
                
                print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): WAITING_FOR_WAP"
                # Receiving block time
                BLOCK_TIME = 5
                
                self.receive_msg = None
                self.receivedNum = 0
                
                # senderNum is the number of senders
                # which is the number of messages to receive
                self.senderNum = self.myAgent.vipInviteeNum
                print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): getting vipInviteeNum"
                print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): ready to receive WAP messages"
                
                self.receive_msg = self._receive(True, BLOCK_TIME)
                self.WAPList = []
                
                if self.receive_msg:
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): receiving first WAP message"
                    self.receivedNum += 1
                else:
                    if self.receivedNum == 0:
                        print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): no message received in %s seconds, seems all invitees are not active"%(BLOCK_TIME)
                
                # If there is incoming messages
                while self.receive_msg: 
 
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): receiving WAP message, message number: " + str(self.receivedNum) + "(this message could be possibly not of the valid date)"
                    
                    ######## Processing message in the loop: START ########
                    
                    # Content received
                    single_content = self.receive_msg.content 
                    # Use SPADE's SL0 parser to parse the message content into a list(dict)
                    date,single_WAP = SL0ParseWAP(single_content)

                    #DEBUG#print date,single_WAP
                    
                    
                    ####################################################################
                    # Only if date is the current recomDate
                    # Sub-branches: single_WAP != None and single_WAP == None
                    #
                    # * single_WAP != None : append single_WAP to WAPList
                    # * single_WAP == None : break out the loop and go back to YIELD_PERIOD
                    #
                    # Because this branch (WAITING_FOR_WAP) received all WAP messages no matter what the content's date is
                    # This branch may receive WAP messages of previous (invalid) dates (ignored and not immediately received  
                    # when breaking out for a VIP has no Available Period )
                    #
                    # self.myAgent.recomDate is updated in YIELD_PERIOD branch, so it is the current scheduling date at all times
                    ####################################################################
                    if date == self.myAgent.recomDate:
                        # single_WAP != None
                        if single_WAP:
                        ##### VALIDATED BRANCH #####   
                                self.WAPList.append(single_WAP)
                                print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): this VIP's WAP is valid, append it to the WAPList and continue"
                        
                        # If any VIP invitee has no Available Period
                        # (If single_WAP == None)
                        else:
                        ##### VALIDATED BRANCH #####
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): a VIP invitee has no Available Period, going back to YIELD_PERIOD branch to get another date"
                            #DEBUG#print "DATE: ",date
                            # Block WAITING_FOR_WAP
                            self.myAgent.removeBelieve("WAITING_FOR_WAP")
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): removeBelieve => WAITING_FOR_WAP"
                            # Go back to YIELD_PERIOD to yield next Recommended Period
                            self.myAgent.addBelieve("YIELD_PERIOD")
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): addBelieve => YIELD_PERIOD"

                            # Terminate the loop
                            break
                    
                    else:
                        print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): previous invalid date (not the current scheduling date)"
                        # Subtract self.receivedNum by 1, because this message is not of the vaild date
                        self.receivedNum -= 1
                        
                    ######## Processing message in the loop: END ########
                    
                    if self.receivedNum == self.senderNum:
                        print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): having received sufficient WAP messages, number of messages received: " + str(self.receivedNum)
                        break
                    else:
                        print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): having received only %s messages; there are still %s messages to receive"%(self.receivedNum,self.senderNum-self.receivedNum)                                            
                    
                    
                    self.receive_msg = self._receive(True, BLOCK_TIME)
                    
                    if self.receive_msg:
                        self.receivedNum += 1 # Self incrementing by 1
                
                if self.receivedNum < self.senderNum:
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): receiving only %s WAP messages, less than number of senders: %s"%(self.receivedNum,self.senderNum)
                
                # This "if not" avoids execution when process breaks from the previous "while" (while self.receive_msg:)
                if not self.myAgent.askBelieve("YIELD_PERIOD"):
                    
                    self.confirmPeriod = None
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process():  WAP receiving complete"
                    
                   
                    # If WAPList contains at least one WAPDict
                    ### If WAPList is empty (not received any messages from previous codes),
                    ### Then pass this branch and CONFIRM_PERIOD branch to the next loop
                    if self.receivedNum > 0:        
                        method = self.myAgent.conf['CONFIRM_METHOD']
                        
                        if method == "AUTO":
                            #DEBUG#print self.WAPList
                            self.confirmPeriod = getConfirmPeriod(self.WAPList, method)
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): automatically getting Confirmed Period using getConfirmPeriod() from WAP list"
                        
                        ###########################  
                        # method == 'PROMPT'      #      
                        # Debug in the last stage #
                        ###########################     
                        elif method == 'PROMPT':
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): waiting for the host to determine the Confirmed Period"
                            
                            # wPeriods is a list of 2-tuple 
                            # [(period1,weight2),(period2,weight2),...]
                            wPeriods = getConfirmPeriod(self.WAPList, method)
                            
                            # Wait until user choose a period
                            # If user does not give response within specific time
                            # The system chooses a Confirmed Period instead
                            self.confirmPeriod = self.myAgent.toConfirmPeriod(wPeriods)
     
                        # If no Common Period exists
                        if not self.confirmPeriod:
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): no Common Period exists, going back to YIELD_PERIOD branch to get another date"
                            self.myAgent.removeBelieve("WAITING_FOR_WAP")
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): removeBelieve => WAITING_FOR_WAP"
                            
                            # Go back to YIELD_PERIOD to yield next Recommended Period
                            self.myAgent.addBelieve("YIELD_PERIOD")
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): addBelieve => YIELD_PERIOD"
                                
                        # If Common Period exists
                        else:
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): Common Period exits, going to CONFIRM_PERIOD branch"
                            # Block WAP receiving
                            self.myAgent.removeBelieve("WAITING_FOR_WAP") 
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): removeBelieve => WAITING_FOR_WAP"
                            
                            # Unblock CONFIRM_PERIOD
                            self.myAgent.addBelieve("CONFIRM_PERIOD")
                            print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): addBelieve => CONFIRM_PERIOD"
                       
            if self.myAgent.askBelieve("CONFIRM_PERIOD"):
                print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): CONFIRM_PERIOD"   
                 
                # If Common Period exists, ready to send Confirmed Period
                if self.confirmPeriod:
                    # Save Confirmed Period and Date into self.myAgent
                    # This is for use in STATISTICS when calling Interact.toInvite()
                    self.myAgent.confirmPeriod = self.confirmPeriod
                    self.myAgent.confirmDate = self.myAgent.recomDate
                    
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): CONFIRM_PERIOD: Common Period exists, ready to send Confirmed Period"

                    # Instantiate message
                    self.msg = spade.ACLMessage.ACLMessage()
                    
                    # Add all invitee to receivers
                    self.msg.receivers = self.receiverList

                    sender = self.myAgent.user['NAME']
                    mLen = self.myAgent.mLen
                    
                    # Create message structure and content
                    confirm_period_content = "((period :date %s :value %s :mlen %s :sender %s ))"%(self.myAgent.recomDate,self.confirmPeriod,mLen,sender)
                    #DEBUG#print confirm_period_content
                    
                    self.msg.setPerformative("inform")   
                    self.msg.setOntology("CONFIRM_PERIOD")
                    self.msg.setLanguage("fipa-sl") 
                    self.msg.setContent(confirm_period_content)    
                    
                    self.myAgent.send(self.msg)
                    
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): CONFIRM_PERIOD: sending CONFIRM_PERIOD message"
                    
                    self.myAgent.removeBelieve("CONFIRM_PERIOD")
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): removeBelieve => CONFIRM_PERIOD"
                    
                    self.myAgent.addBelieve("STATISTICS")
                    print self.myAgent.getName(),"-->MSA.ConfirmPeriod._process(): addBelieve => STATISTICS"
                    
                """    
                # If no Common Period exists 
                # self.confirmPeriod = None
                else: 
                    # Traverse back to GeneratePeriod to yield next available date's period
                    self.myAgent.addBelieve("YIELD_PERIOD") 
                    # Block Confirm Period
                    self.myAgent.removeBelieve("CONFIRM_PERIOD") 
                """    

            time.sleep(self.sleep)
                
    """
    ### Behaviour
    
    MSA.Invite
    
    Branches:
        * STATISTICS
    """            

    class Invite(spade.Behaviour.Behaviour): 

        def onStart(self):
            self.sleep = 1
            self.onetime = False
            print self.myAgent.getName(),"-->MSA.Invite.onStart(): starting Invite"
            #self.receiverList = self.myAgent.setReceiverList(inviteeList) 
            
        def _process(self):

            if self.myAgent.askBelieve("STATISTICS"):
                ##### VALIDATED BRANCH #####
                print self.myAgent.getName(),"-->MSA.Invite._process(): STATISTICS"
                # Receiving block time
                BLOCK_TIME = 5
                print self.myAgent.getName(),"-->MSA.Invite._process(): start to receive REPLY_CONFIRM_PERIOD messages"
                
                self.receive_msg = None
                self.receivedNum = 0
                
                # senderNum is the number of senders
                # which is the number of messages to receive
                self.senderNum = self.myAgent.allInviteeNum
                
                self.receive_msg = self._receive(True, BLOCK_TIME)
                self.stat = []
                
                if self.receive_msg:
                    print self.myAgent.getName(),"-->MSA.Invite._process(): receiving first REPLY_CONFIRM_PERIOD message"
                    self.receivedNum += 1
                else:
                    if self.receivedNum == 0:
                        print self.myAgent.getName(),"-->MSA.Invite._process(): no message received in %s seconds, seems all invitees are not active"%(BLOCK_TIME)                
                
                # If there is incoming messages
                while self.receive_msg: 
                    print self.myAgent.getName(),"-->MSA.Invite._process(): receiving REPLY_CONFIRM_PERIOD message, message number: " + str(self.receivedNum)
                    
                    ######## Processing message in the loop: START ########
                    
                    # Content received
                    single_content = self.receive_msg.content
                    #DEBUG#print single_content
                    # Use SPADE's SL0 parser to parse the message content into a list
                    single_stat = SL0ParseStat(single_content)
                    # single_stat = (date, confPeriod, mLen, result, sender)
                    self.stat.append(single_stat)
                    
                    ######## Processing message in the loop: END ########                    

                    if self.receivedNum == self.senderNum:
                        print self.myAgent.getName(),"-->MSA.Invite._process(): having received sufficient REPLY_CONFIRM_PERIOD messages, number of messages received: " + str(self.receivedNum)
                        break
                    else:
                        print self.myAgent.getName(),"-->MSA.Invite._process(): having received only %s messages; there are still %s messages to receive"%(self.receivedNum,self.senderNum-self.receivedNum) 
                        
                    self.receive_msg = self._receive(True, BLOCK_TIME)
                    
                    if self.receive_msg:
                        self.receivedNum += 1
                
                if self.receivedNum < self.senderNum:
                    print self.myAgent.getName(),"-->MSA.Invite._process(): receiving only %s REPLY_CONFIRM_PERIOD messages, less than number of senders: %s"%(self.receivedNum,self.senderNum)
                            
                print " ***** CONFIRMED PERIOD *****"
                print self.stat
                print bin(self.stat[0][1])
                print "----------FST ENDS------------"        
                """
                FST
                
                ## STOP HERE !!!
                """           
                #pdb.set_trace()         
                
                # Get the statistics of meeting attendees   
                # getStatistics in idleness.py
                statistics = getStatistics(self.stat) 

                # Variables used in the following codes
                meetingID = self.myAgent.mt['ID']
                userID = self.myAgent.user['ID']
                hostID = userID
                confirmPeriod = self.myAgent.confirmPeriod
                confirmDate = self.myAgent.confirmDate
                
                # Add the stat to dms.meeitng_stat
                confNum, declNum = statistics
                #addMeetingStat(meetingID, confirmDate, confirmPeriod, confNum, declNum)
                addMeetingStat(meetingID, confirmDate, confirmPeriod, confNum, declNum)
                
                # Get invitee IDs who confirmed the Confirmed Periods
                confList = getConfInviteeID(self.stat)
                
                # Get invitee IDs who declined the Confirmed Periods
                declList = getDeclInviteeID(self.stat)
                
                # Update user_invitee_meeting.available
                for c_id in confList:
                    inviteeID = c_id
                    updateUIMavailable(hostID, inviteeID, meetingID, True)
                    
                for d_id in declList:
                    inviteeID = d_id
                    updateUIMavailable(hostID, inviteeID, meetingID, False)
                
                # Add the meeting to dms.meeting_success
                addMeetingSuccess(meetingID, hostID, confirmDate, confirmPeriod)
                
                # Call Interact.toInvite() to indefinitely wait for host's response
                interact = Interact(meetingID, userID, confirmPeriod, confirmDate)
                result = interact.toInvite()
                
                """
                # Instantiate message
                self.msg = spade.ACLMessage.ACLMessage() 
                # Add all invitee to receivers
                self.msg.receivers = self.receiverList 
                sender = self.myAgent.user['NAME']
                meeting_id = self.myAgent.mt['ID']
                
                # Create message structure and content
                # create Confirmed Period in FIPA-SL0 format
                invitation_content = "((invitation :id %s :sender %s))"%(meeting_id,sender)

                self.msg.setPerformative("inform")   
                self.msg.setOntology("INVITATION")
                self.msg.setLanguage("fipa-sl") 
                self.msg.setContent(invitation_content)
              
                self.myAgent.send(self.msg)
                print self.myAgent.getName(),"-->MSA.Invite._process(): sending INVITATION message"
                """
                
                # If result is True,
                # means the host choose to send invitation
                if result:
                    # Unblock START_FEEDBACK
                    self.myAgent.addBelieve("START_FEEDBACK")
                    print self.myAgent.getName(),"-->MSA.Invite._process(): addBelieve => START_FEEDBACK"
                    # Block STATISTICS        
                    self.myAgent.removeBelieve("STATISTICS")
                    print self.myAgent.getName(),"-->MSA.Invite._process(): removeBelieve => STATISTICS"
                
                else:
                    # Block START_FEEDBACK        
                    self.myAgent.removeBelieve("START_FEEDBACK")
                    print self.myAgent.getName(),"-->MSA.Invite._process(): removeBelieve => START_FEEDBACK"
            
            else:
                pass
            
            time.sleep(self.sleep)     
    
    """
    ### Behaviour
    
    MSA.Feedback
    
    Branches:
        * START_FEEDBACK
    """           
        
    class Feedback(spade.Behaviour.Behaviour):
    
        def onStart(self):
            self.sleep = 1
            print self.myAgent.getName(),"-->MSA.Feedback.onStart(): starting Feedback"  
            self.meetingID = self.myAgent.mt['ID']
            self.userID = self.myAgent.user['ID']
            
        def _process(self):
            """
            If any VIP Invitee declines the invitation, call Interact.toCancel()
            Query table dms.user_invitee_meeting
            """
            if self.myAgent.askBelieve("START_FEEDBACK"):
                
                # inviteeList: Intermediate list of invitees whose accept == "False"
                # This is an exception list in the loop to avoid repeatedly sending identical system messages
                inviteeList = []
                
                interact = Interact(self.meetingID, self.userID)
                #contentID = 2
                #uri = "" # To be specified
                
                while True:
                    # Periodically fetch result from dms.user_invitee_meeting
                    rows = inspectUIM(self.meetingID,self.userID)
                    
                    # Parse the fetched rows
                    for row in rows:
                        inviteeID = row[0]
                        accept = row[1]
                        
                        if inviteeID not in inviteeList:
                            if accept == "False":
                                # If this invitee is a VIP
                                if isInviteeVIP(self.userID,inviteeID):
                                    inviteeList.append(inviteeID)
                                    #interact._sendMessage(contentID, uri)
                                    interact.toCancel()
                    time.sleep(0.5)    
                            
            time.sleep(self.sleep)                                    
                            

    """
    MSA._setup()  
    
    Built-in initializing
    """
    
    def _setup(self): 
        print self.getName(),"-->MSA._setup(): Agent starting... adding behaviours"  
        
        # Prefix b_: behaviour ; t_: template
        # Add behaviours to the MSA agent
        
        b_config = self.Config()
        b_request_idleness= self.RequestIdleness()
        b_generate_period = self.GeneratePeriod()
        
        # Set template for receiving idleness
        t_receive_idleness = spade.Behaviour.ACLTemplate() 
        t_receive_idleness.setOntology("REPLY_IDLENESS")
        mt_receive_idleness = spade.Behaviour.MessageTemplate(t_receive_idleness)
        

        b_confirm_period = self.ConfirmPeriod()
        # Set template for receiving Weighted Available Period (WAP)
        t_receive_WAP = spade.Behaviour.ACLTemplate() 
        t_receive_WAP.setOntology("REPLY_WAP")
        mt_receive_WAP = spade.Behaviour.MessageTemplate(t_receive_WAP)
        
        
        b_invite = self.Invite()
        # Set template for receiving invitation reply
        t_invite = spade.Behaviour.ACLTemplate()
        t_invite.setOntology("REPLY_CONFIRM_PERIOD")
        mt_invite = spade.Behaviour.MessageTemplate(t_invite)
        
        ##b_feedback = self.Invite()
        # Set template for receiving feedback
        ##t_feedback = spade.Behaviour.ACLTemplate()
        ##t_feedback.setOntology("FEEDBACK")
    
        # Add instantiated behaviours to the MSA agent
        #self.addBehaviour(b_config, None)
        
        self.addBehaviour(b_config, None)
        self.addBehaviour(b_request_idleness, None)

        self.addBehaviour(b_generate_period, mt_receive_idleness)
        self.addBehaviour(b_confirm_period, mt_receive_WAP)
        self.addBehaviour(b_invite, mt_invite)
        # Feedback not used in First Stage Test
        ##self.addBehaviour(b_feedback, t_feedback)
                    
"""
class CA:
(Agent Class)
Common Agent (CA) classes:
"""
class CA(spade.bdi.BDIAgent):
    
    # initialize() initializes variables for this agent to avoid overwriting __init__()
    def initialize(self, user, conf=None):
        
        self.user = user  # User data (dict) {'ID':'USER_ID','NAME':'USER_NAME'}
        self.conf = conf  # Configuration variables (dict) {'RESPONSE_METHOD':ACCEPT | DECLINE | SILENT}
    # Overwrite askBelieve() so that it returns True instead of {} (no substitution for true query)   
    def askBelieve(self, sentence): 
        if isinstance(sentence,types.StringType): 
            r = self.kb.ask(expr(sentence)) 
        else: 
            r = self.kb.ask(sentence) 
        if r == {}:
            return True
        else:
            return r
    
    """
    ### Behaviour
     
    CA.Config
    """

    class Config(spade.Behaviour.OneShotBehaviour):
    
        def onStart(self):
            print self.myAgent.getName(),"-->CA.Config.onStart(): starting CA Configuration"
            # Enable ProcIdleness behaviour
            self.myAgent.addBelieve("RECEIVE_IDLENESS_REQUEST")
            print self.myAgent.getName(),"-->CA.Config.onStart(): addBelieve => RECEIVE_IDLENESS_REQUEST"
            # Enable ProcRecomPeriod behaviour
            self.myAgent.addBelieve("RECEIVE_RECOM_PERIOD")
            print self.myAgent.getName(),"-->CA.Config.onStart(): addBelieve => RECEIVE_RECOM_PERIOD"
            # Enable ConfirmPeriod behaviour
            self.myAgent.addBelieve("RECEIVE_CONF_PERIOD")
            print self.myAgent.getName(),"-->CA.Config.onStart(): addBelieve => RECEIVE_CONF_PERIOD"

        def _process(self):
            print self.myAgent.getName(),"-->CA.Config.onStart(): CA Configuration Complete"
        
        def onEnd(self):
            pass
        
    """
    ### Behaviour
     
    CA.ProcIdleness
    """

    class ProcIdleness(spade.Behaviour.Behaviour):
    
        def onStart(self):
            print self.myAgent.getName(),"-->CA.ProcIdleness.onStart(): starting ProcIdleness"  
            self.userID = self.myAgent.user['ID']
        
        def _process(self):
            # RECEIVE_IDLENESS_REQUEST is always on

            if self.myAgent.askBelieve("RECEIVE_IDLENESS_REQUEST"):
                ##### VALIDATED BRANCH #####

                #print self.myAgent.getName(),"-->CA.ProcIdleness._process(): RECEIVE_IDLENESS_REQUEST"  
                BLOCK_TIME = 5
                
                self.dayRange = None
                
                # self.sender is the username of MSA who sends idleness request
                self.sender = None
                self.receive_msg = None
                self.receive_msg = self._receive(True, BLOCK_TIME)

                if self.receive_msg:
                    print self.myAgent.getName(),"-->CA.ProcIdleness._process(): RECEIVE_IDLENESS_REQUEST: receiving message"  
                    single_content = self.receive_msg.content 
                    #DEBUG#print single_content
                    # dayRange = [date1,date2,...]
                    self.dayRange,self.mLen,self.sender = SL0ParseIdleReq(single_content) 
                    #DEBUG#print self.mLen,self.sender
                else:
                    print self.myAgent.getName(),"-->CA.ProcIdleness._process(): RECEIVE_IDLENESS_REQUEST: no message received, try in the next loop"  
                # If dayRange exists, meaning the behaviour receives and parses the idleness request
                if self.dayRange:
                    idlenessDict = getRangeIdleness(self.dayRange,self.mLen,self.userID)
                    #DEBUG#print idlenessDict
                    
                    # Create message
                    self.msg = spade.ACLMessage.ACLMessage()

                     # Create Idleness in FIPA-SL0 format
                    """
                    :content
                        "((idleness
                        :value (set
                        (20120304 5)
                        (20120305 6)
                        (20120306 3)
                        )
                    """
                    content = "((idleness :value (set"
                    for date in idlenessDict.keys():
                        content += " (%s %s) "%(date,idlenessDict[date])
                    content += ") ))"
                    
                    # Add sender as receiver
                    sender = self.sender+".msa"
                    #print sender
                    #print hostname
                    receiver = spade.AID.aid(name="%s@%s"%(sender,hostname), 
                                     addresses=["xmpp://%s@%s"%(sender,hostname)])
                    #print receiver.getName()
                    self.msg.addReceiver(receiver)
                    #pdb.set_trace()
                    self.msg.setPerformative("inform")  
                    self.msg.setOntology("REPLY_IDLENESS")
                    self.msg.setLanguage("fipa-sl") 
                    self.msg.setContent(content)
                    
                    # Send the message                        
                    self.myAgent.send(self.msg)
                    
                    print self.myAgent.getName(),"-->CA.ProcIdleness._process(): sending REPLY_IDLENESS message"  
                    
                else:
                    # If no message is normally received, this print displays every 5 seconds as the BLOCK_TIME
                    #print self.myAgent.getName(),"-->CA.ProcIdleness.onStart(): no REPLY_IDLENESS message received"
                    pass

    """
    ### Behaviour
     
    CA.ProcRecomPeriod
    """
                
    class ProcRecomPeriod(spade.Behaviour.Behaviour):
    
        def onStart(self):
            print self.myAgent.getName(),"-->CA.ProcRecomPeriod.onStart(): starting ProcRecomPeriod"
            self.userID = self.myAgent.user['ID']
        
        def _process(self):

            # RECEIVE_RECOM_PERIOD is always on
            if self.myAgent.askBelieve("RECEIVE_RECOM_PERIOD"):
                ##### VALIDATED BRANCH #####
                
                #print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): RECEIVE_RECOM_PERIOD"
                BLOCK_TIME = 5            
                # Initialize temporary variables
                date = ""
                recomPeriod = ""
                mLen = ""
                sender = ""
                WAP = ""
                availablePeriod = None
                self.receive_msg = None
                    
                self.receive_msg = self._receive(True, BLOCK_TIME)
                if self.receive_msg:
                    
                    print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): RECEIVE_RECOM_PERIOD: receiving message"
                    single_content = self.receive_msg.content 
                    #print single_content
                    date,recomPeriod,mLen,sender = SL0ParseRecPeriod(single_content) 
                    #print date,recomPeriod,mLen,sender
                else:    
                    print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): RECEIVE_RECOM_PERIOD: no message received, try in the next loop"  
                    
                # If recomPeriod exists (not empty), meaning the behaviour receives and parses the idleness request    
                if recomPeriod:
                    print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): Recommended Period exists" 
                    userID = self.userID
                    #DEBUG#print (date, userID, recomPeriod, mLen)
                    availablePeriod = getAvailablePeriod(date, userID, recomPeriod, mLen)
                    #DEBUG#print "availablePeriod:",availablePeriod
                    
                    print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): getting Available Period" 
                    content = ""
                    
                    # If availablePeriod exists (is NOT None)
                    if availablePeriod:
                        date,WAP = getWAP(date,userID,availablePeriod,mLen)
                        print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): getting WAP" 
                        
                        """
                        :content
                            "((wap
                                :date 20120311
                                :value (set
                                (548 3)
                                (468 2)
                                (421 4)
                                )
                            ))"
                        """   
                        #DEBUG#print WAP
                        content = "((wap :date %s :value (set"%date
                        for p in WAP.keys():
                            content += " (%s %s) "%(p,WAP[p])
                        content += ") ))"
                        
                    # If availablePeriod DOES NOT exist (is None)
                    else:                        
                        content = "((wap :date %s :value none))"%(date)  
                    
                    #DEBUG#print content
                    
                    # Create message
                    self.msg = spade.ACLMessage.ACLMessage()
                    
                    # Add sender as receiver
                    sender = sender+".msa"
                    #print sender
                    #print hostname
                    receiver = spade.AID.aid(name="%s@%s"%(sender,hostname), 
                                     addresses=["xmpp://%s@%s"%(sender,hostname)])

                    self.msg.addReceiver(receiver)
                    self.msg.setPerformative("inform")   
                    self.msg.setOntology("REPLY_WAP")
                    self.msg.setLanguage("fipa-sl") 
                    self.msg.setContent(content)
                    
                    # Send the message                        
                    self.myAgent.send(self.msg)
                    print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): sending REPLY_WAP message" 
                    
                else:
                    # If no message is normally received, this print displays every 5 seconds as the BLOCK_TIME
                    #print self.myAgent.getName(),"-->CA.ProcRecomPeriod._process(): no REPLY_WAP message received"  
                    pass                 
    """
    ### Behaviour
     
    CA.ConfirmPeriod
    """    
    
    class ConfirmPeriod(spade.Behaviour.Behaviour):
    
        def onStart(self):
            print self.myAgent.getName(),"-->CA.ConfirmPeriod.onStart(): starting ConfirmPeriod"
            self.userID = self.myAgent.user['ID']
            self.username = self.myAgent.user['NAME']
        
        def _process(self):

            # RECEIVE_CONF_PERIOD is always on
            if self.myAgent.askBelieve("RECEIVE_CONF_PERIOD"):
                ##### VALIDATED BRANCH #####
                
                #print self.myAgent.getName(),"-->CA.ConfirmPeriod._process(): RECEIVE_CONF_PERIOD: "
                BLOCK_TIME = 5
                # Initialize temporary variables
                date = ""
                confPeriod = ""
                mLen = ""
                sender = ""
                
                self.receive_msg = self._receive(True, BLOCK_TIME)
                if self.receive_msg:
                    print self.myAgent.getName(),"-->CA.ConfirmPeriod._process(): RECEIVE_CONF_PERIOD: receiving message"
                    single_content = self.receive_msg.content
                    date,confPeriod,mLen,sender = SL0ParseConfPeriod(single_content) 

                else:
                    print self.myAgent.getName(),"-->CA.ConfirmPeriod._process(): RECEIVE_CONF_PERIOD:  no message received, try in the next loop"
                
                # If confPeriod exists
                if confPeriod:
                    # Get available period with confPeriod and this user's agenda
                    availablePeriod = getAvailablePeriod(date, self.userID, confPeriod, mLen)
                    print self.myAgent.getName(),"-->CA.ConfirmPeriod._process(): getting Available Period"  
                    content = ""
                    
                    # REPLY_CONFIRM_PERIOD
                    # If availablePeriod exists
                    if availablePeriod:
                        # Reply to MSA to ACCEPT the Confirmed Period
                        
                        """
                        :content
                            "((period 
                                :date 20120311
                                :value 501
                                :mlen 3
                                :result confirmed
                                :sender ca_username
                            ))"

                        """
                        content = "((period :date %s :value %s :mlen %s :result confirmed :sender %s :sender_id %s))"%(date, confPeriod, mLen, self.username, self.userID)
                        #DEBUG#print content
                        
                        # Enable Feedback behaviour 
                        # Because host may send invitation
                        self.myAgent.addBelieve("START_FEEDBACK")
                        print self.myAgent.getName(),"-->CA.Config.onStart(): addBelieve => START_FEEDBACK"
                    
                    else:
                        # Reply to MSA to DECLINE the Confirmed Period because of no Available Period
                        """
                        :content
                            "((period 
                                :date 20120311
                                :value 501
                                :mlen 3
                                :result declined
                                :sender ca_username
                            ))"

                        """
                        content = "((period :date %s :value %s :mlen %s :result declined :sender %s :sender_id %s))"%(date, confPeriod, mLen, self.username, self.userID)
                        
                    
                    # Create message
                    self.msg = spade.ACLMessage.ACLMessage()
                    
                    # Add sender as receiver
                    sender = sender+".msa"
                    receiver = spade.AID.aid(name="%s@%s"%(sender,hostname), 
                                     addresses=["xmpp://%s@%s"%(sender,hostname)])
                    
                    self.msg.addReceiver(receiver)
                    self.msg.setPerformative("inform")   
                    self.msg.setOntology("REPLY_CONFIRM_PERIOD")
                    self.msg.setLanguage("fipa-sl") 
                    self.msg.setContent(content)   

                    # Send the message                        
                    self.myAgent.send(self.msg)   
                    print self.myAgent.getName(),"-->CA.ConfirmPeriod._process(): sending REPLY_CONFIRM_PERIOD message" 
                    
                else:
                    # If no message is normally received, this print displays every 5 seconds as the BLOCK_TIME
                    #print self.myAgent.getName(),"-->CA.ConfirmPeriod._process(): no REPLY_CONFIRM_PERIOD message received"                      
                    pass

    """
    ### Behaviour
    ######### NOT IMPLEMENTED !!!! ###################
    CA.Feedback
    
    Offer system's and human's feedback to MSA.Feedback


    """
    ######### NOT IMPLEMENTED !!!! ###################
    class Feedback(spade.Behaviour.Behaviour):
        def onStart(self):
            self.sleep = 1
            
            # Defunct!!!
            self.response = self.myAgent.conf['RESPONSE_METHOD']
        def _process(self):   
            if self.myAgent.askBelieve("START_FEEDBACK"):
                """
                Periodically inspect database to get user's feedback (ACCEPT | DECLINE)
                Objective table: user_invitee_meeting, column: accept
                """

            
            time.sleep(self.sleep)
            
    # CA._setup()    
    def _setup(self): 
        print self.getName(),"-->CA._setup(): Agent starting... adding behaviours"   
          
        # Prefix b_: behaviour ; t_: template
        b_config = self.Config()
        b_proc_idleness = self.ProcIdleness()
        
        # Set template for receiving idleness
        # Template for receiving idleness request
        t_receive_idlereq = spade.Behaviour.ACLTemplate() 
        t_receive_idlereq.setOntology("REQUEST_IDLENESS")
        mt_receive_idlereq = spade.Behaviour.MessageTemplate(t_receive_idlereq)
         
        b_proc_recperiod = self.ProcRecomPeriod()
        # Template for receiving recommended period
        t_receive_recperiod = spade.Behaviour.ACLTemplate() 
        t_receive_recperiod.setOntology("RECOMMEND_PERIOD")
        mt_receive_recperiod = spade.Behaviour.MessageTemplate(t_receive_recperiod)
    
    
        b_confirm_period = self.ConfirmPeriod()
        # Template for receiving confirmed period
        t_receive_confperiod = spade.Behaviour.ACLTemplate() 
        t_receive_confperiod.setOntology("CONFIRM_PERIOD")
        mt_receive_confperiod = spade.Behaviour.MessageTemplate(t_receive_confperiod)
        
        ##b_feedback = self.Feedback()
               
        self.addBehaviour(b_config, None)
        self.addBehaviour(b_proc_idleness, mt_receive_idlereq)
        self.addBehaviour(b_proc_recperiod, mt_receive_recperiod)
        self.addBehaviour(b_confirm_period, mt_receive_confperiod)
        ##self.addBehaviour(b_feedback, None)
        
"""
Interact:
Interact with users based on messages
Implemented at the last stage

"""
class Interact(object):
    
    def __init__(self,meetingID,hostID=None,confirmPeriod=None,confirmDate=None):
        
        # Initialize member variables that may be used
        self.meetingID = meetingID
        self.hostID = hostID
        self.userID = self.hostID
        self.confirmPeriod = confirmPeriod
        self.confirmDate = confirmDate
        ##self.counter = 0  # For self.toCancel to record number of times of calling
        
    """
    # Asks the user whether to reschedule or cancel the meeting upon MSA.GeneratePeriod.scheduleFailed()
    """
    
    def failed(self):

        read = False
        contentID = 1 # Failed
        uri = "" # To be specified
        
        stage = 'GEN'
        WAIT_TIME = 60
        
        # Update dms.meeting.conf_period to False to fail the meeting
        result = updateConfPeriod(self.meetingID,'False')

        if result > 0:
            print "Interact.failed() --> Updated dms.meeting.conf_period: => False"

        # Send the system message to user
        self._sendMessage(contentID, uri)

        counter = 0
        meetingID = self.meetingID
        # Waiting for the host
        # Periodically query dms.meeting and dms.meeting_canceled to check whether
        # the meeting is canceled or rescheduled
        print "Interact.failed()  --> Waiting for the host's choice"
        while True:
            
            """
            # If Django added the meeting to dms.meeting_canceled
            if isMeetingCanceled(meetingID):
                print "Interact.failed()  --> Meeting is alreay in dms.meeting_canceled, now cancel it"
                # If the meeting is added to the dms.meeting_canceled, cancel the meeting, and break
                self._cancel(stage)
                break
            """
            
            if isRescheduled(meetingID):
                # If the meeting is rescheduled, break
                break
            
            if counter == WAIT_TIME:
                # If waiting time is due, automatically cancel the meeting 
                self._cancel(stage)
                break
            
            counter += 1
            time.sleep(1)
        
        ######################################
        # The rest is implemented in Django  #
        ######################################     
        
            
    """ 
    # Asks the user which period to confirm and get the Confirmed Period
    """
    # value here is wPeriods
    def toConfirmPeriod(self,value):
        contentID = 2 # Confirm Period?
        uri = "" # To be specified
        
        WAIT_TIME = 10
        confirmPeriod = None
        
        # Join the value (wPeriod)(list of 2-tuples) into a string
        # Join with ";"
        period_list = []
        for tuple in value:
            period_list.append(str(tuple[0]))
            
        value = ";".join(period_list)
        #print value
        # Update dms.meeting.choose_period
        result = updateChoosePeriod(self.meetingID,value)
        
        if result > 0:
            print "Interact.toConfirmPeriod() --> Updated dms.meeting.choose_period: => %s"%value
        
        # Update dms.meeting.conf_period tp True to wait for host's response to choose
        print result
        result = updateConfPeriod(self.meetingID,'True')
        if result > 0:
            print "Interact.toConfirmPeriod()  --> Updated dms.meeting.conf_period: => True"
        
        # Send the message to the host
        self._sendMessage(contentID, uri)    
        
        # Periodically query dms.meeting.conf_period to see if user chooses the confirmed period
        # Wait until host chooses the confirmed period or the time is up
        counter = 0
        print "Interact.toConfirmPeriod()  --> Waiting for the host's choice"
        while True:
            # confirmPeriod = dms.meeting.conf_period
            confirmPeriod = checkConfPeriod(self.meetingID)
            if confirmPeriod != 'True':
                break
            
            # If waiting time is due
            # Return the first tuple's period of the wPeriod (a.k.a. value) list
            if counter == WAIT_TIME:
                confirmPeriod = value[0][0]
                break
            
            counter += 1
            # Query database every 1 seconds
            time.sleep(1)
            
        return confirmPeriod
    
    
    """    
    # Asks the user whether to invite, cancel or reschedule upon CAs' confirmations
    # Get the result
    # Called in MSA.Invitee
    """
    def toInvite(self):
        # Set stage to INVT (Invitation)
        stage = "INVT"
        result = None
        
        # Indefinitely waiting for host's choice
        print "Interact.toInvite() --> Waiting (indefinitely) for host's choice"
        while True:
            # invite = dms.meeting.invite
            invite = checkInvite(self.meetingID)
            
            # If host chooses to send invitation
            # Two options implemented here
            # Invite | Cancel
            # Reschedule is not explicitly implemented here, but in ALCC
            
            if invite == 'True':
                result = True
                # Send system messages to invitees
                self._toAcceptInvite()
                break
                # Then process goes on to START_FEEDBACK
            
            elif invite == 'False': 
                # Cancel the meeting
                self._cancel(stage)
                result = False
                break
                # Then process blocks the Behaviour
                
            time.sleep(1)
        return result
     
    """
    # Asks the user whether to cancel, reschedule or continue upon any VIP's delayed refusal
    # Get the result
    # This method is called in MSA.Feedback
    
    """
    def toCancel(self):
        stage = "FB"
        WAIT_TIME = 30
        
        read = False
        contentID = 2
        uri = "" # To be specified
        
        self._sendMessage(contentID, uri)
        
        # Inspect host's response
        # Waiting for WAIT_TIME
        counter = 0
        print "Interact.toCancel() --> Waiting for host's choice"
        while True:
            # cancel = dms.meeting.cancel
            cancel = checkMeetingToCancel(self.meetingID)
            
            if cancel == 'True':
                self._cancel(stage)
                break
            
            # If cancel is False, continue this loop and Feedback behaviour
            elif cancel == 'False':
                pass
            
            if counter == WAIT_TIME:
                break
            
            counter += 1
            time.sleep(1)
        
    """   
    # Asks Invitee whether to accept the invitation   
    """
    
    def _toAcceptInvite(self):
        
        contentID = 5 # Accept Invitation?
        uri = "" # To be specified
        read = False
        # Get invitee id list
        inviteeList = inspectUIM(self.meetingID,self.hostID)
        
        # The the first element of each 2-tuple in the list
        sequence = [(invitee[0],contentID,uri,read) for invitee in inviteeList]
        print sequence
        result = addManyMessage(sequence)
        
        if result>0:
            print "Interact --> Added many messages to dms.message"


    """
    Interact._cancel():
    cancel the meeting and shutdown the agent
    
    """
    def _cancel(self,stage):
        
        # Add meeting to dms.meeting_canceled
        result = addMeetingCanceled(self.meetingID,self.hostID,self.confirmDate,self.confirmPeriod,stage)
        
        # If successful
        if result>0:
            print "Interact._cancel() --> Added meeting_id: %s to dms.meeting_canceled"%(self.meetingID)
        
        # Add host to dms.msa, with dms.msa.active = False, ALCC will thus shutdown the agent
        result = addMSA(self.meetingID, self.userID, 'False')
        if result>0:
            print "Interact --> Added meeting_id: %s and user_id: %s to dms.msa"%(self.meetingID,self.userID)
        
        
        #### Change dms.user_msa.active to False ## This is done by ALCC
        
    """
    Interact._sendMessage():
    add a message to dms.message
    
    """   
    def _sendMessage(self, contentID, uri, read=False):
        
        result = addMessage(self.userID,contentID,uri,read)
        if result > 0:
            print "Interact --> Add a message with user_id: %s to dms.message"%(self.userID)
    
"""
FST: First Stage Test
###Agent Life Cycle Control (ALCC)
"""
def FST():
    hostname = '127.0.0.1'
    password = 'secret'
    
    # First register CAs
    
    i = 1
    for i in range(1,4):
        ca = CA("vip%s.ca@%s"%(i,hostname), password)
        user = {'NAME': 'vip%s'%i,'ID':'%s'%(i+1)}
        conf = {'RESPONSE_METHOD':'ACCEPT'}
        ca.initialize(user, conf)
        ca.start()
       
    i = 1    
    for i in range(1,4):
        ca = CA("ci%s.ca@%s"%(i,hostname), password)
        user = {'NAME': 'ci%s'%i,'ID':'%s'%(i+4)}
        conf = {'RESPONSE_METHOD':'ACCEPT'}
        ca.initialize(user, conf)
        ca.start()
    
    """ 
    # Test one CA
    i = 1
    ca = CA("vip%s.ca@%s"%(i,hostname), password)
    user = {'NAME': 'vip%s'%i,'ID':'%s'%(i+1)}
    conf = {'RESPONSE_METHOD':'ACCEPT'}
    ca.initialize(user, conf)
    ca.start()
    """
    
    # Register MSA
    msa = MSA("host.msa@%s"%(hostname), password)
    
    user = {'ID':'1','NAME':'host'}
    dayRange = [20120601,20120602,20120603]
    pPeriod = 0b0011110000011111
    mLen = 1
    
    mID = 39 # Random number
    #mTopic = "Computer Science"
    #mt = {'ID':mID,'TOPIC':mTopic,'LOCATION':'Beijing'}
    mt = {'ID':mID}
    conf  = {
            'SEARCH_BIAS': 
                {
                'METHOD': 'DAY_LENGTH', # (AVERAGE_IDLE | DAY_LENGTH)
                'DELIMIT': 3,
                },
                
            'CONFIRM_METHOD': 'AUTO', # (PROMPT | AUTO)
            }
    msa.initialize(user,dayRange,pPeriod,mLen,mt,conf)
    msa.start()

# Trial code begins
if __name__ == "__main__": # Instantiate Agents
    
    # Instantiator / Agent Life Cycle Control
    # 
    """
    msa = MSA(JID,password)
    msa.initialize(dayRange,pPeriod,mLen,mID,mTopic,conf) # Initialize MSA with variables passed from Django-level view
    msa.start() # equivalent to msa.run()
    """
    
    """
    FST start:
    """
    FST()

