# Copyright (c) 2023, ErpTech and contributors
# For license information, please see license.txt

# import frappe
from datetime import datetime, timedelta
import frappe
from frappe.model.document import Document

class HoodCredentials:
    def __init__(self):
        self.key = self.__get_key()
        self.key_secret = self.__get_secret()

    def __get_key(self):
        return frappe.get_doc("Hood Settings", "api").key
    
    def __get_secret(self):
        return frappe.get_doc("Hood Settings", "api").secret_key
    
    def exist(self) -> bool:
        if self.__get_key() is not None and self.__get_secret() is not None:
            return True
        else:
            return False 

class HoodSettingsOptions:
    def __init__(self):
        self.number_of_days_back = self.__get_number_of_days_back()
        self.date_after_subtract = self.__get_date_after_subtract()
        self.date_after_subtract_iso = self.__get_date_iso_format()

    def __get_date_after_subtract(self) -> datetime:
        current_date = datetime.now()
        date_after_subtract = None
        days_to_subtract = self.__get_number_of_days_back()
        if days_to_subtract is not None:
            date_after_subtract = current_date - timedelta(days=days_to_subtract)
        else:
            date_after_subtract = current_date
        return date_after_subtract
    
    def __get_date_iso_format(self):
        return self.__get_date_after_subtract().date().isoformat() + "T00:00:00Z"     
        
    def __get_number_of_days_back(self) -> int:
        return frappe.get_doc("Hood Settings", "api").number_of_days_back
class HoodSettings(Document):
	pass
