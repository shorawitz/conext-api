## conext-api

API built using the Flask web application framework to provide a ModBusTCP gateway to Schneider Conext Gateway.

# Notes
Some of the links may have changed since I originally wrote this, but you should have enough bread crumbs to follow to get the information you need.

At the time of this writing (2021/05/14,) the Modbus documentation could be downloaded from Schneider's website under "Technical Publications" on the Conext Gateway page.

The code is a little rough.  I haven't decided if separating the registers from the code is worthwhile or not.  It is just as easy to edit the Python code to update the devices and register data.  For more information you can check out my YouTube channel: JC/DC in the AZ.

# Setup
You'll of course need a Schneider Conext Gateway connected to your network or using a serial ModBus connection to your computer.

Some sort of server: In my use case, I am using an Ubuntu 20.04 LXD container running on my Ubuntu 20.04 server, but this could easily run on Docker, a virtual machine or a dedicated system (e.g Raspberry Pi) and not necessarily Linux.  The only requirements are Python, Flask, and NGINX.  I will provide some references to how I setup my installation, but getting the base setup is a bit beyond this guide

- Install NGINX: https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04
- Install Flask: https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-20-04

**Make sure you do not have any firewalls interfering with your web server or connection to the Conext Gateway port 503.  We will be using a socket for the Flask application, so no fw issues to worry there.**