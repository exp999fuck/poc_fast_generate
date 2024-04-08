import argparse
import re
import subprocess
import os
from colorama import init, Fore, Back, Style

def get_top(line):
    if line:
        return line.split()[0], line.split()[1]
def split_header_body(lines):
    # 如果在文本中没有空行来分割头部和主体，会导致 header 和 body 变量未定义而引发 UnboundLocalError 异常
    header = {}
    body = ''
    for index, line in enumerate(lines):
        if line.strip() == '':
            header = lines[:index]
            body = ''.join(lines[index + 1:]).replace('"', '\\"').replace('\r\n', '\\r\\n').replace('\n','\\r\\n').replace(
                '\r', '\\r\\n')
            break
    if not header:
        header = lines
    return header, body

def get_headers(lines):
    headers = {}
    for line in lines:
        keywords = {'Host', 'Accept:', 'sec-ch-ua-platform', 'sec-ch-ua', 'sec-ch-ua-mobile','Sec-Ch-Ua','Sec-Ch-Ua-Mobile','Sec-Ch-Ua-Platform','Sec-Fetch-Site','Sec-Fetch-Mode','Sec-Fetch-User','Sec-Fetch-Dest'}
        if ':' in line and not any(keyword in line for keyword in keywords):
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    return headers

def run_exe():
    init(autoreset=True)

    url = input('请输入url : ')
    re_url = re.findall(r'https?://.*', url)

    try:
        if re_url:
            # 定义命令和参数列表
            commands = [
                ['xray.exe', 'ws', '-p', 'post.yml', '-u'] + re_url,
                ['fscan.exe', '-proxy', 'http://127.0.0.1:8080', '-pocpath', 'get.yml', '-u'] + re_url,
                ['afrog.exe', '-proxy', 'http://127.0.0.1:8080', '-P', 'option.yml','-doh','-t'] + re_url
                # 添加更多的可执行文件及参数
            ]
            # xray.exe ws  -p post.yml -u https://61.132.38.122:4430
            # fscan.exe -proxy http://127.0.0.1:8080 -pocpath get.yml -u https://61.132.38.122:4430
            # afrog.exe -proxy http://127.0.0.1:8080  -P option.yml  -doh -t https://61.132.38.122:4430
            for i, command in enumerate(commands):
                print(Fore.GREEN + f'===== 执行程序 {i} =====')
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                for byte_line in process.stdout:
                    line = byte_line.decode('utf-8', errors='replace')  # 尝试使用utf-8解码，遇到无法解码的字符用问号替换
                    print(Fore.GREEN + line, end='')
                process.wait()

                exit_code = process.returncode
                print(Fore.GREEN + f'程序 {i} 退出码: {exit_code}')

                if i < len(commands) - 1:
                    user_input = input('继续执行下一个程序？(yes/no): ')
                    if user_input.lower() != 'yes':
                        break

    except KeyboardInterrupt as e:
        print('ctrl +c 退出')

def main():
    with open('xray-full-sample.yml', encoding='utf-8') as f1, open('r.txt', encoding='utf-8') as f2, open('post.yml','w',encoding='utf-8') as f3,open('fscan-full-sample.yml',encoding='utf-8') as f4,open('get.yml','w',encoding='utf-8') as f5,open('afrog-full-sample.yml',encoding='utf-8') as f6,open('option.yml','w',encoding='utf-8') as f7:
        RED = '\033[91m'
        RESET = '\033[0m'
        a = argparse.ArgumentParser(RED + '-name   -follow   -type   -retext 都是必填项，切记\n' + RESET)
        a.add_argument('-name', dest='name', type=str, help='poc的名字', metavar='demo',required=True)
        a.add_argument('-follow', dest='follow', type=str, help='是否自动跟随，默认true', metavar='false',required=True)
        a.add_argument('-type', dest='type', type=str,help='poc的类型-->(sqli,upload,read(/..2F..2Fetc2Fpasswd),unleak,xxe,head,200),200为判断返回包是否为200', metavar='sqli',required=True)
        a.add_argument('-r', dest='r', type=str, help='原始数据包文件，默认当前目录下的r.txt，不需要命令行指定txt', metavar='r.txt')
        a.add_argument('-retext',dest='retext',type=str,help='返回包body或者header里面匹配的内容',metavar='4ra1n',required=True)
        args = a.parse_args()

        one_lines = f2.readlines()
        header_data, body_data = split_header_body(one_lines) # 分离请求头 和  请求体
        header = get_headers(header_data) # 提取请求头

        method, path = get_top(one_lines[0]) # 获得请求方法和 path

        xray_yml = f1.readlines()  # xray_sample模板
        fscan_yml = f4.readlines() # fscan_sample模板
        afrog_yml = f6.readlines() # afrog_sample模板
########################################################################################################################
        for f_index, f_line in enumerate(fscan_yml):
            if 'method:' in f_line:
                fscan_yml[f_index] = f'  - method: {method}\n'
            if 'path:' in f_line:
                fscan_yml[f_index] = f'    path: {path}\n'
            if 'headers:' in f_line:
                fscan_yml[f_index] = f'    headers:\n'
                for key, value in header.items():
                    if key != 'Content-Length':
                        fscan_yml[f_index] += f'      {key}: {value}\n'
            if 'body:' in f_line and body_data != '':
                fscan_yml[f_index] = f'    body: "{body_data}"\n'
            if args.name is not None:
                fscan_yml[0] = f'name: {args.name}\n'
            if args.follow == 'false' and 'follow_redirects' in f_line:
                fscan_yml[f_index] = f'      follow_redirects: {args.follow}\n'
            if args.type in ['sqli', 'upload', 'read', 'unleak', '200'] and 'response.status' in f_line:
                if args.type == 'sqli':
                    fscan_yml[f_index] = f'    expression: response.latency >= 6000 && response.status == 200 && response.body.bcontains(b"{args.retext}")\n'
                if args.type == 'upload':
                    fscan_yml[f_index] = f'    expression: response.status == 200 && response.body.bcontains(b"{args.retext}")\n'
                if args.type == 'read':
                    fscan_yml[f_index] = f'    expression: response.status == 200 && response.body.bcontains(b"{args.retext}")\n'
                if args.type == 'unleak':
                    fscan_yml[f_index] = f'    expression: response.status == 200 && response.body.bcontains(b"{args.retext}")\n'
                if args.type == '200':
                    fscan_yml[f_index] = f'    expression: response.status == 200\n'
