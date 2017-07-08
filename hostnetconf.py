# !/usr/bin/env python
# coding=utf-8
# Author:TonyZhang
# onlyzq@outlook.com
# Copyright 2017, ZbStor

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

#print_function在该程序没有用到
#locale本程序设置编码
#os sys系统环境相关
#re 正则
#subprocess调用shell
#strip删除字符串头尾指定的字符
#netifaces调用网卡信息
#socket提供网络服务

# 在原ISO的基础上需要安装:dialog python-netifaces python2-dialog

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


def clearQuit():
    """
    清除并返回
    :return:
    """
    os.system('clear')
    sys.exit(0)


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


def network_restart(strSelIface):
    """
    重启指定网卡
    :param strSelIface:网络名称
    :return: 执行结果 
    """
    # strCmd = "ifdown " + strSelIface + " ; ifup " + strSelIface
    # 涉及路由，所以要重启服务
    strCmd = "systemctl restart network"
    ditRun = run_process(strCmd)

    try:
        # 由于上面重启了网络服务，Web配置的静态路由失效，所以这里。。。
        strFn = "/zbstormag/init.d/P.04.Routes"

        if os.path.isfile(strFn):
            run_process("sh " + strFn)

    except Exception:
        pass
    return ditRun


def res_other_nic_defroute(strNic):
    """
       将除了指定网卡以外的其它网卡defroute变为no
    """
    arrNet = netifaces.interfaces()
    #输出网卡列表['lo', 'eno1', 'eno2', 'enp2s0f0', 'eno3', 'eno4', 'enp2s0f1']

    for strNet in arrNet:
        if strNet.lower() != "lo" and strNic.lower() != strNet.lower():
            strFn = "/etc/sysconfig/network-scripts/ifcfg-" + strNet
            if os.path.isfile(strFn):
                run_process("sed -i '/DEFROUTE/d'  " + strFn)
                run_process("echo 'DEFROUTE=no' >> " + strFn)


def write_network_conf(arrIf, strSelIface, strMac):
    """
    写网络配置文件
    :param arrIf: 配置内容  [ip,mask,gw]
    :param strMac:选择的网卡MAC地址
    :param strSelIface:选择的网卡名称
    :return:
    """
    strFn = "/etc/sysconfig/network-scripts/ifcfg-" + strSelIface

    if os.path.isfile(strFn):  # 有可能网卡配置文件不存在，如果strFN是一个文件返回True
        run_process("sed -i '/BOOTPROTO/d' " + strFn)
        run_process("sed -i '/ONBOOT/d' " + strFn)
        run_process("sed -i '/IPADDR/d'  " + strFn)
        run_process("sed -i '/NETMASK/d'  " + strFn)
        run_process("sed -i '/GATEWAY/d'  " + strFn)
        run_process("sed -i '/IPV6INIT/d'  " + strFn)
        run_process("sed -i '/DEFROUTE/d'  " + strFn)

        run_process("sed -i '/IPV4_FAILURE_FATAL/d'  " + strFn)
        run_process("sed -i '/IPV6INIT/d'  " + strFn)
        run_process("sed -i '/IPV6_AUTOCONF/d'  " + strFn)
        run_process("sed -i '/IPV6_DEFROUTE/d'  " + strFn)
        run_process("sed -i '/IPV6_PEERDNS/d'  " + strFn)
        run_process("sed -i '/IPV6_PEERROUTES/d'  " + strFn)
        run_process("sed -i '/IPV6_FAILURE_FATAL/d'  " + strFn)
    else:
        run_process("echo 'TYPE=Ethernet' > " + strFn)
        run_process("echo 'PEERDNS=yes' >> " + strFn)
        run_process("echo 'PEERROUTES=yes' >> " + strFn)
        run_process("echo 'NAME=" + strSelIface + "' >> " + strFn)
        run_process("echo 'DEVICE=" + strSelIface + "' >> " + strFn)
        run_process("echo 'HWADDR=" + strMac + "' >> " + strFn)

    # 使用该管理工具配置时，没有网关就会写入no，
    #   如果通过管理平台其它的网卡时,CMON会写入DEFROUTE=yes，这样可以保证外网是默认路由（但是目前解决不了，在管理平台配置多个的问题后面要改，20170411）
    #   如果通过该工具配置时，配置网关就会写入yes，这样可以先配置内网不指定网关，再配置外网指定网关
    if strip(arrIf[2]) == "":
        run_process("echo 'DEFROUTE=no' >> " + strFn)
    else:
        run_process("echo 'DEFROUTE=yes' >> " + strFn)

    run_process("echo 'IPV4_FAILURE_FATAL=no' >> " + strFn)
    run_process("echo 'IPV6INIT=no' >> " + strFn)
    run_process("echo 'IPV6_AUTOCONF=no' >> " + strFn)
    run_process("echo 'IPV6_DEFROUTE=no' >> " + strFn)
    run_process("echo 'IPV6_PEERDNS=no' >> " + strFn)
    run_process("echo 'IPV6_PEERROUTES=no' >> " + strFn)
    run_process("echo 'IPV6_FAILURE_FATAL=no' >> " + strFn)

    if strip(arrIf[0]) != "":  # IP为空表示清空配置
        if strip(arrIf[2]) != "":  # 可以不输入GW，所以要判断下
            run_process("sed -i '1i GATEWAY=" + arrIf[2] + "' " + strFn)
            res_other_nic_defroute(strSelIface)

        run_process("sed -i '1i NETMASK=" + arrIf[1] + "' " + strFn)
        run_process("sed -i '1i IPADDR=" + arrIf[0] + "' " + strFn)
        run_process("sed -i '1i BOOTPROTO=static' " + strFn)
        run_process("sed -i '1i ONBOOT=yes' " + strFn)
    else:
        run_process("sed -i '1i ONBOOT=no' " + strFn)

    results = network_restart(strSelIface)

    strFinMsg = Constants.TXT_NETWORK_CFG_ERROR
    if results['retcode'] == 0:
        strFinMsg = Constants.TXT_NETWORK_CFG_SUCCESS

    strCode = objDig.msgbox(strFinMsg)
    show_option_dialog()


