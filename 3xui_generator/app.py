import base64, io, json, os, secrets, time, urllib.parse, uuid
from functools import wraps
import qrcode, requests
from flask import Flask, jsonify, request, send_from_directory

PORT = 8099
ROOT = "/app/static"
app = Flask(__name__, static_folder=ROOT)

try:
    CFG = json.load(open("/data/options.json", encoding="utf-8"))
except Exception:
    CFG = {}

BASE = str(CFG.get("3xui_url", os.getenv("3XUI_URL", ""))).rstrip("/")
TOKEN = str(CFG.get("api_token", os.getenv("API_TOKEN", "")))
VERIFY = bool(CFG.get("verify_tls", True))
SERVER_ADDRESS = str(CFG.get("server_address", "")).strip()
SUB_BASE = str(CFG.get("subscription_base_url", "")).rstrip("/")

def call(method, path, **kwargs):
    if not BASE or not TOKEN:
        raise RuntimeError("3x-ui URL/API token is not configured")
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = "Bearer " + TOKEN
    headers.setdefault("Accept", "application/json")
    r = requests.request(method, BASE + path, headers=headers, verify=VERIFY, timeout=25, **kwargs)
    try:
        data = r.json()
    except Exception:
        data = {"success": r.ok, "msg": r.text}
    if r.status_code >= 400 or (isinstance(data, dict) and data.get("success") is False):
        raise RuntimeError(data.get("msg") or f"3x-ui HTTP {r.status_code}")
    return data

def obj(d):
    return d.get("obj") if isinstance(d, dict) else d

def qpath(value):
    return urllib.parse.quote(str(value), safe="")

def normalize(x):
    if not isinstance(x, dict):
        return x
    y = dict(x)
    for k in ("settings", "streamSettings", "sniffing"):
        if isinstance(y.get(k), str):
            try: y[k] = json.loads(y[k])
            except Exception: pass
    return y

def find_client(email):
    raw = obj(call("GET", "/panel/api/clients/get/" + qpath(email))) or {}
    # 3x-ui 3.9.0 returns a hydration object:
    # {"client": {...}, "inboundIds": [...], ...}
    if isinstance(raw, dict) and isinstance(raw.get("client"), dict):
        c = dict(raw["client"])
        if "inboundIds" in raw:
            c["inboundIds"] = raw.get("inboundIds") or []
        return c
    return raw

def client_update_payload(cur, overrides=None):
    overrides = overrides or {}
    c = dict(cur or {})
    c.update(overrides)
    data = {}
    for k in (
        "email","subId","password","auth","flow","security","totalGB","expiryTime",
        "limitIp","limitHwid","tgId","reset","resetDay","resetWeekday","resetMax",
        "trafficReset","trafficResetDay","group","comment","enable"
    ):
        if k in c:
            data[k] = c[k]
    data["id"] = c.get("uuid") or c.get("id") or ""
    if isinstance(c.get("reverse"), dict) and c["reverse"].get("tag"):
        data["reverse"] = {"tag": c["reverse"]["tag"]}
    return data

def find_inbound(iid):
    return normalize(obj(call("GET", f"/panel/api/inbounds/get/{int(iid)}")) or {})

def new_uuid():
    try:
        o = obj(call("GET", "/panel/api/server/getNewUUID"))
        if isinstance(o, str) and o: return o
        if isinstance(o, dict) and (o.get("uuid") or o.get("id")): return o.get("uuid") or o.get("id")
    except Exception:
        pass
    return str(uuid.uuid4())

def reality_keys():
    o = obj(call("GET", "/panel/api/server/getNewX25519Cert")) or {}
    private = o.get("privateKey") or o.get("private_key")
    public = o.get("publicKey") or o.get("public_key")
    if not private or not public:
        raise RuntimeError("3x-ui did not return X25519 keys")
    return private, public

