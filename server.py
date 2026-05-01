import http.server
import json
import socketserver
import os
import gzip
import threading
import hashlib
import queue
import socket

DEFAULT_PROGRAMS = [
    {"number":"01","type":"舞蹈","title":"双生","performer":"高二2班 宋俊航、高二14班 祝婉诗","desc":"这支舞蹈演绎一场关于自我平衡与心灵觉醒的成长之旅。每个人内心都存在两面自我：一面迷茫脆弱，一面坚韧向阳。作品通过肢体拉扯、对峙与和解的演绎，诠释接纳自我、打破内耗、重塑内心，最终完成成长蜕变的人生主题。"},
    {"number":"02","type":"舞蹈","title":"Wonderful U","performer":"高一30班 黄心妍","desc":"以温柔且有力量的现代舞肢体表达，诠释青春路上的自我成长与破茧蜕变，传递直面困境、心怀暖阳、向阳而生的坚定力量。"},
    {"number":"03","type":"舞蹈","title":"No Doubt","performer":"高二16班 刘宝莲、高二26班 莫子婷、高二13班 梁绮琳、高二6班 袁梓妍、高二3班 叶乐怡、高二27班 陈蜜儿、高一29班 吴心妍","desc":"整支舞蹈围绕友情主题展开，演绎绵绵思念与内心牵绊，诠释朋友之间不离不弃、彼此守护、坚信情谊永恒不变的初心与信念。"},
    {"number":"04","type":"舞蹈","title":"La La Land","performer":"高二13班 韩诗嘉、高二24班 袁嘉淇、高二20班 袁娜娜、高二24班 钟梓妍、高二24班 区梓瑶、高二27班 周霏霏、高二17班 苏莉莉、高二24班 贺嘉宝、高一25班 莫蕴晴、高二6班 郭忆楠、高二31班 肖雅徽、高一5班 崔思宜、高二31班 方梓妍、高二10班 李楚烨、高一3班 雷焮熠、高二23班 廖茵潼、高二13班 孙思敏、高二7班 钟紫珊、高二19班 刘鑫恺、高二4班 莫雯莉、高二23班 刘婉忻","desc":"舞步浪漫灵动，旋律温柔缱绻。作品借拉丁舞的风情韵律，演绎逐梦路上的欢喜与怅惘，展现奔赴理想时的昂扬姿态与浪漫情怀。"},
    {"number":"05","type":"舞蹈","title":"乡愁无边","performer":"高一25班 洪欣楠","desc":"改编自余光中经典诗作《乡愁》，以古典舞含蓄温婉的肢体语言，寄托对故土家园的绵长思念与悠悠情怀，意境悠远，共情满满。"},
    {"number":"06","type":"舞蹈","title":"非人哉","performer":"高二18班 汪奥雪、高二27班 陈相远、高二18班 黄蔼佳、高二23班 陈婧欢、高二18班 万玥澜、高二29班 林嘉韵、高二3班 叶乐怡、高二12班 聂琪、高二21班 杨晨、高二25班 肖瑾萱","desc":"融合国风元素与元气宅舞风格，以灵动轻快的舞步勾勒国风韵味，用少年元气活力燃动舞台，尽显青春朝气与国风魅力。"},
    {"number":"07","type":"舞蹈","title":"姑娘的红裙","performer":"高二31班 王雅熙","desc":"以彝族少女的成长心境与青涩情愫为主线，萃取彝族传统舞蹈动律特色。以红裙为情感符号，勾勒少女的灵动俏皮、对生活的热爱以及对美好未来的无限向往，将民族文化与青春诗意完美融合。"},
    {"number":"08","type":"舞蹈","title":"月亮弯弯","performer":"高二8班 宾恩儿、高二9班 卢泳桥、高二8班 邵若曦、高二29班 何晟琳、高二23班 马艺宸、高二23班 陈佳安、高一22班 杨梓玉、高二2班 宋俊航、高二31班 张秀鑫、高二5班 高妍、高二31班 周盈、高二27班 陈蜜儿、高一9班 桂梓涵、高一28班 罗海璇、高一16班 李雅琳、高一30班 蒋丰远","desc":"作品意境古朴恢宏，以舞蹈演绎家国情怀与少年担当。月色苍茫，山河壮阔，舞者以刚柔并济的舞姿，诠释君子生于乱世、心怀家国、舍身逐光、勇担使命的崇高志向。"},
    {"number":"09","type":"舞蹈","title":"藤蔓花","performer":"高二25班 杨紫怡、高二18班 冯雨薇","desc":"作品取材自然意象，以傣族经典「三道弯」舞姿为核心，用柔婉的手臂与腰肢，模拟蔓藤缠绕、繁花摇曳的灵动姿态。尽显傣族舞蹈的柔美韵律，诠释草木生生不息的坚韧，尽显自然之美与民族风情。"},
    {"number":"10","type":"舞蹈","title":"More Jump More","performer":"高二20班 陈秀妍、高二11班 钱宝媛、高二30班 李嘉怡、高二29班 林嘉韵、高二29班 廖芷甄","desc":"以跳跃律动为核心编排，节奏轻快、动作元气满满，尽情展现当代少年肆意洒脱、奔赴热爱、活力满满的青春风采。"},
    {"number":"11","type":"舞蹈","title":"咏春","performer":"高二6班 袁梓妍、高二6班 郭忆楠、高二13班 梁绮琳、高二20班 何泳潼、高二24班 李诗棋、高二26班 王子莹、高二26班 梁钰熙","desc":"扇影翩跹，温婉雅致。舞者以轻盈身段、灵动扇舞传情达意，一颦一笑皆是东方古韵，举手投足尽显咏春诗意风雅与古典温婉气质。"},
    {"number":"12","type":"舞蹈","title":"迦陵频伽","performer":"高二31班 郑铭佩、高二31班 王雅熙、高二31班 张秀鑫、高二31班 周盈","desc":"取材莫高窟经典壁画，以传说中人首鸟身、声韵绝美的迦陵频伽神鸟为原型。依托敦煌乐舞根基，结合古典舞舞姿形态，用翘三指、小跳步等经典身段，还原神鸟振翅栖居、随梵音起舞的空灵画面，带观众穿越千年，沉浸式感受敦煌舞蹈的神韵与灵动。"},
    {"number":"13","type":"舞蹈","title":"Maestro","performer":"高一30班 蒋丰远","desc":"以街舞强劲节奏为底色，化身舞台节奏掌控者。用利落舒展的肢体动作，勾勒节拍秩序，释放少年力量感与气场，演绎街舞独有的律动之美、力量之美。"}
]

