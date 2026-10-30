import json
import os
import socket
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest import mock

from . import server


def _can_bind():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        s.close()
        return True
    except OSError:
        return False


class TestWeb(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pages = {"/": server.page("T", "<h1>hello</h1>" + server.svg_line([1, 2, None, 4], marks=[3])),
                      "/detail": lambda: server.page("D", "<p>detail</p>")}

    def tearDown(self):
        self.tmp.cleanup()

    def test_svg_line(self):
        svg = server.svg_line([1, 3, 2], marks=[1], title="<x>")
        self.assertIn("<polyline", svg)
        self.assertEqual(svg.count("<circle"), 1)
        self.assertIn("&lt;x&gt;", svg)
        self.assertIn("no data", server.svg_line([None, "a", True, float("nan")]))
        from fractions import Fraction
        self.assertIn("<polyline", server.svg_line([Fraction(1), Fraction(2)]))

    def test_fallback_when_bind_denied(self):  # 소켓 가능 여부와 무관하게 항상 실행
        with mock.patch.object(server, "ThreadingHTTPServer", side_effect=PermissionError("denied")):
            res = server.serve(self.pages, port=8000, fallback_dir=self.tmp.name, quiet=True)
        self.assertEqual(res["mode"], "static")
        with open(os.path.join(self.tmp.name, "dashboard.html"), encoding="utf-8") as f:
            self.assertIn("<h1>hello</h1>", f.read())
        self.assertTrue(os.path.exists(os.path.join(self.tmp.name, "detail.html")))

    def test_live_server_or_fallback(self):
        if not _can_bind():  # 소켓이 막힌 환경: 실제 serve 호출이 폴백으로 내려가는지 확인
            res = server.serve(self.pages, host="127.0.0.1", port=0, block=False, fallback_dir=self.tmp.name, quiet=True)
            self.assertEqual(res["mode"], "static")
            return
        res = server.serve(self.pages, {"/api/s": lambda: {"n": 3, "한글": True}, "/api/err": lambda: 1 / 0},
                           host="127.0.0.1", port=0, block=False, quiet=True)
        httpd = res["server"]
        try:
            base = "http://127.0.0.1:%d" % httpd.server_address[1]
            with urllib.request.urlopen(base + "/", timeout=5) as r:
                self.assertIn("hello", r.read().decode("utf-8"))
            with urllib.request.urlopen(base + "/api/s", timeout=5) as r:
                self.assertEqual(json.loads(r.read().decode("utf-8")), {"n": 3, "한글": True})
            with urllib.request.urlopen(base + "/health", timeout=5) as r:
                self.assertEqual(r.status, 200)
            for path, code in (("/nope", 404), ("/api/err", 500)):
                with self.assertRaises(urllib.error.HTTPError) as cm:
                    urllib.request.urlopen(base + path, timeout=5)
                self.assertEqual(cm.exception.code, code)
                cm.exception.close()
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_svg_bar(self):
        svg = server.svg_bar([("T1", 0.05), ("T3<", 0.25), ("bad", None)], title="rate")
        self.assertEqual(svg.count("<rect"), 3)
        self.assertIn("T3&lt;", svg)
        self.assertIn("0.25", svg)

    def test_post_route_validation(self):
        if not _can_bind():
            self.skipTest("socket bind blocked")

        def judge(d):
            if not isinstance(d.get("value"), (int, float)):
                raise ValueError("value must be a number")
            return {"alert": d["value"] > 80}
        res = server.serve(self.pages, post_routes={"/api/judge": judge}, host="127.0.0.1", port=0, block=False,
                           quiet=True)
        httpd = res["server"]
        base = "http://127.0.0.1:%d" % httpd.server_address[1]

        def post(path, body):
            req = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json"})
            return urllib.request.urlopen(req, timeout=5)
        try:
            with post("/api/judge", b'{"value": 90}') as r:
                self.assertEqual(json.loads(r.read().decode("utf-8")), {"alert": True})
            for path, body, code in (("/api/judge", b'{"value": "x"}', 400), ("/api/judge", b"{bad", 400),
                                     ("/nope", b"{}", 404)):
                with self.assertRaises(urllib.error.HTTPError) as cm:
                    post(path, body)
                self.assertEqual(cm.exception.code, code)
                cm.exception.close()
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_default_host_is_all_interfaces(self):
        with mock.patch.object(server, "ThreadingHTTPServer", side_effect=OSError("x")) as m:
            server.serve(self.pages, port=1234, fallback_dir=self.tmp.name, quiet=True)
        self.assertEqual(m.call_args[0][0], ("0.0.0.0", 1234))


if __name__ == "__main__":
    unittest.main()
