from urllib3.exceptions import InsecureRequestWarning
from subprocess import run, CalledProcessError
from warnings import filterwarnings
from fileinput import FileInput
from requests import post

filterwarnings('ignore', category=InsecureRequestWarning)

class GetData:
    def __init__(self, ip):
        self.rotina = []
        self.ip = ip
        self.timer_path = '/etc/systemd/system/alivescan.timer'
        self.service_path = '/etc/systemd/system/alivescan.service'
        self.api_url = "" # URL API ENDPOINT
        self.timer_info = self.get_timer_info()
        self.execute_updates()


    def get_timer_info(self):
        try:
            with open(self.timer_path, 'r') as file:
                for line in file:
                    if line.startswith('OnCalendar='):
                        return line.strip().split('=')[1]
        except FileNotFoundError:
            return False


    def update_timer_schedule(self, new_time):
        if self.timer_info and new_time:
            with FileInput(self.timer_path, inplace=True) as file:
                for line in file:
                    if line.startswith('OnCalendar='):
                        print(f'OnCalendar={new_time}')
                    else:
                        print(line, end='')
        else:
            return False


    def get_filial_rotinas(self):
        response = post(self.api_url, verify=False)
        rotinas = response.json().get('Rotinas', [])
        for rotina in rotinas:
            if rotina.get('nome') == 'alivescan':
                self.rotina.append(rotina)
    

    def get_macvendor(self):
        response = post(self.api_url, verify=False)
        devices = response.json().get('Macvendor', [])
        mac_vendor_dict = {device['MAC']: device['VENDOR'] for device in devices}
        return mac_vendor_dict


    def get_ipvendor(self):
        response = post(self.api_url, verify=False)
        devices = response.json().get('Ipvendor', [])
        ip_vendor_dict = {device['IP']: device['VENDOR'] for device in devices}
        return ip_vendor_dict


    def update_service_file(self, new_argument):
        try:
            with FileInput(self.service_path, inplace=True) as file:
                for line in file:
                    if line.strip().startswith('ExecStart='):
                        line = f'ExecStart=/var/scripts_rd/rotinas/alivescan {new_argument}\n'
                    print(line, end='')
        except Exception as e:
            return False


    def apply_systemd_changes(self):
        try:
            run(['systemctl', 'daemon-reload'], check=True)
        except CalledProcessError as e:
            return False

        
    def execute_updates(self):
        self.get_filial_rotinas()
        if self.rotina:
            for rotina in self.rotina:
                novo_horario = rotina.get('horario_execucao')
                if novo_horario:
                    self.update_timer_schedule(novo_horario)
                    self.update_service_file('4')
                    self.apply_systemd_changes()
    

    def get_last_scan(self):
        last_scan = self.rotina[0]['data_execucao']
        return last_scan
