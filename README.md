# openadr-ven
An implementation of an OpenADR 3.0 VEN with local VTN discovery via DNS-SD over mDNS.

## Cloning the Repo
```
git clone --recurse-submodules https://github.com/chpmk98/openadr-ven
cd openadr-ven
```
or 
```
git clone https://github.com/chpmk98/openadr-ven
cd openadr-ven
git submodule update --init --recursive
```

## Environment Setup
```
conda create --name ven_env "python>=3.10"
conda activate ven_env
pip install -r requirements.txt
```

## Running
```
python test_ven.py
```

Tested using Python 3.13.2.

## Additional Information

### Local VTN Setup

This VEN was tested with the OpenADR3 [VTN Reference Implementation](https://github.com/oadr3-org/openadr3-vtn-reference-implementation/tree/main) that was modified to advertise a service over mDNS, with the following fields:
- service type: `_openadr-http._tcp.local.` \*
- service name: `My VTN Server._openadr-http._tcp.local.`
- server: `My-VTN-Server.local.`
- port: `8081` \*
- addresses: [list of IP addresses] \*
- properties: 
  - `OpenADR 3.0.1`
  - `version=3.0.1`
  - `base_url=/openadr3/3.0.1` \*
  - `role=vtn` \*
  - `documentation=https://www.openadr.org/openadr-3-0`

\* These fields are necessary (i.e., used in [ven.py](https://github.com/chpmk98/openadr-ven/blob/main/ven.py#L127)) to find and connect to the local VTN.

### Provided VENs

The [VEN class](https://github.com/chpmk98/openadr-ven/blob/main/ven.py#L14) is an abstract class that handles the nitty gritty of the mDNS service discovery and the subsequent network connection to the local VTN and selection of the desired program. Theoretically, an appliance manufacturer would only need to implement [two appliance-specific methods](https://github.com/chpmk98/openadr-ven/blob/main/ven.py#L258), the first defining what the appliance should do using the price data and the second defining what the appliance should do while it waits until the next price data update. Then the [main operational loop](https://github.com/chpmk98/openadr-ven/blob/main/ven.py#L292) just alternates between these two function calls indefinitely. 

We have provided three different children of the VEN class in [test_ven.py](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py) to demonstrate the flexibility of the code base, and describe them in more detail below. All three of these VENs can be tested by commenting and uncommenting the appropriate lines at the bottom of [test_ven.py](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L63) and by running `python test_ven.py` in the command line.

[TestVEN](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L8) is the most basic implementation, which uses the default functionality of prompting for user input during [local VTN discovery](https://github.com/chpmk98/openadr-ven/blob/main/ven.py#L135) and [program selection](https://github.com/chpmk98/openadr-ven/blob/main/ven.py#L221). Upon receiving the events, TestVEN prints out the events and waits for five seconds before querying for new events. This VEN is made to work with the local VTN setup described above, and does not provide any [default addresses](https://github.com/chpmk98/openadr-ven/blob/main/configs/default.json#L15) to connect to.

[AutoVEN](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L46) is a child of TestVEN that removes the need for user inputs and instead [automatically connects](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L51) to the first local VTN it finds and [uses the first program](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L61) listed on the VTN. AutoVEN demonstrates the simplicity of changing the desired response and mode of user interactions, e.g., in cases when a keyboard and monitor are not available, or when there's only expected to be one VTN available at any moment in time.

[OlivineVEN](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L24) is a child of TestVEN that connects to a [prespecified global server](https://github.com/chpmk98/openadr-ven/blob/main/configs/olivine.json#L14). As such, this VEN is functional without the local VTN setup, and does not conduct local VTN discovery or [advertise itself](https://github.com/chpmk98/openadr-ven/blob/main/configs/olivine.json#L3) over mDNS. Since the Olivine servers are not exactly OpenADR 3.0 servers, OlivineVEN uses a separate (preexisting) codebase for [establishing a connection](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L30) to the server, does not require [program selection](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L37), and uses different API calls to [query data](https://github.com/chpmk98/openadr-ven/blob/main/test_ven.py#L41) from the server. OlivineVEN demonstrates the simplicity of switching between a local VTN and global VTN, and in changing the desired protocol used to communicate with the VTN. 

