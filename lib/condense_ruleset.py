import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox

def condense_ruleset(input_file, output_file, new_ruleset_name, start_in, remove_source):
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Find all ruleGroups
    rule_groups = root.findall(".//ruleGroup")

    # Create a new ruleset
    new_rule_group = ET.Element("ruleGroup", {
        "id": "9999",  # Assuming a new unique id, adjust as needed
        "defaultRights": "2",
        "name": new_ruleset_name,
        "enabled": "true",
        "cycleRequest": "true",
        "cycleResponse": "false",
        "cycleEmbeddedObject": "false",
        "cloudSynced": "false"
    })

    # Add empty elements to the new ruleset
    ET.SubElement(new_rule_group, "acElements")
    ET.SubElement(new_rule_group, "condition", {"always": "true"}).append(ET.Element("expressions"))
    ET.SubElement(new_rule_group, "description")
    rules_element = ET.SubElement(new_rule_group, "rules")
    ET.SubElement(new_rule_group, "ruleGroups")

    # Collect all rules from existing ruleGroups
    for rule_group in rule_groups:
        rules = rule_group.find("rules")
        if rules is not None:
            for rule in list(rules):
                # Modify the rule ID by adding "1" to the front
                original_id = rule.get("id")
                new_id = "1" + original_id
                rule.set("id", new_id)
                rules_element.append(rule)
            if remove_source:
                root.remove(rule_group)

    # Add the new rule group to the XML tree
    root.append(new_rule_group)

    # Write the modified XML to the output file
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

def condense_ruleset_gui():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    input_file = filedialog.askopenfilename(title="Select Input XML File", filetypes=[("XML Files", "*.xml")])
    if not input_file:
        return

    output_file = filedialog.asksaveasfilename(title="Save Output XML File", defaultextension=".xml", filetypes=[("XML Files", "*.xml")])
    if not output_file:
        return

    new_ruleset_name = simpledialog.askstring("Input", "Enter New Ruleset Name (default: Condensed Ruleset):", initialvalue="Condensed Ruleset")
    if new_ruleset_name is None:
        return

    start_in = simpledialog.askstring("Input", "Enter Start In (default: Forwarding Layer):", initialvalue="Forwarding Layer")
    if start_in is None:
        return

    remove_source = messagebox.askyesno("Remove Source", "Do you want to remove the source rule/ruleset?")

    condense_ruleset(input_file, output_file, new_ruleset_name, start_in, remove_source)

    messagebox.showinfo("Success", f"Ruleset has been condensed and saved to {output_file}")

if __name__ == "__main__":
    condense_ruleset_gui()