########################################################################################################################
        for af_index, af_line in enumerate(afrog_yml):
            if args.name is not None:
                afrog_yml[0] = f'id: {args.name}\n'
            if 'method:' in af_line:
                afrog_yml[af_index] = f'      method: {method}\n'
            if 'path:' in af_line:
                afrog_yml[af_index] = f'      path: {path}\n'
            if 'headers:' in af_line:
                afrog_yml[af_index] = f'      headers:\n'
                for key, value in header.items():
                    if key != 'Content-Length':
                        afrog_yml[af_index] += f'        {key}: {value}\n'
            if 'body:' in af_line and body_data != '':
                afrog_yml[af_index] = f'      body: "{body_data}"\n'
            if args.follow == 'false' and 'follow_redirects' in af_line:
                afrog_yml[af_index] = f'      follow_redirects: {args.follow}\n'
            if args.type in ['sqli', 'upload', 'read', 'unleak', 'xxe','head','200'] and 'response.status' in af_line:
                if args.type == 'sqli':
                    afrog_yml[af_index] = f'    expression: response.latency >= 6000 && response.status == 500 &&  response.body.bcontains(b"{args.retext}")\n'
                if args.type == 'upload':
                    afrog_yml[af_index] = f'    expression: response.status == 200 && response.body.bcontains(b"{args.retext}")\n'
                if args.type == 'read':
                    afrog_yml[af_index] = f'    expression: response.status == 200 && "root:.*?:[0-9]*:[0-9]*:".bmatches(response.body)\n'
                if args.type == 'unleak':
                    afrog_yml[af_index] = f'    expression: response.status == 200 && response.body.bcontains(b"{args.retext}")\n'
                if args.type == 'xxe':
                    afrog_yml[af_index] = f'    expression: oobCheck(oob, oob.ProtocolHTTP, 3)\n'
                if args.type == 'head':
                    afrog_yml[af_index] = f'    expression: response.status == 200 && "set-cookie" in response.headers && response.headers["{args.retext}"].contains("JSESSIONID=")\n'
                if args.type == '200':
                    afrog_yml[af_index] = f'    expression: response.status == 200\n'
########################################################################################################################
        for x_index, x_line in enumerate(xray_yml):
            if 'method:' in x_line:
                xray_yml[x_index] = f'      method: {method}\n'
            if 'path:' in x_line:
                xray_yml[x_index] = f'      path: {path}\n'
            if 'headers:' in x_line:
                xray_yml[x_index] = f'      headers:\n'
                for key, value in header.items():
                    if key != 'Content-Length':
                        xray_yml[x_index] += f'        {key}: {value}\n'
            if 'body:' in x_line and body_data != '':
                xray_yml[x_index] = f'      body: "{body_data}"\n'
            if args.name is not None:
                xray_yml[0] = f'name: {args.name}\n'
            if args.follow == 'false' and 'follow_redirects' in x_line:
                xray_yml[x_index] = f'      follow_redirects: {args.follow}\n'
            if args.type in ['sqli', 'upload', 'read', 'unleak', 'xxe','head','200'] and 'response.status' in x_line:
                if args.type == 'sqli':
                    xray_yml[x_index] = f'    expression: response.latency >= 4000 && response.status == 500 && response.body.bcontains(bytes(md5(string(s1)))) && response.body_string.contains("{args.retext}")\n'
                if args.type == 'upload':
                    xray_yml[x_index] = f'    expression: response.status == 200 && response.body_string.contains("{args.retext}")\n'
                if args.type == 'read':
                    xray_yml[x_index] = f'    expression: response.status == 200 && "root:[x*]:0:0:".matches(response.body_string)\n'
                if args.type == 'unleak':
                    xray_yml[x_index] = f'    expression: response.status == 200 && response.body_string.contains("{args.retext}")\n'
                if args.type == 'xxe':
                    xray_yml[x_index] = f'    expression: reverse.wait(5)\n'
                if args.type == 'head':
                    xray_yml[x_index] = f'    expression: response.status == 200 && "set-cookie" in response.headers && response.headers["{args.retext}"].contains("JSESSIONID=")\n'
                if args.type == '200':
                    xray_yml[x_index] = f'    expression: response.status == 200\n'

        poc_yml = ''.join(xray_yml)
        fpoc_yml = ''.join(fscan_yml)
        afpoc_yml = ''.join(afrog_yml)

        f3.write(poc_yml)
        print(poc_yml)
        print('\n-------------xray_poc-->post.yml----------------------')
        f5.write(fpoc_yml)
        print(fpoc_yml)
        print('-------------fscan_poc-->get.yml----------------------\n')
        f7.write(afpoc_yml)
        print(afpoc_yml)
        print('-------------afrog_poc-->option.yml----------------------\n')

    run_exe()

if __name__ == '__main__':
    main()
