from database.dbsqlite import db_select_values

class CollectData:
    def __init__(self):
        self.data = {}

    def collect(self):
        desktop_inventory = self.get_desktop_inventory()
        pdv_screen_type = self.get_pdv_screen_type()
        devices_inventory = self.get_devices_inventory()

        self.data['desktop_inventory'] = desktop_inventory
        self.data['pdv_screen_type'] = pdv_screen_type
        self.data['devices_inventory'] = devices_inventory

        return self.data


    def get_desktop_inventory(self):
        return db_select_values("DESKTOP_INVENTORY", type_select="TABLE")


    def get_pdv_screen_type(self):
        return db_select_values("PDV_SCREEN_TYPE", type_select="TABLE")


    def get_devices_inventory(self):
        return db_select_values("DEVICES_INVENTORY", type_select="TABLE")
