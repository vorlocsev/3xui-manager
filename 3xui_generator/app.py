import base64,io,json,os,secrets,urllib.parse,uuid
from functools import wraps
import requests
from flask import Flask,request,jsonify,send_from_directory
import qrcode

PORT=8099
ROOT="/app/static"
app=Flask(__name__,static_folder=ROOT)
try:
    CFG=json.load(open("/data/options.json"))
except Exception:
    CFG={}
CFG.update({k:v for k,v in {
    "3xui_url":os.getenv("3XUI_URL",""),
    "api_token":os.getenv("API_TOKEN",""),
    "verify_tls":True,
    "server_address":"",
    "subscription_base_url":""
}.items() if k not in CFG})
BASE=str(CFG.get("3xui_url","")).rstrip("/")
VERIFY=bool(CFG.get("verify_tls",True))
TOKEN=str(CFG.get("api_token",""))
S=requests.Session()
S.headers.update({"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"})

def call(method,path,**kw):
    if not BASE: raise RuntimeError("3x-ui URL is not configured")
    r=S.request(method,BASE+path,verify=VERIFY,timeout=20,**kw)
    try: d=r.json()
    except Exception: d={"success":False,"msg":r.text}
    if r.status_code>=400 or d.get("success") is False: raise RuntimeError(d.get("msg") or f"HTTP {r.status_code}")
    return d
def obj(d): return d.get("obj") if isinstance(d,dict) else None
def auth(f):
    @wraps(f)
    def w(*a,**k): return f(*a,**k)
    return w
def xkey():
    d=call("POST","/panel/api/server/getNewX25519Cert")
    o=obj(d) or {}
    return o.get("privateKey") or o.get("private_key"),o.get("publicKey") or o.get("public_key")
def find_client(email):
    d=call("GET","/panel/api/clients/get/"+urllib.parse.quote(email,safe=""))
    return obj(d) or {}
def find_inbound(iid):
    return obj(call("GET",f"/panel/api/inbounds/get/{iid}")) or {}
def vlink(c,ib,address):
    rs=(ib.get("streamSettings") or {}).get("realitySettings") or {}
    st=rs.get("settings") or {}
    sid=(rs.get("shortIds") or [""])[0]
    sni=(rs.get("serverNames") or [st.get("serverName","")])[0]
    q={"type":"tcp","security":"reality","pbk":st.get("publicKey",""),"fp":st.get("fingerprint","chrome"),"sni":sni,"sid":sid,"spx":st.get("spiderX","/")}
    flow=c.get("flow") or "xtls-rprx-vision"
    if flow:q["flow"]=flow
    return "vless://"+str(c.get("id") or c.get("uuid"))+"@"+address+":"+str(ib.get("port"))+"?"+urllib.parse.urlencode(q,quote_via=urllib.parse.quote)+"#"+urllib.parse.quote(str(c.get("email","client")),safe="")
@app.get("/")
def index(): return send_from_directory(ROOT,"index.html")
@app.get("/health")
def health(): return jsonify({"ok":True})
@app.get("/api/status")
def status():
    d=call("GET","/panel/api/server/status")
    return jsonify(d)
@app.get("/api/inbounds")
def inbounds(): return jsonify(call("GET","/panel/api/inbounds/list"))
@app.get("/api/inbounds/<int:iid>")
def inbound(iid): return jsonify(call("GET",f"/panel/api/inbounds/get/{iid}"))
@app.post("/api/inbounds/<int:iid>/enable")
def inbound_enable(iid):
    en=bool((request.get_json(silent=True) or {}).get("enable"))
    return jsonify(call("POST",f"/panel/api/inbounds/setEnable/{iid}",json={"enable":en}))
