@echo off
rem Starts AzCamImageWriter under Windows.

set ROOT="/azcam/azcam-imageserver/azcam_imageserver"
start /high /min /d %ROOT% "AzCamImageServer" python -m imageserver -l 6543 -v
