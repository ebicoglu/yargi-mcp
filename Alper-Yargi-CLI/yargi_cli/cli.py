import argparse
import json
import sys
from collections import Counter, OrderedDict

from .articles import extract_articles
from .mcp_client import McpClient, McpError

COURTS = {
    "yargitay": "YARGITAYKARARI",
    "danistay": "DANISTAYKARAR",
    "yerel": "YERELHUKUK",
    "istinaf": "ISTINAFHUKUK",
    "kyb": "KYB",
}


def out_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_tools(a):
    with McpClient() as c:
        tools = c.list_tools()
    if a.schema:
        for t in tools:
            if t["name"] == a.schema:
                return out_json(t)
        raise McpError(f"Araç yok: {a.schema}")
    if a.json:
        return out_json(tools)
    for t in tools:
        desc = (t.get("description") or "").strip().splitlines()
        print(f"{t['name']:<40} {desc[0][:70] if desc else ''}")


def cmd_search(a):
    args = {
        "phrase": a.phrase,
        "court_types": [COURTS[x] for x in a.court],
        "pageNumber": a.page,
    }
    if a.chamber:
        args["birimAdi"] = a.chamber
    if a.date_from:
        args["kararTarihiStart"] = a.date_from
    if a.date_to:
        args["kararTarihiEnd"] = a.date_to
    with McpClient() as c:
        r = c.call("search_bedesten_unified", args)
    if a.json:
        return out_json(r)
    print(f"Toplam: {r.get('total_records')}  (sayfa {r.get('requested_page')})\n")
    print(f"{'ID':<12} {'Daire':<22} {'Esas':<12} {'Karar':<12} Tarih")
    for d in r.get("decisions", []):
        print(
            f"{d['documentId']:<12} {str(d.get('birimAdi')):<22} "
            f"{d.get('esasNo', ''):<12} {d.get('kararNo', ''):<12} {d.get('kararTarihiStr', '')}"
        )


def cmd_get(a):
    with McpClient() as c:
        r = c.call("get_bedesten_document_markdown", {"documentId": a.document_id})
    if a.json:
        return out_json(r)
    text = r.get("markdown_content", r) if isinstance(r, dict) else r
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Yazıldı: {a.output}")
    else:
        print(text)



def cmd_articles(a):
    args = {"phrase": a.phrase, "court_types": [COURTS[x] for x in a.court], "pageNumber": 1}
    if a.chamber:
        args["birimAdi"] = a.chamber
    counts, ctxs, lines = Counter(), {}, []
    with McpClient() as c:
        r = c.call("search_bedesten_unified", args)
        decisions = r.get("decisions", [])[: a.limit]
        lines.append(f"Arama: {a.phrase}")
        lines.append(f"Toplam sonuç: {r.get('total_records')} | İncelenen karar: {len(decisions)}")
        lines.append("")
        for d in decisions:
            doc = c.call("get_bedesten_document_markdown", {"documentId": d["documentId"]})
            text = doc.get("markdown_content", "") if isinstance(doc, dict) else str(doc)
            arts = extract_articles(text)
            for k, ctx in arts.items():
                counts[k] += 1
                ctxs.setdefault(k, ctx)
            lines.append(f"- {d['birimAdi']} {d['esasNo']} E., {d['kararNo']} K. ({d['kararTarihiStr']}): "
                         + (", ".join(arts) if arts else "madde atfı bulunamadı"))
    lines += ["", "ÖZET - Kararlarda geçen kanun maddeleri (karar sayısı):", ""]
    for k, n in counts.most_common():
        lines.append(f"{k}  [{n} kararda]")
        lines.append(f"    örnek: ...{ctxs[k]}...")
    text = "\n".join(lines) + "\n"
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Yazıldı: {a.output}")
    else:
        print(text)


def cmd_health(a):
    with McpClient() as c:
        out_json(c.call("check_government_servers_health", {}))


def cmd_call(a):
    with McpClient() as c:
        r = c.call(a.tool, json.loads(a.args))
    out_json(r) if not isinstance(r, str) else print(r)


def build_parser():
    p = argparse.ArgumentParser(prog="yargi", description="Yargı MCP komut satırı istemcisi")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("tools", help="Sunucudaki araçları listele")
    s.add_argument("--schema", metavar="ARAC", help="Bir aracın şemasını göster")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_tools)

    s = sub.add_parser("search", help="Bedesten üzerinden karar ara (Yargıtay, Danıştay, yerel, istinaf, KYB)")
    s.add_argument("phrase", help='Arama ifadesi; tam eşleşme için tırnak kullanın: "\\"kira tespiti\\""')
    s.add_argument("-c", "--court", nargs="+", choices=COURTS, default=["yargitay"])
    s.add_argument("-d", "--chamber", help="Daire, örn. H3, C1, HGK")
    s.add_argument("-p", "--page", type=int, default=1)
    s.add_argument("--date-from", help="Başlangıç tarihi (sunucunun beklediği biçimde)")
    s.add_argument("--date-to", help="Bitiş tarihi")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("get", help="Karar tam metnini (markdown) getir")
    s.add_argument("document_id")
    s.add_argument("-o", "--output", help="Dosyaya yaz")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_get)

    s = sub.add_parser("articles", help="Kararları ara, metinlerindeki kanun maddesi atıflarını çıkar")
    s.add_argument("phrase")
    s.add_argument("-c", "--court", nargs="+", choices=COURTS, default=["yargitay"])
    s.add_argument("-d", "--chamber")
    s.add_argument("-n", "--limit", type=int, default=10, help="İncelenecek karar sayısı (en fazla 10)")
    s.add_argument("-o", "--output", help="Metin dosyası")
    s.set_defaults(fn=cmd_articles)

    s = sub.add_parser("health", help="Devlet sunucularının durumunu kontrol et")
    s.set_defaults(fn=cmd_health)

    s = sub.add_parser("call", help="Herhangi bir MCP aracını doğrudan çağır")
    s.add_argument("tool")
    s.add_argument("--args", default="{}", help="JSON argümanlar")
    s.set_defaults(fn=cmd_call)
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
    except McpError as e:
        print(f"Hata: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
