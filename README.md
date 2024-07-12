# azcam-imageserver

*azcam-imageserver* is an *azcam* application which creates a process to receive an image from a remote system running azcam.

## Installation

`pip install azcam-imageserver`

Or download from github: https://github.com/mplesser/azcam-imageserver.git.


## Usage Examples

Command line options are:

- -port *portnumber* (default 6543): set socket port for listening
- -b: set beep ON when an image is received
- -v: set verbose mode ON
- -g: set guide mode ON

```
imageserver
or
imageserver -p 1234 -b -v -g
or
python -m azcam_imageserver.imageserver -p 1234 -b -v
```