def vless_link(client, inbound, address):
    ss = inbound.get("streamSettings") or {}
    rs = ss.get("realitySettings") or {}
    st = rs.get("settings") or {}
    sid = (rs.get("shortIds") or [""])[0]
    sni = (rs.get("serverNames") or [st.get("serverName", "")])[0]
    params = {
        "type": ss.get("network", "tcp"),
        "security": "reality",
        "pbk": st.get("publicKey", ""),
        "fp": st.get("fingerprint", "chrome"),
        "sni": sni,
        "sid": sid,
        "spx": st.get("spiderX", "/"),
    }
    if client.get("flow"):
        params["flow"] = client["flow"]
    host = address or SERVER_ADDRESS
    if not host:
        raise RuntimeError("Server address is not configured")
    return f"vless://{client.get('uuid') or client.get('id')}@{host}:{inbound.get('port')}?{urllib.parse.urlencode(params)}#{urllib.parse.quote(str(client.get('email','client')), safe='')}"

def client_inbound(email):
    c = find_client(email)
    ids = c.get("inboundIds") or []
    if ids:
        return c, find_inbound(ids[0])
    all_ib = obj(call("GET", "/panel/api/inbounds/list")) or []
    for raw in all_ib:
        ib = normalize(raw)
        if any(x.get("email") == email for x in (ib.get("settings", {}).get("clients") or [])):
            return c, ib
    raise RuntimeError("Inbound for client was not found")

@app.get("/health")
def health(): return jsonify({"ok": True})

@app.get("/")
@app.get("/<path:path>")
def static_files(path=""):
    if path and os.path.exists(os.path.join(ROOT, path)):
        return send_from_directory(ROOT, path)
    return send_from_directory(ROOT, "index.html")

@app.get("/api/status")
def status(): return jsonify(call("GET", "/panel/api/server/status"))

@app.get("/api/panel-info")
def panel_info():
    status_data = call("GET", "/panel/api/server/status")
    update_data = call("GET", "/panel/api/server/getPanelUpdateInfo")
    return jsonify({"success": True, "status": obj(status_data), "update": obj(update_data)})

@app.post("/api/panel-update")
def panel_update():
    result = call("POST", "/panel/api/server/updatePanel", data={})
    return jsonify({"success": True, "obj": obj(result)})

@app.get("/api/panel-update-status")
def panel_update_status():
    return jsonify(call("GET", "/panel/api/server/getUpdateStatus"))

@app.get("/api/settings")
def settings():
    return jsonify({"success": True, "server_address": SERVER_ADDRESS, "subscription_base_url": SUB_BASE})

@app.get("/api/inbounds")
def inbounds():
    rows = [normalize(x) for x in (obj(call("GET", "/panel/api/inbounds/list")) or [])]
    return jsonify({"success": True, "obj": rows})

@app.get("/api/inbounds/<int:iid>")
def inbound_get(iid): return jsonify(find_inbound(iid))

@app.post("/api/inbounds/<int:iid>/enable")
def inbound_enable(iid):
    enabled = bool((request.get_json(silent=True) or {}).get("enable"))
    return jsonify(call("POST", f"/panel/api/inbounds/setEnable/{iid}", json={"enable": enabled}))

@app.post("/api/inbounds/<int:iid>/reset-traffic")
def inbound_reset(iid): return jsonify(call("POST", f"/panel/api/inbounds/{iid}/resetTraffic"))

@app.delete("/api/inbounds/<int:iid>")
def inbound_delete(iid): return jsonify(call("POST", f"/panel/api/inbounds/del/{iid}"))

@app.post("/api/inbounds/<int:iid>/update")
def inbound_update(iid):
    p = request.get_json(silent=True) or {}
    cur = find_inbound(iid)
    data = {k: p[k] for k in ("remark","listen","port","protocol","settings","streamSettings","sniffing") if k in p}
    for k in ("settings","streamSettings","sniffing"):
        if k not in data and k in cur: data[k] = cur[k]
    if isinstance(data.get("settings"), dict):
        data["settings"] = dict(data["settings"])
        data["settings"]["clients"] = cur.get("settings", {}).get("clients", [])
    return jsonify(call("POST", f"/panel/api/inbounds/update/{iid}", json=data))

@app.get("/api/clients")
def clients(): return jsonify(call("GET", "/panel/api/clients/list"))

@app.post("/api/clients/presence")
def client_presence():
    try:
        online = obj(call("POST", "/panel/api/clients/onlines")) or []
    except Exception:
        online = []
    try:
        last = obj(call("POST", "/panel/api/clients/lastOnline")) or {}
    except Exception:
        last = {}
    return jsonify({"success": True, "online": online, "last_online": last})

