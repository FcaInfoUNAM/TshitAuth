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
    
    def getCredentials(self,email,passwd):
        path = self.auth["path"]
        #validar base de datos
        self.connect.start()
        get = self.connect.search("users",{"email":email}, "AND")
        if(len(get["msg"])==0):
            get["get"]={"code":204,"msg":"No content"}
        #gen user object
        self.user = user(get["msg"][0][1], get["msg"][0][2],get["msg"][0][3],str(get["msg"][0][4]),str(get["msg"][0][5]),get["msg"][0][6])
        self.user.setId(get["msg"][0][0])
        #validar archivo en path
        if (os.path.isfile(path+"/"+self.user.id+".json")):
            return {"code":200,"data":self.user.id}

        #validar passwd
        #open file
        with open(self.auth["pvtRsa"], mode='rb') as pvtFile:
            keydata = pvtFile.read()
        #load key as bynary
        pvtKey = rsa.PrivateKey.load_pkcs1(keydata)
        #set b64 as binary
        encrypted_b64 = self.user.passwd.encode()
        encrypted = base64.b64decode(encrypted_b64)
        #decrypt
        decypted = rsa.decrypt(encrypted, pvtKey)
        passwdDecrypted = decypted.decode()
        if passwd != passwdDecrypted:
            return {"code":401,"msg":"wrong password"}
        
        #set in object
        self.user.passwd=""

        #escribir credenciales en servidor
        with open(path+"/"+f"{self.user.id}.json", 'w') as file:
            json.dump(vars(self.user), file)
        #regresar llave
        return {"code":200,"get":get,"data":self.user.id}