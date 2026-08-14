import yaml
import base64
import json

def convert_clash_to_v2ray():
    try:
        with open('clash.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        proxies = config.get('proxies', [])
        v2ray_links = []
        
        for p in proxies:
            p_type = str(p.get('type', '')).lower()
            name = p.get('name', 'Server')
            server = p.get('server', '')
            port = p.get('port', '')
            password = p.get('password', p.get('uuid', ''))
            
            # 1. VLESS
            if p_type == 'vless':
                link = f"vless://{password}@{server}:{port}?encryption=none&security="
                if p.get('tls'): link += "tls"
                if p.get('sni'): link += f"&sni={p['sni']}"
                link += f"#{name}"
                v2ray_links.append(link)
                
            # 2. Trojan
            elif p_type == 'trojan':
                link = f"trojan://{password}@{server}:{port}?"
                if p.get('sni'): link += f"sni={p['sni']}"
                link += f"#{name}"
                v2ray_links.append(link)
                
            # 3. Shadowsocks (ss)
            elif p_type == 'ss':
                cipher = p.get('cipher', '')
                userinfo = base64.b64encode(f"{cipher}:{password}".encode()).decode()
                link = f"ss://{userinfo}@{server}:{port}#{name}"
                v2ray_links.append(link)
                
            # 4. VMess
            elif p_type == 'vmess':
                vmess_config = {
                    "v": "2", "ps": name, "add": server, "port": str(port),
                    "id": password, "aid": "0", "scy": "auto", "net": "tcp",
                    "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""
                }
                vmess_json = json.dumps(vmess_config)
                vmess_b64 = base64.b64encode(vmess_json.encode()).decode()
                v2ray_links.append(f"vmess://{vmess_b64}")

        with open('v2ray_links.txt', 'w', encoding='utf-8') as f:
            for link in v2ray_links:
                f.write(link + '\n')
                
        print(f"✨ Done! Extracted {len(v2ray_links)} links (VLESS, Trojan, SS, VMess).")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    convert_clash_to_v2ray()
