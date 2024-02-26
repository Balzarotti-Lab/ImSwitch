import threading
import Pyro5
import Pyro5.server
from imswitch.imcommon.framework import Worker
from imswitch.imcommon.model import initLogger
from ._serialize import register_serializers
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import imswitch
import uvicorn
from functools import wraps
import os
import socket 
import time
import zeroconf
from zeroconf import ServiceInfo, Zeroconf
import socket
from fastapi.middleware.cors import CORSMiddleware

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)

origins = [
    "http://localhost:8001",
    "http://localhost:8000",
    "http://localhost",
    "http://localhost:8080",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ImSwitchServer(Worker):

    def __init__(self, api, setupInfo):
        super().__init__()
        
        self._api = api
        self._name = setupInfo.pyroServerInfo.name
        self._host = setupInfo.pyroServerInfo.host
        self._port = setupInfo.pyroServerInfo.port

        self._paused = False
        self._canceled = False

        self.__logger =  initLogger(self)
        
        # start broadcasting server IP
        self.startmdns()

    def run(self):

        # serve APP
        self.startAPP()

        # serve the fastapi
        self.createAPI()
        # To operate remotely we need to provide https
        # openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
        # uvicorn your_fastapi_app:app --host 0.0.0.0 --port 8001 --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
        _baseDataFilesDir = os.path.join(os.path.dirname(os.path.realpath(imswitch.__file__)), '_data')
        print(os.path.join(_baseDataFilesDir,"ssl", "key.cert"))
        uvicorn.run(app, host="0.0.0.0", port=8001, ssl_keyfile=os.path.join(_baseDataFilesDir,"ssl", "key.pem"), ssl_certfile=os.path.join(_baseDataFilesDir,"ssl", "cert.pem"))
        self.__logger.debug("Started server with URI -> PYRO:" + self._name + "@" + self._host + ":" + str(self._port))
        try:
            Pyro5.config.SERIALIZER = "msgpack"

            register_serializers()

            Pyro5.server.serve(
                {self: self._name},
                use_ns=False,
                host=self._host,
                port=self._port,
            )

        except:
            self.__loger.error("Couldn't start server.")
        #self.__logger.debug("Loop Finished")

    def stop(self):
        self.__logger.debug("Stopping ImSwitchServer")
        self._daemon.shutdown()
        print("Unregistering...")
        zeroconf.unregister_service(self.info)
        zeroconf.close()


    # SRC: https://code-maven.com/static-server-in-python
    class StaticServer(BaseHTTPRequestHandler):

        def do_GET(self):
            root = os.path.dirname(os.path.abspath(__file__).split("imswitch")[0]+"imswitch/app/public/")

            if self.path == '/':
                filename = root + '/index.html'
            else:
                filename = root + self.path

            self.send_response(200)
            if filename[-4:] == '.css':
                self.send_header('Content-type', 'text/css')
            elif filename[-5:] == '.json':
                self.send_header('Content-type', 'application/javascript')
            elif filename[-3:] == '.js':
                self.send_header('Content-type', 'application/javascript')
            elif filename[-4:] == '.ico':
                self.send_header('Content-type', 'image/x-icon')
            else:
                self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open(filename, 'rb') as fh:
                    html = fh.read()
                    #html = bytes(html, 'utf8')
                    self.wfile.write(html)
            except FileNotFoundError as e:
                print(f'file not found {filename}')

    def start_server(self, httpd):
        #print('Starting httpd')
        httpd.serve_forever()

    def startAPP(self, server_class=HTTPServer, handler_class=StaticServer, port=5001):
        server_address = ('', port)
        try:
            httpd = server_class(server_address, handler_class)
            t = threading.Thread(target=self.start_server, args=(httpd,))
            t.start()

            print('httpd started on port {}'.format(port))
        except Exception as e:
            print('httpd failed to start on port {}'.format(port))
            print(e)
            return



    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def startmdns(self):
        service_type = "_https._tcp.local."  # Changed to HTTPS
        service_name = "imswitch._https._tcp.local."
        server_ip = self.get_ip()
        server_port = 8001  # Change to your server's port

        self.info = ServiceInfo(
            service_type,
            service_name,
            addresses=[socket.inet_aton(server_ip)],
            port=server_port,
            properties={},
        )

        zeroconf = Zeroconf()
        print(f"Registering service {service_name}, type {service_type}, at {server_ip}:{server_port}")
        zeroconf.register_service(self.info)

        


    @app.get("/")
    def createAPI(self):
        api_dict = self._api._asdict()
        functions = api_dict.keys()


        def includeAPI(str, func):
            #self.__logger.debug(str)
            #self.__logger.debug(func)
            @app.get(str)
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper



        '''
            @Pyro5.server.expose
            def move(self, positionerName=None, axis="X", dist=0) -> np.ndarray:
                return self._channel.move(positionerName, axis=axis, dist=dist)

            @Pyro5.server.expose
            def run_mda(self, sequence: MDASequence) -> None:
                self.__logger.info("MDA Started: {}")
                self._paused = False
                paused_time = 0.0
                t0 = time.perf_counter()  # reference time, in seconds

                def check_canceled():
                    if self._canceled:
                        self.__logger.warning("MDA Canceled: ")
                        self._canceled = False
                        return True
                    return False

                for event in sequence:
                    while self._paused and not self._canceled:
                        paused_time += 0.1  # fixme: be more precise
                        time.sleep(0.1)

                    if check_canceled():
                        break

                    if event.min_start_time:
                        go_at = event.min_start_time + paused_time
                        # We need to enter a loop here checking paused and canceled.
                        # otherwise you'll potentially wait a long time to cancel
                        to_go = go_at - (time.perf_counter() - t0)
                        while to_go > 0:
                            while self._paused and not self._canceled:
                                paused_time += 0.1  # fixme: be more precise
                                to_go += 0.1
                                time.sleep(0.1)

                            if self._canceled:
                                break
                            if to_go > 0.5:
                                time.sleep(0.5)
                            else:
                                time.sleep(to_go)
                            to_go = go_at - (time.perf_counter() - t0)

                    # check canceled again in case it was canceled
                    # during the waiting loop
                    if check_canceled():
                        break

                    self.__logger.info(event.x_pos)

                    # prep hardware
                    if event.x_pos is not None or event.y_pos is not None:
                        x = event.x_pos or self.getXPosition()
                        y = event.y_pos or self.getYPosition()
                        self._channel.sigSetXYPosition.emit(x, y)
                    if event.z_pos is not None:
                        self._channel.sigSetZPosition.emit(event.z_pos)
                    if event.exposure is not None:
                        self._channel.sigSetExposure.emit(event.exposure)

                self.__logger.info("MDA Finished: ")
                pass

        '''



        def includePyro(func):
            @Pyro5.server.expose
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        for f in functions:
            func = api_dict[f]
            if hasattr(func, 'module'):
                module = func.module
            else:
                module = func.__module__.split('.')[-1]
            #DEBUGGING: self.__logger.debug("/"+module+"/"+f)
            self.func = includePyro(includeAPI("/"+module+"/"+f, func))



# Copyright (C) 2020-2022 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
