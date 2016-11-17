'''
Created on Oct 12, 2016
@author: mwitt_000
@modified by: Megan Weller and Ashley Bertrand
'''
import network_2
import link_2
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 2 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network hosts
    host1 = network_2.Host(1)
    object_L.append(host1)
    host2 = network_2.Host(2)
    object_L.append(host2)
    host3 = network_2.Host(3)
    object_L.append(host3)
    
    #create routers and routing tables for connected clients (subnets)
    forwarding_table = [[['A', 0], ['B', 0], ['D',0]], [['D',0], ['C',0], ['A',1]]]
    router_a_rt_tbl_D = {1: {0: 1}} # packet to host 1 through interface 1 for cost 1
    router_a = network_2.Router(name='A', 
                              intf_cost_L=[1,1], 
                              rt_tbl_D = router_a_rt_tbl_D, 
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_a)
    router_b_rt_tbl_D = {1: {1: 3}} # packet to host 2 through interface 0 for cost 3
    router_b = network_2.Router(name='B', 
                              intf_cost_L=[1,3], 
                              rt_tbl_D = router_b_rt_tbl_D, 
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_b)
    router_c_rt_tbl_D = {1: {0: 1}} # packet to host ? through interface ? for cost ?
    router_c = network_2.Router(name='C', 
                              intf_cost_L=[1,1], 
                              rt_tbl_D = router_c_rt_tbl_D, 
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_c)
    router_d_rt_tbl_D = {3: {1: 3}} # packet to host ? through interface ? for cost ?
    router_d = network_2.Router(name='D', 
                              intf_cost_L=[1,3], 
                              rt_tbl_D = router_d_rt_tbl_D, 
                              max_queue_size=router_queue_size,
                              forwarding_table = forwarding_table)
    object_L.append(router_d)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link_2.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    link_layer.add_link(link_2.Link(host1, 0, router_a, 0))
    #link_layer.add_link(link_2.Link(host2, 0, router_a, 1))
    link_layer.add_link(link_2.Link(router_a, 0, router_b, 0))
    link_layer.add_link(link_2.Link(router_b, 0, router_d, 0))
    link_layer.add_link(link_2.Link(router_d, 0, host3, 0))
    
    link_layer.add_link(link_2.Link(host3, 0, router_d, 0))
    link_layer.add_link(link_2.Link(router_d, 1, router_c, 0))
    link_layer.add_link(link_2.Link(router_c, 0, router_a, 1))
    link_layer.add_link(link_2.Link(router_a, 0, host1, 0))



    
    #start all the objects
    thread_L = []
    for obj in object_L:
        thread_L.append(threading.Thread(name=obj.__str__(), target=obj.run)) 
    
    for t in thread_L:
        t.start()
    
    #send out routing information from router A to router B interface 0
    router_a.send_routes(1)
 

    
    #create some send events    
    for i in range(1):
        host1.udt_send(3, 1, 'Sample host1 data %d' % i)
        #host3.udt_send(1, 3, 'Sample host3 data %d' % i)
        
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)

    #print the final routing tables
    for obj in object_L:
        if str(type(obj)) == "<class 'network_2.Router'>":
            obj.print_routes()
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically
