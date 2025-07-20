# mcp_server.py
from fastmcp import FastMCP
from banking_api import app as banking_api_app # FastAPI uygulamamızı import ediyoruz

# FastMCP'nin sihirli `from_fastapi` metodunu kullanıyoruz.
# Bu metod, API'deki tüm endpoint'leri gezer (@app.get, @app.post vs.)
# ve her birini otomatik olarak bir MCP aracına dönüştürür.
# `operation_id`'ler araç ismi olur.
mcp = FastMCP.from_fastapi(
    app=banking_api_app,
    name="Riskometre Portföy API Sunucusu",
    instructions="Bu sunucu, kullanıcıların banka hesaplarını yönetmek ve para transferi yapmak için araçlar sunar."
)

if __name__ == "__main__":
    mcp.run()