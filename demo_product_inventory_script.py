#!/usr/bin/env python

"""
    This script is used to create/update the Ansible Tower inventory for the supplied product.

    Tower invokes this script with '--list' to list the inventory
        and the script returns back to Tower a JSON hash/dictionary.

    This script reads in the supplied customer environment properties files, generates the product hierarchy,
        groups/regions for each environment, and associated hosts and variables for each group/region.

    The following Tower inventory environment variables are mandatory:
        product: <PRODUCT in upper case e.g. APP1>

    At least one of the following Tower inventory environment variables needs to be set:
        prod_properties_file: <local path on Tower host to property file>
        uat_properties_file: <local path on Tower host to property file>
              

   
"""

import os
import os.path
import sys
import json
import ConfigParser
import argparse
import re


class EnvProps(object):
    # ---------------------------------------------------------------------------------------------------
    #  EnvProps - object representing inventory for the environment property file provided:
    #       ENV_DA_Customer_Environments.properites
    # ---------------------------------------------------------------------------------------------------

    def __init__(self, properties_file):
        self.sections = []
        self.customer_grouping = ''
        self.environment_group = ''

        self.config = ConfigParser.RawConfigParser()
        self.config.read(properties_file)

        self.product = product
        self.product_groups = {}
        self.product_group_props = {}

        self.environment = re.split(r'[/\\]', properties_file)[-1].lower().split("_")[0]
        self.environment_hierarchy = {}

    def set_environment_group(self):
        self.environment_group = "all_{}_{}_{}".format(self.environment, self.customer_grouping, self.product.lower())

    def get_product_groups(self):
        self.product_groups[self.environment_group] = {"children": [_section.lower() for _section in self.sections]}
        return self.product_groups

    def get_product_group_props(self):
        _sections = self.sections
        # section in file = group in Tower
        for _section in _sections:
            _section_hosts = []
            _section_vars = {}

            # hosts for the current group
            if self.config.has_option(_section, hosts_option):
                _section_hosts = [i for i in self.config.get(_section, hosts_option).split(",")]

            # build out vars for current group
            options = self.config.options(_section)
            for option in options:
                if option != hosts_option:
                    _section_vars[option] = self.config.get(_section, option)
            if product == 'APP1':
                _temp = _section.lower() + "_vars"
                _section_vars = {_temp: _section_vars}

            self.product_group_props[_section.lower()] = {"hosts": _section_hosts, "vars": _section_vars}

        return self.product_group_props


class SaaSEnvProps(EnvProps):
    # ---------------------------------------------------------------------------------------------------
    #  SaaSProperties - subclass of EnvProps object representing SaaS inventories
    # ---------------------------------------------------------------------------------------------------

    def __init__(self, properties_file):
        EnvProps.__init__(self, properties_file)
        self.customer_grouping = 'saas'
        self.set_environment_group()

        _sections = self.config.sections()
        for _section in _sections:
            if self.product != 'all':
                if _section.endswith(product):
                    self.sections.append(_section)
            else:
                self.sections.append(_section)


def args_parser():
    # ---------------------------------------------------------------------------------------------------
    #  args_parser - parse commandline arguments passed to script
    # ---------------------------------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description='Ansible requires either --list or --host')
    parser.add_argument('--list', action='store_true', default=True,
                        help='List all inventory and variables (default)')
    parser.add_argument('--host', action='store',
                        help='Get only host')
    return parser.parse_args()


def customer_grouping_children(customer_grouping, property_files):
    # ---------------------------------------------------------------------------------------------------
    #  customer_grouping_children - return all children of a product in a supplied customer group for all
    #   property files supplied
    # ---------------------------------------------------------------------------------------------------
    children = ["all_{}_{}_{}".format(env, customer_grouping, product.lower())
                for env in (re.split(r'[/\\]', f)[-1].lower().split("_")[0] for f in property_files)]
    return children


# Start of Main #############################################
def main():

    global hosts_option
    global product

    # Get properties file for each environment and pass silently if no value given
    property_files = []
    env_property_params = [
                            'uat_properties_file',
                            'prod_properties_file']

    for env_property_param in env_property_params:
        try:
            property_files.append(os.environ[env_property_param])
        except KeyError:
            pass

    # Verify we have at least one property file
    if not property_files:
        sys.exit('Error - no environment property files supplied')

    # Verify files in property_files exists
    for property_file in property_files:
        if not os.path.isfile(property_file):
            sys.exit('Error - property file: ' + property_file + ' not found')

    # If specific product isn't supplied, exit with error
    try:
        product = os.environ['product']
    except KeyError, err:
        sys.exit('Error - environment parameter "%s" not found' % str(err))

    # set defaults
    product_hierarchy = {}
    product_children = []
    inventory = {}
    meta = {}
    hosts_option = "servers"

    # Retrieve which argument was passed
    args = args_parser()

    # This should always be true since Tower will supply --list
    if args.list:

        # Process SaaS environments
        saas_product = "all_saas_" + product.lower()
        product_children.append(saas_product)
        product_hierarchy[saas_product] = {"children": customer_grouping_children('saas', property_files)}

        for property_file in property_files:
            saas = SaaSEnvProps(property_file)

            # Get product groups in environment
            inventory.update(saas.get_product_groups())

            # Get properties (Hosts/Vars) for product groups in environment
            inventory.update(saas.get_product_group_props())

        # Add product's children hierarchy
        product_hierarchy[product.lower()] = {"children": product_children}
        inventory.update(product_hierarchy)

        # Add meta to prevent Tower from invoking --host for each host:
        meta['_meta'] = {'hostvars': {}}
        inventory.update(meta)

    # Print json.dump for Tower to use
    print(json.dumps(inventory, sort_keys=True, indent=2))


# ---------------------------------------------------------------------------------------------------
#    Execute MAIN CODE
# ---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.exit('Exception running main() with error - "%s"' % str(e))