@app.get("/api/clients/<path:email>")
def client_get(email): return jsonify(find_client(email))

@app.post("/api/clients/<path:email>/update")
def client_update(email):
    p = request.get_json(silent=True) or {}
    cur = find_client(email)
    data = client_update_payload(cur, p)
    return jsonify(call("POST", "/panel/api/clients/update/" + qpath(email), json=data))

@app.post("/api/clients/<path:email>/enable")
def client_enable(email):
    p = request.get_json(silent=True) or {}
    cur = find_client(email)
    data = client_update_payload(cur, {"enable": bool(p.get("enable"))})
    return jsonify(call("POST", "/panel/api/clients/update/" + qpath(email), json=data))

@app.post("/api/clients/<path:email>/reset-traffic")
def client_reset(email): return jsonify(call("POST", "/panel/api/clients/resetTraffic/" + qpath(email)))

@app.post("/api/clients/<path:email>/ips")
def client_ips(email): return jsonify(call("POST", "/panel/api/clients/ips/" + qpath(email)))

@app.post("/api/clients/<path:email>/clear-ips")
def clear_ips(email): return jsonify(call("POST", "/panel/api/clients/clearIps/" + qpath(email)))

@app.post("/api/clients/<path:email>/hwids")
def client_hwids(email): return jsonify(call("POST", "/panel/api/clients/hwids/" + qpath(email)))

@app.delete("/api/clients/<path:email>/clear-hwids")
def clear_hwids(email): return jsonify(call("DELETE", "/panel/api/clients/hwids/" + qpath(email)))

@app.delete("/api/clients/<path:email>")
def client_delete(email): return jsonify(call("POST", "/panel/api/clients/del/" + qpath(email) + "?keepTraffic=0"))

@app.post("/api/clients/bulk-delete")
def bulk_delete():
    emails = (request.get_json(silent=True) or {}).get("emails") or []
    return jsonify(call("POST", "/panel/api/clients/bulkDel", json={"emails": emails}))

@app.post("/api/clients/del-depleted")
def del_depleted(): return jsonify(call("POST", "/panel/api/clients/delDepleted"))

@app.post("/api/clients/del-orphans")
def del_orphans(): return jsonify(call("POST", "/panel/api/clients/delOrphans"))

@app.get("/api/clients/<path:email>/link")
def existing_link(email):
    p = request.args.get("server_address") or SERVER_ADDRESS
    c, ib = client_inbound(email)
    link = vless_link(c, ib, p)
    sub = f"{SUB_BASE}/{qpath(c.get('subId'))}" if SUB_BASE and c.get("subId") else None
    return jsonify({"success": True, "link": link, "subscription": sub, "client": c, "inbound": ib})

@app.post("/api/inbounds/create")
def inbound_create():
    p = request.get_json(silent=True) or {}
    address = str(p.get("server_address") or SERVER_ADDRESS).strip()
    sni, dest = str(p.get("sni","")).strip(), str(p.get("dest","")).strip()
    if not address or not sni or not dest:
        return jsonify({"success":False,"msg":"server address, SNI and destination are required"}),400
    private, public = reality_keys()
    sid = secrets.token_hex(8)
    inbound = {
        "remark": p.get("remark") or "VLESS Reality",
        "enable": True,
        "listen": "",
        "port": int(p.get("port") or 443),
        "protocol": "vless",
        "expiryTime": 0,
        "total": 0,
        "settings": {"clients": [], "decryption": "none", "fallbacks": []},
        "streamSettings": {"network":"tcp","security":"reality","realitySettings":{
            "show":False,"xver":0,"dest":dest,"serverNames":[sni],"privateKey":private,
            "shortIds":[sid],"settings":{"publicKey":public,"fingerprint":p.get("fingerprint","chrome"),"serverName":sni,"spiderX":"/"}}},
        "sniffing":{"enabled":True,"destOverride":["http","tls","quic"],"metadataOnly":False,"routeOnly":False}
    }
    added = obj(call("POST", "/panel/api/inbounds/add", json=inbound)) or {}
    iid = added.get("id") or added.get("inboundId") or (added.get("inbound") or {}).get("id")
    if not iid:
        # 3x-ui may return only a success message; resolve the newly created inbound by port/remark.
        rows = [normalize(x) for x in (obj(call("GET", "/panel/api/inbounds/list")) or [])]
        matches = [x for x in rows if int(x.get("port",0) or 0) == int(inbound["port"]) and x.get("remark") == inbound["remark"]]
        if len(matches) == 1:
            iid = matches[0].get("id")
    if not iid:
        raise RuntimeError("Inbound created but ID was not returned")
    return jsonify({"success":True,"inbound":find_inbound(int(iid))})

