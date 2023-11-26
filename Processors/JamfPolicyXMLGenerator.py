#!/usr/local/autopkg/python

import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from autopkglib import Processor, ProcessorError

__all__ = ["JamfPolicyXMLGenerator"]


class JamfPolicyXMLGenerator(Processor):
    """Generates JAMF XML configuration for a policy."""

    input_variables = {
        "general": {
            "description": "General settings for the policy.",
            "required": True
        },
        "scope": {
            "description": "Scope settings for the policy.",
            "required": True
        },
        "self_service": {
            "description": "Self service settings for the policy.",
            "required": True
        },
        "maintenance": {
            "description": "Maintenance settings for the policy.",
            "required": True
        },
        "files_processes": {
            "description": "File process settings for the policy.",
            "required": True
        },
        "user_interaction": {
            "description": "User interaction settings for the policy.",
            "required": True
        },
        "output": {
            "description": "Where the XML is outputted to.",
            "required": True
        },
    }

    output_variables = {}

    description = __doc__

    @staticmethod
    def bool_to_str(value):
        """Converts a boolean value to a lowercase string."""
        if isinstance(value, bool):
            return str(value).lower()
        return value

    def create_policy_xml(self, general, scope, self_service, maintenance, files_processes, user_interaction):
        """Generates the XML structure for the policy."""
        policy = ET.Element("policy")
        self.add_general_section(policy, general)
        self.add_scope_section(policy, scope)
        self.add_package_configuration(policy)
        self.add_scripts_section(policy)
        self.add_self_service_section(policy, self_service)
        self.add_maintenance_section(policy, maintenance)
        self.add_files_processes_section(policy, files_processes)
        self.add_user_interaction_section(policy, user_interaction)

        # Formatting XML output
        xml_str = ET.tostring(policy, encoding="unicode")
        return minidom.parseString(xml_str).toprettyxml(indent="    ")

    def add_general_section(self, policy, general):
        """Adds the general section to the policy."""
        general_element = ET.SubElement(policy, "general")
    
        # Mandatory elements
        ET.SubElement(general_element, "name").text = general.get("policy_name", "DefaultPolicyName") # policy name
        ET.SubElement(general_element, "trigger").text = general.get("trigger", "EVENT") # policy trigger
        category = ET.SubElement(general_element, "category") # policy category
        ET.SubElement(category, "name").text = general.get("policy_category", "DefaultCategory")
    
        # Optional elements
        if "enabled" in general and general["enabled"] != "":
            ET.SubElement(general_element, "enabled").text = self.bool_to_str(general["enabled"])
        if "trigger_checkin" in general and general["trigger_checkin"] != "":
            ET.SubElement(general_element, "trigger_checkin").text = self.bool_to_str(general["trigger_checkin"])
        if "trigger_enrollment_complete" in general and general["trigger_enrollment_complete"] != "":
            ET.SubElement(general_element, "trigger_enrollment_complete").text = self.bool_to_str(general["trigger_enrollment_complete"])
        if "trigger_login" in general and general["trigger_login"] != "":
            ET.SubElement(general_element, "trigger_login").text = self.bool_to_str(general["trigger_login"])
        if "trigger_logout" in general and general["trigger_logout"] != "":
            ET.SubElement(general_element, "trigger_logout").text = self.bool_to_str(general["trigger_logout"])
        if "trigger_network_state_changed" in general and general["trigger_network_state_changed"] != "":
            ET.SubElement(general_element, "trigger_network_state_changed").text = self.bool_to_str(general["trigger_network_state_changed"])
        if "trigger_startup" in general and general["trigger_startup"] != "":
            ET.SubElement(general_element, "trigger_startup").text = self.bool_to_str(general["trigger_startup"])
        if "trigger_other" in general and general["trigger_other"] != "":
            ET.SubElement(general_element, "trigger_other").text = general["trigger_other"].lower().replace(" ", "_")
        if "frequency" in general and general["frequency"] != "":
            ET.SubElement(general_element, "frequency").text = general["frequency"]

    def add_scope_section(self, policy, scope):
        """Adds the scope section to the policy."""
        scope_element = ET.SubElement(policy, "scope")
        self.create_scope_xml(scope_element, scope)

    def add_package_configuration(self, policy):
        """Adds package configuration to the policy."""
        package_config = ET.SubElement(policy, "package_configuration")
        packages = ET.SubElement(package_config, "packages")
        ET.SubElement(packages, "size").text = "1"
        package = ET.SubElement(packages, "package")
        ET.SubElement(package, "name").text = self.env.get("pkg_name")
        ET.SubElement(package, "action").text = "Install"

    def add_scripts_section(self, policy):
        """Adds scripts section to the policy."""
        scripts = ET.SubElement(policy, "scripts")
        ET.SubElement(scripts, "size").text = "0"

    def add_self_service_section(self, policy, self_service):
        """Adds self-service settings to the policy."""
        self_service_element = ET.SubElement(policy, "self_service")
        ET.SubElement(self_service_element, "use_for_self_service").text = self.bool_to_str(self_service["show"])
        if "show" in self_service and self.bool_to_str(self_service["show"]) != "false":
            ET.SubElement(self_service_element, "install_button_text").text = self_service.get("install_button_text", "Install")
            ET.SubElement(self_service_element, "reinstall_button_text").text = self_service.get("reinstall_button_text", "Reinstall")
            ET.SubElement(self_service_element, "self_service_display_name").text = self_service["display_name"]
            
            # Get current date and time in the specified format
            current_datetime = datetime.datetime.now().strftime("%d/%m/%y %I:%M%p").lower()
            
            # Update self_service_description with additional information
            description_with_info = self_service["description"] + "\n**Package Information**\n"
            description_with_info += f"Version: {self.env.get('version', 'Unknown')}\n"
            description_with_info += f"Last Update: {current_datetime}"
            ET.SubElement(self_service_element, "self_service_description").text = description_with_info
    
            # Adding categories
            self_service_categories = ET.SubElement(self_service_element, "self_service_categories")
            # Iterate over each category
            for category in self_service["categories"]:
                category_element = ET.SubElement(self_service_categories, "category")
                ET.SubElement(category_element, "name").text = category["name"]
                ET.SubElement(category_element, "display_in").text = self.bool_to_str(category["display_in"])
                ET.SubElement(category_element, "feature_in").text = self.bool_to_str(category["feature_in"])


    def add_maintenance_section(self, policy, maintenance):
        """Adds maintenance settings to the policy."""
        maintenance_element = ET.SubElement(policy, "maintenance")
        recon = self.bool_to_str(maintenance.get("recon", "")) if maintenance else ""
        ET.SubElement(maintenance_element, "recon").text = recon

    def add_files_processes_section(self, policy, files_processes):
        """Adds files_processes settings to the policy."""
        maintenance_element = ET.SubElement(policy, "files_processes")
        if files_processes:
            if files_processes.get("run_command"):
                ET.SubElement(maintenance_element, "run_command").text = files_processes["run_command"]

    def add_user_interaction_section(self, policy, user_interaction):
        """Adds user interaction settings to the policy."""
        user_interaction_element = ET.SubElement(policy, "user_interaction")
        # Use .get() to provide a default value if the key is not present
        message_start = user_interaction.get("message_start", "") if user_interaction else ""
        message_finish = user_interaction.get("message_finish", "") if user_interaction else ""
    
        ET.SubElement(user_interaction_element, "message_start").text = message_start
        ET.SubElement(user_interaction_element, "message_finish").text = message_finish      

    def create_scope_xml(self, scope_element, scope_details):
        """Generates the XML structure for the scope"""
        # Handle all_computers
        ET.SubElement(scope_element, "all_computers").text = self.bool_to_str(scope_details["all_computers"])

        if not scope_details["all_computers"]:
            # Handle include section
            include = scope_details.get("include", {})
            self.create_scope_subsection(scope_element, include)

            # Handle exclude section
            exclude = scope_details.get("exclude", {})
            exclusions_element = ET.SubElement(scope_element, "exclusions")
            self.create_scope_subsection(exclusions_element, exclude)

    def create_scope_subsection(self, parent_element, section_details):
        """Creates a scope subsection for include/exclude"""
        # Handle computers
        computers = ET.SubElement(parent_element, "computers")
        for computer in section_details.get("computers", []):
            computer_element = ET.SubElement(computers, "computer")
            ET.SubElement(computer_element, "id").text = str(computer["id"])
            ET.SubElement(computer_element, "name").text = computer["name"]
            if "udid" in computer:
                ET.SubElement(computer_element, "udid").text = computer["udid"]

        # Handle computer_groups
        computer_groups = ET.SubElement(parent_element, "computer_groups")
        for group in section_details.get("computer_groups", []):
            group_element = ET.SubElement(computer_groups, "computer_group")
            ET.SubElement(group_element, "id").text = str(group["id"])
            ET.SubElement(group_element, "name").text = group["name"]

        # Handle departments
        departments = ET.SubElement(parent_element, "departments")
        for department in section_details.get("departments", []):
            department_element = ET.SubElement(departments, "department")
            ET.SubElement(department_element, "id").text = str(department["id"])
            ET.SubElement(department_element, "name").text = department["name"]

    def main(self):
        # Collect input variables
        general = self.env.get("general", {})
        scope = self.env.get("scope", {})
        self_service = self.env.get("self_service", {})
        maintenance = self.env.get("maintenance", {})
        files_processes = self.env.get("files_processes", {})
        user_interaction = self.env.get("user_interaction", {})

        xml_data = self.create_policy_xml(
            general, scope, self_service, maintenance, files_processes, user_interaction)

        # Writing XML to file
        output_location = self.env.get("output")
        with open(f"{output_location}.xml", "w") as file:
            file.write(xml_data)


if __name__ == "__main__":
    processor = JamfPolicyXMLGenerator()
    processor.execute_shell()
