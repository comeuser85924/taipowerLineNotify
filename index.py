from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import base64
import requests
import json

def lineNotifyMessage(msg):
    lineNotifyToken = 'Input Your Line Notify Token'
    headers = {
        "Authorization": "Bearer " + lineNotifyToken,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {'message': msg}
    requests.post( "https://notify-api.line.me/api/notify", headers = headers, params = payload)

# 主要用途為取消網頁中的彈出視窗，避免妨礙網路爬蟲的執行。
options = Options()
options.add_argument("--disable-notifications")
 
chrome = webdriver.Chrome('./chromedriver', chrome_options=options)
chrome.get("https://ebpps2.taipower.com.tw/simplebill/simple-query-bill")

# 使用 Js canvas 繪製一個當前的 captcha 
img_base64 =chrome.execute_script("""
  var ele = arguments[0];
  var cnv = document.createElement('canvas');
  cnv.width = ele.width; cnv.height = ele.height;
  cnv.getContext('2d').drawImage(ele, 0, 0, ele.width ,ele.height);
  return cnv.toDataURL('image/jpeg').substring(22);    
  """, chrome.find_element_by_xpath("//*[@id='captcha_id']"))
with open("captcha_login.png", 'wb') as image:
  image.write(base64.b64decode(img_base64))

file = {'file': open('captcha_login.png', 'rb')}

api_key = 'Input Your 2captcha KEY' # 2captcha KEY
payload = {
  'key': api_key,
}

# 代表一般驗證碼(Normal Captcha)提交成功，後面的數字則是驗證碼ID
response = requests.post('http://2captcha.com/in.php', files = file, params = payload) 
print(f'response:{response.text}') # e.g. response:OK|67645583547

if response.ok and response.text.find('OK') > -1:
  captcha_id = response.text.split('|')[1]  # 擷取驗證碼ID
  # 由於2Captcha服務有時無法即時辨識與回應結果，所以實作一個 retry 機制
  for i in range(10):
    # 取得辨識結果
    response = requests.get(
        f'http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}')
    if response.text.find('CAPCHA_NOT_READY') > -1:  # 尚未辨識完成
      time.sleep(3)
    elif response.text.find('OK') > -1:
      captcha_text = response.text.split('|')[1]  # 擷取辨識結果
      custNo = chrome.find_element_by_xpath("//*[@id='custNo']") # 取得電號欄位
      captchaAnswer = chrome.find_element_by_xpath("//*[@id='answer']") # 取得 captcha 欄位
      searchBtn = chrome.find_element_by_xpath("//*[@id='appmain_simplequery']/div[3]/input[1]") # 取得 查詢 按鈕

      custNo.send_keys('Input Your Bill CustNo') # 輸入電號 - 電費帳單上的電號
      captchaAnswer.send_keys(captcha_text) # 輸入辨識完的 captcha
      searchBtn.click()
      if chrome.current_url == 'https://ebpps2.taipower.com.tw/simplebill/post-simple-query-bill': # 檢查網址
        showBillQueryDetail = chrome.find_element_by_xpath("//*[@id='showBillQueryDetail']") # 取得 查看帳單明細 按鈕
        showBillQueryDetail.click()
        billName = chrome.find_element_by_xpath("//*[@id='billName']") # 取得 用電戶名
        billName.send_keys('Input Your Bill Name') # 輸入 用電戶名 - 電費帳單上的戶名
        searchBtn2 = chrome.find_element_by_xpath("//*[@id='appmain_simplequery2']/div[2]/input") # 取得 查詢明細 按鈕
        searchBtn2.click()
        billMonth = chrome.find_element_by_xpath("/html/body/div[2]/div/div/section/div[2]/div[1]/table/tbody/tr[1]/td")  #本期帳單月份
        billIntervalTime = chrome.find_element_by_xpath("/html/body/div[2]/div/div/section/div[2]/div[1]/table/tbody/tr[2]/td") #本期計費期間
        billStatus = chrome.find_element_by_xpath("/html/body/div[2]/div/div/section/div[2]/div[2]/table/tbody/tr[2]/td") #本期繳費狀態
        billDegree = chrome.find_element_by_xpath('/html/body/div[2]/div/div/section/div[2]/div[1]/table/tbody/tr[6]/td') #本期用電度數
        billMoney =  chrome.find_element_by_xpath("/html/body/div[2]/div/div/section/div[2]/div[2]/table/tbody/tr[5]/td/b") #本期電費金額
        billDeadline =  chrome.find_element_by_xpath("/html/body/div[2]/div/div/section/div[2]/div[2]/table/tbody/tr[1]/td")  #本期繳費期限
        billNextDeadlineStart =  chrome.find_element_by_xpath("/html/body/div[2]/div/div/section/div[2]/div[1]/table/tbody/tr[4]/td") #下一期計費期間 起始月
        billNextDeadlineEnd =  chrome.find_element_by_xpath("/html/body/div[2]/div/div/section/div[2]/div[1]/table/tbody/tr[5]/td") #下一期計費期間 結算日
       
        lineNotifyMessage('\n' + 
        '本期帳單月份:' + billMonth.text + '\n'
        '本期計費期間:' + billIntervalTime.text + '\n'
        '本期繳費狀態:' + billStatus.text + '\n'
        '本期用電度數:' + billDegree.text + '\n'
        '本期電費金額:' + billMoney.text + '\n'
        '本期繳費期限:' + billDeadline.text + '\n'
        '---------------' + '\n'
        '下一期計費期間:' + billNextDeadlineStart.text + ' 至 ' + billNextDeadlineEnd.text
        )
      break
    else:
      lineNotifyMessage('取得驗證碼發生錯誤!')
      print('取得驗證碼發生錯誤!')
else:
  lineNotifyMessage('提交驗證碼發生錯誤!')
  print('提交驗證碼發生錯誤!')