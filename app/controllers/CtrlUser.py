from app.models.user import user
from app.controllers.CtrlMain import CtrlMain
from app.database.mysqlConn import mysqlConn
import os.path
import rsa
import json
import os
import base64


class CtrlUser(CtrlMain):
    def __init__(self,user:user=None):
        if(user!=None):
            self.user=user
        self.connect = mysqlConn(self.conn)
        self.auth = self.config["auth"]
    
    def generateId(self):
        snowflake=self.snowflake()
        self.user.setId(snowflake) 

    def insert(self):
        self.connect.start()
        self.generateId()
        #open file, Aquí abrimos la llave pública con la que vamos a cifrar la contraseña proporcionada
        with open(self.auth["pubRsa"], mode='rb') as pubFile:
            keydata = pubFile.read()
        #load key, Aqí la biblioteca rsa nos pide cargar la llave privada a un objeto rsa para abrirla como una cadena de bytes
        pubKey = rsa.PublicKey.load_pkcs1_openssl_pem(keydata)
        #encrypt, Aquí encriptamos la cadena del password ambas como cadenas de bytes
        rsaPasswd= rsa.encrypt(self.user.passwd.encode('ascii'),pubKey)
        #set as string, para poder manejar las cadenas utilizamos base64, un cifrado que utiliza 64 caracteres para representar las cadenas como un texto legible
        encryptedB64 = base64.b64encode(rsaPasswd)
        encryptedB64Str = encryptedB64.decode()
        #set in object, Aquí guardamos la cadena ya cifrada en el objeto
        self.user.passwd=encryptedB64Str
        #storage in database, utilizando la clase app/database/MysqlConn.py hacemos una inserción
        val = (self.user.id, self.user.name,self.user.user,self.user.email,self.user.status,self.user.type,self.user.passwd)
        insertion = self.connect.insert("users",val)
        return {"insertion":insertion,"data":vars(self.user)}