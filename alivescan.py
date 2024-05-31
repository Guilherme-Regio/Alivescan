import util.actions as actions
from util.structure import *
import sys
from database.dbsqlite import *
from util.getdata import GetData
from util.postdata import PostData
from util.collectdata import CollectData

VERSION = "2.1.1"

class ExecuteAlivescan:

    def __init__(self, mode):
        self.ip = get_ipaddr()
        self.alivescan_interval = False
        self.mode = mode
        self.data = {}
        self.devices = {}
        self.terminal = {}
        self.collectdata = CollectData()
    

    def manager_service(self):
        self.getdata = GetData(self.ip)
        self.devices = self.getdata.get_macvendor()
        self.terminal = self.getdata.get_ipvendor()


    def manager_data(self):
        self.data = self.collectdata.collect()
        self.postdata = PostData(self.ip, self.data)


    def choice(self, opt):
        while True:
            if not opt in "1234":
                opt = input("Digite a opção correta: ")
            else:
                break


    def show_inventory(self):

        print("1 - Desktops")
        print("2 - Monitores PDV")
        print("3 - Impressora Laser / Consulta Preço / Encantômetro Legado / Impressora Térmica Ethernet")
        print("4 - Hosts de rede ONLINE")
        print()
        
        opt = str(input("Digite a opção: "))

        self.choice(opt)

        if opt == "1":
            show_tables('DESKTOP_INVENTORY')
        elif opt == "2":
            show_tables('PDV_SCREEN_TYPE')
        elif opt == "3":
            show_tables("DEVICES_INVENTORY")
        elif opt == "4":
            show_tables("HOSTS_ONLINE")


    def get_inventory(self):

        print("1 - Desktops")
        print("2 - Monitores PDV")
        print("3 - Impressora Laser / Consulta Preço / Encantômetro Legado / Impressora Térmica Ethernet")
        print("4 - Hosts de rede ONLINE")
        print()
        
        opt = str(input("Digite a opção: "))

        self.choice(opt)

        if opt == "1":
            db_extract_table_csv('DESKTOP_INVENTORY', 'DESKTOP_INVENTORY.csv')
        elif opt == "2":
            db_extract_table_csv('PDV_SCREEN_TYPE', 'PDV_SCREEN_TYPE.csv')
        elif opt == "3":
            db_extract_table_csv('DEVICES_INVENTORY', 'DEVICES_INVENTORY.csv')
        elif opt == "4":
            db_extract_table_csv('HOSTS_ONLINE', 'HOSTS_ONLINE.csv')


    def execute(self):
        if not self.mode:
            print("1 - EXIBIR dados de SCAN/INVENTÁRIO")
            print("2 - EXTRAIR dados de SCAN/INVENTÁRIO")
            print()
            
            opt = str(input("Digite a opção: "))

            while True:
                if not opt in "12":
                    opt = input("Digite a opção correta: ")
                else:
                    break

            if opt == "1":
                self.show_inventory()
            elif opt == "2":
                self.get_inventory()

        if self.mode:
            
            if self.mode == 3:
                self.manager_service()
            elif self.mode == 4:
                print('=' * 80)
                print(f'{"Varredura de hosts da rede:":^80}')
                print('=' * 80)
                print()
                
                self.manager_service()  
                last_scan = self.getdata.get_last_scan()
                date_today = get_timenow()[0]
                if last_scan == date_today:
                    print('Scan de rede já efetuado na data corrente...')

                else:
                    actions.full_inventory(self.devices, self.terminal)
                    self.manager_data()
    

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(f"Versão do script: {VERSION}")
        sys.exit()

    if len(sys.argv) > 1:
        try:
            mode = int(sys.argv[1])
            executor = ExecuteAlivescan(mode)
            executor.execute()
        except ValueError:
            False
    else:
        mode = False
        executor = ExecuteAlivescan(mode)
        executor.execute()