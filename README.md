# little-stars-hack
python script(s) to comunicate with (very insecure) IP cams compatible with the Little Stars phone app

# Background
You may have purchased a very cheap IP cam from Alibaba or eBay and are frustrated to find that it doesn't have something simple like an RTP stream but instead asks you to download an app like [Little Stars](https://play.google.com/store/apps/details?id=com.jxl.app.littlestars.project) in order to get video from it. It uses an insecure protocol to stream video out to a server then back to your phone. It allows one to view the camera feed from outside of their home network but is vulnerable to attack.

More info on the attack vectors and which cameras are vulnerable can be found here: [https://hacked.camera/](https://hacked.camera/).

These types of cameras often support 2 modes: the insecure "over the Internet to an app" mode, and the also insecure but much more useful Wifi AP mode. In Wifi AP mode the camera acts as a Wifi hotspot. Once a device connects to the AP that device performs a simple handshake and can then begin recieving video frames. The exact nature of the handshake may vary from device to device. Some cameras will respond to initiation requests on the broadcast IP at a specific port (usually 32108 from waht I have read), other models will only respond to initiation requests on their IP at a specific port. The cameras that I am working with for this require 2 UDP packets be sent to the cameras IP at port 8070 followed by a third packet at 8080. The camera then begins spamming what I believe to be video frames back at the client in rapid succession. Whatever flavor of this protocol your camera uses the command list can be found in [pmarrapese's repo](https://github.com/pmarrapese/iot/blob/master/p2p/dissector/pppp.fdesc). That's the same person that discovered the camera vulnerabilities in the link above.

# Figuring Out Your Device's Handshake
The easiest way to figure out how to get data from your camera is to watch the [Little Stars](https://play.google.com/store/apps/details?id=com.jxl.app.littlestars.project) app do it then copy the initiation requests in a script or program. It can be difficult to sniff packets from an actual phone running the app due to encryption. A much easier method is to emulate an Android phone on your laptop or desktop. To do this you'll need the following software installed:

* [Wireshark](https://www.wireshark.org/#download)
  * Linux users: check your package manager for the package `wireshark`
* [Android Studio](https://developer.android.com/studio/#downloads)

Once the software is installed and configured follow these steps to get the handshake network traffic to appear in Wireshark:

1. [Open Android Studio and setup an AVD](https://developer.android.com/studio/run/managing-avds)
  i. Once the AVD is running, open the Google Play Store app and install the Little Stars app
  ii. Make sure to close the Little Stars app before the next step
2. Turn on your IP camera
  i. put the camera into Wifi AP mode (some do this automatically, mine do)
  ii. Find the camera Wifi AP on your laptop or desktop and connect to it
3. Open Wireshark and begin monitoring your laptop or desktop's Wifi interface
4. Now return to the AVD from step 1, open the Little Stars app, and watch the network traffic on Wireshark
  i. Things will move fast in Wireshark, but the AVD probably sent a group of 3 2 byte payload UDP packets to the camera and was promptly flooded by packets from the camera. Those 3 packets correspond to the command list linked above.

# What Does It Mean?
