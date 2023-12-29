import frappe
from hood_integration.hood_integration.scheduler.hood import get_orders
from hood_integration.hood_integration.scheduler.Helper.erpnext.integrations import IntegrationMenu
from hood_integration.hood_integration.scheduler.translations import translations
from hood_integration.hood_integration.scheduler.Helper.erpnext.payment import Payment


def install():
    # payment = Payment()
    # payment.addKauflandPayments()

    translationsObj = translations()
    translationsObj.add_translations(translationsObj.get_translation_list())

    integration_menu = IntegrationMenu()
    integration_menu.add_links()
    
