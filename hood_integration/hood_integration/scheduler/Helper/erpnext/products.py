import frappe
from datetime import datetime, timedelta
from hood_integration.hood_integration.scheduler.Helper.exceptions import CustomException
from hood_integration.hood_integration.scheduler.Helper.jobs import add_comment_to_job


class Products:
    def __init__(self):
        self.products = None

    def product_exist(self,ean, log):
        customer = frappe.db.get_value('Item', {'item_code': ean}, 'name')
        if customer:
            return True
        else:
            add_comment_to_job(
                log, f"Product with ean: '{ean}' does not exist in ErpNext. Adding new Item")
            return False

    def __brand_exist(self,name):
        brand = frappe.db.get_value('Brand', {'name': name}, 'name')
        if brand:
            return True
        else:
            return False
        
    def __add_days_to_date(self,po_date, days_to_add:int):
        datetime_obj = datetime.strptime(po_date, "%Y-%m-%d")
        new_date = datetime_obj + timedelta(days=days_to_add)
        new_date_str = new_date.strftime("%Y-%m-%d")
        return new_date_str    

    def __create_brand(self,name):
        brand = frappe.get_doc({
            "doctype": "Brand",
            "brand": name
        })
        brand.insert()


    def create_product(self, item, log):
        ean = item.find("ean").text
        
        name_length = len(item.find("prodName").text)
        title = item.find("prodName").text
        if name_length > 140:
            name = title[:140]
        else:
            name = title
            
        if not self.__brand_exist("Meblito"):
           self.__create_brand("Meblito")
        
        product = frappe.get_doc({
            "doctype": "Item",
            "item_code": ean,
            "item_group": "Produkty",
            "item_name": name,
            "brand": "Meblito",
            "stock_uom": "szt.",
            "is_purchase_item": 1,
            "purchase_uom": "szt.",
            "sales_uom": "szt.",
            "is_sales_item": 1
        })
        product.insert()

    def get_sales_order_item_structure(self,item,count,po_date):
        
        product = item.find("item")
        ean = product.find("ean").text
        
        delivery_days =  frappe.db.get_value("Item",{"item_code": ean},"lead_time_days")
        delivery_date = self.__add_days_to_date(po_date,delivery_days)
        
            
        count += 1
        
        return {
            "doctype": "Sales Order Item",
            "idx":str(count),
            "item_code": ean,
            "delivery_date": delivery_date,
            "qty": int(product.find("quantity").text),
            "rate": float(product.find("price").text)
        }
