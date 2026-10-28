import json, sys, pymupdf
from rapidocr_onnxruntime import RapidOCR
src, out = sys.argv[1], sys.argv[2]
d = pymupdf.open(src); o = RapidOCR(); res = []
for i, p in enumerate(d):
    p.get_pixmap(dpi=150).save("page.png")
    r, _ = o("page.png")
    res.append([[[int(b[0][0]), int(b[0][1]), int(b[2][0]), int(b[2][1])], t] for b, t, c in (r or [])])
    print(i + 1, len(res[-1]), flush=True)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
