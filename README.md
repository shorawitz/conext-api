## conext-api

API built using the Flask web application framework to provide a ModBusTCP gateway to Schneider Conext Gateway.  The Python code which does the actual querying to the Conext Gateway relies on the 'pyModbusTCP' Python module.

# Notes
Some of the links may have changed since I originally wrote this, but you should have enough bread crumbs to follow to get the information you need.

At the time of this writing (2021/05/14,) the Modbus documentation could be downloaded from Schneider's website under "Technical Publications" on the Conext Gateway page.

The code is a little rough.  I haven't decided if separating the registers from the code is worthwhile or not.  It is just as easy to edit the Python code to update the devices and register data.  For more information, check out my YouTube channel:
[JC/DC in the AZ](https://www.youtube.com/channel/UC8_TU2g-Yl1oMCts3pkXCbQ)

# Setup - stand alone instance running on bare metal or a VM
You'll of course need a Schneider Conext Gateway connected to your network or using a serial ModBus connection to your computer.

Some sort of server: In my use case, I am using an Ubuntu 20.04 LXD container running on my Ubuntu 20.04 server, but this could easily run on Docker, a virtual machine or a dedicated system (e.g Raspberry Pi) and not necessarily Linux.  The only requirements are Python, Flask, and NGINX.  I will provide some references to how I setup my installation, but getting the base setup is a bit beyond this guide

- Install NGINX: https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04
- Install Flask: https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-20-04

**Make sure you do not have any firewalls interfering with your web server or connection to the Conext Gateway port 503.  We will be using a socket for the Flask application, so no fw issues to worry there.**

In order to use 'solarmonitor.py' or 'query.py', you'll need to 'pip' install 'pyModbusTCP' (obviously, you'll also need pip installed):
```
sudo pip3 install pyModbusTCP
```
In this case, I'm using Python 3.8 (which you should be using Python3 by now - right?!?!?)

**I have hard-coded my Conext Gateway IP address into solarmonitor.py.  You will need to update that address with your own Conext Gateway IP address: Line 123 in the file.**

## Add to systemd for startup control
You will need to edit the 'solarmonitor.service' file to reflect the correct path to the solarmonitor installation directory and then copy the file to:
```
/etc/systemd/system/solarmonitor.service
```
At this point, you can:
```
sudo systemctl daemon-reload
sudo systemctl start solarmonitor
sudo systemctl status solarmonitor
sudo systemctl enable solarmonitor
```
If you encounter a problem with 'start':
```
sudo journalctl -xe
```
and check out the errors.  You probably have a path issue.

Once 'solarmonitor' is running:
```
ps -ef | grep solarmonitor
```
You can enable NGINX to proxy the connections to 'solarmonitor' and start serving the data for API access.  See NGINX docs for how to enable/configure as a reverse proxy.

Once NGINX is up and ready to proxy the connections to 'solarmonitor', use 'curl' or a web browswer to test the API endpoints:
```
curl http://<IP | FQDN of NGINX server>/inverter
{"primary": {"name": "XW6848-21", "state": "Operating", "enabled": 1, "faults": 0, "warnings": 0, "status": "AC Pass Through", "load": 1622}}
```
Here we can see the return data shows the "name" assigned to the inverter, the "state" of "Operatoring" and that the inverter is "enabled", as well as the "faults" and "warnings", "status" (which in my current use case is using "AC Pass Through") and the current "load".

# For an easier experience... try Docker
I have included a working setup for using Docker with all of the necessary files.

**You will still need to edit "solarmonitor.py" to change my IP address to your IP for your Conext Gateway.  See above**

With this option, you don't need to be a Linux guru to run the app.  Just install Docker on your favorite O/S (Mac, Windows or Linux) and you can get this working too.

To get things going, you'll obviously need Docker.  Check out this reference if you're new to Docker:
https://docs.docker.com/

```
docker build -t solarmonitor
```
*You may need to modify for Windows - never tried it myself*

This will build a Docker image (<500MB) named **"solarmonitor"** based on Ubuntu LTS 20.04 and install the application along with all of the needed packages and modules to run the application.  Along with **"solarmonitor"**, the image contains a working NGINX proxy listening on port 80.  You can test it out:
```
docker run -p 8080:80 solarmonitor
```

Point your browser to http://localhost:8080/inverter and you should see your XW information.

This image works exactly the same as the manual install, just makes it a bit easier to deploy.  

# How to use "query.py"
query.py is a test app to query the gateway for a single register value along with some debug data.  You have to take care to use the correct options in order to get accurate/readable results:

To query the BatMon for the battery voltage:
```
./query.py -i <Conext Gateway IP | FQDN> -p 503 -u 190 -r 70 -t uint32
port: 503
unit_id: 190
reg: 70
type: uint32
reg_count: 2
hold_register: [0, 53280]
converted value: 53280
```

This return data demonstrates what we are sending to the gateway and what the raw data looks like that is returned: "53280" which when devided by 1000 we get 53.28V which is what we want to know.

# Home Assistant Integration
I've added a snippet of my HA configuration.yaml file to this repo as well.  I hope it helps.

# Todo's
- Get the image to load on Home Assistant and create an interation.
- Integrate with HA Energy cards
- Show how to use Grafana to miminc capabilities of Conext Gateway software.  (This is useful for remote monitoring as Schneider's app is currently lacking)