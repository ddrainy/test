# !/usr/bin/env python
# coding=utf-8


from __future__ import print_function
import locale
import os
import sys
import subprocess
import socket
import re
from strop import strip
from dialog import Dialog
import netifaces

class Constants:
    """
        定义提示内容
    """
    TXT_BACKGROUND_TITLE = 'ZbStor Network Configuration Tools.'
    TXT_ERR_ROOT_REQUIRED = 'root privileges required. run with sudo'
    TXT_NETWORK_CFG_SUCCESS = 'Network configuration completed successfully!\n\n'
    TXT_NETWORK_CFG_ERROR = 'Error occured while configuring network interface!\n\n'
    TXT_HOSTNAME_CFG_SUCCESS = 'Hostname configuration completed successfully!\n\n'
    TXT_HOSTNAME_CFG_ERROR = 'Error occured while configuring hostname interface!\n\n'
    TXT_SELECT_INTERFACE = 'Select interface'
    TXT_SELECT_OPTION = 'Select option'
    TXT_SELECT_SOURCE = 'Select address source'
    TXT_MESSAGE_NETWORK = 'Configuring for static IP address...'
    TXT_MESSAGE_HOSTNAME = 'Configuring for hostname...'
    TXT_MESSAGE_ERROR = '\Zb\Z1Error: %s\n\n\Z0Please try again.'
    TXT_IP_ERROR = ' format error.'
    TXT_CONF_NULLIP = 'Are you sure disabled NIC?'
    TXT_CONFIG_STATIC_TITLE = 'Network interface:'
    TXT_GATEWAY = 'Gateway'
    TXT_NETMASK = 'Netmask'
    TXT_IP = 'IP'

def run_process(strCmd, stderr=False):
    """
    执行系统命令
    :param strCmd:命令内容
    :param stderr:是否需要返回错误信息
    :return: 执行结果 
    """
    p = subprocess.Popen([strCmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output = ""
    while (True):
        retcode = p.poll()
        if stderr:
            line = p.stderr.readline().decode('utf-8')
        else:
            line = p.stdout.readline().decode('utf-8')
        output = output + line

        if retcode is not None:
            break

    return {'retcode': retcode, 'output': output}

def show_sambapath_dialog()
    strFile = "/etc/samba/smb.conf"

    if os.path.isfile(strFile):
        arrPath = run_process("sed -i 'path' ")

def show_hostip_dialog(arrIp)
    arrNet = netifaces.interfaces()
    for strNet in arrNet:
        if strNet.lower() != "lo":
            arrIp = netifaces.ifaddresses(strNet)

            if arrIp.has_key(netifaces.AF_LINK):

                arrIp = arrIp[netifaces.AF_LINK]

def dd_write()
    run_process("cd show_sambapath_dialog.arrPath ")
    run_process("dd if=/dev/zero of=./test.dd bs=10M count=2")

def show_option_dialog():
    """
    打开操作选择
    :return:
    """
    arrOpt = [
        ("HostName", "Hostname Configuration"),
        ("Network", "Network Configuration")
    ]

    strCode, strSel = objDig.menu(Constants.TXT_SELECT_OPTION, choices=arrOpt)

    if strCode == Dialog.OK:
        if strSel == "Network":
            dd_write()
        else:
            dd_write()
    else:
        clearQuit()

locale.setlocale(locale.LC_ALL, '')

if os.getuid() != 0:  # 只有Root用户才可以执行
    print(Constants.TXT_ERR_ROOT_REQUIRED)
    sys.exit(1)

objDig =Dialog(dialog='dialog', autowidgetsize=True)
objDig.set_background_title(Constants.TXT_BACKGROUND_TITLE)

show_option_dialog()