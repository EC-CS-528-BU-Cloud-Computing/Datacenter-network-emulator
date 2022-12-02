** **
# Datacenter Network Emulator
** **

## 1. Vision and Goals Of The Project:

Network emulation is a technique for testing the performance of real applications and validating the correctness of configurations over a virtual network. Different from simulators, a network emulator mirrors the network which connects end-systems, not the end-systems themselves. A network emulator example is [Crystalnet](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/p599-liu.pdf), which is published in SOSP 2017.

In this project, we will build a network emulator to emulate a data center network. Production data center networks typically use [Clos topology](https://cseweb.ucsd.edu//~vahdat/papers/sigcomm08.pdf) and [BGP/ECMP](https://docs.jetstream-cloud.org/attachments/bgp-in-the-data-center.pdf) for routing. We will use public image of [SONiC](https://sonic-net.github.io/SONiC/
), an open source cross-platform switch OS. On the top of the emulated data center network, we will develop tools to automatically generate network configurations, and diagnosis tools to debug network faults, e.g., [Pingmesh](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/pingmesh_sigcomm2015.pdf). 

## 2. Users/Personas Of The Project:

Roles in this project include datacenter network emulator, network configuration generator, and network diagnosis tool(s).
* The datacenter network emulator emulates a data center network. Specifically, it runs Fat Tree topology which is a special case of Clos topology aand uses SONiC image for switch OS. 
* Network configuration generator automatically generates network configurations. In this project, it will generate BGP/ECMP routing rules. 
* Network diagnosis tools are to debug network faults. We will use Pingmesh to test the connectivity of all pairs of end-hosts to diagnose the correctness of BGP protocol configuration.

** **

## 3.   Scope and Features Of The Project:

The project aims at generating a  dataceneter network emulator using the Fat Tree topology. For the purpose of this project we will be extending the topology to include 16 nodes which can be tested using the PingMesh topology.

Initially, for testing connectivity, PingMesh will use ICMP Pings to test if the nodes are connected within the system. As an extension a TCP/IP Ping will be sent to ensure the connectivity of the system. The project does not require the implementation of PingMesh from scratch but an extension from existing users can be provided.

A visual representation of the topology will be generated to easily assess the topology of various nodes in the system. We will be using frameworks such as iftree that provide a neat representation of the network topology.
** **

## 4. Solution Concept

This section provides a high-level outline of the solution.

Global Architectural Structure Of the Project:

This section provides a high-level architecture or a conceptual diagram showing the scope of the solution. If wireframes or visuals have already been done, this section could also be used to show how the intended solution will look. This section also provides a walkthrough explanation of the architectural structure.

 

Design Implications and Discussion:

This section discusses the implications and reasons of the design decisions made during the global architecture design.

## 5. Acceptance criteria
Acceptance criteria of this project will be as following:
1. A 2 tier fat tree topology is created which can scale up to 16 pods.
2. Routing between servers and routers is configured using BGP protocol.
3. BGP configuration is automated.
3. Each server can ping any other server in the topology using ICMP, TCP, and UDP.

Implementation of a FatTree topology including the use of BGP to route data within the topology.

## 6.  Release Planning:

Sprint 1:
* Understand project goals.
* Read the paper on fat tree topology to develop an understanding of a data center networks
* Read the book [2] to develop an understanding of BGP deployment in data centers.
* Prepare a presentation for the mentor.

Sprint 2: 
* Understand network namespaces and implement network connectivity and BGP configuration on simple examples three node topologies.

Sprint 3: 
* Create a tool to set up topology and add connectivity between nodes.

Sprint 4: 
* Create a tool to configure BGP automatically in core, aggregation, and edge switches and servers.

Sprint 5: 
* Create a testing tool to test the connectivity between servers and connect all the tools together.


** **

## General comments

The project successfully builds the network topologies and can be visually represented in a tree-like topology.

## References
* https://sonic-net.github.io/SONiC/
* https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/pingmesh_sigcomm2015.pdf
* https://cseweb.ucsd.edu//~vahdat/papers/sigcomm08.pdf
* https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/p599-liu.pdf
* https://docs.jetstream-cloud.org/attachments/bgp-in-the-data-center.pdf
* https://github.com/rafayopen/pingmesh

