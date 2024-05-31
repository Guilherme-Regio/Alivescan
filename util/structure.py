import socket
from subprocess import Popen, PIPE
from datetime import datetime, timezone
from paramiko import SSHClient, AutoAddPolicy
import socket
import psutil
import subprocess
import ntplib
import pytz
import requests
from scapy.all import ARP, Ether, srp
from asyncio import get_event_loop


user = 'user'
pwd = 'pass'

class SSH:

    def __init__(self, ip):
        self.ssh = SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(AutoAddPolicy())
        self.ip = ip
        self.user = 'user'
        self.pwd = 'pass'


    def ssh_connection(self):  
        try:
            self.ssh.connect(hostname=self.ip, username=self.user, password=self.pwd, timeout=2)
            return True
        except Exception as e:
            return False
        

    def ssh_close(self):
        self.ssh.close()


    def exec_cmd(self, cmd):
        if self.user != "root":
            cmd = f"echo {self.pwd} | sudo -S {cmd}"
        try:
            stdin, stdout, stderr = self.ssh.exec_command(cmd, get_pty=True)
            stdin.write(self.pwd + '\n')
            stdin.flush()

            if stderr.channel.recv_exit_status() != 0:
                return False
            else:
                full_result = stdout.readlines()
                last_result = len(full_result) - 1
                result = full_result[last_result]
                result = result.replace('\r\n', '')
                return result
        except:
            return False


def cmd(cmd_input, wine=False):
    # Prepara o comando para ser executado em uma shell com sudo, passando corretamente para `bash -c`
    cmd_new = f"echo {pwd} | sudo -S bash -c \"{cmd_input}\""
    cmd_wine = f"echo {pwd} | sudo -S -H -u pdv bash -c \"{cmd_input}\""
    try:
        # Utilizar shell=True para permitir a execução de comandos complexos
        if wine == True:
            process = Popen(cmd_wine, stdout=PIPE, stderr=PIPE, shell=True, encoding="utf-8")
            stdout, stderr = process.communicate()
        else:
            process = Popen(cmd_new, stdout=PIPE, stderr=PIPE, shell=True, encoding="utf-8")
            stdout, stderr = process.communicate()
            
        if process.returncode != 0:
            print(f"Error: {stderr}")
            print(f"Saida: {stdout}")
            return False
        else:
            return stdout.strip()  # Remove espaços em branco no início e no fim
    except Exception as e:
        print(f"Error Exeception: {e}")
        return False
    

def host_ttl(ip):
    try:
        output = Popen(f"ping {ip} -c 1 -W 1", stdout=PIPE, stderr=PIPE, shell=True, encoding="utf-8")
        stdout, stderr = output.communicate()

        if "ttl=" in stdout.lower():
            ttl_index = stdout.lower().index("ttl=") + 4
            ttl = stdout[ttl_index:].split()[0]
            return int(ttl)
        else:
            return None
    except Exception as e:
        print(f"Erro ao obter TTL para {ip}: {str(e)}")
        return None
    

def check_openport(host, porta):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        resultado = s.connect_ex((host, porta))
        s.close()

        if resultado == 0:
            return True
        elif resultado == 111:
            return 'filtered'
        else:
            return False
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False
          

