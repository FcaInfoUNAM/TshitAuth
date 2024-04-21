# TShit
FCA UNAM Informática VI

API rest app to teach how to develop from scratch an API using flask

## Required

- python3
- python3-mysql-connector
- flask
- python3-rsa

to install it try the next commands

```pip install flask```

```sudo apt install python3-mysql.connector```
or
```pip install python3-mysql-connector```

to start the app run : ``` flask --app main run --debug ``` 

## clone the repository

```cmd
git clone "{url}"
```
visualiza la estructura de archivos en del repositorio

## Creación de la configuración

Para configurar la autenticación es necesario que conoscas que es un [cifrado RSA](https://www.veritas.com/es/mx/information-center/rsa-encryption#:~:text=Las%20claves%20p%C3%BAblicas%20RSA%20son,con%20un%20resto%20de%201))
En resumen requieres dos llaves, una pública y una privada y existen algunos generadores de llaves como este: [travistidwell](https://travistidwell.com/jsencrypt/demo/) que no se recomiendan en un uso profesional por temas de seguridad.

### PASO1
1. Copia el archivo de configuración config.json.sample a config.json y agrega los siguientes elementos:

```json
{...
"auth":{
        "path":"./auth",
        "pubRsa":"./pub.pem",
        "pvtRsa":"./pvt.pem"
    }
}
```
Analizando el elemento auth del archivo de configuración podemos observar que se agrega una ruta a una carpeta y dos rutas a archivos.
- Los archivos vabn a contener las llaves publicas y privadas correspondientemente que se usaran para el cifrado y descifrado de contraseñas
- La ruta path será un lugar donde almacenaremos los tockens de acceso como archivos .json que contendran la información de un usuario

2. Crea la carpeta auth en la raíz del proyecto
3. Crea los archivos de las llaves en la raíz del proyecto respetando los nombres del archivo de configuración

## Crear un nuevo usuario
Para este caso se utilizará una tabla users en la conexión de mysql (para montar un servidor myslq revista este tutorial de [Digital Ocean](https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-22-04))
## Paso1 (modelo)
1. Crea la tabla en la base de datos y añade al cambio al documento app/database/schema/main.sql
```sql
CREATE TABLE users(
	id varchar(16) PRIMARY KEY,
	name varchar (250),
	user varchar (30),
	email varchar (70) unique,
	status numeric,
	type numeric,
	passwd varchar (532)

);
```
2. Crea en app/models/user.py el modelo user
```python
   class user:
    
    def __init__(self,name:str,user:str,email:str,status:int,type:int,passwd:str):
        self.name = name
        self.user = user
        self.email = email
        self.status = status
        self.type = type
        self.passwd = passwd

    def setId(self,id:str):
        self.id= id
```        
3. Compara este modelo con el modelo proveedor y agrega a tus notas el por qué usamos un método aparte para generar un id 

## Paso2 (controlador)
1. Crea el archivo app/controllers/CtrlUser.py
```python
from app.models.user import user
from app.controllers.CtrlMain import CtrlMain
from app.database.mysqlConn import mysqlConn
import os.path


class CtrlUser(CtrlMain):
    def __init__(self,user:user=None):
        if(user!=None):
            self.user=user
        self.connect = mysqlConn(self.conn)
        self.auth = self.config["auth"]
    
    def generateId(self):
        snowflake=self.snowflake()
        self.user.setId(snowflake) 
    
```

2. Revisa el alchivo CrtlMain y recuerda qué hace la función snowflake

Para este ejercicio vamos a requerir leer y escribir archivos json, encriptar de desencriptar por lo que vamos a requerir agregar las siguientes bibliotecas a CtrlUser
```python
import rsa
import json
import os
import base64
```
3. Agrega la siguiente función
```python
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
```
4. Analiza el código y explica cómo crees que descifraremos la contraseña posteriormente

## Paso3 (enrutamiento con blueprint)

1. Crea el archivo app/modules/auth.py
```python
from flask import Blueprint,request
import json
from app.controllers.CtrlUser import CtrlUser
from app.models.user import user

#Create a blueprint
auth = Blueprint('auth', __name__,template_folder='modules')
keys = ["name","user","email","status","type","passwd","passwd2"]
#CREAR users
@auth.post("/v1/signUp")
def signUp():
    r = request.json
    #validate if contain all data
    for key in keys:
        if not key in r:
            return '{"msg":"missing' +f'"{key}"'+'}',409
    
    if (r["passwd"]!=r["passwd2"]):
        return '{"msg":"password not match"}',409

    u = user(r["name"],r["user"],r["email"],r["status"],r["type"],r["passwd"])
    ctrl= CtrlUser(u)
    insert = ctrl.insert()
    if (insert["insertion"]["code"]==500):
        return json.dumps(insert),409
    return json.dumps(insert["data"]),201

```
2. Explica
   - ¿por qué recibimos pasamos passwd y passwd2?
   - ¿Cómo validamos que se reciban todos los datos necesarios?
## Paso4 (pruebas)
1. Utilizando Postman o algun otro método de consultar añade al body lo siguiente:
```json
{
    "name":"Juan Perez",
    "user":"JP",
    "email":"juanperez@gmail.com"
}
```
2. Explica en qué parte del código mandamos el mensaje de error
3. Manda el siguiente body ahora en el request
```json
{
    "name":"Juan Perez",
    "user":"JP",
    "email":"juanperez@gmail.com",
    "status":1,
    "type":0,
    "passwd":"texto",
    "passwd2":"texto2"
}
```
4. Explica en qué parte del código manejamos la contraseña duplicada
5. Pon el mismo valor en passwd y passwd2 en el body, ejecuta la función y si no tuviste ningún error revisa tu base de datos
6. Responde ¿Por qué la contraseña tiene un valor diferente al que mandamos en el request?

### Generar la autenticación
## Paso 1 (controlador)
1. Agrega el siguiente código y analizalo para responder estas preguntas
 - ¿por qué revisamos si hay un archivo generado?
 - ¿Dónde generamos un archivo?
 - ¿Cuál es el valor que se asigna como nombre al archivo?
 - ¿Cómo evitamos guardar la contraseña en el archivo?
 - ¿Cómo hacemos el descifrado de la contraseña guardada en la base de datos?
```python
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
```
Si revisaste todo el código habrás notado que ocupamos una función que no existe en la clase app/database/mysqlConn.py
para eso crearemos la función search de la siguiente manera
```python
def search(self,tabla:str, values:dict, search:str):
        sql = f"SELECT * FROM {tabla} WHERE "
        sqlSets = []
        for key in values:
            if(type(values[key])is int):
                sqlSets.append( f"{key} = {values[key]}")
            else:
                sqlSets.append( f"{key} = '{values[key]}'")
        if(search == "AND"):
            sql =sql + "AND  ".join(sqlSets)
        if(search == "OR"):
            sql =sql + "OR  ".join(sqlSets)
        try:
            self.cursor.execute(sql)
            myresult = self.cursor.fetchall()
            self.cursor.close()
            return {"code":200,"msg":myresult}
        except (mysql.connector.Error) as e:
            return {"code":309,"msg":e.msg}
```
2. Explica cómo mandarías a mandar a llamar search para validar si el usuario es de tipo 0 y sus estatus es 1
3. Para auxiliarno a revisar si se generaron en la ruta las credenciales crearemos una función llamada kerberos en app/controllers/CtrlMain.py
```python
def kerberos(self,id):
        path = self.auth["path"]
        #validar base de datos
        if (os.path.exists(path+"/"+str(id)+".json")):
            return True
        else:
            return False
```
## Paso 2 (enrutamiento)

1. crea la ruta auth de la siguiente manera en app/modules/auth.py
```python
#Auth
@auth.post("/v1/auth")
def login():
    r = request.json
    authKeys=["email","passwd"]
    for key in authKeys:
            if not key in r:
                return '{"msg":"missing' +f'{key}"'+'}',401
    #hacer authenticación
    ctrl= CtrlUser()
    auth = ctrl.getCredentials(r["email"],r['passwd'])
    if (auth["code"]==200):
        return auth["data"],200
    return auth["msg"] ,auth["code"]
```
2. Responde las siguientes preguntas
   - ¿Cómo validas que te pasen los datos requerido para el logueo?
   - ¿Qué devuelve la función?
   - ¿Cómo usarías el valor devuelto?

## Paso 3 (pruebas)
1.- prueba la función con el usuario y la contraseña previamente creados y analiza cómo implementarías esto un una función previamente creada

### Implementando autenticación en proveedores

en app/modules/proveedores.py agrega las siguientes lineas en la función GetAll después de la instanciación de la clase proveedor ```ctrl = CtrlProveedor()``` 

```python
    authKey = request.args.get("authKey")
    if not(ctrl.kerberos(authKey)):
        return {"msg":"unauthorized"},409
```

debe quedar similar a esto 
```python
@proveedores.route("/v1/proveedor")
def getAll():
    ctrl= CtrlProveedor()
    authKey = request.args.get("authKey")
    if not(ctrl.kerberos(authKey)):
        return {"msg":"unauthorized"},409
    get = ctrl.getAll()
    if(get["get"]["code"]!=200):
        return json.dumps(get["get"]),get["get"]["code"]
    return json.dumps((get["data"])),200

```
1. prueba en postman la url
2. Al marcarte que no tienes acceso agrega lo siguiente al final de la url ```?authKey=``` y el id del usuario previamente creado
3. explica qué sucedió
