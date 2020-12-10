# -*- coding: utf-8 -*-
import json
import socket
import threading
import messages
import model
import view
import pyaudio
import base64


BUFFER_SIZE = 2 ** 10


class Application(object):

    instance = None

    def __init__(self, args):
        self.args = args
        self.closing = False
        self.host = None
        self.port = None
        self.device = None
        self.receive_worker = None
        self.sock = None
        self.username = None
        self.ui = view.EzChatUI(self)
        Application.instance = self
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.seconds = 1
        self.not_stoped = None
        self.dur = None
        self.frames = None
        self.ready = False

    def execute(self):
        if not self.ui.show():
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except (socket.error, OverflowError):
            self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
            return
        self.receive_worker = threading.Thread(target=self.receive)
        self.receive_worker.start()
        self.ui.loop()

    def receive(self):
        try:
            message = (model.Message(**json.loads(self.receive_all())))
            threading.Thread(target=self.receive).start()
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
            return
        p = pyaudio.PyAudio()
        stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.rate,
                        frames_per_buffer=self.chunk,
                        output=True)
        self.ui.show_message(message.username + ' speaks')
        for i in range(0, int(self.rate / self.chunk * self.seconds * message.duration)):
            stream.write(base64.b64decode(message.message[i].encode("UTF-8")), self.chunk)
        self.ui.show_message(message.username + ' ended speaks')

    def receive_all(self):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += self.sock.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def send(self):
        if self.ready:
            message = model.Message(username=self.username, message=self.frames, duration=self.dur, quit=False)
            try:
                self.sock.sendall(message.marshal())
                self.ui.show_message('Message sended!')
            except (ConnectionAbortedError, ConnectionResetError):
                if not self.closing:
                    self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def record(self):
        self.ui.show_message('Recording!')
        threading.Thread(target=self.recording).start()

    def recording(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.rate,
                        frames_per_buffer=self.chunk,
                        input=True)
        self.frames = []
        self.dur = 0;
        self.not_stoped = True
        while self.not_stoped:
            self.dur+=1
            for i in range(0, int(self.rate / self.chunk * self.seconds)):
                data = stream.read(self.chunk)
                data = base64.b64encode(data)
                data = data.decode("UTF-8")
                self.frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        self.ui.show_message('Finished recording!')
        self.ready = True

    def exit(self):
        self.closing = True
        try:
            self.sock.sendall(model.Message(username=self.username, message=[], duration = 0, quit=True).marshal())
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print(messages.CONNECTION_ERROR)
        finally:
            self.sock.close()