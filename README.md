# af18-demo
AnsibleFest 2018 - Jenkins and Tower Integration Session Demo Files

**coordinate_script.py:** Example of Jenkins coordination script that coordinates the job being
run in Jenkins including reading in the specified properties files to get the servers 
part of the and application specific parameters to use in the action script (example not provided).

**demo_product_inventory_script.py**: Example script that parses the property files and the product
specified in the environment variables set in the **demo_commands.txt** files 

***_Customer_Environments.properties**: Example properties files parsed by the coordinate_script.py and
demo_product_inventory_script.py

**json_output.txt**: JSON output from demo_product_inventory_script.py after parsing the 2 environment properties file 
for product APP1

**env_vs_ansible_limit.yml**: Example yaml of getting variables for a specific group to handle hosts being members of 
multiple groups at the same level with the same variables.


Run demo_product_inventory_script.py locally
--------------------------
**You will need Python locally installed**


1. Copy/Paste commands to set environment variables for your OS in demo_commands.txt
2. Run 

        python demo_product_inventory_script.py --list
