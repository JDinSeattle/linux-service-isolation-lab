import json,pathlib,socket,tempfile,threading,time,unittest
from broker import Broker

class RpcLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
        self.broker=Broker(self.root/'rpc.sock',{'version':1,'users':{}},'/not-executed','/not-executed',self.root,request_timeout=.15)
    def tearDown(self):self.broker.close();self.tmp.cleanup()
    def start(self):
        self.results=[];self.errors=[]
        def serve():
            try:self.results.append(self.broker.serve_one())
            except Exception as e:self.errors.append(e)
        t=threading.Thread(target=serve);t.start();return t
    def call(self,data):
        t=self.start()
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c:
            c.connect(str(self.broker.path));c.sendall(data);c.shutdown(socket.SHUT_WR);raw=b''
            while block:=c.recv(4096):raw+=block
        t.join(2);self.assertFalse(t.is_alive());self.assertFalse(self.errors)
        return json.loads(raw)
    def test_malformed_and_truncated_then_next_peer(self):
        for data in [b'{\n',b'{',b'x'*4097+b'\n']:
            self.assertFalse(self.call(data)['authorized'])
        self.assertIn('operation not granted',self.call(b'{"operation":"gemm","m":1,"n":1,"k":1,"seed":0}\n')['reason'])
    def test_slow_sender_cannot_reset_total_deadline(self):
        t=self.start();start=time.monotonic()
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c:
            c.connect(str(self.broker.path))
            for _ in range(8):
                try:c.sendall(b' ')
                except OSError:break
                time.sleep(.04)
            raw=c.recv(4096)
        t.join(1);self.assertFalse(t.is_alive());self.assertFalse(self.errors)
        self.assertLess(time.monotonic()-start,.6);self.assertFalse(json.loads(raw)['authorized'])
    def test_disconnected_peer_does_not_kill_broker(self):
        t=self.start()
        c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(self.broker.path));c.close()
        t.join(1);self.assertFalse(t.is_alive());self.assertFalse(self.errors)
        self.assertFalse(self.call(b'{}\n')['authorized'])
    def test_close_does_not_remove_replacement_path(self):
        self.broker.path.unlink();self.broker.path.write_text('replacement')
        self.broker.close();self.assertEqual(self.broker.path.read_text(),'replacement')
