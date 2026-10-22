import argparse
import contextlib
import http.server
import json
import tempfile
import threading
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse,urldefrag
from urllib.request import urlopen

from scripts.analysis.audit_approximate_distance import ROOT,sha


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        for key in ("href","src"):
            if key in values:
                self.urls.append(values[key])


def crawl(base):
    base=base.rstrip("/")+"/"
    queue=[base,urljoin(base,"presentation/"),urljoin(base,"presentation/legacy.html")]
    seen=set()
    pages=0
    assets=0
    while queue:
        url=urldefrag(queue.pop())[0]
        if url in seen:
            continue
        seen.add(url)
        with urlopen(url,timeout=15) as response:
            assert response.status==200,url
            data=response.read()
            content=response.headers.get("Content-Type","")
        if "text/html" in content:
            pages+=1
            parser=Links()
            parser.feed(data.decode())
            for link in parser.urls:
                target=urldefrag(urljoin(url,link))[0]
                if target.startswith(base) and urlparse(target).netloc==urlparse(base).netloc:
                    queue.append(target)
        else:
            assets+=1
            if urlparse(url).path.endswith(".pdf"):
                assert data.startswith(b"%PDF-"),url
    return dict(base_url=base,pages=pages,assets=assets,requests=len(seen),status="passed")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url")
    args=parser.parse_args()
    summary=ROOT/"results/formal_approximate_correspondence/publication_summary.json"
    assert json.loads(summary.read_text())==json.loads((ROOT/"docs/research-evidence.json").read_text())
    assert sha(ROOT/"output/pdf/approximate_computing_aig_correspondence_research.pdf")==sha(ROOT/"docs/publications/approximate_computing_aig_correspondence_research.pdf")
    if args.base_url:
        report=crawl(args.base_url)
    else:
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/"aig_optimization_experiments").symlink_to(ROOT/"docs",target_is_directory=True)
            class Handler(http.server.SimpleHTTPRequestHandler):
                def __init__(self,*args,**kwargs):
                    super().__init__(*args,directory=temp,**kwargs)
                def log_message(self,*args):
                    pass
            with http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                report=crawl(f"http://127.0.0.1:{server.server_port}/aig_optimization_experiments/")
                server.shutdown()
    output=ROOT/"results/formal_approximate_correspondence/website_asset_check.json"
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))


if __name__=="__main__":
    main()
