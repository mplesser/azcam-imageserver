"""
This azcam app listens on a socket to receive an image file from azcamserver.
When data is received it then creates a local image file from that data.
Command line options:
   - the listening port may be changed, with -l PortNumber.  Default is 6543.
   - a beep may sound when the image is created, with -b.
   - GCSLBT guide mode is supported with -g.
   - Verbose mode with -v 1.
"""

import socket
import os
import socketserver
import select
import shutil
import optparse
import time

# parameters
rec_buff_size = 1048576 * 4  # max socket buffer size (4096*256)*4
options = None

# XPA location for image display
if os.name == "posix":
    xpaset = "xpaset"
    xpaget = "xpaget"
else:
    xpaset = "\\ds9\\xpaset.exe"
    xpaget = "\\ds9\\xpaget.exe"


class ProcessClientCommand(socketserver.BaseRequestHandler):
    """
    Class to processes commands.
    """

    def handle(self):
        """
        Called when a socket connection is made.
        """

        global options

        self.port = int(options.port)
        self.gcslbt = int(options.gcslbt)
        self.beep = int(options.beep)
        self.verbose = int(options.verbose)
        self.temp_display_file = "temp_display_file"

        if self.gcslbt:
            # LBT guide mode
            Filesize = self.receive_command1()
            if Filesize == "":
                return
            Filesize = int(Filesize.strip())
            Filename = "test%d.fits" % self.port
            Overwrite = 1
            if os.path.exists(Filename):
                os.remove(Filename)

            s = "Receiving file %s; size %d" % (Filename, Filesize)
            if self.verbose:
                print(s)
            else:
                print(".")
            if self.beep:
                print("\a\r")  # beep

        else:
            # AzCam mode
            # get 256 character header
            command = self.receive_command(256)
            command = command.replace('"', "")

            # if command=='-1' then server should close
            if command[0:2] == "-1":
                abort_is = True
                return

            # parse header: Filesize, Filename, Filetype, Ncols, Nrows, Display
            # Ncols and Nrows for binary only, ignored otherwise
            Filesize = int(command[0:16])
            x = command[17:].split("\00")[0]
            x1 = x.split(" ")
            # x1.remove('')
            Filename = x1[0]
            try:
                Fileflag = int(x1[1])  # 0 FITS, 1 MEF, 2 BIN, 3 BIN no lock
                NumCols = int(x1[2])
                NumRows = int(x1[3])
                Displayflag = int(x1[4])  # 0 no display, 1 ds9
            except Exception:
                Fileflag = 1
                NumCols = 512
                NumRows = 512
                Displayflag = 0

            # read and strip overwrite character (!)
            if Filename.startswith("!"):
                Overwrite = 1
                Filename = Filename.lstrip("!")
            else:
                Overwrite = 0

            s = "Receiving file %s; size %d; overwrite %d" % (
                Filename,
                Filesize,
                Overwrite,
            )
            if self.verbose and self.beep:
                print(s + "\a")
            elif self.verbose:
                print(s)
            elif self.beep:
                print("\a.")
            else:
                print(".")

            # reply to AzCam, 16 characters
            #  0 => OK, -1 => TCP error, -2 => filename error

            # ERROR if file exists and not overwrite
            if os.path.exists(Filename):
                if Overwrite:
                    os.remove(Filename)
                else:
                    s = (
                        "ERROR "
                        + Filename
                        + " already exists but overwrite flag is not set"
                    )
                    print(s)
                    self.reply_to_client("-2              ")
                    return

            # ERROR if folder does not exist
            fldr = os.path.dirname(Filename)
            if fldr != "" and not os.path.exists(fldr):
                s = "ERROR folder %s does not exist" % fldr
                print(s)
                self.reply_to_client("-3              ")  # new Apr09
                return

            # reply OK to AzCam
            self.reply_to_client("0               ")  # OK

        # create image file
        f = open(Filename, "wb")

        # receive and write image data
        data = ""
        total_count = 0
        while total_count < Filesize:
            count1 = min(Filesize, rec_buff_size)
            data = self.request.recv(count1)
            if data == "":
                break
            f.write(data)
            total_count += len(data)

        # close image file
        f.close()

        # finished for LBT guide mode
        if self.gcslbt:
            return

        if total_count < Filesize:
            print(
                "ERROR reading image.  Received %d of %d bytes"
                % (total_count, Filesize)
            )
            self.reply_to_client("-2              ")  # ERROR

        # optionally create lockfile for binary type 2
        if Fileflag == 2:
            Lockfile = Filename.replace(".bin", ".OK")
            f = open(Lockfile, "w")
            f.close()

        # set display parameters based on file type
        if Displayflag == 1:  # fits
            if Fileflag == 0:
                DisplayFile = self.temp_display_file + ".fits"
                s = "type " + DisplayFile + " | " + xpaset + " ds9 fits"
            elif Fileflag == 1:  # MEF
                DisplayFile = self.temp_display_file + ".fits"
                s = xpaset + " ds9 fits mosaicimage iraf < " + DisplayFile
            elif Fileflag == 2 or Fileflag == 3:  # bin
                DisplayFile = self.temp_display_file + ".bin"
                s = "type " + DisplayFile + " | " + xpaset + " ds9 fits"
                s = (
                    xpaset
                    + " ds9 array [xdim="
                    + str(NumCols)
                    + ",ydim="
                    + str(NumRows)
                    + ",bitpix=-16] < "
                    + DisplayFile
                )
            else:
                print("ERROR Unrecognized file format %d" % Fileflag)
                return

            # temp fix, copy image file so not locked by ds9
            shutil.copyfile(Filename, DisplayFile)

            # execute XPA command to display file
            os.system(s)

        # send done to client - 16 chars
        # self.ReplytoClient('0               ')

        return

    def receive_command(self, count):
        """
        Receive fixed length string from AzCam.
        """

        total_data = ""
        data = ""
        total_count = 0
        while total_count < count:
            try:
                data = self.request.recv(count).decode()
            except Exception:
                data = ""
            if data == "":
                break
            total_data += data
            total_count += len(data)

        if total_count < count:
            if total_data[0:2] == "-1":
                return "-1"  # flag to shutdown
            print(
                "ERROR reading all data.  Received %d of %d bytes"
                % (total_count, count)
            )
        return total_data

    def receive_command1(self):
        """
        Receive a terminated string from AzCam.
        """

        # receive with terminator
        msg = chunk = ""
        loop = 0
        while chunk != "\n":
            try:
                chunk = self.request.recv(1).decode()
            except Exception as errorcode:
                print("ERROR reading image file: %s" % repr(errorcode))
                return ""
            if chunk != "":
                msg = msg + chunk
                loop = 0
            else:
                loop += 1
                if loop > 10:
                    return ""

        Reply = msg[:-2]  # remove CR/LF
        if Reply is None:
            Reply = ""

        return Reply

    def reply_to_client(self, reply):
        """
        Reply to client.
        """

        totalsent = 0
        replylen = len(reply)
        while totalsent < replylen:
            try:
                sent = self.request.send(str.encode(reply))
            except Exception:
                sent = 0
            if sent == 0:
                print("ERROR Server socket connection broken during send")
                break
            totalsent = totalsent + sent

        return


