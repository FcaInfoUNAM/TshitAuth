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
