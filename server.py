import http.server
import json
import socketserver
import os
import gzip
import threading
import hashlib
import queue
import socket
import urllib.parse

SETTINGS_FILE = "settings.json"

# 文件缓存配置（最多缓存100个文件）
_file_cache = {}
_max_file_cache = 100

def load_settings_file(filename):
    """加载settings配置文件"""
    settings = {
        "theme": "dark",
        "programs": [],
        "hosts": [],
        "presets": []
    }
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                settings.update(data)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError as e:
        print(f"警告: {filename} JSON格式错误: {e}")
    except Exception as e:
        print(f"警告: 读取 {filename} 失败: {e}")

    settings.setdefault("theme", "dark")
    settings.setdefault("programs", [])
    settings.setdefault("hosts", [])
    settings.setdefault("presets", [])
    settings.setdefault("language", "zh-CN")
    settings.setdefault("animation", {
        "enabled": True,
        "type": "fade",
        "speed": "normal"
    })
    return settings

def save_json_file(filename, data):
    """保存JSON文件"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"错误: 保存 {filename} 失败: {e}")
        return False

SETTINGS = load_settings_file(SETTINGS_FILE)
save_json_file(SETTINGS_FILE, SETTINGS)

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
    "programs": SETTINGS.get("programs", []),
    "hosts": SETTINGS.get("hosts", []),
    "presets": SETTINGS.get("presets", []),
    "leftHostHidden": True,
    "leftHostIndex": 0,
    "leftColor": "rose",
    "rightHostHidden": True,
    "rightHostIndex": 0,
    "rightColor": "blue",
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
_sse_clients = []
_sse_lock = threading.Lock()
_sse_version = 0

def _count_display_clients():
    """统计连接的display客户端数"""
    with _sse_lock:
        return sum(1 for c in _sse_clients if c.get("role") == "display")

def _build_lite():
    """构建精简状态对象（用于前端显示）"""
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
        "displayClients": _count_display_clients(),
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
    """刷新state缓存（检测改变并更新）"""
    global _state_json_cache, _state_gzip_cache, _state_hash
    global _lite_json_cache, _lite_gzip_cache, _lite_hash

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
    return True

def _build_sse_payload(ver):
    """构建SSE消息包（包含版本号），复用缓存的lite JSON"""
    global _lite_json_cache
    if _lite_json_cache is None:
        _refresh_state_cache()
    lite_str = _lite_json_cache.decode("utf-8") if isinstance(_lite_json_cache, bytes) else _lite_json_cache
    return f'data: {{"v":{ver},{lite_str[1:]}\n\n'.encode("utf-8")

def notify_sse_clients():
    """通知所有SSE客户端状态更新"""
    global _sse_version
    _sse_version += 1
    msg = _build_sse_payload(_sse_version)
    with _sse_lock:
        dead = []
        for client in _sse_clients:
            try:
                client["queue"].put_nowait(msg)
            except queue.Full:
                dead.append(client)
            except Exception:
                dead.append(client)
        for d in dead:
            _sse_clients.remove(d)

_refresh_state_cache()

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
    """获取静态文件，支持缓存和gzip压缩"""
    try:
        mtime = os.path.getmtime(filepath)
    except OSError:
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
            # 限制缓存大小，防止无限增长
            if len(_static_cache) >= _max_file_cache:
                # 移除最老的缓存项
                oldest_key = next(iter(_static_cache))
                del _static_cache[oldest_key]
            _static_cache[filepath] = (mtime, data, gzip_data)
        
        return data, gzip_data
    except Exception as e:
        print(f"错误: 读取文件 {filepath} 失败: {e}")
        return None, None


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """多线程HTTP服务器"""
    daemon_threads = True
    request_queue_size = 128

    def server_activate(self):
        """优化TCP连接"""
        super().server_activate()
        try:
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass

    def _cors(self):
        """添加CORS响应头"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _accepts_gzip(self):
        """检查客户端是否支持gzip"""
        return "gzip" in self.headers.get("Accept-Encoding", "")

    def _send_json(self, data_bytes, gzip_data=None):
        """发送JSON响应（支持gzip压缩）"""
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

    def _send_json_dict(self, data_dict):
        """发送dict数据为JSON响应"""
        raw = json.dumps(data_dict, ensure_ascii=False, separators=(',', ':')).encode("utf-8")
        gz = gzip.compress(raw, compresslevel=1)
        self._send_json(raw, gz)

    def _send_static(self, filepath):
        """发送静态文件"""
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
        """处理GET请求"""
        if self.path == "/api/state":
            with _state_lock:
                self._send_json(_state_json_cache, _state_gzip_cache)

        elif self.path == "/api/lite-state":
            with _state_lock:
                lite = _build_lite()
            self._send_json_dict(lite)

        elif self.path.startswith("/api/events"):
            self._handle_sse_connect()

        elif self.path == "/api/hosts":
            with _state_lock:
                payload = STATE.get("hosts", [])
            self._send_json_dict(payload)

        elif self.path == "/api/settings":
            with _state_lock:
                self._send_json_dict(SETTINGS)

        elif self.path in ("/programs.json", "/hosts.json", "/presets.json"):
            # 统一处理JSON端点
            key = self.path[1:-5]  # 移除/ 和 .json
            with _state_lock:
                payload = STATE.get(key, [])
            self._send_json_dict(payload)

        elif self.path == "/settings.json":
            with _state_lock:
                self._send_json_dict(SETTINGS)

        else:
            self._handle_static_file()

    def _handle_sse_connect(self):
        """处理SSE连接"""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        role = params.get("role", ["display"])[0]
        if role != "controller":
            role = "display"
        
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self._cors()
        self.end_headers()

        q = queue.Queue(maxsize=256)
        client = {"queue": q, "role": role}
        with _sse_lock:
            _sse_clients.append(client)
        
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
        except Exception:
            pass
        finally:
            with _sse_lock:
                if client in _sse_clients:
                    _sse_clients.remove(client)

    def _handle_static_file(self):
        """处理静态文件请求"""
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
        """处理POST请求"""
        if self.path == "/api/state":
            self._handle_state_update()
        else:
            self.send_error(404)

    def _handle_state_update(self):
        """处理状态更新"""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                self.send_error(400)
                return
            
            body = self.rfile.read(length)
            data = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400)
            return
        except Exception as e:
            print(f"错误: 读取请求体失败: {e}")
            self.send_error(400)
            return

        changed = False
        try:
            with _state_lock:
                # 更新STATE中的所有字段
                for k in list(STATE.keys()):
                    if k in data:
                        STATE[k] = data[k]
                
                # 同步到SETTINGS并保存
                if "programs" in data:
                    SETTINGS["programs"] = data["programs"]
                if "hosts" in data:
                    SETTINGS["hosts"] = data["hosts"]
                if "presets" in data:
                    SETTINGS["presets"] = data["presets"]
                if "theme" in data:
                    SETTINGS["theme"] = data["theme"]
                
                # 需要保存配置的字段
                if any(k in data for k in ["programs", "hosts", "presets", "theme"]):
                    if save_json_file(SETTINGS_FILE, SETTINGS):
                        changed = _refresh_state_cache()
                    else:
                        self.send_error(500)
                        return
                else:
                    changed = _refresh_state_cache()
            
            if changed:
                notify_sse_clients()
        except Exception as e:
            print(f"错误: 处理状态更新失败: {e}")
            self.send_error(500)
            return

        # 返回精简状态
        with _state_lock:
            self._send_json(_lite_json_cache, _lite_gzip_cache)

    def do_PUT(self):
        """处理PUT请求"""
        if self.path == "/settings.json":
            self._handle_json_put("settings")
        elif self.path == "/programs.json":
            self._handle_json_put("programs")
        elif self.path == "/hosts.json":
            self._handle_json_put("hosts")
        elif self.path == "/presets.json":
            self._handle_json_put("presets")
        else:
            self.send_error(404)

    def _handle_json_put(self, key):
        """统一处理JSON PUT请求"""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                self.send_error(400)
                return
            
            body = self.rfile.read(length)
            data = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400)
            return
        except Exception as e:
            print(f"错误: 读取请求体失败: {e}")
            self.send_error(400)
            return

        try:
            with _state_lock:
                if key == "settings":
                    SETTINGS.update(data)
                    STATE["theme"] = SETTINGS.get("theme", "dark")
                else:
                    SETTINGS[key] = data
                    STATE[key] = data
                
                if save_json_file(SETTINGS_FILE, SETTINGS):
                    _refresh_state_cache()
                    notify_sse_clients()
                    self._send_json_dict({"ok": True})
                else:
                    self.send_error(500)
        except Exception as e:
            print(f"错误: 处理PUT请求失败: {e}")
            self.send_error(500)

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self._cors()
        self.end_headers()


if __name__ == "__main__":
    port = 8000
    server = ThreadedHTTPServer(("0.0.0.0", port), Handler)
    print(f"✓ 服务器已启动: http://localhost:{port}")
    print(f"  • 计分板:       http://localhost:{port}/public/scoreboard.html")
    print(f"  • 节目单:       http://localhost:{port}/public/program.html")
    print(f"  • 主持人字幕条: http://localhost:{port}/public/host.html")
    print(f"  • Logo 挂角:    http://localhost:{port}/public/logo.html")
    print(f"  • 控制面板:     http://localhost:{port}/public/controller.html")
    print(f"  (HTML文件在 public/ 文件夹)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✗ 服务器已关闭")
        server.shutdown()

