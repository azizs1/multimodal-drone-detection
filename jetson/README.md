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
Or you can add the following to the network interfaces file `/etc/network/interfaces` to avoid having to do this everytime:
```
auto eth0
iface eth0 inet static
    address 192.168.50.2
    netmask 255.255.255.0
```
### Docker Deployment
From repository root, run the following commands to build and run Jetson services:
```bash
docker compose -f docker-compose.jetson.yaml build

# Run all Jetson services (sensor ingestion + fusion + inference)
docker compose -f docker-compose.jetson.yaml up -d

# Or run only fusion + inference
docker compose -f docker-compose.jetson.yaml up -d jetson-fusion jetson-inference

# Video-demo mode (uses simulator/videos as inference source)
docker compose -f docker-compose.jetson.yaml --profile videos up -d jetson-fusion jetson-inference-videos
```
>Note that `--network host` must be used to allow for the use of the Jetson Nano network settings for the container.
>Inference services mount `offline_ml/weights` into the container and read:
>`/app/offline_ml/weights/visual_no_augmentation_best.pt` and
>`/app/offline_ml/weights/thermal_no_augmentation_best.pt`.

Useful logs:
```bash
docker compose -f docker-compose.jetson.yaml logs -f jetson-fusion
docker compose -f docker-compose.jetson.yaml logs -f jetson-inference
docker compose -f docker-compose.jetson.yaml logs -f jetson-sensor-ingestion
```
### Running Without Container
If running without the container is desired, navigate to `multimodal-drone-detection/jetson/src` and run:
```
python3 -m sensor_ingestion.ingest_gi
```
