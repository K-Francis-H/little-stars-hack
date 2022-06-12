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
    1. Once the AVD is running, open the Google Play Store app and install the Little Stars app
    2. Make sure to close the Little Stars app before the next step
2. Turn on your IP camera
    1. put the camera into Wifi AP mode (some do this automatically, mine do)
    2. Find the camera Wifi AP on your laptop or desktop and connect to it
3. Open Wireshark and begin monitoring your laptop or desktop's Wifi interface
4. Now return to the AVD from step 1, open the Little Stars app, and watch the network traffic on Wireshark
    1. Things will move fast in Wireshark, but the AVD probably sent a group of 3 2 byte payload UDP packets to the camera and was promptly flooded by packets from the camera. Those 3 packets correspond to the command list linked above.

# What Does It Mean?
I don't even really know but its enough to get the camera to talk to us. For my cameras the 3 UDP payloads look like this:

`0x30 0x67` -> CAMERA_IP:8070

`0x30 0x66` -> CAMERA_IP:8070

`0x42 0x76` -> CAMERA_IP:8080

The first byte corresponds to one of the commands from the list that is linked above. `MSG_LAN_SEARCH = 0x30` and `MSG_P2P_RDY = 0x42`. I don't know what the 2nd byte means but that doesn't matter because afterwards the camera showers my python script with packets.

# Now What?
That's as far as I got. I'm assuming that the packets the camera has begun spamming me with are video frames. I'm not sure though and they're not particularly big (1472 bytes). There may be another authorization step. From the conversation [here](https://community.home-assistant.io/t/popular-a9-mini-wi-fi-camera-the-ha-challenge/230108) there is likely some kind of weak encryption used. I implemented the encryption algorithm described in that forum in my script and have a test to prove it works, well at least for the text 'Hello World'. So my next step is to try to decrypt and/or interpret video data from the packets or figure out the next step in the protocol if the packets I'm getting are not video frames.

I hope this README and the associated scripts, Wireshark dumps, etc are useful to you. If your camera has a different handshake and you feel up to making a pull request for the script please do so.

# Update: I Am Getting Video!

![An image of a scissors handle](https://raw.githubusercontent.com/K-Francis-H/little-stars-hack/main/img.jpeg)

An image of a scissors handle recieved from the camera via some intermediate version of the `little_stars.py` script.

With some help from a user named purplesky on the conversation mentioned above in the "Now What?" section I was able to combine multiple packets into JPEG images and hand them to the Python Image Library (PIL) to get individual frames. I was then able to use Tkinter to render them. The updated script for my particular camera is `camera_feed.py` 

It only kinda works, though. In order to actually get frames to render to a Tkinter canvas I have intentionally left a syntax error on line `183` of that file: `se;f.root.update()` ... I'm not sure why exactly but that seems to allow enough time when the exception is being handled to render the frame. Other things like sleeping or increasing/decreasing the UI update callback don't seem to help. No doubt this will only work for some people and most will only get a blank Tkinter window. I'm new to Tkinter and maybe I'd have better luck with a hardware texture in SDL or pygame with which I have a little more familiarity, but might require a more complex application. 

The basic structure of the program seems sound though: A separate thread initiates contact with the camera and begins reieving packets. Once it has a full frame, it creates an image object and pushes it onto a thread-safe queue. Meanwhile, the UI main loop continually runs an update function on a ~100ms timer and checks the thread-safe queue for new images. If a new one is found, it is rendered to the canvas. But apparently with Tkinter its not quite that simple. I'll keep on improving what I have and try to figure out what data is being sent to port 8070, maybe audio?
