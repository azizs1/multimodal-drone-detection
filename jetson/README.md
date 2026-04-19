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
From repository root, run the following commands to build and run the Docker container:
```bash
docker build -t jetson-si-ml -f jetson/Dockerfile jetson
sudo docker run --rm -it --network host --runtime nvidia --privileged --device /dev/video0:/dev/video0 --env-file .env -v /tmp/argus_socket:/tmp/argus_socket -v /usr/lib/aarch64-linux-gnu/tegra:/usr/lib/aarch64-linux-gnu/tegra -e NVIDIA_DRIVER_CAPABILITIES=all jetson-si-ml

sudo docker run --rm -it --network host --runtime nvidia --privileged --device /dev/video0:/dev/video0 --env-file .env -v /tmp/argus_socket:/tmp/argus_socket -e NVIDIA_DRIVER_CAPABILITIES=all jetson-si-ml

sudo docker run --rm -it --runtime nvidia --network host --privileged --env-file .env -e NVIDIA_DRIVER_CAPABILITIES=all -v /tmp/argus_socket:/tmp/argus_socket --device /dev/video0 jetson-si-ml

http://localhost:9997/v3/paths/list
```
list formats: v4l2-ctl --device=/dev/video0 --list-formats-ext

>Note that `--network host` must be used to allow for the use of the Jetson Nano network settings for the container.
### Running Without Container
If running without the container is desired, navigate to `multimodal-drone-detection/jetson/src` and run:
```
python3 -m sensor_ingestion.ingest_gi
```
# Initialize venv
A dedicated Jetson Docker container was not used due to container network passthrough issues and space issues on a 32GB limited SD card. To maintain dependency management, `uv` was used:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.10 --system-site-packages
UV_SKIP_WHEEL_FILENAME_CHECK=1 uv sync --no-build-isolation
```
# Low Space on Disk
Especially during development when it is easier to work with full JetPack 6.1, space can be a concern. For this, another USB drive can be used (WARNING: THIS WILL COMPLETELY WIPE THE USB):
```bash
# find USB device name (probs /dev/sda1)
lsblk
# format to ext4
sudo mkfs.ext4 /dev/sda1
# create mount point and mount it
sudo mkdir -p /mnt/usb
sudo mount /dev/sda1 /mnt/usb
# set write permissions
sudo chown jetson:jetson /mnt/usb
```
Clone the repo here. Now Docker should be configured to use this USB drive:
```bash
sudo systemctl stop docker
sudo mkdir -p /mnt/usb_storage/docker-data
```
Now we must edit `/etc/docker/daemon.json` and add to the file:
```json
"data-root": "/mnt/usb_storage/docker-data"
```


 and initialize the virtual environment. When creating this virtual environment, it will still try to download packages on the initial SD card, so we need to create a temp cache on the USB drive:
```bash
mkdir -p /mnt/usb_storage/.uv_cache
export UV_CACHE_DIR="/mnt/usb_storage/.uv_cache"
# optional, but add to bashrc for future sessions. remember to source in current one
echo 'export UV_CACHE_DIR="/mnt/usb_storage/.uv_cache"' >> ~/.bashrc
```