# SpikeCom

Communication to the Spike over Bluetooth

The project is divided into two sections, the **host_files** and **hub_files**:

- **hub_files** - This holds all python files to be sent to the hub. The main.py is the program entrance.
- **host_files** - This holds all python files for the host (e.g. the current computer). When the utility is run, the main() function inside the main.py will be executed

## Updating code

Modify and change python files within **hub_files** and **host_files** as you please. To upload the files inside **hub_files** onto the Spike Hub, simply run:

```
sudo python3 spike.py update
```
(N.B. Some errors are printed to the terminal occasionally, but should still work)

## Usage

To run the utility, simply run:

```
sudo python3 spike.py run
```

This will do the following things:

1. Connect to the Hub over BT
2. Run the hub_files/main.py on the Hub
3. Run the host_files/main.py on the host (e.g. current computer)


## Debugging

Sometimes you may want to see traceback from the SpikeHub live. Debugging is currently limited, but there are a few ways to get good traceback for errors:

1. Use `sudo python3 spike.py debug`. This will execute the hub_files/main.py on the host, but listen for any traceback. If an error requires interaction from the host, however, you must use (2)

2. Use try&catch statements in the Hub code, with any exceptions being sent over the BT connection and printed on the client