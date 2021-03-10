'''
1.分析输入的指令，调用对应的BaiduPan函数
（1）分割输入的字符串，将字符串分割为 主命令，跟随字符串，参数，三部分
（2）根据主命令不同，将参数和字符串作为函数的形参传入函数
'''
help_cmd_list = {
    'ls':'Get all files in the folder.',
    'cd':'Adjust current folder.',
    'md':'Create new folder.',
    'upload':'Upload files, currently the largest but this limit size is 4GB for ordinary members.',
    'download':'Download the files in the specified directory and store them in the specified local directory.',
    'del':'Delete the specified asking price or folder.',
    'search':'Search for the folder information with keywords in the network disk.',
    'get_data':'Get specified file information.',
    'get_capacity':'Get network disk capacity information.',
    'copy':'Move files from the network disk to the specified directory without deleting the source files.',
    'move':'Move the network disk file to the specified directory, and delete the source file.',
    'rename':'Rename the specified file.',
    'help':'This project was created by Tian Ruhao, please contact 1927978923 for QQ.'
}
import webbrowser
import json
import requests
import urllib
import time
import sys
import os
import datetime
import hashlib
import BaiduPan

def local_file_md5(path):
    with open(path, 'rb') as fp:
        data = fp.read()
    return hashlib.md5(data).hexdigest()
def local_file_size(path):
    return os.stat(path).st_size#单位是B,可以直接用

class Terminal:
    def __init__(self):
        self.Now_path = "/"
        self.cmd_list=['ls','cd','md','upload','download','del','search','get_data','get_capacity','copy','move','rename','help']
        self.base_path = "/apps/mypan_py/"#上传文件必须要上传到这个文件夹下
        self.pan = BaiduPan.BaiduPan()
        self.pan.login()
    def input_Cmd(self, temp_cmd):
        self.temp_cmd = temp_cmd
        self.cmd = ""
        self.Format_Cmd()
    def Format_Cmd(self):
        # 将//转变为/，以及补充发现的错误
        if len(self.temp_cmd) == 1:
            print('command length error!')
        temp = self.temp_cmd
        for i in range(len(temp)-1):
            if temp[i] =='/' and temp[i+1] == '/':
                continue
            self.cmd = self.cmd + temp[i]
        # 得到了最终的字符串self.cmd
        self.cmd = self.cmd + temp[i+1]
        self.Split_Cmd()#对格式化后的命令进行分割分析
    def Split_Cmd(self):
        s_l = self.cmd.split(" ")#分割字符串
        c_len = len(s_l)
        main_fun = s_l[0]
        if main_fun == 'ls':
            if c_len == 1:
                self.ls(self.Now_path)
                return
            else:
                print('command length error !')
        elif main_fun == 'get_capacity':
            self.get_capacity()
            return 
        elif main_fun == 'md':
            self.md(s_l[1])
            return 
        elif main_fun == 'del':
            self.mydel(s_l[1])
            return
        elif main_fun == 'search':
            if c_len == 2:
                self.search(s_l[1], '/')
                return
            elif c_len == 4:
                self.search(s_l[1], s_l[3])
                return
        elif main_fun == 'getdata':
            file_list = self.pan.search(s_l[1], self.Now_path)
            if len(file_list) != 0:
                self.getdata(file_list[0]['fs_id'])
            else:
                print("The specified file does not exist !")
            return
        elif main_fun == 'upload':
            self.upload(s_l[1], s_l[3])
            return
        elif main_fun == 'download':
            self.download(s_l[1], s_l[3])
            return
        elif main_fun == 'cd':
            self.cd(s_l[1])
            return
        elif main_fun == 'exit':
            sys.exit(0)
        elif main_fun =='help':
            if c_len == 1:
                self.help()
                return
            elif c_len == 2:
                self.help(s_l[1])
                return
        else:
            print("Illegal command, please enter 'help' to view legal commands!")
    def help(self, param = "all"):
        if param == "all":
            print(self.cmd_list)
        else:
            if param in help_cmd_list:
                print(help_cmd_list[param])
            else:
                print('No such command')
    def cd(self, path):
        if path=="..":
            if self.Now_path == '/':
                return
            else:
                t_1 = self.Now_path.split('/')
                temp = '/'.join(t_1[0:-2])
                temp = '/' if temp=='' else temp
                self.Now_path = temp
                return
        else:
            self.Now_path = self.Now_path + path + '/'
    def upload(self, local_path, topath):
        size = local_file_size(local_path)
        md5 = local_file_md5(local_path)
        if self.pan.upload(local_path,[md5],self.base_path + topath, size):
            print("Uploaded successfully, the file location is "+ self.base_path + topath)
        else:
            print("Upload Failed !")
    def download(self, path, local_path):
        if type(path) == list:
            if self.pan.download(path, local_path):
                print("The file is downloaded successfully, and the file is saved in " + local_path)
            else:
                print("File download failed ! ")
        elif type(path) == str:
            if self.pan.download([path], local_path):
                print("The file is downloaded successfully, and the file is saved in " + local_path)
            else:
                print("File download failed ! ")
        else:
            print("Input parameter format error ! ")
    def mydel(self, path):
        if self.pan.mydel(path):
            print("File deleted successfully ! ")
        else:
            print("File deletion failed !")
    def search(self, key, path):
        data = self.pan.search(key, path)
        self.print_data(data)
    def getdata(self, filename):
        if type(filename) == list:
            data = self.pan.get_data(filename)
            self.print_data(data)
        elif type(filename) == str or type(filename) == int:
            data = self.pan.get_data([filename])
            self.print_data(data)
        else:
            print("Input parameter format error ! ")
    def get_capacity(self):
        self.pan.get_capacity()
    def copy(self, oldpath, newpath):
        if self.pan.copy(oldpath, newpath):
            print("File copied successfully !")
        else:
            print("File copy failed !")
    def move(self, oldpath, newpath):
        if self.pan.move(oldpath, newpath):
            print("The file moved successfully, the file location is " + newpath)
        else:
            print("File move failed !")
    def rename(self, oldname, newname):
        if self.pan.rename(oldname, newname):
            print("File renamed successfully !")
        else:
            print("File renaming failed !")
    def md(self, path):
        if self.pan.md(self.base_path + path):
            print("The file was created successfully !")
        else:
            print("The file was created failed !")
    def ls(self, dir = "/"):
        data = self.pan.ls(dir)
        self.print_data(data)
    def print_data(self, data):
        for dic in data:
            print(json.dumps(dic, indent=4,ensure_ascii=False, sort_keys=False,separators=(',', ':')))
    def run(self):
        while True:
            print("Pan " + self.Now_path + "> ", end='')
            self.input_Cmd(input())
if __name__ == '__main__':
    t = Terminal()
    t.run()