import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from web3 import Web3

class AESCipher(object):

  def __init__(self, key, config):
    self.bs = AES.block_size
    self.key = hashlib.sha256(key.encode()).digest()
    self.config = config
    self.w3 = Web3(Web3.HTTPProvider(self.config["airdao_main_rpc"]))

  def encrypt(self, raw):
    raw = self._pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(self.key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw.encode()))

  def decrypt(self, enc):
    enc = base64.b64decode(enc)
    iv = enc[:AES.block_size]
    cipher = AES.new(self.key, AES.MODE_CBC, iv)
    return AESCipher._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

  def _pad(self, s):
    return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
  
  def create_wallet(self):
    wallet = self.w3.eth.account.create()
    address = wallet.address
    private_key = wallet._private_key.hex()
    encrypted_private_key = self.encrypt(private_key),
    return address, encrypted_private_key
  
  def decrypt_wallet(self, encrypted_private_key):
    return self.decrypt(encrypted_private_key)

  @staticmethod
  def _unpad(s):
    return s[:-ord(s[len(s)-1:])]
    
if __name__ == "__main__":
  key = "12345"
  config = {
    "airdao_main_rpc": "https://network.ambrosus-test.io"
  }
  cipher = AESCipher(key, config)
  address, encrypted_private_key = cipher.create_wallet()
  print(len(encrypted_private_key[0]))
  print(encrypted_private_key[0])
  print(f"Address: {address}")
  print(f"Encrypted Private Key: {encrypted_private_key}") # store encrypted private keys in database
  print(f"Decrypted Private Key: {cipher.decrypt(encrypted_private_key[0])}")
  
 
  
  