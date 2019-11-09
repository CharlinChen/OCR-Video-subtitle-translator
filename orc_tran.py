# -*- coding: utf-8 -*-
import sys
import uuid
import requests
import base64
import hashlib
import json
from imp import reload
import cv2
import os
import time
import numpy as np

reload(sys)

YOUDAO_OCR_URL = 'https://openapi.youdao.com/ocrapi'
YOUDAO_FY_URL = 'https://openapi.youdao.com/api'
APP_KEY = '请自行去有道智云申请APPKEY'
APP_SECRET = '同上'
LANGUAGE = 'ja' #设置识别语言en：英语 ja：日语

def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def do_ocr_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(YOUDAO_OCR_URL, data=data, headers=headers)

def do_fy_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(YOUDAO_FY_URL, data=data, headers=headers)


def ocr_connect(filename):
    f = open(filename, 'rb')  # 二进制方式打开图文件
    q = base64.b64encode(f.read()).decode('utf-8')  # 读取文件内容，转换为base64编码
    f.close()

    data = {}
    data['detectType'] = '10012'
    data['imageType'] = '1'
    data['langType'] = LANGUAGE
    data['img'] = q
    data['docType'] = 'json'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['salt'] = salt
    data['sign'] = sign

    response = do_ocr_request(data)
    R = json.loads(response.text)
    stri = ''
    if R['errorCode']=="0":
        for lines in R['Result']['regions']:
            for word in lines['lines']:
                stri = stri + (word['text'])
        if stri=="":
            print("Output Empty!")
            return "Error"
        else:
            print(stri)
            return stri
    else:
        print("OCR Error:"+R['errorCode'])
        return "Error"

def fy_connect(word):
    q = word

    data = {}
    data['from'] = LANGUAGE
    data['to'] = 'zh-CHS'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign

    response = do_fy_request(data)
    contentType = response.headers['Content-Type']
    if contentType == "audio/mp3":
        millis = int(round(time.time() * 1000))
        filePath = "/audio/" + str(millis) + ".mp3"
        fo = open(filePath, 'wb')
        fo.write(response.content)
        fo.close()
    else:
        R = json.loads(response.text)
        if R['errorCode']=="0":
            print(R['translation'][0])
            return R['translation'][0]
        else:
            print("Translation Error:"+R['errorCode'])
            return "Error"


