# azcam-imageserver

*azcam-imageserver* is an *azcam* extension which supports sending an image to a remote host running an image server which receives the image.

## Installation

`pip install azcam-imageserver`

Or download from github: https://github.com/mplesser/azcam-imageserver.git.

## Usage

```python
from azcam_imageserver.sendimage import SendImage
sendimage = SendImage()
remote_imageserver_host = "10.0.0.1"
remote_imageserver_port = 6543
sendimage.set_remote_imageserver(remote_imageserver_host, remote_imageserver_port, "azcam")
```
