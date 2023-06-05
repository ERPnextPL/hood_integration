import frappe
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from hood_integration.hood_integration.doctype.hood_settings.hood_settings import HoodCredentials, HoodSettingsOptions
from hood_integration.hood_integration.scheduler.Helper.orders import get_list_id, get_order_form_hood_by_id, get_orders_form_hood
from hood_integration.hood_integration.scheduler.Helper.jobs import add_comment_to_job, set_job_for_order_async

def get_orders():
    creditionals = HoodCredentials()
    settings = HoodSettingsOptions() 
    datefrom = settings.date_after_subtract
    dateto = datetime.now()

    last_log = frappe.get_last_doc("Scheduled Job Log", filters={"scheduled_job_type": "hood.get_orders", "status": "Start"}, order_by="creation desc")
    add_comment_to_job(last_log,f"Start process at: {datetime.now()} ")
        
    if creditionals.exist():
        orders_xml = get_orders_form_hood(datefrom,dateto)
        if orders_xml != None:
            add_comment_to_job(last_log,f"List of orders retrieved from date {datefrom} to date {dateto}: {str(get_list_id(orders_xml))} ")
            root = ET.fromstring(orders_xml)
            for order in root.findall('.//order'):
                set_job_for_order_async(f"hood.get_order={id}",f"hood_integration.hood_integration.scheduler.Helper.orders.get_order_form_hood_by_id","default",order,last_log)
    else:
        add_comment_to_job(last_log,f"No configuration for the application...")
