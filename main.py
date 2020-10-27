import time,json,requests,random,datetime,os,sys
from campus import CampusCard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=chrome_options)

def main():
    #sectets字段录入
    text, sckey, success, failure, result, phone, password = [], [], [], [], [], [], []
    #多人循环录入
    while True:  
        try:
            users = input()
            info = users.split(',')
            phone.append(info[0])
            password.append(info[1])
            text.append(info[2])
            sckey.append(info[3])
        except:
            break

    templateid = "clockSign2"
    RuleId = 147

    #提交打卡
    for index,value in enumerate(phone):
        print("开始获取用户%sDeptId"%(value[-4:]))
        count = 0
        while (count < 3):
            try:
                campus = CampusCard(phone[index], password[index])
                loginJson = campus.get_main_info()
                token = campus.user_info["sessionId"]
                stuNum = loginJson["outid"]
                userName = loginJson["name"]  
                driver.get('https://reportedh5.17wanxiao.com/collegeHealthPunch/index.html?token=%s#/punch?punchId=180'%token)
                #time.sleep(10)
                response = check_in(text[index],stuNum,userName,RuleId,templateid,token)
                if  response.json()["msg"] == '成功'and count == 0:
                    strTime = GetNowTime()
                    success.append(value[-4:])
                    print(response.text)
                    msg = value[-4:]+"打卡成功-" + strTime
                    result=response
                    break
                elif response.json()["msg"] == '业务异常'and count == 0:
                    strTime = GetNowTime()
                    failure.append(value[-4:])
                    print(response.text)
                    msg = value[-4:]+"打卡失败-" + strTime
                    result=response
                    break
                elif response.json()["msg"] == '成功':
                    strTime = GetNowTime()
                    success.append(value[-4:])
                    print(response.text)
                    msg = value[-4:]+"打卡成功-" + strTime
                    break
                else:
                    strTime = GetNowTime()
                    failure.append(value[-6:])
                    print(response.text)
                    msg = value[-6:] + "打卡异常-" + strTime
                    count = count + 1
                    print('%s打卡失败，开始第%d次重试...'%(value[-6:],count))
                    time.sleep(15)
        
            except:
                msg = "出现错误"
                failure.append(value[-4:])
                break
        print(msg)
        print("-----------------------")
    fail = sorted(set(failure),key=failure.index)
    strTime = GetNowTime()
    title = "成功: %s 人,失败: %s 人"%(len(success),len(fail))
    try:
        if  len(sckey[0])>2:
            print('主用户开始微信推送...')
            WechatPush(title,sckey[0],success,fail,result)
    except:
        print("微信推送出错！")
#时间函数
def GetNowTime():
    cstTime = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
    strTime = cstTime.strftime("%H:%M:%S")
    return strTime

#班级获取函数
def GetDeptId(text):
    try:
        TextStr = text.split('-', 3)
        ClassName = TextStr[2] 
    # 获取deptId
    except:
        print("获取失败，请检查格式")
    try:
        for Class in AllClass:
            if (Class['name'] == ClassName):
                deptId = Class['deptId']
        if deptId:
            print('获取deptId成功!')
    except:
        print("获取deptId失败！")
        exit(1)
    return deptId

#打卡参数配置函数
def GetUserJson(deptId,text,stuNum,userName,RuleId,templateid,token):
    #随机温度(36.2~36.8)
    a=random.uniform(36.2,36.8)
    temperature = round(a, 1)
    return  {
        "businessType": "epmpics",
        "method": "submitUpInfoSchool",
        "jsonData": {
        "deptStr": {
            "deptid": deptId,
            "text": text
        },
        "areaStr": {"streetNumber":"","street":"长椿路辅路","district":"中原区","city":"郑州市","province":"河南省","town":"","pois":"河南工业大学(莲花街校区)","lng":113.55064699999795 + random.random()/1000,"lat":34.83870696238093 + random.random()/1000,"address":"中原区长椿路辅路河南工业大学(莲花街校区)","text":"河南省-郑州市","code":""},
        "reportdate": round(time.time()*1000),
        "customerid": "43",
        "deptid": deptId,
        "source": "app",
        "templateid": templateid,
        "stuNo": stuNum,
        "username": userName,
        "userid": round(time.time()),
        "updatainfo": [  
            {
                "propertyname": "temperature",
                "value": temperature
            },
            {
                "propertyname": "symptom",
                "value": "无症状"
            }
        ],
        "customerAppTypeRuleId": RuleId,
        "clockState": 0,
        "token": token
        },
        "token": token
    }    

#打卡提交函数
def check_in(text,stuNum,userName,RuleId,templateid,token):
    deptId = GetDeptId(text)
    sign_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
    jsons=GetUserJson(deptId,text,stuNum,userName,RuleId,templateid,token)
    #提交打卡
    print(jsons)
    response = requests.post(sign_url, json=jsons,)
    return response

#json读取函数
def GetFromJSON(filename): 
    flag = False
    idStr={} 
    try:
        j_file=open(filename,'r', encoding='utf8')
        idStr=json.load(j_file)
        flag=True
    except:
        print('从%s读取JSON数据出错！'%filename)
    finally:
        if flag:
            j_file.close()

        
    return idStr

#微信通知
def WechatPush(title,sckey,success,fail,result):    
    strTime = GetNowTime()
    page = json.dumps(result.json(), sort_keys=True, indent=4, separators=(',', ': '),ensure_ascii=False)
    content = f"""
`{strTime}` 
#### 打卡成功用户：
`{success}` 
#### 打卡失败用户:
`{fail}`
#### 主用户打卡信息:
```
{page}
```

        """
    data = {
        'appToken':"AT_pqcH9PILCSE0qotKGfv7cTIr2MgtrhrI",
        'content':content,
        'summary':title,
        'contentType':3,
        'uids':[
            "UID_8iMbPWkr8wJYBYSTSvxvSJlY6HY3"
        ]
    }
    try:
        headers = {'Content-Type': 'application/json'}
        req = requests.post(sckey, headers=headers, data = json.dumps(data))
#         print(req.json())
        if req.json()["msg"] == '处理成功':
            print("Server酱推送服务成功")
        else:
            print("Server酱推送服务失败")
    except:
        print("微信推送参数错误")
if __name__ == '__main__':
    filename = r'text.json'
    AllClass = GetFromJSON(filename)['data']['classAll']
    main()