def chkIp(strTest):
    """
    验证IP地址格式
    :param strTest:
    :return: true是
    """
    p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    isOk = False
    if p.match(strTest):
        isOk = True
    return isOk


def show_network_dialog():
    """
    打开网络配置窗口
    :return:
    low()方法是把字符串转换为小写
    append()追加
    """
    arrChoices = []
    arrNet = netifaces.interfaces()
    for strNet in arrNet:
        if strNet.lower() != "lo":
            arrIp = netifaces.ifaddresses(strNet)

            if arrIp.has_key(netifaces.AF_LINK):

                arrIp = arrIp[netifaces.AF_LINK]
                if len(arrIp) > 0:
                    arrChoices.append(
                        (strNet, arrIp[0]["addr"])
                    )

    strCode, strSelNet = objDig.menu(Constants.TXT_SELECT_INTERFACE, choices=arrChoices)

    if strCode == Dialog.OK:
        def getIp():
            """
            得到IP及网关
            :return: 
            """
            strI = ""
            strN = ""
            try:
                arrIp = netifaces.ifaddresses(strSelNet)

                if len(arrIp) > 0:
                    if arrIp.has_key(netifaces.AF_INET):
                        arrTmp = arrIp[netifaces.AF_INET]

                        if len(arrTmp) > 0:
                            arrTmp = arrTmp[0]
                            strI = arrTmp["addr"]
                            strN = arrTmp["netmask"]

            except Exception:
                pass
            return strI, strN

        def getGw():
            """
            得到网关地址
            :return: 
            """
            strW = ""
            try:
                arrIp = netifaces.gateways()

                if arrIp.has_key(netifaces.AF_INET):

                    arrIp = arrIp[netifaces.AF_INET]

                    for strG, strN, isDef in arrIp:
                        if strN == strSelNet:
                            strW = strG
                            break

            except Exception:
                pass
            return strW

        def showMsg_Retrun(strMsg):
            """
            验证错误时提示
            :param strMsg:  提示消息
            :return: true是
            """
            objDig.msgbox(strMsg)
            show_option_dialog()

        strIp, strNetMask = getIp()
        strGw = getGw()

        while True:
            try:
                strCode, arrInput = objDig.form(
                    Constants.TXT_CONFIG_STATIC_TITLE + strSelNet,
                    [
                        (Constants.TXT_IP, 1, 1, strIp, 1, 20, 15, 15),
                        (Constants.TXT_NETMASK, 2, 1, strNetMask, 2, 20, 15, 15),
                        (Constants.TXT_GATEWAY, 3, 1, strGw, 3, 20, 15, 15)
                    ],
                    width=70
                )

                if strCode == Dialog.OK:

                    def doSet():
                        isTest = False

                        if strip(arrInput[0]) == "":
                            isTest = True
                        else:
                            if chkIp(arrInput[0]):
                                if chkIp(arrInput[1]):
                                    if strip(arrInput[2]) == "":  # 可以不填写网关
                                        isTest = True
                                    else:

                                        if chkIp(arrInput[2]):
                                            isTest = True
                                        else:
                                            showMsg_Retrun(Constants.TXT_GATEWAY + " " + Constants.TXT_IP_ERROR)
                                else:
                                    showMsg_Retrun(Constants.TXT_NETMASK + " " + Constants.TXT_IP_ERROR)
                            else:
                                showMsg_Retrun(Constants.TXT_IP + " " + Constants.TXT_IP_ERROR)

                        if isTest:
                            strCode = objDig.infobox(Constants.TXT_MESSAGE_NETWORK)
                            strSm = ""
                            # 得到所选网卡的MAC地址
                            for strName, strMac in arrChoices:
                                if strName == strSelNet:
                                    strSm = strMac
                                    break

                            write_network_conf(arrInput, strSelNet, strSm)

                    if strip(arrInput[0]) == "":
                        code = objDig.yesno(
                            Constants.TXT_CONF_NULLIP,
                            height="5",
                            width=65,
                            yes_label="Yes",
                            no_label="No"
                        )

                        if code == Dialog.CANCEL or code == Dialog.ESC:
                            show_option_dialog()
                        else:
                            doSet()

                    else:
                        doSet()
                else:
                    show_option_dialog()
            except Exception, e:
                strCode = objDig.msgbox(text=Constants.TXT_MESSAGE_ERROR % e, colors=True)
    else:
        show_option_dialog()


