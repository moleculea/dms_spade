import sys
sys.path.append('/home/anshichao/spade/')

import spade
import time
#import algorithms.cnt as cnt

class MSA(spade.Agent.Agent):
    class RequestIdleness(spade.Behaviour.Behaviour): # Behaviour Class: Request Idleness
        def onStart(self):
            print "Starting to Request Idleness. . ."
            self.counter = 0
        
        def _process(self):
            if 1==2 :
                print "Counter:", self.counter
                self.counter = self.counter + 1
                            # First, form the receiver AID
                receiver = spade.AID.aid(name="receiver@127.0.0.1", 
                                         addresses=["xmpp://receiver@127.0.0.1"])
                
                # Second, build the message
                self.msg = spade.ACLMessage.ACLMessage()  # Instantiate the message
                self.msg.setPerformative("inform")        # Set the "inform" FIPA performative
                self.msg.setOntology("myOntology")        # Set the ontology of the message content
                self.msg.setLanguage("English")           # Set the language of the message content
                self.msg.addReceiver(receiver)            # Add the message receiver
                self.msg.setContent("Hello World")        # Set the message content
                
                # Third, send the message with the "send" method of the agent
                self.myAgent.send(self.msg)
                print "message sent"
            time.sleep(1)
    class ReceiveBehav(spade.Behaviour.Behaviour):
        """This behaviour will receive all kind of messages"""

        def _process(self):
            self.msg = None
            
            # Blocking receive for 1 seconds
            self.msg = self._receive(True, 1)
            #print self.getAMS()
            # Check whether the message arrived
            if self.msg:
                print self.getAgent().getAID(),":I got a message!"
                print self.msg.getContent()
            else:
                print "I waited but got no message"

    def _setup(self):
            print "MyAgent starting . . ."
            b = self.RequestIdleness()
            c = self.ReceiveBehav()
            
            t_receive_idleness = spade.Behaviour.ACLTemplate() 
            t_receive_idleness.setOntology("REPLY_IDLENESS")
            
            self.addBehaviour(b)
            self.addBehaviour(c, t_receive_idleness)
            #self.setDefaultBehaviour(b)
                
if __name__ == "__main__":
    a = MSA("agent@127.0.0.1", "secret")
    b = MSA("receiver@127.0.0.1", "secret")
    a.start()
    a.getName()
    b.start()
    #a.takeDown()
     