#!/usr/bin/env python3
"""Safari + 2captcha rendering"""
import os,json,time,base64,sys;from datetime import datetime;from pathlib import Path
import requests;from selenium import webdriver;from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

def detect_captcha(h):
    return 'recaptcha_v2' if'g-recaptcha'in h else 'hcaptcha'if'h-captcha'in h else None

def solve_2captcha(driver,c,url,job):
    k=os.environ.get('TWOCAPTCHA')
    if not k:print('[CAPTCHA]No key');return False
    print(f'[CAPTCHA]{c}')
    try:
        e=driver.find_element(By.CSS_SELECTOR,'[class*=captcha],.g-recaptcha,.h-captcha')
        s=e.screenshot_as_png
        if not s or len(s)<100:print('[CAPTCHA]Small');return False
        b=base64.b64encode(s).decode()
        print(f'[CAPTCHA]{len(s)}bytes')
        t='RecaptchaV2TaskProxyless'if c=='recaptcha_v2'else'HCaptchaTaskProxyless'
        p={'clientKey':k,'task':{'type':t,'websiteURL':url,'websiteKey':'x','body':b}}
        r=requests.post('https://api.2captcha.com/createTask',json=p,timeout=30).json()
        if'taskId'not in r:print(f'[CAPTCHA]Fail:{r.get("errorCode")}');return False
        tid=r['taskId'];print(f'[CAPTCHA]Task{tid}:polling');st=time.time();pc=0
        while time.time()-st<180:
            time.sleep(3);pc+=1
            cr=requests.post('https://api.2captcha.com/getTaskResult',json={'clientKey':k,'taskId':tid},timeout=30).json()
            if cr.get('status')=='ready':
                sol=cr.get('solution',{});tok=sol.get('gRecaptchaResponse')or sol.get('token')
                if tok:print(f'[CAPTCHA]SOLVED({time.time()-st:.0f}s,{pc}polls)');driver.execute_script(f"var e=document.querySelector('[name=g-recaptcha-response]');if(e)e.value='{tok}';");time.sleep(1);return True
            if cr.get('errorId'):print(f'[CAPTCHA]Error:{cr.get("errorCode")}');return False
        print('[CAPTCHA]Timeout');return False
    except Exception as e:print(f'[CAPTCHA]E:{e}');return False

def main():
    u,j=os.environ.get('URL'),os.environ.get('JOB_ID')
    if not u or not j:print('[RENDER]ERROR:URL+JOB_ID');sys.exit(1)
    print(f'[RENDER]URL:{u}\n[RENDER]JobID:{j}\n[RENDER]Browser:Safari')
    d=None
    try:
        d=webdriver.Safari();d.set_page_load_timeout(45)
    except:
        try:d=webdriver.Safari();d.set_page_load_timeout(30)
        except:print('[RENDER]FATAL');sys.exit(1)
    try:
        d.get('about:blank');d.execute_script("if(!Promise.prototype.finally)Promise.prototype.finally=function(f){return this.then(v=>Promise.resolve(f()).then(()=>v),r=>Promise.resolve(f()).then(()=>{throw r}))};")
        print('[RENDER]Polyfill');print('[RENDER]Navigate')
        try:d.get(u)
        except:print('[RENDER]Timeout')
        time.sleep(2);h=d.page_source;c=detect_captcha(h)
        if c:print('[RENDER]CAPTCHA detected');solve_2captcha(d,c,u,j);time.sleep(3);h=d.page_source
        else:print('[CAPTCHA]No')
        Path('render-results').mkdir(exist_ok=True)
        Path(f'render-results/rendered-{j}.html').write_text(h,encoding='utf-8')
        print(f'[RENDER]HTML:{len(h)}bytes')
        Path(f'render-results/meta-{j}.json').write_text(json.dumps({'url':u,'jobId':j,'ts':datetime.utcnow().isoformat(),'size':len(h),'captcha':bool(c)},indent=2),encoding='utf-8')
        print('[RENDER]OK');sys.exit(0)
    except Exception as e:print(f'[RENDER]FATAL:{e}');sys.exit(1)
    finally:
        if d:d.quit()

if __name__=='__main__':main()
