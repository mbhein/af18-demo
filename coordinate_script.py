#!/usr/bin/python
"""

"""

import os
#import sys
import ConfigParser
# import subprocess
import logging
import logging.handlers
import socket
import time
# import glob
import threading


# ####################################### Start of Classes ##########################################
class getProps(object):
    # ---------------------------------------------------------------------------------------------------
    #  getProps - Gets parameters for this script from:
    #        OS, Job Submission, Jenkins Coordinate Property File, Server Property File
    # ---------------------------------------------------------------------------------------------------
    def __init__(self):

        logger.debug('Got Properties For: ' + os.environ.get('JOB_NAME'))
        self.globalErrorCode = 0

        #-----------------------------------------------------------------------------------------
        #  OS Properties (From the Jenkins Job Submission and Jenkins Environment)
        #-----------------------------------------------------------------------------------------
        self.hostname = socket.getfqdn()
        self.nodeName = os.environ.get('NODE_NAME')
        self.workspace = os.environ.get('WORKSPACE')
        self.jobname = os.environ.get('JOB_NAME')
        self.ops_env = self.jobname.split("_")[0].lower()
        self.CustomerEnvironment = os.environ.get('Customer_Environment')


        #Deploy Parameters
        self.ReleaseBuildName = os.environ.get('Release_Build_Name')
        if self.ReleaseBuildName is None:
            self.ReleaseBuildName = ''


        # Print OS/Submission Properties
        logger.debug('Hostname'.ljust(msgFiller,' ') + '= ' + self.hostname)
        logger.debug('NODE_NAME'.ljust(msgFiller,' ') + '= ' + self.nodeName)
        logger.debug('Workspace'.ljust(msgFiller,' ') + '= ' + self.workspace)
        logger.debug('operating Environment'.ljust(msgFiller, ' ') + '= ' + self.ops_env)


        logger.info('CustomerEnvironment'.ljust(msgFiller,' ') + '= ' + self.CustomerEnvironment)
        if (self.ReleaseBuildName != ''):
            logger.info('ReleaseBuildName'.ljust(msgFiller,' ') + '= ' + self.ReleaseBuildName)

        # -----------------------------------------------------------------------------------------
        #  Global Environment Properties (parameters that are common to all environments)
        # -----------------------------------------------------------------------------------------
        cp = ConfigParser.ConfigParser()
        coordinatePropsFName = self.workspace + '/Coordinate.properties'
        logger.debug('Coordinate_Properties'.ljust(msgFiller, ' ') + '= ' + coordinatePropsFName)
        cp.read(coordinatePropsFName)

        self.mailhost = cp.get('main', 'mailhost')

        # Print Global Properties Main
        logger.debug('mailhost'.ljust(msgFiller,' ') + '= ' + self.mailhost)
        logger.debug('custEnvProps'.ljust(msgFiller,' ') + '= ' + self.custEnvProps)
        logger.info('appProduct'.ljust(msgFiller,' ') + '= ' + appProduct)

        # -----------------------------------------------------------------------------------------
        #  Specific Server Properties for the Customer Environment(TSM/UAT/PROD)
        # -----------------------------------------------------------------------------------------
        cp1 = ConfigParser.ConfigParser()
        CustEnvPropsFName = self.workspace + '/' + self.custEnvProps
        logger.debug('CustEnv Properties'.ljust(msgFiller, ' ') + '= ' + CustEnvPropsFName)
        cp1.read(CustEnvPropsFName)
        self.stagingServers = cp1.get(self.CustomerEnvironment, 'stagingServers')

        try:
            self.tomcatHome = cp1.get(self.CustomerEnvironment, 'tomcatHome')
        except ConfigParser.Error:
            self.tomcatHome = ''

        try:
            self.appHostPort = cp1.get(self.CustomerEnvironment, 'appHostPort')
        except ConfigParser.Error:
            self.appHostPort  = ''

        logger.info('stagingServers'.ljust(msgFiller,' ') + '= ' + self.stagingServers)
        logger.debug('tomcatHome'.ljust(msgFiller,' ') + '= ' + self.tomcatHome)
        logger.debug('appHostPort'.ljust(msgFiller,' ') + '= ' + self.appHostPort)

        logger.info(' ')

        return
# ####################################### End of Classes ############################################

# ####################################### Start of Functions ########################################
def appDeploy(hostname):
    logger.info(hostname + ': deploy ' + appProduct)

# ####################################### Start of Main #############################################
def main():
    # ---------------------------------------------------------------------------------------------------
    #   main - sets logging and coordinates this scripts processing.
    # ---------------------------------------------------------------------------------------------------
    global logger
    global props
    global appProduct
    global logPrefix
    global msgPrefix
    global msgFiller

    msgPrefix = '***** '
    msgFiller = 25

    #---------------------------------------------------------------------------------------------------
    # Setup Logger and other Variables for this script
    #---------------------------------------------------------------------------------------------------
    customerEnvironment = os.environ.get('Customer_Environment')
    if customerEnvironment.rfind('_') != -1:
        idx = customerEnvironment.rfind('_') + 1
        appProduct = customerEnvironment[idx:]
    else:
        appProduct = 'NA'

    logPrefix = customerEnvironment.replace('_','-')

    #Set Logger
    logger = logging.getLogger('__name__')
    logger.setLevel(logging.DEBUG)

    nowtime = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())
    jenkinsLogDebug = os.environ.get('WORKSPACE') + '/' + logPrefix + '-jenkinsLogDebug-' + nowtime + '.log'
    jenkinsLogInfo = os.environ.get('WORKSPACE') + '/' + logPrefix + '-jenkinsLogInfo-' + nowtime + '.log'
    outformat = logging.Formatter('%(asctime)s  %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    fh = logging.FileHandler(jenkinsLogDebug)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(outformat)
    logger.addHandler(fh)

    fh1 = logging.FileHandler(jenkinsLogInfo)
    fh1.setLevel(logging.INFO)
    fh1.setFormatter(outformat)
    logger.addHandler(fh1)

    # Jenkins Job Console Output
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(outformat)
    logger.addHandler(ch)

    logger.info(msgPrefix)
    logger.info(msgPrefix + 'START - Jenkins Job: ' + os.environ.get('JOB_NAME'))
    logger.info(msgPrefix)

    logger.debug('logPrefix = ' + logPrefix)
    logger.debug('appProduct = ' + appProduct)

    #---------------------------------------------------------------------------------------------------
    # Get Properties/Paramters for the requested job
    #---------------------------------------------------------------------------------------------------
    props = getProps()

    props.appProduct = appProduct
    props.jenkinsLogDebug = jenkinsLogDebug
    props.jenkinsLogInfo = jenkinsLogInfo
    props.globalErrorCode = 0
    props.logfilelist = []
    msgProduct = appProduct

    for singleserver in props.stagingServers:
        logger.info(' ')

        t = threading.Thread(target=appDeploy, args=(singleserver,))
        t.start()
    t.join()

    logger.info(msgPrefix)
    logger.info(msgPrefix + 'END - Jenkins Job: ' + os.environ.get('JOB_NAME'))
    logger.info(msgPrefix)

#---------------------------------------------------------------------------------------------------
#    Execute MAIN CODE
#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print 'Raise error'
        raise
