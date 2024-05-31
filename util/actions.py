import ipaddress
from util.structure import *
from database.dbsqlite import *

ip_server = get_ipaddr()
   
def scan_network():

    cidr = get_cidr(ip_server)

    # Se a hora do servidor local estiver >60s de diferença de cloud, ajusta!
    check_clock_diff()

    print(f'Escaneando a rede {cidr}...')
    print()

    # Monta os hosts com base no CIDR fornecido
    network = ipaddress.ip_network(cidr)

    # Converte o objeto de hosts do CIDR calculado em lista para processamento
    iplist = list(network.hosts())

    # Efetua o ping e captura o status para cada host da lista de hosts
    for ipping in iplist:
        date_scan = get_timenow()[2]
        ip = str(ipping)
        result = check_ping(ip)
        status = "Online" if result else "Offline"

        #Processa apenas as máquinas que responderem ao ping
        if status == "Online":
            
            db_insert_line('HOSTS_ONLINE', [ip, None, date_scan], ['IP', 'TYPE', 'DATE_SCAN'])


def inventory_desktop(terminal_list):
    #Traz todos os hosts (Online) da lista de Scan de rede que não tenha o type preenchido
    hosts_list = [result[0] for result in db_select_values('HOSTS_ONLINE', 'TYPE', None, columns='IP')]
    if hosts_list:

        #Identifica SOs Window e Linux
        for ip in hosts_list:

            so = "NA"
            terminal = "NA"
            ttl = host_ttl(ip)
            date_scan = get_timenow()[2]

            if ttl is not None:

                #Verifica se o host tem SO Windows ou Linux
                if ttl > 110 and check_openport(ip, 445) == True and check_openport(ip, 139) == True:
                    so = "Windows"
                elif ttl > 50 and check_SSHConnection(ip):
                    so = "Linux"

                #Verifica o status de inventario do host com SO Windows ou Linux
                if not so == "NA":
                    agent_status = glpi_agent_check(ip)
                    terminal = check_terminal(ip, terminal_list)

                    db_insert_line('DESKTOP_INVENTORY', [ip, so, agent_status, terminal, date_scan, ip_server], ['IP', 'SO', 'GLPI_AGENT', 'TERMINAL', 'DATE_SCAN', 'OWNER'])
            
        #Atualiza o type do Host para Desktop na lista de Scan de Rede
        desk_list = [result[0] for result in db_select_values('DESKTOP_INVENTORY', '', '', 'COLUMN', 'IP')]
        for desk in desk_list:
            db_update_dynamic_value('HOSTS_ONLINE', 'IP', desk, ['TYPE'], ['DESKTOP'])
        

def inventory_screen():
    pdv_ips = [result[0] for result in db_select_values("DESKTOP_INVENTORY", "TERMINAL", "PDV", "COLUMN", "IP", "PDV")]
    if pdv_ips:
        for ip_pdv in pdv_ips:
            ssh_con = SSH(ip_pdv)
            date_scan = get_timenow()[2]
            if ssh_con.ssh_connection():
                cmd_out = ssh_con.exec_cmd("sudo echo \"SELECT CASE WHEN nm_valor_chave = '1' THEN 'Touch' ELSE 'Default' END FROM tb_chave WHERE id_chave = 40\" | psql pdv -t -X | tr -d '[:space:]'")
                if cmd_out and '[sudo] password for pdv: ' in cmd_out:
                    cmd_out = cmd_out.replace('[sudo] password for pdv: ', '').strip()
                db_insert_line('PDV_SCREEN_TYPE', [ip_pdv, cmd_out, date_scan, ip_server], ['IP', 'TYPE', 'DATE_SCAN', 'OWNER'])
            else:
                db_insert_line('PDV_SCREEN_TYPE', [ip_pdv, 'ERROR_SSH', date_scan, ip_server], ['IP', 'TYPE', 'DATE_SCAN', 'OWNER'])


def devices_inventory(devices):
    #Traz todos os hosts (Online) da lista de Scan de rede que não tenha o type preenchido
    devices_list = [result[0] for result in db_select_values('HOSTS_ONLINE', 'TYPE', None, columns='IP')]
    if devices_list:
        
        for ip in devices_list:
            device = "NA"
            model = "NA"
            #Atualiza o type do Host para Device na lista de Scan de Rede
            db_update_dynamic_value('HOSTS_ONLINE', 'IP', ip, ['TYPE'], ['DEVICE'])

            date_scan = get_timenow()[2]
            mac = get_MACAddress(ip)
            if mac:
                device = check_device(mac, ip, devices)
                if "Laser" in device:
                    model = get_prn_model(ip)
                else: 
                    model = "NA"
            else:
                mac = "NA"
                
            db_insert_line('DEVICES_INVENTORY', [ip, mac, device, model, date_scan, ip_server], ['IP', 'MAC', 'DEVICE', 'MODEL', 'DATE_SCAN', 'OWNER'])


def full_inventory(devices, terminal):
    #Deleta as tabelas para efetuar um scan limpo.
    db_delete_all('HOSTS_ONLINE')
    db_delete_all('DESKTOP_INVENTORY')
    db_delete_all('PDV_SCREEN_TYPE')
    db_delete_all('DEVICES_INVENTORY')

    scan_network()
    inventory_desktop(terminal)
    inventory_screen()
    devices_inventory(devices)
