# Audio Rogue Base Station #
## Hardware Requirements ##
[Hybertone GoIP-1](http://www.hybertone.com/en/pro_detail.asp?proid=10)\
[bladeRF x40](https://www.nuand.com/product/bladerf-x40/)\
Valid SIM Card\
[Sysmocom USIM Pack](https://shop.sysmocom.de/sysmoISIM-SJA2-SIM-USIM-ISIM-Card-10-pack-with-ADM-keys/sysmoISIM-SJA2-10p-adm)

## Audio Rogue Base Station (ARBS) Code ##
We create our own ARBS using a [bladeRF x40](https://www.nuand.com/product/bladerf-x40/) Software-Defined Radio (SDR) and a [Hybertone GoIP-1 Cellular Gateway](http://www.hybertone.com/en/pro_detail.asp?proid=10). The bladeRF acts as a GSM base station while the gateway routes calls made through the base station to a legitimate cellular network.\
The base station uses the open-source software [YateBTS](https://github.com/yatevoip/yatebts) to run a GSM air interface. You can install YateBTS using their instructions and use our provided Yate configuration files at ```ARBS/yate_config``` to replace the default configuration files usually created in the ```/usr/local/etc/yate``` directory of your host computer. This will enable Yate to use a SIP server created on the cellular gateway to route calls received by the GSM base station.\
Once programs are installed, you must connect the bladeRF x40 to your computer via a USB 3 cable and the GoIP-1 to your computer via an ethernet cable connected to the ```LAN``` connection in the back. You can communicate with the GoIP by setting a static IP to your machine's ethernet port as ```192.168.8.5``` with subnet mask as ```255.255.255.0``` and default gateway as ```192.168.8.1```. Then, you can load the provided configuration file ```ARBS/GoIP/goip_backup.dat``` directly to the gateway to properly interface it to YateBTS. Finally, ensure that your gateway has a valid SIM card inserted so that it can make a connection to a legitimate local tower. If you want a device to connect to your base station under our configuration, it must use a [Sysmocom SIM card](https://shop.sysmocom.de/sysmoISIM-SJA2-SIM-USIM-ISIM-Card-10-pack-with-ADM-keys/sysmoISIM-SJA2-10p-adm), as we only whitelist known IMSI values to avoid capturing foreign devices.

#### Running the ARBS ####

Once everything is installed, you must first load the FPGA image to the bladeRF x40 using the command ```bladeRF-cli -l ./ARBS/hostedx40.rbf```. Then, you can run ```sudo yate``` to start the GSM base station. This will also connect Yate to the SIP server run on the GoIP to fully connect the route from the SDR air interface to the legitimate cell network.