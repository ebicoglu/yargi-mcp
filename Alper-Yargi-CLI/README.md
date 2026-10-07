# yargi-cli

[yargi-mcp](https://github.com/Remilya/yargi-mcp) sunucusunu komut satırından kullanan, bağımlılıksız (stdlib) bir istemci.
Gereksinim: [`uv`](https://docs.astral.sh/uv/) (Python'u ve yargi-mcp'yi kendisi getirir).

## Kurulum (herhangi bir bilgisayarda)

```bash
uv tool install ./Alper-Yargi-CLI          # yerel klasörden
# ya da bir git deposuna koyduktan sonra:
# uv tool install "git+https://github.com/ebicoglu/yargi-mcp#subdirectory=Alper-Yargi-CLI"
```

Kurmadan denemek için: `uvx --from ./Alper-Yargi-CLI yargi tools`

## Kullanım

```bash
yargi tools                                   # araç listesi
yargi tools --schema search_bedesten_unified  # bir aracın şeması
yargi search '"kira bedelinin tespiti"' -c yargitay -d H3
yargi search "tahliye" -c yargitay istinaf -p 2 --json
yargi get 1219369500 -o karar.md              # tam metin
yargi health
yargi call search_kvkk_decisions --args '{"keywords":"açık rıza"}'   # her aracı çağır
```

Tam ifade için arama metnini çift tırnakla sarın (`'"kira tespiti"'`). Daire kodları: H1–H23, C1–C23, HGK, CGK, BGK.

## Notlar

- yargi-mcp 0.2.x, `fastmcp` 3.x / `mcp` 2.x ile çöker; bu yüzden istemci sunucuyu `fastmcp>=2.10.5,<3` sabitlemesiyle başlatır.
- Sunucu komutunu `YARGI_MCP_CMD` ortam değişkeniyle değiştirebilirsiniz (örn. `yargi-mcp`).
- Her komut sunucuyu yeniden başlatır; ilk çalıştırma paketleri indirdiği için yavaştır.


---

## CLAUDE DESKTOP BU MCP EKLEME
`claude_desktop_config.json` dosyasına aşağıdaki bölüm eklenecek. Örnek bir dosya yolu `C:\Users\alper\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

```json
 "coworkUserFilesPath": "C:\\Users\\alper\\Claude",
  "mcpServers": {
    "Yargı MCP": {
      "command": "C:\\Users\\alper\\.local\\bin\\uvx.exe",
      "args": ["--with", "fastmcp>=2.10.5,<3", "yargi-mcp"]
    }
  }
```