def show_hostname_dialog():
    """
    打开主机名配置窗口
    :return:
    """
    strHn = socket.gethostname()

    strCode, arrInput = objDig.form(
        Constants.TXT_CONFIG_STATIC_TITLE,
        [
            (u'Hostname', 1, 1, strHn, 1, 20, 50, 50)
        ],
        width=70
    )

    if strCode == Dialog.OK:
        strCode = objDig.infobox(Constants.TXT_MESSAGE_HOSTNAME)
        strMsg = Constants.TXT_HOSTNAME_CFG_ERROR

        # 先配置主机名，成功后才修改配置文件
        results = run_process("hostname " + arrInput[0])
        if results['retcode'] == 0:
            strMsg = Constants.TXT_HOSTNAME_CFG_SUCCESS

            run_process("sed -i '/HOSTNAME/d' /etc/sysconfig/network ")
            run_process("sed -i '/hostname/d' /etc/sysconfig/network ")
            run_process("echo 'HOSTNAME=" + arrInput[0] + "' >> /etc/sysconfig/network ")

            run_process("echo '" + arrInput[0] + "' > /etc/hostname ")

        strCode = objDig.msgbox(strMsg)

        show_option_dialog()
    else:
        show_option_dialog()


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
            show_network_dialog()
        else:
            show_hostname_dialog()
    else:
        clearQuit()


# locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
locale.setlocale(locale.LC_ALL, '')

if os.getuid() != 0:  # 只有Root用户才可以执行
    print(Constants.TXT_ERR_ROOT_REQUIRED)
    sys.exit(1)

objDig =Dialog(dialog='dialog', autowidgetsize=True)
objDig.set_background_title(Constants.TXT_BACKGROUND_TITLE)

show_option_dialog()