class Server(socketserver.ThreadingTCPServer, ProcessClientCommand):
    """
    Override Server class to allow Abort.
    """

    def __init__(self, a, b):

        self.options = None
        self.abort_is = 0

        socketserver.ThreadingTCPServer.__init__(self, a, b)

    def serve_forever(self):
        """
        Break out of this loop when AbortImageServer is True.
        """

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while not self.abort_is:
            r, w, e = select.select([self.socket], [], [], 0.100)
            if r:
                self.handle_request()
        abort_is = False

        # Exits here when server is aborted
        print("Closing imageserver")
        time.sleep(1)

        return


def start():
    """
    Start imageserver for installed command "imageserver".
    """

    global options

    p = optparse.OptionParser()

    # socket port for listening
    p.add_option("--port", "-p", default=6543, action="store")

    # Beep flag to beep when image is received
    p.add_option("--beep", "-b", default=0, action="store_true")

    # LBTO GuideMode
    p.add_option("--gcslbt", "-g", default=0, action="store_true")

    # Verbosity
    p.add_option("--verbose", "-v", default=0, action="store_true")
    options, arguments = p.parse_args()

    # start server (if OK waits here forever)
    try:
        server_id = ("", int(options.port))
        server = Server(server_id, ProcessClientCommand)
        print("Imageserver listening for images on " + repr(server_id))
        server.serve_forever()
    except Exception as details:
        print("ERROR starting imageserver, is it already running? " + str(details))
        time.sleep(1)


if __name__ == "__main__":
    start()
