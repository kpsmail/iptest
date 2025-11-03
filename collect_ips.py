import requests
from bs4 import BeautifulSoup
import re
import os
import ipaddress

# 目标URL列表
urls = ['https://api.uouin.com/cloudflare.html',
        'https://ip.164746.xyz',
        'https://stock.hostmonit.com/CloudFlareYes'
        ]

# 检查ip.txt文件是否存在,如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

seen = set()

# 创建一个文件来存储IP地址
with open('ip.txt', 'w', encoding='utf-8') as file:
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
        except Exception as e:
            print(f'请求 {url} 失败: {e}')
            continue

        if response.status_code != 200:
            print(f'请求 {url} 返回状态码 {response.status_code}，跳过。')
            continue

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 根据网站的不同结构找到包含IP地址的元素（保留原逻辑）
        if url == 'https://api.uouin.com/cloudflare.html':
            elements = soup.find_all('tr')
        elif url == 'https://ip.164746.xyz':
            elements = soup.find_all('tr')
        else:
            elements = soup.find_all('li')

        # 如果按照结构找不到任何元素，回退为全页文本提取（以防 IP 在 pre/div 或纯文本中）
        if not elements:
            page_text = soup.get_text(separator=' ')
            elements = [page_text]

        # 遍历所有元素,查找IP地址（支持 IPv4 和 IPv6）
        for element in elements:
            element_text = element.get_text() if hasattr(element, 'get_text') else str(element)

            # 用一个宽松的正则先提取可能的 IP 片段（包含 IPv6 的冒号、IPv4 的点、十六进制和可选的 zone）
            candidates = re.findall(r'[A-Fa-f0-9:.%]+', element_text)

            for token in candidates:
                # 清理 token 首尾常见字符
                token = token.strip('[]() ,;\"\'')
                # 如果包含端口（例如 1.2.3.4:8080 或 [::1]:8080）, 去掉端口部分
                if ':' in token and token.count(':') == 1 and token.rfind('.') != -1:
                    # 处理可能的 ip:port（这个情况通常是 IPv4:port），把端口去掉
                    token = token.split(':', 1)[0]
                # 处理带 zone 的 IPv6（例如 fe80::1%eth0），ipaddress 不接受 % 后缀，所以先去掉
                if '%' in token:
                    token = token.split('%', 1)[0]

                # 验证是否为合法的 IP（IPv4 或 IPv6）
                try:
                    ip_obj = ipaddress.ip_address(token)
                except ValueError:
                    continue

                ip_str = str(ip_obj)
                if ip_str in seen:
                    continue
                seen.add(ip_str)

                # IPv6 写入时用方括号包裹（例如 [2a06:...]:443），IPv4 保持原格式
                if ip_obj.version == 6:
                    file.write(f'[{ip_str}]:443#CF优选IPv6-443\n')
                    file.write(f'[{ip_str}]:2053#CF优选IPv6-2053\n')
                else:
                    file.write(f'{ip_str}:443#CF优选IPv4-443\n')
                    file.write(f'{ip_str}:2053#CF优选IPv4-2053\n')

print('IP地址已保存到ip.txt文件中。')
