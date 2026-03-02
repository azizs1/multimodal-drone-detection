### Network Setup
There is some preliminary network setup that is required for the used configuration. The Jetson Nano is connected via ethernet to a PC, while also using a Wi-fi dongle for internet connection (Edimax N150). First, set up the dongle:
```
sudo apt update
sudo apt install -y build-essential dkms git bc
git clone https://github.com/lwfinger/rtl8188eu.git
cd rtl8188eu
sudo make install
sudo modprobe 8188eu
```
With the dongle set up, you can now ssh into this device and perform git operations as needed. Connect the ethernet cable to the PC and disable private network firewall on the PC in order to communicate. If you do not want to do this, you can create inbound firewall rules to allow UDP traffic on ports 3000 and 3002 on the Ethernet network adapter.

You will likely have to set a static IP for the Ethernet network adapter (i.e 192.168.50.1). Additionally, run the following to set this interface private:
```
Set-NetConnectionProfile -InterfaceAlias "Ethernet" -NetworkCategory Private
```
On the Jetson Nano side, set an IP address for the eth0 interface:
```
sudo ip addr add 192.168.50.2/24 dev eth0
sudo ip link set eth0 up
```
### Docker Deployment
From repository root, run the following commands to build and run the Docker container:
```bash
docker build -t jetson-si-ml -f jetson/Dockerfile jetson
sudo docker run --rm -it --network host --runtime nvidia --privileged jetson-si-ml
```
>Note that `--network host` must be used to allow for the use of the Jetson Nano network settings for the container.
### Running Without Container
If running without the container is desired, navigate to `multimodal-drone-detection/jetson/src` and run:
```
python3 -m sensor_ingestion.ingest_gi
```