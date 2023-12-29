import frappe

class IntegrationMenu:
    @staticmethod
    def add_links():
        try:
            IntegrationMenu.__add_link_to_erpnext_integrations()
            print(f"* Adding link to ERPNext Integrations")
        except Exception as e:
            print(e)

    @staticmethod
    def delete_links(self):
        try:
            IntegrationMenu.__dellete_link_from_erpnext_integrations()
            print(f"* Deleting link from ERPNext Integrations")
        except Exception as e:
            print(e)

    def __add_link_to_erpnext_integrations(self):
        workspace = frappe.get_doc("Workspace", {"name": "ERPNext Integrations"})
    
        workspace_links = workspace.get("links") or []

        last_link = workspace_links[-1]
        last_idx = last_link.get("idx") + 1

        new_card = {
            "idx": last_idx,
            "hidden": 0,
            'icon': None,
            "is_query_report": 0,
            "label": "ERPTech Settings",
            "link_count": 0,
            "link_to": None,
            "link_type": None,
            'dependencies': None, 
            'only_for': None, 
            "onboard": 0,
            "type": "Card Break"
        }

        workspace_links.append(new_card)

        last_idx += 1

        new_link = {
            "idx": last_idx,
            "hidden": 0,
            "is_query_report": 0,
            "label": "Symphony Settings",
            "link_count": 0,
            "link_to": "symphony_settings",
            "link_type": "DocType",
            "onboard": 0,
            "type": "Link"
        }
    
        workspace_links.append(new_link)

        workspace.set("links", workspace_links)
        workspace.save()
        frappe.db.commit()

    def __dellete_link_from_erpnext_integrations(self):
        workspace = frappe.get_doc("Workspace", {"name": "ERPNext Integrations"})
        workspace_links = workspace.get("links") or []
        new_workspace_links = []

        for link in workspace_links:
            if link.get("label") not in ["Symphony Settings", "ERPTech Settings"]:
                new_workspace_links.append(link)

        workspace.set("links", new_workspace_links)
        workspace.save()
        frappe.db.commit()