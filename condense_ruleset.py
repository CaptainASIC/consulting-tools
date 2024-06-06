import xml.etree.ElementTree as ET
import argparse

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

def main():
    parser = argparse.ArgumentParser(description="Condense Skyhigh Web Gateway rulesets into a single ruleset.")
    parser.add_argument('-in', '--input', required=True, help='Input XML file')
    parser.add_argument('-out', '--output', required=True, help='Output XML file')
    args = parser.parse_args()

    new_ruleset_name = input("Enter New Ruleset Name (default: Condensed Ruleset): ") or "Condensed Ruleset"
    start_in = input("Enter Start In (default: Forwarding Layer): ") or "Forwarding Layer"
    remove_source = input("Do you want to remove the source rule/ruleset? (yes/no, default: no): ").lower() == "yes"

    condense_ruleset(args.input, args.output, new_ruleset_name, start_in, remove_source)

if __name__ == "__main__":
    main()