if __name__ == '__main__':
    f = open('zm.xml', 'a', encoding='utf-8')
    Str_start = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\" ?>\n<tt xmlns=\"http://www.w3.org/ns/ttml\" xmlns:ttp=\"http://www.w3.org/ns/ttml#parameter\" ttp:dropMode=\"nonDrop\" ttp:frameRate=\"30\" ttp:timeBase=\"smpte\" xmlns:ttm=\"http://www.w3.org/ns/ttml#metadata\" xmlns:tts=\"http://www.w3.org/ns/ttml#styling\">\n\n  <head>\n    <metadata/>\n    <styling>\n      <style tts:color=\"white\" tts:fontFamily=\"monospace\" tts:fontWeight=\"normal\" tts:textAlign=\"left\" xml:id=\"basic\"/>\n    </styling>\n    <layout>\n      <region tts:backgroundColor=\"transparent\" xml:id=\"pop1\"/>\n      <region tts:backgroundColor=\"transparent\" xml:id=\"paint\"/>\n      <region tts:backgroundColor=\"transparent\" xml:id=\"rollup2\"/>\n      <region tts:backgroundColor=\"transparent\" xml:id=\"rollup3\"/>\n      <region tts:backgroundColor=\"transparent\" xml:id=\"rollup4\"/>\n    </layout>\n  </head>\n\n  <body>\n    <div>\n      <p begin=\""
    Str_time1 = "\" end=\""
    Str_time2 = "\" region=\"pop1\" style=\"basic\" tts:origin=\"10% 85.092592592592595%\">\n        <style tts:textAlign=\"center\"/>\n        <span>"
    Str_word = "\n          <style tts:backgroundColor=\"#E8ECEBFF\" tts:color=\"#383B3BFF\" tts:fontFamily=\"华康华综体W5P\" tts:fontSize=\"35px\" tts:textOutline=\"#E8ECEBFF 4px\"/>\n        </span>\n      </p>\n      <p begin=\""
    Str_end = "<style tts:backgroundColor=\"#E8ECEBFF\" tts:color=\"#383B3BFF\" tts:fontFamily=\"华康华综体W5P\" tts:fontSize=\"35px\" tts:textOutline=\"#E8ECEBFF 4px\"/>\n        </span>\n      </p>\n    </div>\n  </body>\n\n</tt>\n"
    f.write(Str_start)
    cap = cv2.VideoCapture('test.mp4')
    if not cap.isOpened():  # 判断文件是否存在
        print("could not open")
        sys.exit()
    length = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # 获得该视频的帧数
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = int(cap.get(cv2.CAP_PROP_FPS))  # 获得该视频的帧率
    print(fps)
    print(length)
    size = (w, h)
    print(size)
    fn = 0
    hour=0
    min=0
    sec=0
    ms=0
    tim=0
    last_inum=0
    write_flag=10
    Timer=True
    last_str_time=""
    have_end=True
    last_img = cv2.imread('output.jpg')
    while (fn<length):
        # 逐帧捕捉
        fn=fn+1
        tim=fn/fps*60
        hour=int(tim/(60*60*60))
        tim=tim-hour*60*60*60
        min=int(tim/(60*60))
        tim=tim-min*60*60
        sec=int(tim/60)
        ms=int(tim-sec*60)
        str_time = "%02d" % hour + ":" + "%02d" % min + ":" + "%02d" % sec + ":" + "%02d" % ms
        ret, frame = cap.read()
        # # 添加文字字幕
        # if ret == True:
        #     cv2.putText(frame, 'hello world', (50, 150), cv2.FONT_HERSHEY_COMPLEX, 5, (0, 255, 0), 12)
        # # show
        # cv2.namedWindow('frame', 0)  # 自适应调整视频大小
        # cv2.imshow('frame', frame)
        cropped = frame[855:1040, 330:1810] #设置识别区域，默认白底黑字（若为黑底白字，请反转）
        im_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)  # 转换成灰度图
        im_at_mean = cv2.adaptiveThreshold(im_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 5,
                                           8)  # 使用自适应阈值进行二值化处理，其他二值化方法可查询API使用
        inum=0
        wh=0
        for pix in np.amin(im_at_mean, axis=0):
             if pix == 0:
                inum=inum+1
             if pix== 255:
                wh=wh+1
        if wh<20:
            print(wh)
            continue
        #print("inum:"+str(inum)," last_inum:"+str(last_inum)+" write_flag:"+str(write_flag))
        if write_flag==10 and inum>last_inum and inum > 4:
            #起始点
            Timer = True

        if Timer==True:
            write_flag=write_flag-1
            if write_flag == 0:
                stime1 = str_time
                print("\n==================\n" + stime1 + "->")
                f.write(stime1 + Str_time1)
                last_inum = inum
                Timer=False
                have_end=False

        if have_end==False and inum<(last_inum-4):
            have_end = True
            #结束点
            stime2 =last_str_time
            print(stime2)
            f.write(stime2 + Str_time2)
            last_inum = inum
            write_flag = 10
            #cv2.imshow('image', last_img)
            #cv2.waitKey(0)
            #srtsrt="XXX"
            cv2.imwrite("output.jpg", last_img)
            stri = ocr_connect("output.jpg")
            if(stri != "Error"):
                srtsrt = fy_connect(stri)
            else:srtsrt = " "
            f.write(srtsrt + Str_word)
        else :last_inum = inum
        last_str_time=str_time
        last_img=im_at_mean
        # if cv2.waitKey(2) & 0xFF == ord('c'):
        #     print(hour, ":", min, ":", sec, ":", ms)
        # if cv2.waitKey(2) & 0xFF == ord('v'):
        #     cv2.imwrite("output.jpg",cropped)
        #
        # if cv2.waitKey(2) & 0xFF == ord('q'):
        #     print(hour,":",min,":",sec,":",ms)
        #     break
    print("All Work Finished!")
    cap.release()
    cv2.destroyAllWindows()
    all_time = "%02d" % hour + ":" + "%02d" % min + ":" + "%02d" % (sec+1) + ":" + "%02d" % ms
    f.write(last_str_time+Str_time1+all_time+Str_time2+"END"+Str_end)
    f.close()
    #stri=ocr_connect("test2.jpg")
    #stri = r"源力照射を受けた414の細胞サンプルの結晶の進行具合は予期と同様。シーケンシング、同様の突然変異を多数観測…"
    #resu=fy_connect(stri)