@app.post("/api/inbounds/<int:iid>/reset-traffic")
def inbound_reset(iid): return jsonify(call("POST",f"/panel/api/inbounds/{iid}/resetTraffic"))
@app.delete("/api/inbounds/<int:iid>")
def inbound_delete(iid): return jsonify(call("POST",f"/panel/api/inbounds/del/{iid}"))
@app.get("/api/clients")
def clients(): return jsonify(call("GET","/panel/api/clients/list"))
@app.get("/api/clients/<path:email>")
def client(email): return jsonify(find_client(email))
@app.post("/api/clients/<path:email>/enable")
def client_enable(email):
    c=find_client(email); p=request.get_json(silent=True) or {}
    data={k:c.get(k,0) for k in ("id","email","totalGB","expiryTime","limitIp","limitHwid","flow","tgId","subId")}
    data["enable"]=bool(p.get("enable"))
    return jsonify(call("POST","/panel/api/clients/update/"+urllib.parse.quote(email,safe=""),json=data))
@app.post("/api/clients/<path:email>/reset-traffic")
def client_reset(email): return jsonify(call("POST","/panel/api/clients/resetTraffic/"+urllib.parse.quote(email,safe="")))
@app.delete("/api/clients/<path:email>")
def client_delete(email): return jsonify(call("POST","/panel/api/clients/del/"+urllib.parse.quote(email,safe="")))
@app.post("/api/clients/<path:email>/ips")
def client_ips(email): return jsonify(call("POST","/panel/api/clients/ips/"+urllib.parse.quote(email,safe="")))
@app.post("/api/clients/<path:email>/clear-ips")
def clear_ips(email): return jsonify(call("POST","/panel/api/clients/clearIps/"+urllib.parse.quote(email,safe="")))
@app.post("/api/clients/<path:email>/hwids")
def client_hwids(email): return jsonify(call("POST","/panel/api/clients/hwids/"+urllib.parse.quote(email,safe="")))
@app.post("/api/clients/<path:email>/clear-hwids")
def clear_hwids(email): return jsonify(call("POST","/panel/api/clients/clearHwids/"+urllib.parse.quote(email,safe="")))
@app.post("/api/generate")
def generate():
    p=request.get_json(silent=True) or {}; email=str(p.get("email","")).strip()
    address=str(p.get("server_address") or CFG.get("server_address","")).strip()
    sni=str(p.get("sni","")).strip(); dest=str(p.get("dest","")).strip()
    if not email or not address or not sni or not dest: return jsonify({"success":False,"msg":"email, server address, SNI and destination are required"}),400
    private,public=xkey(); sid=secrets.token_hex(8)
    iid=obj(call("POST","/panel/api/inbounds/add",json={
      "remark":p.get("remark") or "VLESS Reality","enable":True,"port":int(p.get("port") or 443),"protocol":"vless",
      "settings":{"clients":[],"decryption":"none","fallbacks":[]},
      "streamSettings":{"network":"tcp","security":"reality","realitySettings":{"show":False,"xver":0,"dest":dest,"serverNames":[sni],"privateKey":private,"shortIds":[sid],"settings":{"publicKey":public,"fingerprint":p.get("fingerprint","chrome"),"serverName":sni,"spiderX":"/"}}},
      "sniffing":{"enabled":True,"destOverride":["http","tls","quic"]}
    })) or {}
    iid=iid.get("id") or iid.get("inboundId")
    c={"id":str(uuid.uuid4()),"email":email,"flow":p.get("flow","xtls-rprx-vision"),"totalGB":int(float(p.get("total_gb",0))*1024**3),"expiryTime":0,"enable":True,"limitIp":int(p.get("ip_limit",0) or 0),"limitHwid":int(p.get("hwid_limit",0) or 0)}
    call("POST","/panel/api/clients/add",json={"client":c,"inboundIds":[int(iid)]})
    c=find_client(email); ib=find_inbound(int(iid)); link=vlink(c,ib,address)
    return jsonify({"success":True,"inbound":ib,"client":c,"link":link})
@app.post("/api/qr")
def qr():
    link=str((request.get_json(silent=True) or {}).get("link",""))
    if not link.startswith("vless://"): return jsonify({"success":False,"msg":"Invalid VLESS link"}),400
    b=io.BytesIO(); qrcode.make(link).save(b,format="PNG")
    return jsonify({"success":True,"png_base64":base64.b64encode(b.getvalue()).decode()})
@app.errorhandler(Exception)
def err(e): return jsonify({"success":False,"msg":str(e)}),502
if __name__=="__main__": app.run("0.0.0.0",PORT)
