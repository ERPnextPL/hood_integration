
from hood_integration.hood_integration.scheduler.Helper.erpnext.integrations import IntegrationMenu
from hood_integration.hood_integration.scheduler.translations import translations
from hood_integration.hood_integration.scheduler.Helper.erpnext.payment import Payment
from hood_integration.hood_integration.scheduler.Helper.jobs import delete_all_jobs


def uninstall():
    #
    payment = Payment()
    translationsObj = translations()

    # delete payments
    payment.deletePaymentTerm()
    
    # delete translations
    translationsObj.delete_translations(translationsObj.get_translation_list())
    
    # deleting links from erpnext integrations
    integration_menu = IntegrationMenu()
    integration_menu.delete_links()
    
    # delete all jobs from queue
    delete_all_jobs()