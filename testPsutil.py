# -*- coding:utf-8 -*-
'''
Created on 2016年5月10日

@author: liudong
'''
from __future__ import division
from __future__ import unicode_literals, print_function
import platform
import psutil


def get_mem():
    phymem = psutil.virtual_memory()
    mem_used = int(phymem.used/1024/1024/1024)
    mem_total = int(phymem.total/1024/1024/1024)
    mem_percent = "%5s%%"%(phymem.percent)
    swap = psutil.swap_memory()
    swap_free = swap.free/1024/1024/1024
    swap_total = swap.total/1024/1024/1024
    return mem_total,mem_used,mem_percent,swap_total,swap_free

def get_disk():
    for i in psutil.disk_partitions():
        disk_usage = psutil.disk_usage(i[1])
        return disk_usage[0]/1024/1024/1024,disk_usage[1]/1024/1024/1024,disk_usage[2]/1024/1024/1024
    
def get_cpustatus(interval=1):
    return (" CPU: " + str(psutil.cpu_percent(interval)) + "%")

def get_version():
    version = platform.platform()
    return version
    

def show_SysInfo():

    mem_total,mem_used,mem_percent,swap_free,swap_total = get_mem()
    total,used,free = get_disk()
    print('\033[1;31;40m-------------------------服务器内存使用情况-----------------------------------\033[0m\n总内存：{}G \n剩余内存：{}G \n内存使用百分比：{} \n交换分区总内存：{}G \n剩余内存：{}G'.format(mem_total,mem_used,mem_percent,swap_free,swap_total))
    print('\033[1;31;40m-------------------------服务器磁盘使用情况-----------------------------------\033[0m\n磁盘总空间:{}G \n已使用空间:{}G \n剩余空间:{}G'.format(total,used,free))
    print('\033[1;31;40m-------------------------服务器CPU使用情况-----------------------------------\033[0m\n{}'.format(get_cpustatus()))
    print('\033[1;31;40m-------------------------服务器版本信息-----------------------------------\033[0m\n{}'.format(get_version()))
if __name__ == '__main__':
    show_SysInfo()
