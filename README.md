# TPLab2

### Лабораторная работа № 2

​	Требуется разработать приложение или программный комплекс, обменивающийся данными по сети в формате JSON, XML или Protocol Buffers.

##### 35 вариант

​	Многопользовательский эхо сервис. Пользователи записывают звук в клиентском приложении и слышат с задержкой звук сразу от всех участников.





В первую очередь был реализован класс Message, описывающий сообщения, которыми будет обмениваться сервер и клиент. Среди его методов был метод marshal, производящий перевод сообщения к формату json.

```python
# -*- coding: utf-8 -*-

import json

END_CHARACTER = "\0"
MESSAGE_PATTERN = "{username}>{message}"
TARGET_ENCODING = "utf-8"


class Message(object):

    def __init__(self, **kwargs):
        self.username = None
        self.message = None
        self.duration = None;
        self.quit = False
        self.__dict__.update(kwargs)

    def __str__(self):
        return MESSAGE_PATTERN.format(**self.__dict__)

    def marshal(self):
        return (json.dumps(self.__dict__) + END_CHARACTER).encode(TARGET_ENCODING)
```



Далее был реализован сервер. 

При запуске сервера с передачей ему порта вызывается метод run, который вызывает функцию listen. Функция listen ожидает подключения новых клиентов и для каждого из них запускает новый поток, их обрабатывающий функцией handle, а также добавляет в множество clients.

```python
    def listen(self):
        self.sock.listen(1)
        while True:
            try:
                client, address = self.sock.accept()
            except OSError:
                print(CONNECTION_ABORTED)
                return
            print(CONNECTED_PATTERN.format(*address))
            self.clients.add(client)
            threading.Thread(target=self.handle, args=(client,)).start()
            
    def run(self):
        print(RUNNING)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("", self.port))
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()
        
if __name__ == "__main__":
    try:
        Server(sys.argv).run()
    except RuntimeError as error:
        print(ERROR_OCCURRED)
        print(str(error))
```

Функция handle ждет от клиента сообщения. Как только она его получает с помощью функции receive, она его преобразует из формата json в объект класса model.Message, проверяет, не является ли это сообщением о прекращении соединения с клиентом и, если нет,  ждет некоторое время и отправляет всем клиентам из clients с помощью функции broadcast.

```python
    def handle(self, client):
        while True:
            try:
                message = model.Message(**json.loads(self.receive(client)))
            except (ConnectionAbortedError, ConnectionResetError):
                print(CONNECTION_ABORTED)
                client.close()
                self.clients.remove(client)
                return
            if message.quit:
                client.close()
                self.clients.remove(client)
                return
            print(message.username + ' speaks')
            time.sleep(10)
            self.broadcast(message)
            
    def broadcast(self, message):
        for client in self.clients:
            client.sendall(message.marshal())

    def receive(self, client):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += client.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]
```



Наконец был реализован клиент. Для его реализации было создано два файла, один из которых(view.py) отвечал за графический интерфейс, а второй(application.py) за основную часть работы. Класс application первым делом запускает метод execute, который запускает метод show графического интерфейса, после чего подключается к серверу и запускает метод receive, принимающий сообщения. Метод show отображает графический интерфейс, после чего спрашивает у пользователя ввести имя пользователя, порт и хост сервера.

```python
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
```

```python
    def show(self):
        self.gui = tkinter.Tk()
        self.gui.title(messages.TITLE)
        self.fill_frame()
        self.gui.protocol(CLOSING_PROTOCOL, self.on_closing)
        return self.input_dialogs()

    def loop(self):
        self.gui.mainloop()

    def fill_frame(self):
        self.frame = tkinter.Frame(self.gui)
        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.message_list = tkinter.Text(self.frame, state=TEXT_STATE_DISABLED)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.message_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
        self.message = tkinter.StringVar()
        self.frame.pack()
        self.record_button = tkinter.Button(self.gui, text=messages.RECORD, command=self.application.record)
        self.record_button.pack()
        self.stop_button = tkinter.Button(self.gui, text=messages.STOP, command=self.stop)
        self.stop_button.pack()
        self.send_button = tkinter.Button(self.gui, text=messages.SEND, command=self.application.send)
        self.send_button.pack()
        
            def input_dialogs(self):
        self.gui.lower()
        self.application.username = simpledialog.askstring(messages.USERNAME, messages.INPUT_USERNAME, parent=self.gui)
        if self.application.username is None:
            return False
        self.application.host = simpledialog.askstring(messages.SERVER_HOST, messages.INPUT_SERVER_HOST,
                parent=self.gui)
        if self.application.host is None:
            return False
        self.application.port = simpledialog.askinteger(messages.SERVER_PORT, messages.INPUT_SERVER_PORT,
                parent=self.gui)
        if self.application.port is None:
            return False
        return True
```

Графический интерфейс также имеет метод show_message, для вывода сообщений в окно для логов.

```python
    def show_message(self, message):
        self.message_list.configure(state=TEXT_STATE_NORMAL)
        self.message_list.insert(tkinter.END, str(message) + END_OF_LINE)
        self.message_list.configure(state=TEXT_STATE_DISABLED)
```

Кнопки графического интерфейса вызывают различные методы класса application, а именно record и send. Единственная кнопка, вызывающая метод самого графического интерфейса вызывает метод stop, который устанавливает значение параметра stopped класса application как True.

Метод receive класса application отвечает за получение сообщений от сервера. После получения сообщения, он запускает в новом потоке функцию rec, отвечающую воспроизведение этого сообщения(работа со звуком осуществляется с помощью модуля pyaudio).

```python
    def receive(self):
        while 1:
            try:
                message = (model.Message(**json.loads(self.receive_all())))
                threading.Thread(target=self.rec, args=(message,)).start()
            except (ConnectionAbortedError, ConnectionResetError):
                if not self.closing:
                    self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
                return

    def rec(self, message):
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
```

Метод send отправляет уже записанное сообщение на сервер.

```python
    def send(self):
        if self.ready:
            message = model.Message(username=self.username, message=self.frames, duration=self.dur, quit=False)
            try:
                self.sock.sendall(message.marshal())
                self.ui.show_message('Message sended!')
            except (ConnectionAbortedError, ConnectionResetError):
                if not self.closing:
                    self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
```

А метод record запускает в новом потоке recording, записывающий звук с микрофона до тех пор, пока параметр stoped не станет равен True, что произойдет после нажатия на кнопку stop графического интерфейса. 

```python
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
```

