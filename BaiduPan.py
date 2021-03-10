# coding=utf-8
import webbrowser
import json
import requests
import urllib
import time
import sys
import os
import datetime
import hashlib
API_KEY = 'xx'
SECRET_KEY = 'xx'

def local_file_md5(path):
    with open(path, 'rb') as fp:
        data = fp.read()
    return hashlib.md5(data).hexdigest()
def local_file_size(path):
    return os.stat(path).st_size#单位是B,可以直接用
class BaiduPan:
    def __init__(self):
        self.login_status = False
    def login(self):
        flag = os.path.exists('access_token.txt')
        access_data = []
        today = datetime.date.today() #获得今天的日期
        if not flag:
            self.first_login()
            return
        else:
            with open('access_token.txt') as f:
                for l in f:
                    access_data.append(l)
        if len(access_data)!=2 or access_data[0] <= str(today):
            #长度不等于2 文件损坏或者到日子了，或者过了规定日期了
            self.first_login()
            return
        else:
            self.access_token = access_data[1][0:-1]
        self.get_user_info()
    def first_login(self):
        code_url = f'https://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id={API_KEY}&redirect_uri=oob&scope=basic,netdisk&display=tv&qrcode=1&force_login=1'
        webbrowser.open(code_url)
        code = input('输入授权码（浏览器扫码登录）：')
        access_token_url = f'https://openapi.baidu.com/oauth/2.0/token?grant_type=authorization_code&code={code}&client_id={API_KEY}&client_secret={SECRET_KEY}&redirect_uri=oob'
        #access_token申请的这个可以用一年
        today = datetime.date.today() #获得今天的日期
        yearday = today + datetime.timedelta(days = 360)#360天，在access_token失效前在申请一次
        #print(access_token_url)
        data_json = requests.get(access_token_url).json()
        self.access_token = data_json['access_token']
        with open('access_token.txt','w') as f: # 如果filename不存在会自动创建， 'w'表示写数据，写之前会清空文件中的原有数据！
            f.write(str(yearday) + "\n")
            f.write(self.access_token + "\n")
        self.get_user_info()
    def get_user_info(self):
        url = "https://pan.baidu.com/rest/2.0/xpan/nas?access_token=" + self.access_token + "&method=uinfo"
        headers = {
            'User-Agent': 'pan.baidu.com'
            }
        info = requests.get(url, headers=headers).json()
        self.login_status = info['errno'] == 0
        if self.login_status:
            print('-' * 10, info['baidu_name'], '-' * 10)
            print('欢迎【', info['netdisk_name'], '】')
            vip = '普通用户'
            if info['vip_type'] == 1:
                vip = '普通会员'
            elif info['vip_type'] == 2:
                vip = '超级会员'
            print('等级：', vip)
        else:
            print('登录失败！')
    def upload(self,local_path,path_md5,topath, file_size):
        # 由于第三方上传应用的接口限制，上传的文件会存储在/apps/mypan_py/下，文件上传分为三个阶段：预上传、分片上传、创建文件,先不支持分片上传，即大于4G的文件无法上传
        # path_md5:list类型
        #topath:带文件名
        #base_path = "/apps/mypan_py/"
        #topath = base_path + topath
        md5_list_str  = '['
        for i in path_md5:
            md5_list_str = md5_list_str + '"' + i + '"'+','
        md5_list_str = md5_list_str[0:-1]#把最后一个逗号去掉
        md5_list_str = md5_list_str + ']'
        #---------- 预上传 ----------#
        url_1 = "https://pan.baidu.com/rest/2.0/xpan/file?method=precreate"
        url_1 = url_1 + "&access_token=" + self.access_token
        payload = {
            'path': topath,
            'size': file_size,
            'rtype': '1',
            'isdir': '0',
            'autoinit': '1',
            'block_list': md5_list_str
            }
        res_1 = requests.request("POST", url_1, data = payload)
        data_json = json.loads(res_1.text)
        uploadid = data_json['uploadid']
        # ---------- 分片上传 ---------- #
        url_2 = "https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?method=upload"
        url_2 = url_2 + "&access_token=" + self.access_token + "&type=tmpfile&path=" + topath + "&uploadid=" + uploadid + "&partseq=0"
        files = [
            ('file', open(local_path,'rb'))
            ]
        res_2 = requests.request("POST", url_2, files = files)
        data_json = json.loads(res_2.text)
        # ----------创建文件 ---------- # 
        url_3 = "https://pan.baidu.com/rest/2.0/xpan/file?method=create"
        url_3 = url_3 + "&access_token=" + self.access_token
        payload = {
            'path': topath,
            'size': file_size,
            'rtype': '1',
            'isdir': '0',
            'uploadid': uploadid,
            'block_list': md5_list_str
            }
        res_3 = requests.request("POST", url_3, data = payload)
        data_json = json.loads(res_3.text)
        return not res_3['errno']
    def download(self, filename,topath):
        # topath只要给出路径即可无需添加下载的文件的名称,且路径以‘/’结尾
        # filename为数组
        file_list = self.search(filename)
        download_url = []
        for f in filename:
            file_list = self.search(f)
            download_url.append(pan.get_data([file_list[0]['fs_id']])[0]['dlink'])
        for index in range(len(download_url)):
            path = topath + filename[index]
            url = download_url[index] + "&access_token=" + self.access_token
            #urllib.request.urlretrieve(self.download_url[index] + "&access_token=" + self.access_token, download_path + self.filename[index]) 
            start = time.time()
            size = 0
            response = requests.get(url,stream = True)#stream参数设置成True时，它不会立即开始下载，当你使用iter_content或iter_lines遍历内容或访问内容属性时才开始下载
            chunk_size = 1024#每次块大小为1024
            content_size = int(response.headers['content-length'])#返回的response的headers中获取文件大小信息
            print("文件大小："+str(round(float(content_size/chunk_size/1024),4))+"[MB]")
            with open(path,'wb') as file:
                for data in response.iter_content(chunk_size=chunk_size):#每次只获取一个chunk_size大小
                    file.write(data)#每次只写入data大小
                    size = len(data)+size        #'r'每次重新从开始输出，end = ""是不换行
                    print('\r'+"已经下载："+int(size/content_size*100)*"█"+" 【"+str(round(size/chunk_size/1024,2))+"MB】"+"【"+str(round(float(size/content_size)*100,2))+"%"+"】",end="")
            end = time.time()
            print("下载完成，总耗时:"+str(end-start)+"秒")
    def mydel(self,path):
        url = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager"
        url = url + "&opera=delete&access_token=" + self.access_token
        payload = {
            'async': '1',
            'filelist': '["'+ path +'"]',
            'ondup': 'fail'
            }
        res = requests.request("POST", url, data = payload)
        data_json = json.loads(res.text)
        return not data_json['errno']
    def search(self,key,path='/'):
        # key搜索的关键词，path搜索的路径
        url = "https://pan.baidu.com/rest/2.0/xpan/file?method=search"
        if path == "/":
            get_data = requests.get(url, params={'access_token': self.access_token, 'key':key, 'recursion':1})
        else:
            get_data = requests.get(url, params={'access_token': self.access_token, 'key':key, 'recursion':1, 'dir':path})
        data_json = json.loads(get_data.text)
        file_list_json = data_json['list']
        file_list = []
        for f in file_list_json: 
            # fs_id, 路径， 大小（B）,是否是文件夹
            element = {
                'fs_id':f['fs_id'],
                'path':f['path'],
                'size':f['size'],
                'isdir':f['isdir']
                }
            file_list.append(element)
        return file_list
    def get_data(self,fsid):
        #获取文件信息
        url = "https://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas"
        fsid_str = ""
        fsid = fsid[0:99]
        for i in fsid:
            fsid_str = fsid_str +  str(i) + ","
        fsid_str = fsid_str[0:-1]#最后一个多余的逗号去除
        url = url + '&access_token='+self.access_token+f"&fsids=[{fsid_str}]&dlink=1"
        get_data = requests.get(url)
        data_json = json.loads(get_data.text)
        file_list_json = data_json['list']
        file_list = []
        for f in file_list_json: 
            # fs_id, 路径， 大小（B）,是否是文件夹
            element = {
                'fs_id':f['fs_id'],
                'path':f['path'],
                'size':f['size'],
                'isdir':f['isdir'],
                'dlink':f['dlink']
                }
            file_list.append(element)
        return file_list
    def get_capacity(self):
        url = "https://pan.baidu.com/api/quota"
        get_data = requests.get(url, params={'access_token': self.access_token})
        data_json = json.loads(get_data.text)
        # 总空间大小，已使用大小
        return data_json['total'], data_json['used']
    def copy(self,oldpath,newpath):
        #复制
        url = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager"
        url = url + "&opera=copy&access_token=" + self.access_token
        d_l = newpath.split('/')
        dest = "/".join(d_l[0:-1])
        newname = d_l[-1]
        payload = {
            'async': '1',
            'filelist': '[{"path":"'+ oldpath +'","dest":"'+ dest +'","newname":"'+ newname +'","ondup":"fail"}]',
            'ondup': 'fail'
            }
        res = requests.request("POST", url, data = payload)
        data_json = json.loads(res.text)
        return not data_json['errno'] 
    def move(self, oldpath, newpath):
        #复制
        url = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager"
        url = url + "&opera=move&access_token=" + self.access_token
        d_l = newpath.split('/')
        dest = "/".join(d_l[0:-1])
        newname = d_l[-1]
        payload = {
            'async': '2',
            'filelist': '[{"path":"'+ oldpath +'","dest":"'+ dest +'","newname":"'+ newname +'","ondup":"fail"}]',
            'ondup': 'fail'
            }
        files = [
        ]
        res = requests.request("POST", url, data = payload, files = files)
        data_json = json.loads(res.text)
        return not data_json['errno']       
    def rename(self,oldname,newname):
        #注意调用时oldname包含绝对路径，newname只是新文件名称
        url = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager"
        url = url + "&opera=rename&access_token=" + self.access_token
        d_1 = oldname.split('/')
        dest = '/'.join(d_1[0:-1]) 
        payload = {
            'async': 2,
            #'filelist': ':[{path":"'+ oldname +'","newname":'+ newname +'"}]',
            'filelist':'[{"path":"'+ oldname + '","dest":"' + dest + '","newname":"' + newname + '"}]',
            'ondup': 'fail'
            }
        res = requests.request("POST", url, data = payload)
        data_json = json.loads(res.text)
        return not data_json['errno']
    def md(self, path):
        url = 'https://pan.baidu.com/rest/2.0/xpan/file?method=create'
        url = url + '&access_token=' + self.access_token
        payload = {
            'path': path,
            'size': '0',
            'isdir': '1',
            }
        res_3 = requests.request("POST", url, data = payload)
        return not res_3['errno']
    def ls(self, dir='/'):
        files = 'https://pan.baidu.com/rest/2.0/xpan/file?method=list'
        get_data = requests.get(files, params={'access_token': self.access_token, 'dir': dir, 'order': 'name', 'desc': '0'})
        data_json = json.loads(get_data.text)
        #print(data_json)
        file_data = []
        for f in data_json['list']:
            element = {
                'path':f['path'],
                'fs_id':f['fs_id'],
                'isdir':f['isdir'],
                'size':f['size']
            }
            file_data.append(element)
        return file_data
if __name__ == '__main__':
    base_path = "/apps/mypan_py/"
    pan = BaiduPan()
    pan.login()
    #pan.md(base_path+"trh/真牛逼")#成功
    #pan.rename('/书籍/强化学习.pdf','强化学习——程序改.pdf')#成功
    #pan.get_capacity()#成功
    #pan.move('/书籍/强化学习.pdf','/书籍/数据挖掘/强化学习.pdf')#成功
    #pan.copy('/书籍/数据挖掘/强化学习.pdf', '/书籍/强化学习.pdf')#成功
    #pan.search('强化学习')#成功
    #pan.get_data([213859322459216])#成功，但注意调用格式
    #pan.mydel('/书籍/强化学习.pdf')#成功
    #pan.download(['第11章 方差分析.pdf'],'E:/')#成功，但注意调用格式
    '''
    local_path = "E:/VSC_project/VSC py/captcha.jpg"
    size = local_file_size(local_path)
    md5 = local_file_md5(local_path)
    pan.upload(local_path,[md5],'/书籍/captcha.jpg',size)#成功
    '''
    #pan.ls('/')#成功
    
