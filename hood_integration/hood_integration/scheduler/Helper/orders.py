import json
import requests
import time
import hmac
import hashlib
import urllib.parse
import frappe
from datetime import datetime, timedelta
from hood_integration.hood_integration.doctype.hood_settings.hood_settings import HoodCredentials
from hood_integration.hood_integration.scheduler.Helper.exchange_rates import ExchangeRates
from hood_integration.hood_integration.scheduler.Helper.erpnext.selling import Selling
from hood_integration.hood_integration.scheduler.Helper.erpnext.products import Products
from hood_integration.hood_integration.scheduler.Helper.erpnext.payment import Payment
from hood_integration.hood_integration.scheduler.Helper.erpnext.customer import Customer
from hood_integration.hood_integration.scheduler.Helper.jobs import add_comment_to_job, set_job_async
import xml.etree.ElementTree as ET


def createContentStringToGetOrderList(from_date: datetime, to_date: datetime):
    keys = HoodCredentials()
    name = keys.key
    password = hash_md5(keys.key_secret)
    # root element
    root = ET.Element("api")
    root.set("type", "public")
    root.set("version", "2.0")
    root.set("user", name)
    root.set("password", password)

    # child elements and set their values
    account_name = ET.SubElement(root, "accountName")
    account_name.text = name

    account_pass = ET.SubElement(root, "accountPass")
    account_pass.text = password

    function = ET.SubElement(root, "function")
    function.text = "orderList"

    
    list_mode = ET.SubElement(root, "listMode")
    list_mode.text = "details"

    date_range = ET.SubElement(root, "dateRange")
    date_range_type = ET.SubElement(date_range, "type")
    date_range_type.text = "orderDate"
    start_date = ET.SubElement(date_range, "startDate")
    start_date.text = from_date.strftime("%m/%d/%Y")
    end_date = ET.SubElement(date_range, "endDate")
    end_date.text = to_date.strftime("%m/%d/%Y")

    order_id = ET.SubElement(root, "orderID")
    order_id.text = ""

    # Create the XML string
    xml_string = ET.tostring(root, encoding="utf-8",
                             method="xml").decode("utf-8")

    return xml_string

def CreateContentStringToGetItemDetail(itemId):
    keys = HoodCredentials()
    name = keys.key
    password = hash_md5(keys.key_secret)
    root = ET.Element("api")
    root.set("type", "public")
    root.set("version", "2.0")
    root.set("user", name)
    root.set("password", password)

    account_name = ET.SubElement(root, "accountName")
    account_name.text = name
    account_pass = ET.SubElement(root, "accountPass")
    account_pass.text = password
    function = ET.SubElement(root, "function")
    function.text = "itemDetail"
    item_id = ET.SubElement(root, "itemID")
    item_id.text = itemId
    return ET.tostring(root, encoding="utf-8", method="xml").decode()

def CreateContentStringToGetItemStatus(itemId):
    keys = HoodCredentials()
    name = keys.key
    password = hash_md5(keys.key_secret)
    root = ET.Element("api")
    root.set("type", "public")
    root.set("version", "2.0")
    root.set("user", name)
    root.set("password", password)

    account_name = ET.SubElement(root, "accountName")
    account_name.text = name
    account_pass = ET.SubElement(root, "accountPass")
    account_pass.text = password
    function = ET.SubElement(root, "function")
    function.text = "itemStatus"
    item_id = ET.SubElement(root, "itemID")
    item_id.text = itemId
    return ET.tostring(root, encoding="utf-8", method="xml").decode()



def hash_md5(string):
    md5_hash = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))
    hashed_string = md5_hash.hexdigest()
    return hashed_string


#################################################################################################

def get_list_id(xml_str):
    root = ET.fromstring(xml_str)
    order_ids = []
    for order in root.findall('.//order'):
        for item in order.findall('.//details'):
            item_id = item.find('orderID').text
            order_ids.append(item_id)
    return order_ids


