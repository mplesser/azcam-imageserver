# azcam-imageserver

*azcam-imageserver* is an *azcam* extension to create an application which receives an image from a remote system running azcam.

Options include setting listen port (-l xxxx), beeping when an image is received (-b 1), verbose mode (-v), and a special guide mode (-g).

## Installation

`pip install azcam-imageserver`

Or download from github: https://github.com/mplesser/azcam-imageserver.git.

## Usage Examples

```
azcamimageserver
or
azcamimageserver -l 1234 -b 1 -v -g
or
python -m imageserver -l 1234 -b 1 -v
```
