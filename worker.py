from glob import escape
import json
import socket
import select
import multiprocessing


import simulator
import message


LOCK = 0
R_LOCK = 1

class Worker(object):
    
    def __init__(self, sock, name, address) -> None:
        self.name = name
        self.sock = sock
        self.pid = None
        self.timeout = 9999
        self.lock = LOCK
        self.worker_sock = self.create_sock(address)
        self.master_sock = None

    @staticmethod
    def create_sock(address):
        """ 创建与master通信的socket
        Args: address: ip端口号 例子: ("127.0.0.1", 8888)

        Return: socket对象
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(address)
        sock.listen(10000)
        return sock

    def run(self):
        """ woker进程

            主要负责与 master通信(如果空闲会给master通信，并且告诉当前read_list的监听数量)
            和 解析收到客户端的请求数据包内容、执行操作。
 
        """
        read_list = []
        client, _, _ = select.select([self.worker_sock], [], [], 100)
        sim = simulator.Simulator() 
        if client:
            cli, _ = self.worker_sock.accept()
            self.master_sock = cli
            read_list.append(self.master_sock)
        
        while True:
            if read_list:
                length = len(read_list)
                self.master_sock.send(str(length).encode())

                r_l, _, _ = select.select(read_list, [], [], self.timeout)

                for fd in r_l:
                    if fd == self.master_sock:
                        g = self.master_sock.recv(1)

                        if g == b'1':
                            c, _ = self.sock.accept()
                            read_list.append(c)
                            print("new client arrive", self.name)
                    else:
                        # 接收数据

                        f = fd.recv(4)
                        if f:
                            head = message.get_msg_length(f)
                            msg = message.get_payload(head)
                            exec_cutstom_func(sim, fd, msg)
                        else:
                            print("client %s close" % str(self.name))
                            read_list.remove(fd)
                            fd.close()
    def make_worker(self):
        """启动一个worker子进程
        """
        return multiprocessing.Process(name="worker_"+str(self.name), target=self.run)


def reply_msg(msgid, sid, result, fd):
    return fd.send(json.dumps([msgid, sid, result]))

def exec_cutstom_func(sim, fd, msg):

    if msg.type == 0:
        get_method = msg.content[0]
        args = msg[1]
        kwargs = msg[2]
        if get_method == 'init':
            """init(self, sid, **sim_params)"""
            sid =  args[0]
            result = simulator.Simulator.init(sid, **kwargs)

        elif get_method == 'create':
            """create(self, num, model, **model_params)"""
            num = args[0]
            model = args[1]
            result = simulator.Simulator.create(num, model, **kwargs)
            

        elif get_method == 'setup_done':
            """setup_done(self)"""
            result = simulator.Simulator.setup_done()
            

        elif get_method == 'step':
            """step(self, time, inputs)"""
            time = args[0]
            inputs = args[1]
            result = simulator.Simulator.step(time, inputs)
            

        elif get_method == 'get_data':
            """get_data(self, outputs)"""
            outputs = args[0]
            result = simulator.Simulator.get_data(outputs)
            

        elif get_method == 'finalize':
            """finalize(self)"""
            result = simulator.Simulator.finalize()
            # 断开链接，删除 这个链接
        else:
            print("error!")
            # 发送错误，断开链接      
            # send_error 
            # reuturn 
    
        reply_msg(1, msg.id, result, fd)
    else:
        # 可能接受一个回复类型的消息。
        print("其他类型")
        # 这个暂时考虑不做处理
