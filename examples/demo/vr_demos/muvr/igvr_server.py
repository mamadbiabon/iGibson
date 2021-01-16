"""Server code that handles physics simulation and communicates with remote IGVRClient objects."""


import numpy as np
import time

from gibson2.render.mesh_renderer.mesh_renderer_cpu import Instance, InstanceGroup
from gibson2.utils.vr_utils import VrData

from PodSixNet.Channel import Channel
from PodSixNet.Server import Server


class IGVRChannel(Channel):
    """
    This is a server representation of a single, connected IGVR client.
    """
    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
    
    def Close(self):
        print(self, "Client disconnected")
        
    def Network_vrdata(self, data):
        self.vr_data_cb(data["vr_data"])

    def set_vr_data_callback(self, cb):
        """
        Sets callback to be called when vr data is received. In this case,
        we call a function on the server to update the positions/constraints of all the
        VR objects in the scene.

        Note: cb should take in one parameter - vr_data
        """
        self.vr_data_cb = cb
        
    def send_frame_data(self, frame_data):
        """
        Sends frame data to an IGVRClient.
        """
        self.Send({"action":"syncframe", "frame_data":frame_data})
    

class IGVRServer(Server):
    """
    This is the IGVR server that handles communication with remote clients.
    """
    # Define channel class for the server
    channelClass = IGVRChannel
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the IGVRServer.
        """
        Server.__init__(self, *args, **kwargs)
        print('IGVR server launched!')
        # This server manages a single vr client
        self.vr_client = None
        # Single VrData object that gets refreshed every frame
        # This is used to update the client agent's server-side VR data
        self.vr_data_persistent = None
        self.last_comm_time = time.time()

    def has_client(self):
        """
        Returns whether the server has a client connected.
        """
        return self.vr_client is not None

    def register_data(self, sim, client_agent):
        """
        Register the simulator and renderer and VrAgent objects from which the server will collect frame data
        """
        self.s = sim
        self.renderer = sim.renderer
        self.client_agent = client_agent

    def update_client_vr_data(self, vr_data):
        """
        Updates VR objects based on data sent by client. This function is called from the asynchronous
        Network_vrdata that is first called by the client channel.
        """
        time_since_last_comm = time.time() - self.last_comm_time
        self.last_comm_time = time.time()
        print("Time since last comm: {}".format(time_since_last_comm))
        print("Comm fps: {}".format(1/max(0.0001, time_since_last_comm)))
        # Set new VR data object - this is used each frame to update the client agent
        self.vr_data_persistent = vr_data
    
    def Connected(self, channel, addr):
        """
        Called each time a new client connects to the server.
        """
        print("New connection:", channel)
        self.vr_client = channel
        self.vr_client.set_vr_data_callback(self.update_client_vr_data)
        
    def generate_frame_data(self):
        """
        Generates frame data to send to client
        """
        # Frame data is stored as a dictionary mapping pybullet uuid to pose/rot data
        frame_data = {}
        # It is assumed that the client renderer will have loaded instances in the same order as the server
        for instance in self.renderer.get_instances():
            # Loop through all instances and get pos and rot data
            # We convert numpy arrays into lists so they can be serialized and sent over the network
            # Lists can also be easily reconstructed back into numpy arrays on the client side
            if isinstance(instance, Instance):
                pose = instance.pose_trans.tolist()
                rot = instance.pose_rot.tolist()
                frame_data[instance.pybullet_uuid] = [pose, rot]
            elif isinstance(instance, InstanceGroup):
                poses = []
                rots = []
                for pose in instance.poses_trans:
                    poses.append(pose.tolist())
                for rot in instance.poses_rot:
                    rots.append(rot.tolist())

                frame_data[instance.pybullet_uuid] = [poses, rots]

        return frame_data

    def refresh_server(self):
        """
        Pumps the server to refresh incoming/outgoing connections.
        """
        self.Pump()

        if self.vr_client:
            frame_data = self.generate_frame_data()
            self.vr_client.send_frame_data(frame_data)