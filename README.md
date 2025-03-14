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