def ping(target_host):
    try:
        subprocess.check_call(['ping', '-c', '1', '-W', '2', f'{target_host}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def clock_adjust():
    ntp_servers = ['lista de ntp_serves']
    for ntp_server in ntp_servers:
        cmd = ['ntpdate', '-u', f'{ntp_server}']
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            if ntp_server == ntp_servers[len(ntp_servers) - 1]:
                return print(f' {e} - Erro ao ajustar a hora com os servidores NTP definidos')


def check_ping(target_host):
    response = ping(target_host)
    if response:
        return response
    else:
        return False


def get_timenow():
    getdata = datetime.now()
    getdata = getdata.strftime('%Y-%m-%d %H:%M:%S')
    data = getdata[0:10]
    hour = getdata[11:19]
    return str(data), str(hour), str(getdata)


def get_ipaddr():
    interfaces = psutil.net_if_addrs()

    for interface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                ipaddr = addr.address
    
    return ipaddr
 

def get_cidr(ipaddr):
    
    cont = 0
    range = ""

    #Extrair o range de rede
    for s in ipaddr:
        if s == ".":
            cont += 1
        range += s
        if cont == 3:
            break
            
    network_cidr = range + "0/24"        
    return str(network_cidr)


def get_ntp_time():
    ntp_servers = ['ntp serves list']
    client = ntplib.NTPClient()
    for ntp_server in ntp_servers:
        try:
            response = client.request(ntp_server, version=3)
            time_utc = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)  # Correção: especificar 'timezone.utc' corretamente
            timezone_obj = pytz.timezone('America/Sao_Paulo')
            time_zone = time_utc.astimezone(timezone_obj)
            # Formatar a data e a hora no formato desejado
            return time_zone.strftime('%Y-%m-%d %H:%M:%S')
        except (ntplib.NTPException, OSError) as e:
            if ntp_server == ntp_servers[len(ntp_servers) - 1]:
                return print(f'{e} - Erro ao capturar a hora nos servidores NTP definidos')
    

def check_clock_diff():
    local_data = get_timenow()[2]
    ntp_data = get_ntp_time()
    formato = '%Y-%m-%d %H:%M:%S'
    diff_data = datetime.strptime(local_data, formato) - datetime.strptime(ntp_data, formato)
    conv_data = abs(diff_data)
    if conv_data.total_seconds() > 60:
        clock_adjust()


def get_textfromweb(url):
    html = requests.get(url)
    raw = html.content.decode('utf8')
    return str(raw).replace('\n', '')


def glpi_agent_check(ipagent):

    url_agent = f"http://{ipagent}:62354"
    status = read_version = ''

    try:
        #Captura o status do agente local
        html_read = requests.get(url_agent, timeout=2)
        read_version = html_read.content.decode("utf-8")

    except:
        status = 'STOPPED'
    
    else:

        #Captura a versão do agente em produção
        try:
            latest_version = get_textfromweb('http://url/farm_version.html')
        except:
            latest_version = "OFFLINE"

    if not status == 'STOPPED':
        if latest_version in read_version:
            status = 'COMPLIANCE'
        else:
            status = 'NO COMPLIANCE'

    return status


def check_terminal(ip_terminal, terminal):
    partes_ip = ip_terminal.split('.')
    ultimo_numero = partes_ip[-1]

    # Verifica se o último número está presente no dicionário
    if int(ultimo_numero) in terminal:
        return terminal[int(ultimo_numero)]
    else:
        return "NA"

    

def check_device(mac_address, ip, devices):
    mac_vendor = mac_address[:8]
    if mac_vendor in devices:
        return devices[mac_vendor]
    elif mac_vendor == "00:1d:5b":
        port_17_status = check_openport(ip, 17)
        port_136_status = check_openport(ip, 136)
        
        if port_17_status == 'filtered' and port_136_status == 'filtered':
            return "SAT Gertec"
        else:
            return "Encantomêtro Gertec"
    else:
        return "NA"
    

def check_SSHConnection(ip):
    ssh_conn = SSH(ip)
    if ssh_conn.ssh_connection():
        ssh_conn.ssh_close()
        return True
    return False
        

def get_MACAddress(ip):
    from scapy.all import ARP, Ether, srp
    
    # O endereço de broadcast MAC e o tipo de pacote ARP
    broadcast = "ff:ff:ff:ff:ff:ff"
    ether_layer = Ether(dst=broadcast)
    arp_layer = ARP(pdst=ip)
    
    # Combine as camadas
    packet = ether_layer / arp_layer
    
    # Envie o pacote e receba a resposta
    result = srp(packet, timeout=5, verbose=False)  # Aumentei o timeout para 5 segundos

    # Verifica se há respostas no resultado
    answers = result[0]
    if answers:
        for sent, received in answers:
            return received.hwsrc  # Retorna o MAC do primeiro dispositivo que respondeu

    return None 


async def open_browser_url(url):
    try:
        content = cmd(f'google-chrome --no-sandbox --headless --disable-gpu --ignore-certificate-errors --dump-dom --virtual-time-budget=10000 {url}')
        return content
    except:
        return False
    

def load_html_page(url):
    try:
        content = get_event_loop().run_until_complete(open_browser_url(url))
        return content
    except:
        return False


def get_prn_model(ip):
    if check_ping(ip):
        html_prn = load_html_page(f'http://{ip}')
        if html_prn:

            # HP
            if "M454dw" in html_prn:
                return "M454dw"
            elif "M404dw" in html_prn:
                return "M404dw"
            elif "Laser 408" in html_prn:
                return "Laser 408"
                
            # Samsung 
            elif "SL-M4020ND" in html_prn:
                return "SL-M4020ND"
            elif "SL-M4070FR" in html_prn:
                return "SL-M4070FR"
            elif "ML-451x" in html_prn:
                return "ML-451x"
            
            # Lexmark
            elif "CS521dn" in html_prn:
                return "CS521dn"
            elif "CS622de" in html_prn:
                return "CS622de"
            elif "CS632de" in html_prn:
                return "CS632de"
            

            # Canon
            elif "iR1643P" in html_prn:
                return "iR1643P"
            
            #Não encontrado
            else:
                return "UNKNOW"
            
        else:
            return "NA"
    else:
        return "OFFLINE"
        