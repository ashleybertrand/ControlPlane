'''
Created on Oct 12, 2016
@author: mwitt_000
@modified by: Megan Weller and Ashley Bertrand
'''
import queue
import threading
import ast

## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    #  @param cost - of the interface used in routing
    def __init__(self, cost=0, maxsize=0):
        self.in_queue = queue.Queue(maxsize);
        self.out_queue = queue.Queue(maxsize);
        self.cost = cost
    
    ##get packet from the queue interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
#                 if pkt_S is not None:
#                     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
#                 if pkt_S is not None:
#                     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
#             print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
#             print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    prot_S_length = 1
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst_addr, prot_S, data_S):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.prot_S = prot_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        prot_S = byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length : ]        
        return self(dst_addr, prot_S, data_S)

## Implements a network host for receiving and transmitting data
## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        p = NetworkPacket(dst_addr, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return

## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_cost_L, rt_tbl_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        #note the number of interfaces is set up by out_intf_cost_L
        self.intf_L = []
        for cost in intf_cost_L:
            self.intf_L.append(Interface(cost, max_queue_size))
        #set up the routing table for connected hosts
        self.rt_tbl_D = rt_tbl_D 

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            
    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is also i
            #forward packets based on routing tables that are computed through the distance vector protocol
            self.intf_L[(i+1)%2].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, (i+1)%2))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass
        
    #a router will receive and update its own routing tables
    #call Bellman-Ford equation to compute updated costs to destinations
    #as you update costs, you may need to send out changes in routing table to other nodes using send_routes()
    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p):
        #update own routing table based on what is received
        #TODO: add logic to update the routing tables and
        # possibly send out routing updates
        print('%s: Received routing update %s' % (self, p))
        message = p.data_S  #ie. B received 1---

        int_0_cost = -99
        int_1_cost = -99

        for i in range(len(message)):
            if (message[i].isdigit()):
                #there is a cost at interface 0
                if (i == 0):
                    int_0_cost = int(message[i])
                #there is a cost at interface 1
                if (i == 2):
                    int_1_cost = int(message[i])

        if (self.name == "A"):
            to_host = 2
            cost = self.intf_L[1].cost
        elif (self.name == "B"):
            to_host = 1
            cost = self.intf_L[0].cost

        if (int_0_cost != -99):
            self.rt_tbl_D[to_host] = {0: (int_0_cost + cost)}

        if (int_1_cost != -99):
            self.rt_tbl_D[to_host] = {1: (int_1_cost + cost)}

        #send_routes()


    
    #communicate routing table to nearby routers     
    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        message = Message(self.rt_tbl_D)
        p = NetworkPacket(0, 'control', message.to_byte_S())

        if (self.name == "A"):
            i = 1   #to send routing table to router B through A, must go through interface 1
            p.dst_addr = 2  #sending to host 2

        elif (self.name == "B"):
            i = 0   #to send routing table to router A through B, must go through interface 0
            p.dst_addr = 1  #sending to host 1

        try:
            #TODO: add logic to send out a route update
            #decide which interfaces to use to send out the routing table updates
            #figure out correct interface to send out of
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        #TODO: print the routes as a two dimensional table for easy inspection
        # Currently the function just prints the route table as a dictionary
        #print(self.rt_tbl_D)

        rt_tbl_items = self.rt_tbl_D.items()
        rt_tbl_L = [["-", "-"], ["-", "-"]]

        for host, intf_cost in rt_tbl_items:
            #router is utilizing 1 interface
            if (len(intf_cost) == 1):
                intf_cost = str(intf_cost)
                intf = str(intf_cost[1])
                cost = str(intf_cost[4])
                rt_tbl_L[int(intf)][host-1] = cost
            #router is utilizing 2 interfaces
            elif (len(intf_cost) == 2):
                intf_cost = str(intf_cost)
                intf1 = str(intf_cost[1])
                cost1 = str(intf_cost[4])
                intf2 = str(intf_cost[7])
                cost2 = str(intf_cost[10])
                rt_tbl_L[int(intf1)][host-1] = cost1
                rt_tbl_L[int(intf2)][host-1] = cost2

        interface0 = ' '.join(rt_tbl_L[0])
        interface1 = ' '.join(rt_tbl_L[1])

        print()
        print("     Cost to")
        print("       | 1 2")
        print("     --+----")
        print("From 0 |", interface0)
        print("     1 |", interface1)
        print()
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 

class Message:
    def __init__(self, rt_tbl_D):
        self.rt_tbl_D = rt_tbl_D

    #convert routing table to a byte string for transmission over links
    def to_byte_S(self):
        rt_tbl_items = self.rt_tbl_D.items()
        rt_tbl_L = [["-", "-"], ["-", "-"]]

        for host, intf_cost in rt_tbl_items:
            #router is utilizing 1 interface
            if (len(intf_cost) == 1):
                intf_cost = str(intf_cost)
                intf = str(intf_cost[1])
                cost = str(intf_cost[4])
                rt_tbl_L[int(intf)][host-1] = cost
            #router is utilizing 2 interfaces
            elif (len(intf_cost) == 2):
                intf_cost = str(intf_cost)
                intf1 = str(intf_cost[1])
                cost1 = str(intf_cost[4])
                intf2 = str(intf_cost[7])
                cost2 = str(intf_cost[10])
                rt_tbl_L[int(intf1)][host-1] = cost1
                rt_tbl_L[int(intf2)][host-1] = cost2

        interface0 = ''.join(rt_tbl_L[0])
        interface1 = ''.join(rt_tbl_L[1])
        byte_S = interface0 + interface1
        return byte_S

    #extract a message from a byte string
    #@param byte_S: byte string representation of a message
    @classmethod
    def from_byte_S(self, byte_S, return_msg):
        #host 1 is utilizing 2 interfaces
        if (byte_S[0].isdigit() and byte_S[2].isdigit()):
            c0 = byte_S[0]
            c2 = byte_S[2]
            rt_tbl_S += ", 1: {0: " + c0 + ", 1: " + c2 + "}"
        #host 1 is only utilizing interface 0
        elif (byte_S[0].isdigit()):
            c0 = byte_S[0]
            rt_tbl_S = ", 1: {0: " + c0 + "}"
        #host 1 is only utilizing interface 1
        elif (byte_S[2].isdigit()):
            c2 = byte_S[2]
            rt_tbl_S = ", 1: {1: " + c2 + "}"

        #host 2 is utilizing 2 interfaces
        if (byte_S[1].isdigit() and byte_S[3].isdigit()):
            c1 = byte_S[1]
            c3 = byte_S[3]
            rt_tbl_S += ", 2: {0: " + c1 + ", 1: " + c3 + "}"
        #host 2 is only utilizing interface 0
        elif (byte_S[1].isdigit()):
            c1 = byte_S[1]
            rt_tbl_S += ", 2: {0: " + c1 + "}"
        #host 2 is only utilizing interface 1
        elif (byte_S[3].isdigit()):
            c3 = byte_S[3]
            rt_tbl_S += ", 2: {1: " + c3 + "}"

        rt_tbl_S = rt_tbl_S[2:]
        rt_tbl_S = "{" + rt_tbl_S + "}"

        rt_tbl_D = ast.literal_eval(rt_tbl_S)

        if (return_msg):
            return self(rt_tbl_D)
        else:
            return rt_tbl_D