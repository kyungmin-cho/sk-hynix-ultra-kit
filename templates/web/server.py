"""server — stdlib http.server 대시보드(0.0.0.0:$PORT) + 바인드 실패 시 정적 dashboard.html 폴백.

언제 쓰나: "화면으로 보여 달라"는 요구가 있고 Flask/FastAPI가 없거나 설치를 못 할 때.
  svg_line      의존성 없는 SVG 선 차트(표시할 인덱스 marks는 빨간 점).
  svg_bar       의존성 없는 SVG 가로 막대(그룹별 불량률·건수 비교용).
  page          본문 HTML → 완성된 페이지(선택: meta refresh 초).
  serve         pages={"/": 함수 또는 문자열}, json_routes={"/api/x": 함수}. /health 기본 제공.
                post_routes={"/api/judge": 함수(dict) → 결과}: JSON 본문 입력 → 판정 → JSON 응답.
                함수가 ValueError를 내면 400(입력 검증 실패), 저장은 함수 안에서 파일·sqlite3로.
                바인드 실패(소켓 차단·포트 사용 중)면 예외 대신 정적 HTML 파일을 쓰고 그 경로를 돌려준다.
  write_static  각 페이지를 파일로 저장("/" → dashboard.html). 서버가 되더라도 제출 증거로 남기기 좋다.
실행: python3 server.py            (PORT 환경변수, 기본 8000. 브라우저에서 http://<호스트>:8000/)
      python3 server.py --static   (서버 없이 dashboard.html만 생성)
참고 출력: CLI·함수 결과는 참고 구현의 출력이다. 결론은 근거(행 수·실패 수·입력 검증)로 확인하고, 결과물에는 필요한 함수만 자기 코드로 옮긴다.
가정: 0.0.0.0에 바인드한다(localhost만 바인드하면 외부 미리보기에서 안 보인다). 핸들러 오류는 500으로 응답하고
  서버는 계속 돈다. 장시간 실행은 재시작 가능하게 하고 결과는 파일로도 남긴다.
한계: 인증·동시성·HTTPS 없음(시연용). 큰 데이터는 서버에서 요약한 뒤 보낸다.
출처: wildrage98/hackathon-kit kitlib/webapp.py (MIT, Copyright (c) 2026 wildrage98,
  commit 1728cafc4b568fdc860c34b6512a8c5921627f0b)의 "라우트 dict + 바인드 실패 시 정적 파일 폴백" 구조를 참고해 다시 씀.
  바꾼 점: 폴백을 serve 안에서 자동 수행, 결과를 dict로 반환, SVG 차트 함수 포함, 외부 CSS 의존 제거.
"""
from __future__ import annotations

import html
import json
import math
import numbers
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, Optional, Sequence, Union
from urllib.parse import urlparse

Page = Union[str, Callable[[], str]]

_CSS = ("body{font-family:system-ui,sans-serif;margin:24px;max-width:1000px}"
        "table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px 8px}"
        ".bad{color:#c00;font-weight:bold}")


def svg_line(values: Sequence, width: int = 640, height: int = 180, marks: Sequence[int] = (), title: str = "") -> str:
    pts = [(i, float(v)) for i, v in enumerate(values)
           if isinstance(v, numbers.Real) and not isinstance(v, bool) and math.isfinite(v)]
    if not pts:
        return "<svg width='%d' height='%d'><text x='8' y='20'>no data</text></svg>" % (width, height)
    lo, hi = min(v for _, v in pts), max(v for _, v in pts)
    span, n, pad = (hi - lo) or 1.0, max(1, len(values) - 1), 20

    def xy(i, v):
        return pad + (width - 2 * pad) * i / n, height - pad - (height - 2 * pad) * (v - lo) / span

    marked = set(marks)
    path = " ".join("%.1f,%.1f" % xy(i, v) for i, v in pts)
    dots = "".join("<circle cx='%.1f' cy='%.1f' r='3' fill='#c00'/>" % xy(i, v) for i, v in pts if i in marked)
    return ("<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d'><title>%s</title>"
            "<polyline fill='none' stroke='#36c' stroke-width='1.5' points='%s'/>%s"
            "<text x='2' y='12' font-size='10'>%.4g</text><text x='2' y='%d' font-size='10'>%.4g</text></svg>"
            % (width, height, html.escape(title), path, dots, hi, height - 4, lo))