DEFAULT_HOSTS = [
    {"name": "主持人", "title": "晚会主持人", "photo": "", "bio": "在这里填写主持人的个人介绍和履历。"}
]

DEFAULT_PRESETS = [
    {"name": "默认", "left": {"hostIndex": 0}, "right": {"hostIndex": 0}, "color": "rose"}
]

HOSTS_FILE = "hosts.json"
PROGRAMS_FILE = "programs.json"
PRESETS_FILE = "presets.json"
SETTINGS_FILE = "settings.json"

_file_cache = {}

def load_json_file(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                _file_cache[filename] = data
                return data
    except:
        pass
    return default

def save_json_file(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        _file_cache[filename] = data
        return True
    except:
        return False

PROGRAMS = load_json_file(PROGRAMS_FILE, DEFAULT_PROGRAMS)
HOSTS = load_json_file(HOSTS_FILE, DEFAULT_HOSTS)
PRESETS = load_json_file(PRESETS_FILE, DEFAULT_PRESETS)
SETTINGS = load_json_file(SETTINGS_FILE, {"theme": "dark"})

STATE = {
    "theme": SETTINGS.get("theme", "dark"),
    "team1": 0, "team2": 0, "hidden": False,
    "team1Name": "红队", "team1Class": "一班",
    "team2Name": "蓝队", "team2Class": "二班",
    "gameClock": 720, "shotClock": 24,
    "period": 1, "timerRunning": False,
    "team1Fouls": 0, "team2Fouls": 0,
    "showClass": True,
    "programIndex": 0,
    "programHidden": False,
    "logoHidden": False,
    "logoMode": "alternate",
    "hostHidden": True,
    "hostIndex": 0,
    "programs": PROGRAMS,
    "hosts": HOSTS,
    "leftHostHidden": True,
    "leftHostIndex": 0,
    "leftColor": "rose",
    "rightHostHidden": True,
    "rightHostIndex": 0,
    "rightColor": "blue",
    "presets": PRESETS,
    "hostSlots": [
        {"hostIndex": 0, "hidden": False, "color": "rose"},
        {"hostIndex": 1, "hidden": False, "color": "purple"},
        {"hostIndex": 2, "hidden": False, "color": "blue"},
        {"hostIndex": 3, "hidden": False, "color": "green"}
    ],
    "hostSlotCount": 2,
    "hostsAllHidden": True,
    "logoImgX": 40, "logoImgY": 40, "logoImgHidden": False,
    "hostX": 25, "hostY": 20,
    "logoX": 47, "logoY": 49,
}

# ══════════════════════════════════════
#  State Cache
# ══════════════════════════════════════
_state_lock = threading.Lock()
_state_json_cache = None
_state_gzip_cache = None
_state_hash = None
_lite_json_cache = None
_lite_gzip_cache = None
_lite_hash = None
_sse_msg_bytes = None

def _build_lite():
    hs = STATE.get("hostSlots", [])
    ah = STATE.get("hostsAllHidden", True)
    r = {
        "theme": STATE["theme"],
        "programIndex": STATE["programIndex"],
        "programHidden": STATE["programHidden"],
        "hidden": STATE["hidden"],
        "logoHidden": STATE["logoHidden"],
        "hostsAllHidden": ah,
        "hostSlotCount": STATE["hostSlotCount"],
        "hostSlots": hs,
        "hostX": STATE.get("hostX", 25),
        "hostY": STATE.get("hostY", 20),
        "team1": STATE["team1"],
        "team2": STATE["team2"],
        "team1Fouls": STATE["team1Fouls"],
        "team2Fouls": STATE["team2Fouls"],
        "team1Name": STATE["team1Name"],
        "team1Class": STATE["team1Class"],
        "team2Name": STATE["team2Name"],
        "team2Class": STATE["team2Class"],
        "showClass": STATE["showClass"],
        "logoX": STATE["logoX"],
        "logoY": STATE["logoY"],
    }
    if len(hs) >= 1:
        r["leftHostHidden"] = hs[0].get("hidden", False) or ah
        r["leftHostIndex"] = hs[0].get("hostIndex", 0)
        r["leftColor"] = hs[0].get("color", "rose")
    if len(hs) >= 2:
        r["rightHostHidden"] = hs[1].get("hidden", False) or ah
        r["rightHostIndex"] = hs[1].get("hostIndex", 0)
        r["rightColor"] = hs[1].get("color", "blue")
    r["hostHidden"] = ah
    return r

def _refresh_state_cache():
    global _state_json_cache, _state_gzip_cache, _state_hash
    global _lite_json_cache, _lite_gzip_cache, _lite_hash
    global _sse_msg_bytes

    raw = json.dumps(STATE, ensure_ascii=False, separators=(',', ':')).encode("utf-8")
    h = hashlib.md5(raw).hexdigest()
    if h == _state_hash:
        return False
    _state_json_cache = raw
    _state_gzip_cache = gzip.compress(raw, compresslevel=1)
    _state_hash = h

    lite = _build_lite()
    lite_raw = json.dumps(lite, ensure_ascii=False, separators=(',', ':')).encode("utf-8")
    _lite_json_cache = lite_raw
    _lite_gzip_cache = gzip.compress(lite_raw, compresslevel=1)
    _lite_hash = hashlib.md5(lite_raw).hexdigest()

    # 预构建 SSE 消息字节，发送时零开销
    _sse_msg_bytes = None  # 在 notify 时动态构建（需要最新版本号）
    return True

_refresh_state_cache()

# ══════════════════════════════════════
#  SSE
# ══════════════════════════════════════
_sse_clients = []
_sse_lock = threading.Lock()
_sse_version = 0

def _build_sse_payload(ver):
    """用字符串拼接构建 SSE 消息，避免重复 JSON 序列化"""
    t = _sse_msg_template
    if t is None:
        return f'data: {{"v":{ver}}}\n\n'.encode("utf-8")
    return f'data: {{"v":{ver},{t[1:]}\n\n'.encode("utf-8")

# 预计算模板（_refresh_state_cache 中更新）
_sse_msg_template = None

def _rebuild_sse_template():
    global _sse_msg_template
    lite = _build_lite()
    _sse_msg_template = json.dumps(lite, ensure_ascii=False, separators=(',', ':'))

def notify_sse_clients():
    global _sse_version
    _sse_version += 1
    msg = _build_sse_payload(_sse_version)
    with _sse_lock:
        dead = []
        for client in _sse_clients:
            try:
                client.put_nowait(msg)
            except:
                dead.append(client)
        for d in dead:
            _sse_clients.remove(d)

# 初始化模板
_rebuild_sse_template()

# ══════════════════════════════════════
#  Static File Cache
# ══════════════════════════════════════
_static_cache = {}
_static_cache_lock = threading.Lock()

STATIC_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
}

def get_static_file(filepath):
    try:
        mtime = os.path.getmtime(filepath)
    except:
        return None, None
    with _static_cache_lock:
        cached = _static_cache.get(filepath)
        if cached and cached[0] == mtime:
            return cached[1], cached[2]
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        ext = os.path.splitext(filepath)[1].lower()
        ct = STATIC_CONTENT_TYPES.get(ext, "application/octet-stream")
        gzip_data = gzip.compress(data, compresslevel=1)
        with _static_cache_lock:
            _static_cache[filepath] = (mtime, data, gzip_data)
        return data, gzip_data
    except:
        return None, None


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    request_queue_size = 128

    def server_activate(self):
        super().server_activate()
        try:
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except:
            pass


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _accepts_gzip(self):
        return "gzip" in self.headers.get("Accept-Encoding", "")

    def _send_json(self, data_bytes, gzip_data=None):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self._cors()
        if gzip_data and self._accepts_gzip():
            self.send_header("Content-Encoding", "gzip")
            self.end_headers()
            self.wfile.write(gzip_data)
        else:
            self.send_header("Content-Length", str(len(data_bytes)))
            self.end_headers()
            self.wfile.write(data_bytes)

    def _send_static(self, filepath):
        raw, gz = get_static_file(filepath)
        if raw is None:
            self.send_error(404)
            return
        ext = os.path.splitext(filepath)[1].lower()
        ct = STATIC_CONTENT_TYPES.get(ext, "application/octet-stream")
        etag = hashlib.md5(raw).hexdigest()
        if self.headers.get("If-None-Match", "") == etag:
            self.send_response(304)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "max-age=0, must-revalidate")
        self._cors()
        if gz and self._accepts_gzip():
            self.send_header("Content-Encoding", "gzip")
            self.end_headers()
            self.wfile.write(gz)
        else:
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/state":
            with _state_lock:
                self._send_json(_state_json_cache, _state_gzip_cache)

        elif self.path == "/api/lite-state":
            with _state_lock:
                self._send_json(_lite_json_cache, _lite_gzip_cache)

        elif self.path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self._cors()
            self.end_headers()

            q = queue.Queue(maxsize=64)
            with _sse_lock:
                _sse_clients.append(q)
            try:
                # 连接即推当前完整状态
                self.wfile.write(_build_sse_payload(_sse_version))
                self.wfile.flush()

                while True:
                    try:
                        msg = q.get(timeout=25)
                        self.wfile.write(msg)
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except:
                pass
            finally:
                with _sse_lock:
                    if q in _sse_clients:
                        _sse_clients.remove(q)

        elif self.path == "/api/hosts":
            raw = json.dumps(HOSTS, ensure_ascii=False, separators=(',', ':')).encode("utf-8")
            gz = gzip.compress(raw, compresslevel=1)
            self._send_json(raw, gz)

        elif self.path == "/api/settings":
            raw = json.dumps(SETTINGS, ensure_ascii=False, separators=(',', ':')).encode("utf-8")
            gz = gzip.compress(raw, compresslevel=1)
            self._send_json(raw, gz)

        else:
            path = self.path.split("?")[0]
            if path == "/":
                path = "/controller.html"
            # 处理 /public/ 前缀
            if path.startswith("/public/"):
                path = path[len("/public"):]
            # 从 public 文件夹加载
            filepath = os.path.join(os.getcwd(), "public", path.lstrip("/"))
            if not os.path.isfile(filepath):
                # 如果 public 里没有，尝试从根目录加载
                filepath = os.path.join(os.getcwd(), path.lstrip("/"))
            if os.path.isfile(filepath):
                self._send_static(filepath)
            else:
                self.send_error(404)

    def do_POST(self):
        if self.path == "/api/state":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            changed = False
            try:
                data = json.loads(body)
                with _state_lock:
                    old_hash = _state_hash
                    for k in STATE:
                        if k in data:
                            STATE[k] = data[k]
                    global PROGRAMS, HOSTS, PRESETS, SETTINGS
                    if "programs" in data:
                        PROGRAMS = data["programs"]
                    if "hosts" in data:
                        HOSTS = data["hosts"]
                    if "presets" in data:
                        PRESETS = data["presets"]
                    # 保存主题到 settings.json
                    if "theme" in data:
                        SETTINGS["theme"] = data["theme"]
                        save_json_file(SETTINGS_FILE, SETTINGS)
                    changed = _refresh_state_cache()
                    if changed:
                        _rebuild_sse_template()
                if changed:
                    notify_sse_clients()
            except:
                pass
            with _state_lock:
                self._send_json(_lite_json_cache, _lite_gzip_cache)
        else:
            self.send_error(404)

    def do_PUT(self):
        if self.path == "/" + PROGRAMS_FILE:
            self._handle_json_put(PROGRAMS_FILE)
        elif self.path == "/" + HOSTS_FILE:
            self._handle_json_put(HOSTS_FILE)
        elif self.path == "/" + PRESETS_FILE:
            self._handle_json_put(PRESETS_FILE)
        elif self.path == "/" + SETTINGS_FILE:
            self._handle_json_put(SETTINGS_FILE)
        else:
            self.send_error(404)

    def _handle_json_put(self, filename):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            if save_json_file(filename, data):
                with _state_lock:
                    global PROGRAMS, HOSTS, PRESETS, SETTINGS
                    if filename == PROGRAMS_FILE:
                        PROGRAMS = data
                        STATE["programs"] = data
                    elif filename == HOSTS_FILE:
                        HOSTS = data
                        STATE["hosts"] = data
                    elif filename == PRESETS_FILE:
                        PRESETS = data
                        STATE["presets"] = data
                    elif filename == SETTINGS_FILE:
                        SETTINGS = data
                        STATE["theme"] = data.get("theme", "dark")
                    _refresh_state_cache()
                    _rebuild_sse_template()
                notify_sse_clients()
                raw = json.dumps({"ok": True}).encode("utf-8")
                self._send_json(raw)
            else:
                self.send_error(500)
        except:
            self.send_error(400)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()


if __name__ == "__main__":
    port = 8000
    server = ThreadedHTTPServer(("0.0.0.0", port), Handler)
    print(f"服务器已启动: http://localhost:{port}")
    print(f"  计分板:      http://localhost:{port}/public/scoreboard.html")
    print(f"  节目单:      http://localhost:{port}/public/program.html")
    print(f"  主持人字幕条: http://localhost:{port}/public/host.html")
    print(f"  Logo 挂角:   http://localhost:{port}/public/logo.html")
    print(f"  控制面板:    http://localhost:{port}/public/controller.html")
    print(f"  (HTML文件在 public/ 文件夹)")
    server.serve_forever()
