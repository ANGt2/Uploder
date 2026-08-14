import yaml
import json
from urllib.parse import quote

def main():
    try:
        with open('clash.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print("Error reading YAML:", e)
        return

    proxies = config.get('proxies', [])
    vless_links = []

    for p in proxies:
        if p.get('type') == 'vless':
            try:
                server = p.get('server')
                port = p.get('port')
                uuid = p.get('uuid')
                name = quote(p.get('name', ''))
                
                # پارامترهای اصلی
                tls = "tls" if p.get('tls') else "none"
                flow = p.get('flow', '')
                network = p.get('network', 'tcp')
                
                link = f"vless://{uuid}@{server}:{port}?type={network}&security={tls}"
                if flow:
                    link += f"&flow={flow}"
                
                # بررسی Reality
                if p.get('reality-opts'):
                    ropts = p.get('reality-opts', {})
                    link = link.replace("security=tls", "security=reality")
                    if ropts.get('public-key'):
                        link += f"&pbk={ropts.get('public-key')}"
                    if ropts.get('short-id'):
                        link += f"&sid={ropts.get('short-id')}"
                
                # بررسی SNI یا ServerName
                sni = p.get('servername')
                if sni:
                    link += f"&sni={sni}"
                    
                # بررسی gRPC یا WebSocket
                if network == 'grpc' and p.get('grpc-opts'):
                    gopts = p.get('grpc-opts', {})
                    gname = gopts.get('grpc-service-name', '')
                    if gname:
                        link += f"&serviceName={gname}"
                elif network == 'ws' and p.get('ws-opts'):
                    wopts = p.get('ws-opts', {})
                    path = wopts.get('path', '')
                    if path:
                        link += f"&path={quote(path)}"
                        
                link += f"#{name}"
                vless_links.append(link)
            except:
                continue

    with open('v2ray_links.txt', 'w', encoding='utf-8') as out:
        out.write("\n".join(vless_links))
    print(f"Done! Extracted {len(vless_links)} clean VLESS links.")

if __name__ == '__main__':
    main()
