from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, urllib.request, shutil, datetime, os

ROOT = Path(__file__).resolve().parent
BASE = "https://raw.githubusercontent.com/kti6988-jpg/viral-finder-updates/main/"
VERSION_FILE = ROOT / "version.json"
ALLOWED_UPDATE_FILES = {"index.html", "updater_server.py", "VIRAL_FINDER_열기.bat"}

def load_ytdlp():
    try:
        import yt_dlp
        return yt_dlp
    except ImportError:
        raise RuntimeError("yt-dlp가 설치되지 않았습니다. VIRAL_FINDER_열기.bat을 다시 실행해 설치하세요.")

def search_youtube(query, max_results=10, region="US", after=None):
    import yt_dlp
    max_results = max(1, min(int(max_results or 10), 50))
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True,
            "extract_flat": False, "playlistend": max_results, "noplaylist": False,
            "geo_bypass": True, "geo_bypass_country": str(region or "US"),
            "socket_timeout": 20, "retries": 1}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
    results = []
    for v in (info or {}).get("entries") or []:
        if not v or not v.get("id"): continue
        upload = str(v.get("upload_date") or "")
        if after and len(upload) == 8:
            try:
                cutoff = datetime.datetime.fromisoformat(str(after).replace("Z","+00:00")).date()
                if datetime.datetime.strptime(upload,"%Y%m%d").date() < cutoff: continue
            except Exception: pass
        thumb = v.get("thumbnail")
        if not thumb and v.get("thumbnails"): thumb = v["thumbnails"][-1].get("url")
        published = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if len(upload)==8 else None
        results.append({"id":v["id"],"title":v.get("title") or "(제목 없음)",
            "channel":v.get("channel") or v.get("uploader") or "채널 정보 없음",
            "channelId":v.get("channel_id") or v.get("uploader_id"),
            "subscribers":v.get("channel_follower_count"),"description":v.get("description") or "",
            "published":published,"thumb":thumb,"views":int(v.get("view_count") or 0),
            "likes":v.get("like_count"),"comments":v.get("comment_count"),
            "duration":int(v.get("duration") or 0),"region":region})
    return results

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def end_headers(self): self.send_header("Cache-Control","no-store"); super().end_headers()
    def send_json(self,status,payload):
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path.split("?",1)[0]=="/api/health":
            try: load_ytdlp(); self.send_json(200,{"ok":True,"engine":"yt-dlp"})
            except Exception as e: self.send_json(503,{"ok":False,"error":str(e)})
            return
        super().do_GET()
    def do_POST(self):
        route=self.path.split("?",1)[0]
        try:
            length=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(length) or b"{}")
            if route=="/api/search":
                query=str(payload.get("query","")).strip()
                if not query: raise ValueError("검색어가 비어 있습니다.")
                items=search_youtube(query,payload.get("max_results",10),payload.get("region","US"),payload.get("after"))
                self.send_json(200,{"ok":True,"items":items,"count":len(items)}); return
            if route=="/api/update":
                requested=str(payload.get("version","")); stamp=str(datetime.datetime.now().timestamp())
                req=urllib.request.Request(BASE+"version.json?ts="+stamp,headers={"User-Agent":"VIRAL-FINDER-Updater"})
                with urllib.request.urlopen(req,timeout=25) as response: manifest=json.loads(response.read().decode("utf-8"))
                latest=str(manifest.get("version",""))
                if not latest or latest!=requested: raise ValueError("요청한 버전과 GitHub 최신 버전이 일치하지 않습니다.")
                files=manifest.get("files",["index.html"])
                for name in files:
                    if name not in ALLOWED_UPDATE_FILES: raise ValueError("허용되지 않은 업데이트 파일: "+str(name))
                backup=ROOT/("backup_"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")); backup.mkdir(exist_ok=True)
                for name in files:
                    target=ROOT/name
                    if target.exists(): shutil.copy2(target,backup/name)
                    req=urllib.request.Request(BASE+name.replace(" ","%20")+"?ts="+stamp,headers={"User-Agent":"VIRAL-FINDER-Updater"})
                    with urllib.request.urlopen(req,timeout=60) as response: content=response.read()
                    if name=="index.html" and b"VIRAL FINDER" not in content: raise ValueError("index.html 검증 실패")
                    temp=target.with_suffix(target.suffix+".tmp"); temp.write_bytes(content); os.replace(temp,target)
                VERSION_FILE.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
                self.send_json(200,{"ok":True,"version":latest,"backup":backup.name,"restart_required":"updater_server.py" in files}); return
            self.send_error(404)
        except Exception as e: self.send_json(500,{"ok":False,"error":str(e)})

if __name__=="__main__":
    print("VIRAL FINDER 2.0.0 server: http://127.0.0.1:8765")
    print("종료하려면 이 창에서 Ctrl+C")
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