@app.post("/api/clients/create")
def client_create():
    p = request.get_json(silent=True) or {}
    email = str(p.get("email","")).strip()
    address = str(p.get("server_address") or SERVER_ADDRESS).strip()
    iid = int(p.get("inbound_id") or 0)
    if not email or not address or not iid:
        return jsonify({"success":False,"msg":"email, server address and inbound are required"}),400
    ib = find_inbound(iid)
    if not ib:
        raise RuntimeError("Inbound not found")
    existing = None
    try:
        existing = find_client(email)
    except Exception:
        existing = None
    attached = (existing or {}).get("inboundIds") or []
    if existing and iid in [int(x) for x in attached]:
        raise RuntimeError("Client with this email is already attached to this inbound")
    client = {
        "id": new_uuid(),
        "email": email,
        "flow": p.get("flow","xtls-rprx-vision"),
        "totalGB": int(float(p.get("total_gb",0) or 0) * 1024**3),
        "expiryTime": 0 if int(p.get("days",0) or 0) <= 0 else int((time.time()+int(p["days"])*86400)*1000),
        "enable": True,
        "limitIp": int(p.get("ip_limit",0) or 0),
        "limitHwid": int(p.get("hwid_limit",0) or 0)
    }
    call("POST", "/panel/api/clients/add", json={"client":client,"inboundIds":[iid]})
    c = find_client(email)
    ib = find_inbound(iid)
    link = vless_link(c, ib, address)
    sub = f"{SUB_BASE}/{qpath(c.get('subId'))}" if SUB_BASE and c.get("subId") else None
    return jsonify({"success":True,"client":c,"inbound":ib,"link":link,"subscription":sub})

@app.post("/api/setup")
def setup_inbound_client():
    p = request.get_json(silent=True) or {}
    email = str(p.get("email","")).strip()
    address = str(p.get("server_address") or SERVER_ADDRESS).strip()
    sni, dest = str(p.get("sni","")).strip(), str(p.get("dest","")).strip()
    port = int(p.get("port") or 443)
    if not email or not address or not sni or not dest:
        return jsonify({"success":False,"msg":"email, server address, SNI and destination are required"}),400
    try:
        existing = find_client(email)
    except Exception:
        existing = None
    if existing:
        raise RuntimeError("Client with this email already exists. Use «Добавить клиента» for an existing client.")
    private, public = reality_keys()
    sid = secrets.token_hex(8)
    inbound = {
        "remark": p.get("remark") or "VLESS Reality", "enable": True, "listen": "",
        "port": port, "protocol": "vless", "expiryTime": 0, "total": 0,
        "settings": {"clients": [], "decryption": "none", "fallbacks": []},
        "streamSettings": {"network":"tcp","security":"reality","realitySettings":{
            "show":False,"xver":0,"dest":dest,"serverNames":[sni],"privateKey":private,
            "shortIds":[sid],"settings":{"publicKey":public,"fingerprint":p.get("fingerprint","chrome"),
            "serverName":sni,"spiderX":"/"}}},
        "sniffing":{"enabled":True,"destOverride":["http","tls","quic"],"metadataOnly":False,"routeOnly":False}
    }
    iid = None
    try:
        added = obj(call("POST", "/panel/api/inbounds/add", json=inbound)) or {}
        iid = added.get("id") or added.get("inboundId") or (added.get("inbound") or {}).get("id")
        if not iid:
            rows = [normalize(x) for x in (obj(call("GET", "/panel/api/inbounds/list")) or [])]
            matches = [x for x in rows if int(x.get("port",0) or 0) == port and x.get("remark") == inbound["remark"]]
            if len(matches) == 1: iid = matches[0].get("id")
        if not iid: raise RuntimeError("Inbound created but ID was not returned")
        client = {
            "email": email, "flow": p.get("flow","xtls-rprx-vision"),
            "totalGB": int(float(p.get("total_gb",0) or 0) * 1024**3),
            "expiryTime": 0 if int(p.get("days",0) or 0) <= 0 else int((time.time()+int(p["days"])*86400)*1000),
            "enable": True, "limitIp": int(p.get("ip_limit",0) or 0),
            "limitHwid": int(p.get("hwid_limit",0) or 0)
        }
        call("POST", "/panel/api/clients/add", json={"client":client,"inboundIds":[int(iid)]})
    except Exception:
        if iid:
            try: call("POST", f"/panel/api/inbounds/del/{int(iid)}")
            except Exception: pass
        raise
    c = find_client(email); ib = find_inbound(int(iid))
    link = vless_link(c, ib, address)
    sub = f"{SUB_BASE}/{qpath(c.get('subId'))}" if SUB_BASE and c.get("subId") else None
    return jsonify({"success":True,"inbound":ib,"client":c,"link":link,"subscription":sub,
                    "reality":{"public_key":public,"short_id":sid,"sni":sni,"dest":dest,
                    "fingerprint":p.get("fingerprint","chrome"),"flow":p.get("flow","xtls-rprx-vision")}})