def svg_bar(items: Sequence, width: int = 480, bar_h: int = 18, title: str = "", fmt: str = "%.3g") -> str:
    """items: [(라벨, 값)]. 0 기준 가로 막대, 음수·비숫자는 0으로 그린다(값 글자는 원래 값)."""
    rows = [(str(k), float(v) if isinstance(v, numbers.Real) and math.isfinite(v) else 0.0) for k, v in items]
    top = max([v for _, v in rows] + [0.0]) or 1.0
    lab, h = 120, bar_h * len(rows) + 8
    bars = "".join("<text x='0' y='%d' font-size='11'>%s</text><rect x='%d' y='%d' width='%.1f' height='%d' "
                   "fill='#36c'/><text x='%.1f' y='%d' font-size='11'>%s</text>"
                   % (i * bar_h + 13, html.escape(k[:18]), lab, i * bar_h + 2, max(0.0, v) / top * (width - lab - 50),
                      bar_h - 4, lab + max(0.0, v) / top * (width - lab - 50) + 4, i * bar_h + 13, fmt % v)
                   for i, (k, v) in enumerate(rows))
    return "<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d'><title>%s</title>%s</svg>" % (
        width, h, html.escape(title), bars)


def page(title: str, body_html: str, refresh: Optional[int] = None) -> str:
    meta = "<meta http-equiv='refresh' content='%d'>" % refresh if refresh else ""
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>%s<title>%s</title><style>%s</style>"
            "</head><body>%s</body></html>" % (meta, html.escape(title), _CSS, body_html))


def _render(p: Page) -> str:
    return p() if callable(p) else p


def write_static(pages: Dict[str, Page], out_dir: str = ".") -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    written = {}
    for route, p in pages.items():
        name = "dashboard.html" if route == "/" else route.strip("/").replace("/", "_") + ".html"
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_render(p))
        written[route] = path
    return written


def _handler(pages: Dict[str, Page], json_routes: Dict[str, Callable[[], object]], quiet: bool,
             post_routes: Optional[Dict[str, Callable[[Dict], object]]] = None):
    post_routes = post_routes or {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path not in post_routes:
                return self._send(404, ("not found: %s" % path).encode("utf-8"), "text/plain; charset=utf-8")
            try:
                n = int(self.headers.get("Content-Length") or 0)
                data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
                out = post_routes[path](data)
            except ValueError as e:  # JSON 깨짐·입력 검증 실패
                return self._send(400, json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"),
                                  "application/json; charset=utf-8")
            except Exception as e:
                return self._send(500, ("error: %r" % e).encode("utf-8"), "text/plain; charset=utf-8")
            self._send(200, json.dumps(out, ensure_ascii=False, default=str).encode("utf-8"),
                       "application/json; charset=utf-8")

        def do_GET(self):
            path = urlparse(self.path).path.rstrip("/") or "/"
            try:
                if path in json_routes:
                    body = json.dumps(json_routes[path](), ensure_ascii=False, default=str).encode("utf-8")
                    self._send(200, body, "application/json; charset=utf-8")
                elif path in pages:
                    self._send(200, _render(pages[path]).encode("utf-8"), "text/html; charset=utf-8")
                elif path == "/health":
                    self._send(200, b'{"ok": true}', "application/json")
                else:
                    self._send(404, ("not found: %s" % path).encode("utf-8"), "text/plain; charset=utf-8")
            except Exception as e:
                self._send(500, ("error: %r" % e).encode("utf-8"), "text/plain; charset=utf-8")

        def _send(self, code, body, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            if not quiet:
                sys.stderr.write("[web] %s\n" % (fmt % args))
    return H


def serve(pages: Dict[str, Page], json_routes: Optional[Dict[str, Callable[[], object]]] = None,
          host: str = "0.0.0.0", port: Optional[int] = None, block: bool = True, fallback_dir: str = ".",
          quiet: bool = False, post_routes: Optional[Dict[str, Callable[[Dict], object]]] = None) -> Dict:
    """성공: {"mode": "server", "url", "server"}(block=False일 때 server.shutdown()으로 종료).
    실패: {"mode": "static", "error", "files"} — 정적 파일을 fallback_dir에 쓴다."""
    port = int(os.environ.get("PORT", "8000")) if port is None else int(port)
    try:
        httpd = ThreadingHTTPServer((host, port), _handler(pages, json_routes or {}, quiet, post_routes))
    except OSError as e:
        files = write_static(pages, fallback_dir)
        if not quiet:
            print("[web] bind %s:%d failed (%s) -> static files: %s" % (host, port, e, files), file=sys.stderr)
        return {"mode": "static", "error": str(e), "files": files}
    url = "http://%s:%d/" % (host, httpd.server_address[1])
    if not quiet:
        print("[web] serving %s" % url, file=sys.stderr)
    if not block:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return {"mode": "server", "url": url, "server": httpd}
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return {"mode": "server", "url": url, "server": None}


def _demo_pages() -> Dict[str, Page]:
    vals = [10 + (i % 7) * 0.3 for i in range(60)]
    vals[42] = 14.0
    body = "<h1>Demo</h1>%s<p class='bad'>flag: index 42</p>" % svg_line(vals, marks=[42], title="sensor")
    return {"/": page("Demo", body)}


if __name__ == "__main__":
    if "--static" in sys.argv[1:]:
        print(write_static(_demo_pages()))
    else:
        serve(_demo_pages(), {"/api/summary": lambda: {"n": 60, "flags": [42]}})