def get_orders_form_hood(dateFrom: datetime, dateTo: datetime,log):
    uri = f'https://www.hood.de/api.htm'
    try:
        response = requests.post(
            uri, data=createContentStringToGetOrderList(dateFrom, dateTo))
        response.raise_for_status()
        return response.content.decode("utf-8")
    except requests.exceptions.HTTPError as e:
        add_comment_to_job(log, f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        add_comment_to_job(log, f"Request error: {e}")

#################################################################################################


def get_order_form_hood_by_id(order, log = None):
    add_comment_to_job(log, ET.tostring(order, "unicode"))
    idOrder = order.find('details').find("orderID").text
    if not order_exist(idOrder, log):
        create_order_from_hood_data(order,log)
    else:
        add_comment_to_job(log, f"No data for order {idOrder}")    
   

#################################################################################################


def create_order_from_hood_data(order, log=None):
    uri = f'https://www.hood.de/api.htm'
    details = order.find('details')
    idOrder = details.find("orderID").text
        
    buyer = order.find("buyer")
    date = details.find('date').text[5:-2]
    datetime_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    po_date = datetime_obj.strftime("%Y-%m-%d")

    # price list section
    selling = Selling()

    # customer section
    customer = Customer()
    if not customer.customer_exist(buyer.find("email").text, log):
        customer_name = customer.create_customer(order, log)
    else:
        customer_name = customer.get_customer_name(buyer.find("email").text)
        customer_doc = customer.get_customer(customer_name)
        if customer_doc.mobile_no != buyer.find("phone").text:
            try:
                contact = frappe.get_doc('Contact', f"{customer_name}-{customer_name}")
                contact.mobile_no = buyer.find("phone").text
                if len(contact.phone_nos) > 0:
                    contact.phone_nos[0].mobile_no = buyer.find("phone").text
                contact.save()
                frappe.db.commit()

                #contact_phone = frappe.db.get_value('Contact Phone', {'parent': f"{customer_name}-{customer_name}"}, 'name')

                #frappe.db.set_value('Contact Phone', contact_phone, 'phone', buyer.find("phone").text)
                #frappe.db.commit()
                #frappe.db.set_value('Contact', f"{customer_name}-{customer_name}", 'mobile_no', buyer.find("phone").text)
                #frappe.db.commit()

                billing_address = frappe.db.get_list('Address',
                    filters={
                        'address_title': customer_name,
                        'is_primary_address': 1
                    },
                    fields=['name'],
                    as_list=True
                )

                if len(billing_address) > 0:
                    billing = frappe.get_doc("Address", billing_address[0])
                    billing.phone = buyer.find("phone").text
                    billing.save()
                    frappe.db.commit()

                customer_doc = frappe.get_doc("Customer", customer_name)
                customer_doc.mobile_no = buyer.find("phone").text
                customer_doc.save()
                frappe.db.commit()
            except Exception as e:
                add_comment_to_job(f"Update phone number failed: {e}")


    # product section
    products = Products()
    sales_order_items = []
    order_items = order.find(".//orderItems").findall('item')
    add_comment_to_job(log, f"Item count: {len(order_items)}")
    for product in order_items:
        try:
            response = requests.post(uri, data=CreateContentStringToGetItemDetail(product.find("itemID").text))
            data = response.content.decode("utf-8")
            root = ET.fromstring(data)
            #add_comment_to_job(log, f"ItemId: {product.find('itemID').text}")
            #add_comment_to_job(log, f"Item Data: {data}")
        except requests.exceptions.HTTPError as e:
            add_comment_to_job(log, f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            add_comment_to_job(log, f"Request error: {e}")
        if not products.product_exist(product.find("ean").text, log):
            products.create_product(product, log)
        sales_order_items.append(
            products.get_sales_order_item_structure(product, len(sales_order_items),po_date))

    shipping_cost = details.find("shipCost").text
    #add_comment_to_job(log, f"Items: {sales_order_items}")

    # # first unit
    status_order = details.find("orderStatusActionSeller").text

    # # Payment terms
    payment = Payment()

    # Exchange Rates
    exchange_rates = ExchangeRates()
    country_code = str(buyer.find("countryTwoDigit").text).lower()
    currency = customer.get_currency_by_code(country_code)
    eur = exchange_rates.get_currancy_rate(currency)

    # order section
    order = frappe.get_doc({
        "doctype": 'Sales Order',
        "naming_series": "SO-HOOD-.YYYY.-",
        "customer": customer_name,
        "order_type": "Sales",
        "po_no": idOrder,
        "po_date": po_date,
        "transaction_date": po_date,
        "selling_price_list": selling.get_price_list(),
        "currency": currency,
        "conversion_rate": eur,
        "orderstatus": status_order,
        "items": sales_order_items,
        "taxes": [{
            "charge_type": "Actual",
            "account_head": "5205 - Koszty dostaw i przesyłek - Mebli",
            "description": "Koszty dostaw i przesyłek",
            "tax_amount": shipping_cost
        }],
        "payment_schedule": [{
            "idx": 1,
            "due_date": po_date,
            "invoice_portion": 100.0,
            "payment_term": payment.getPaymentTerm(),
            "doctype": "Payment Schedule",
        }]
    })

    try:
        order.insert()
        add_comment_to_job(
            log, f"Sales order [{idOrder}] added to {order.name}")
    except Exception as e:
        data_string = frappe.as_json(order)
        add_comment_to_job(
            log, f"Something went wrong: {e}, insert data: {data_string}")

#################################################################################################


def order_exist(id_order: str, log):
    sales_order = frappe.db.get_value(
        'Sales Order', {'po_no': id_order}, 'name')
    if sales_order:
        add_comment_to_job(
            log, f"Sales Order {id_order} exists under the name {sales_order}.")
        return True
    else:
        add_comment_to_job(
            log, f"Sales Order {id_order} does not exist in ErpNext. Start creating new document...")
        return False
