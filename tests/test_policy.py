import copy, unittest
from broker import Denied, authorize

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.request={'operation':'gemm','m':1,'n':1,'k':1,'seed':0}; self.policy={'users':{'1000':['gemm']}}
    def test_authorized(self): self.assertEqual(authorize(self.policy,1000,self.request),self.request)
    def test_unknown_uid_and_operation(self):
        with self.assertRaises(Denied): authorize(self.policy,1001,self.request)
        self.request['operation']='shell'
        with self.assertRaises(Denied): authorize(self.policy,1000,self.request)
    def test_spoofed_uid_field_rejected(self):
        self.request['uid']=1000
        with self.assertRaises(Denied): authorize(self.policy,1001,self.request)
    def test_invalid_dimensions(self):
        for bad in [0,129,True,'1',-1]:
            r=dict(self.request,m=bad)
            with self.assertRaises(Denied): authorize(self.policy,1000,r)

if __name__=='__main__': unittest.main()
