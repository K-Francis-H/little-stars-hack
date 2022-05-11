# little-stars-hack
python script(s) to comunicate with (very insecure) IP cams compatible with the Little Stars phone app

# Background
You may have purchased a very cheap IP cam from Alibaba or eBay and are frustrated to find that it doesn't have something simple like an RTP stream but instead asks you to download an app like [Little Stars](https://play.google.com/store/apps/details?id=com.jxl.app.littlestars.project) in order to get video from it. It uses an insecure protocol to stream video out to a server then back to your phone. It allows one to view the camera feed from outside of their home network but is vulnerable to attack.

More info on the attack vectors and which cameras are vulnerable can be found here: [https://hacked.camera/](https://hacked.camera/).

These types of cameras often support 2 modes: the insecure "over the Internet to an app" mode, and the also insecure but much more useful Wifi AP mode. In Wifi AP mode the camera acts as a Wifi hotspot. Once a device connects to the AP that device performs a simple handshake and can then begin recieving video frames. The exact nature of the handshake may vary from device to device. Some cameras will respond to initiation requests on the broadcast IP at a specific port (usually 32108 from waht I have read), other models will only respond to initiation requests on their IP at a specific port. The cameras that I am working with for this require 2 UDP packets be sent to the cameras IP at port 8070 followed by a third packet at 8080. The camera then begins spamming what I believe to be video frames back at the client in rapid succession. Whatever flavor of this protocol your camera uses the command list can be found in [pmarrapese's repo](https://github.com/pmarrapese/iot/blob/master/p2p/dissector/pppp.fdesc). That's the same person that discovered the camera vulnerabilities in the link above.