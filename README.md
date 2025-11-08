# openadr-ven
A MicroPython implementation of an OpenADR 3.0 VEN with local VTN discovery via DNS-SD over mDNS, for the [Olimex ESP32-POE](https://www.olimex.com/Products/IoT/ESP32/ESP32-POE/open-source-hardware).

## Cloning the Repo

```
git clone -b micropython --single-branch https://github.com/chpmk98/openadr-ven.git
cd openadr-ven
```

## Installation instructions
(Sources: [MicroPython.org](https://micropython.org/download/OLIMEX_ESP32_POE/), [cbrand/micropython-mdns](https://github.com/cbrand/micropython-mdns), [SparkFun.com](https://learn.sparkfun.com/tutorials/micropython-programming-tutorial-getting-started-with-the-esp32-thing/setup))
1. Install `esptool`:

```
pip install --upgrade esptool
```

   - Windows users may find the installed program is called `esptool` instead of `esptool.py`. 

2. Connect the Olimex ESP32-POE to your computer using a USB cable.

3. Erase the entire flash:

```
esptool.py erase_flash 
```

OR 

```
esptool.py --chip esp32 -p PORTNAME erase_flash
```

e.g., `esptool.py --chip esp32 -p /dev/cu.wchusbserial1410 erase_flash`

   - On Linux, the port name is usually similar to `/dev/ttyUSB` or `/dev/ttyACM0`.
   - On Mac, the port name is usually similar to `/dev/tty.usbserial-<letters and numbers>`. The port name used during development was `/dev/cu.wchusbserial1410`.
   - On Windows, the port name is usually similar to `COM4`.

4. Download the latest MicroPython firmware (`firmware.mp.*.esp32.bin`) from the cbrand/micropython-mdns [releases page](https://github.com/cbrand/micropython-mdns/releases). Version 1.6.0 (`firmware.mp.1.24.esp32.bin`) was used during development.

5. Flash the firmware

```
esptool.py --chip esp32 -p PORTNAME write_flash -z 0x1000 FIRMWARE_PATH
```

e.g., `esptool.py --chip esp32 -p /dev/cu.wchusbserial1410 write_flash -z 0x1000 firmware.mp.1.24.esp32.bin`

6. Install [ampy](https://github.com/adafruit/ampy).

```
pip install adafruit-ampy
```

7. Open `load_files.sh` in a text editor, modify the port name (on [line 4](https://github.com/chpmk98/openadr-ven/blob/0b13adaa8651e44b92f6b6e81f1c31589857387a/load_files.sh#L4)) to match your setup, and save the file.

8. Open `files_to_load/wifi_credentials.py` in a text editor, add your local Wi-Fi credentials, and save the file. If you are connected to Ethernet, I _think_ you can skip this step, but I have not tested using Ethernet so I cannot promise that the program will still work.

9. Run the following from the root `openadr-ven` directory to avoid uploading your Wi-Fi credentials to GitHub:

```
git update-index --skip-worktree files_to_load/wifi_credentials.py
```

10. Load program files onto the ESP32 by executing the `load_files.sh` bash script. On Mac, this is done with:

```
bash load_files.sh
```

   - This may require updating the permissions of the file, which can be done by running `chmod +rwx load_files.sh`.
   - This may take several minutes, but should probably finish within 10 minutes.
   - Individual files can be loaded with `ampy --port PORTNAME put SRC_FILE DST_FILE` (e.g., `ampy --port /dev/cu.wchusbserial1410 put files_to_load/oadr30/ven.py oadr30/ven.py`), and should take around 10-20 seconds each.
   - After files are already loaded onto the ESP32, any subsequent attempts at loading new or modified files must be accompanied by _holding down the `BUT1` button on the ESP32_. See Troubleshooting notes for more details.

11. Download a serial terminal (I use CoolTerm, which can be downloaded [here](https://freeware.the-meiers.org/), but there are [other terminal options](https://learn.sparkfun.com/tutorials/terminal-basics) available), open it, and connect to the ESP32 using the following connection details:
   - Speed: 115200 bits per second 
   - Data Bits: 8
   - Parity: None
   - Stop Bits: 1

After you connect, you should see the printout below. There may be some additional lines for downloading libraries, but that is ok.

```
MicroPython v1.25.0-preview.97ets Jul 29 2019 12:21:46
rst:0x1 (POWERON_RESET), boot:0x1b (SPI_FAST_FLASH_BOOT)
configsip: 0, SPIWP:0xee
clk_drv:0x00,q_drv:0x00,d_drv:0x00,csO_drv:0x00,hd_drv:0x00,wp_drv:0x00
mode:DIO, clock div:2
load:0x3fff0030,len:4892
ho 0 tail 12 room 4
load:0x40078000,len:14896
load:0x40080400,len:4
load:0x40080404,len:3372
entry 0x400805b0
Connecting to Wi-Fi..
Wi-Fi successfully connected!
No config file provided for the VEN. Using ./configs/default.json by default.
Looking for a VTN on the local network using DNS-SD...
Scanning for _openadr3._tcp
Received 0 responses.
Scanning for _openadr3._tcp
Received 0 responses.
...
```

Once you get here, you are done with the installation. Press and hold `BUT1` to drop to Read-Eval-Print Loop (REPL) mode. In REPL mode, you can run code snippets as if using a Python command prompt. For example, you can inspect the file structure using the following lines:

```
import os
os.listdir()
os.listdir("oadr30")
```

Press the `RST1` button to restart the ESP32.

To discover and connect to a VTN, you must now add a VTN to the local area network, which is outside the scope of this repo. A small amount of additional information is included in Local VTN Setup.

## Troubleshooting notes
 - __The ESP32 must be in Read-Eval-Print Loop (REPL) mode when loading files with `ampy`,__ otherwise `ampy` will hang indefinitely. This is automatically true when only the firmware is installed, but after files are loaded, you must _hold the `BUT1` button_ when uploading new or modified files.
   - `BUT1` is defined as the drop-to-REPL button in [line 59](https://github.com/chpmk98/openadr-ven/blob/0b13adaa8651e44b92f6b6e81f1c31589857387a/files_to_load/ven.py#L59) of `files_to_load/ven.py` and regularly polled throughout the program (e.g., while scanning for a VTN on the local area network; [line 229](https://github.com/chpmk98/openadr-ven/blob/0b13adaa8651e44b92f6b6e81f1c31589857387a/files_to_load/ven.py#L229) of `files_to_load/ven.py`)
   - Modifications to the program should include places where the REPL button is polled and the program drops to REPL as needed, to allow `ampy` to upload files when reprogramming. Whether or not the program successfully drops to REPL can be confirmed by observing ESP32 output through the serial terminal.
   - If the ESP32 gets stuck in a state where it never drops to REPL, you can reprogram the ESP32 by using `esptool.py` to erase the entire flash, flash the firmware, and load in files again.

## Local VTN Setup

This VEN was tested with the OpenADR3 VTN Reference Implementation that was modified to advertise a service over mDNS, with the following properties:
- Service type: `"_openadr3._tcp"` \*
- Service name: `"My VTN Server._openadr3._tcp.local."`
- Host name: `"My-VTN-Server.local."`
- Port: `8026` \*
- IP address: `10.0.0.194` \*
- TXT records: 
  - `version="3.0.1"`
  - `base_path="/openadr3/3.0.1"` \*
  - `local_url="https://My-VTN-Server.local:8026/openadr3/3.0.1"`
  - `role="vtn"` \*
  - `program_names="local,GHG,"`
  - `requires_auth`
  - `openapi_url="https://www.openadr.org/openadr-3-0"`

\* These fields are necessary (i.e., used in [ven.py](https://github.com/chpmk98/openadr-ven/blob/0b13adaa8651e44b92f6b6e81f1c31589857387a/files_to_load/ven.py#L116)) to find and connect to the local VTN.

## Outstanding TODOs

This branch is currently a rough proof-of-concept for service discovery and message passing over HTTPS on an ESP32 device. There are many poorly-written aspects of this code that should be changed, but I did not have the time to change them. The ones that I am aware of are listed below. 
 - On Mac, `load_files.sh` loads `.DS_Store` files onto the ESP32, which is unnecessary. Updating the bash script to to filter out `.DS_Store` files could be useful.
 - There is no `datetime` module for MicroPython, so in `files_to_load/oadr30/vtn.py`, I replaced `datetime.now()` with `time.time()` and replaced `timedelta` with integer numbers of seconds. This should be functional, but I never set the `time` module, so `time.time()` returns some time in the year 2000, which is incorrect. Incorporating some way to grab the actual time and set the `time` module would be useful.
 - The `Event` class in `files_to_load/oadr30/events.py` relies heavily on the `IntervalPeriod` and `Intervals` classes in `files_to_load/oadr30/interval.py`, which relies on the `datetime` Python module and several other time-related libraries in the `ISO8601_DT` class in `datetime_util.py`. In a perfect world, someone would get all this time-keeping working and debugged in MicroPython, and thus have a functional `Events` class. I gave up and commented out lines in `files_to_load/oadr30/vtn.py` where `Events` was used to parse JSON packets received from the VTN, and instead save and display the raw JSON packets directly. Updating the code to parse JSON events more intelligently could be useful.
 - The `Programs` class does not work in `files_to_load/oadr30/vtn.py` for some reason -- `Program(response.json())` returns `None` when trying to parse JSON packets received from the VTN. I did not bother to troubleshoot this, and instead save and display the raw JSON packets directly. Updating the code to parse JSON programs more intelligently could be useful.
 - This code base currently only prints out to serial terminal and does not interface with any displays or outputs. Adding in some PWM control based on the received prices, as we did for the [may22demo](https://github.com/chpmk98/openadr-ven/blob/ca39435994e2a826c03de6a90d441be5884bad0e/hvac.py#L125), would be cool.
 - I used `print` statements instead of `logging` statements throughout my code. Changing these to `logging` statements could be useful. There are [some examples](https://github.com/chpmk98/openadr-ven/blob/0b13adaa8651e44b92f6b6e81f1c31589857387a/files_to_load/oadr30/vtn.py#L3) of this in the code base already.
 - The current code base is inconsistent with the published [specifications](https://github.com/oadr3-org/specification/blob/main/3.1.0/Definition.md#local-scenarios) for discovering local VTNs. Updating the code to align with the listed specifications could be useful.
   - This code does not utilize the `requires_auth` boolean TXT record when connecting to a VTN, but instead always authenticates. I believe authentication is done somewhere in `files_to_load/oadr30/vtn.py`, but the exact location escapes me.
   - This code uses IP addresses to connect instead of using the `.local` hostname.
   - This code supports end-user configuration of the VTN URL, `clientID`, and `clientSecret` through the configuration file at `files_to_load/configs/default.json`. The [main branch](https://github.com/chpmk98/openadr-ven/tree/main) of this repo has an example configuration file at `configs/olivine.json` that builds on top of the default configuration file and includes a [full VTN URL](https://github.com/chpmk98/openadr-ven/blob/e3f6f0460d12ec15996496a35ffa223ec062a52b/configs/olivine.json#L14). Whether you want to expose the rest of the contents of the configuration file to the end-user or if you want to create a user-level config file with only the VTN URL, `clientID`, and `clientSecret` fields available is up to you.

## Externally-sourced code 
This repo includes code that has been copied and/or modified from existing sources.
 - `files_to_load/http.py` contain just enough `HTTPStatus` values for `files_to_load/oadr30/vtn.py` to function. These values were copied from the [cpython/Lib/http](https://github.com/python/cpython/blob/3.13/Lib/http/__init__.py) source code.
 - `files_to_load/traceback.py` was downloaded and copied over from [micropython-traceback](https://pypi.org/project/micropython-traceback/).
 - `files_to_load/logging` was downloaded and copied over from [micropython-logging](https://pypi.org/project/micropython-logging/).
 - `files_to_load/oadr30` contains files from [universaldevices/oadr30](https://github.com/universaldevices/oadr30/tree/main) that were copied over and trimmed and hacked until they ran in MicroPython.

