"""Local dev server for the parallax site.

usage:  python tools/serve.py [port]      (default 4190; serves this site's folder from anywhere)

Two things Python's built-in server lacks and this page needs:
  * Range requests: browsers can only seek (scrub) a <video> when the server answers byte ranges.
  * No-cache headers, so edits show on reload.
"""
import functools
import http.server
import os
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
RANGE = re.compile(r"bytes=(\d*)-(\d*)$")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        m = RANGE.match(self.headers.get("Range", "").strip())
        path = self.translate_path(self.path)
        if not m or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2) or 0))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser cancels range requests all the time while scrubbing
        finally:
            self._remaining = None


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4190
    handler = functools.partial(Handler, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Techfest parallax site on http://localhost:{port}  (Ctrl+C to stop)")
    server.serve_forever()