@app.post("/api/generate")
def generate():
    p = request.get_json(silent=True) or {}
    email = str(p.get("email", "")).strip()
    address = str(p.get("server_address") or SERVER_ADDRESS).strip()
    sni, dest = str(p.get("sni","")).strip(), str(p.get("dest","")).strip()
    if not email or not address or not sni or not dest:
        return jsonify({"success":False,"msg":"email, server address, SNI and destination are required"}),400
    private, public = reality_keys()
    sid = secrets.token_hex(8)
    inbound = {
        "remark": p.get("remark") or "VLESS Reality", "enable": True,
        "port": int(p.get("port") or 443), "protocol": "vless",
        "settings": {"clients": [], "decryption": "none", "fallbacks": []},
        "streamSettings": {"network":"tcp","security":"reality","realitySettings":{
            "show":False,"xver":0,"dest":dest,"serverNames":[sni],"privateKey":private,
            "shortIds":[sid],"settings":{"publicKey":public,"fingerprint":p.get("fingerprint","chrome"),"serverName":sni,"spiderX":"/"}}},
        "sniffing":{"enabled":True,"destOverride":["http","tls","quic"],"metadataOnly":False,"routeOnly":False}
    }
    added = obj(call("POST", "/panel/api/inbounds/add", json=inbound)) or {}
    iid = added.get("id") or added.get("inboundId") or (added.get("inbound") or {}).get("id")
    if not iid: raise RuntimeError("Inbound created but ID was not returned")
    client = {"id":new_uuid(),"email":email,"flow":p.get("flow","xtls-rprx-vision"),
              "totalGB":int(float(p.get("total_gb",0))*1024**3),
              "expiryTime":0 if int(p.get("days",0) or 0)<=0 else int((time.time()+int(p["days"])*86400)*1000),
              "enable":True,"limitIp":int(p.get("ip_limit",0) or 0),"limitHwid":int(p.get("hwid_limit",0) or 0)}
    call("POST", "/panel/api/clients/add", json={"client":client,"inboundIds":[int(iid)]})
    c, ib = client_inbound(email)
    link = vless_link(c, ib, address)
    sub = f"{SUB_BASE}/{qpath(c.get('subId'))}" if SUB_BASE and c.get("subId") else None
    return jsonify({"success":True,"inbound":ib,"client":c,"link":link,"subscription":sub,
                    "reality":{"public_key":public,"short_id":sid,"sni":sni,"dest":dest,
                               "fingerprint":p.get("fingerprint","chrome"),"flow":p.get("flow","xtls-rprx-vision")}})

@app.post("/api/qr")
def qr():
    link = str((request.get_json(silent=True) or {}).get("link",""))
    if not link.startswith("vless://"): return jsonify({"success":False,"msg":"Invalid VLESS link"}),400
    b=io.BytesIO(); qrcode.make(link).save(b,format="PNG")
    return jsonify({"success":True,"png_base64":base64.b64encode(b.getvalue()).decode()})

@app.errorhandler(Exception)
def error(e): return jsonify({"success":False,"msg":str(e)}),502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
