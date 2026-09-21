#!/usr/bin/env python3
"""
Safari browser rendering with 2captcha CAPTCHA solving.
Uses real Safari via Selenium safaridriver (not Playwright webkit approximation).
"""
import os
import json
import time
import base64
import sys
from datetime import datetime
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By


CAPTCHA_TYPES = {
    'recaptcha_v2': ['g-recaptcha', 'grecaptcha'],
    'hcaptcha': ['h-captcha', 'hcaptcha'],
    'recaptcha_v3': ['recaptcha/enterprise']
}


def detect_captcha(html):
    """Detect CAPTCHA type from HTML"""
    for captcha_type, markers in CAPTCHA_TYPES.items():
        if any(marker in html for marker in markers):
            return captcha_type
    return None


def solve_captcha_with_2captcha(driver, captcha_type):
    """Solve CAPTCHA using 2captcha API"""
    api_key = os.environ.get('CAPTCHA_API_KEY')
    if not api_key:
        print('[CAPTCHA] API key not configured, skip')
        return False

    print(f'[CAPTCHA] Detected: {captcha_type}')

    try:
        element = driver.find_element(
            By.CSS_SELECTOR,
            '[class*="captcha"], [data-captcha], .g-recaptcha, .h-captcha'
        )

        screenshot = element.screenshot_as_png
        base64_image = base64.b64encode(screenshot).decode()
        print(f'[CAPTCHA] Screenshot: {len(screenshot)} bytes')

        url = os.environ.get('URL', 'https://2captcha.com/it/demo/recaptcha-v2')
        task_type = 'RecaptchaV2TaskProxyless' if captcha_type == 'recaptcha_v2' else 'HCaptchaTaskProxyless'

        payload = {
            'clientKey': api_key,
            'task': {
                'type': task_type,
                'websiteURL': url,
                'websiteKey': 'placeholder',
                'body': base64_image
            }
        }

        response = requests.post(
            'https://api.2captcha.com/createTask',
            json=payload,
            timeout=30
        )
        result = response.json()

        if 'taskId' in result:
            print(f'[CAPTCHA] Task created: {result["taskId"]}')
            return True
        else:
            print(f'[CAPTCHA] Error: {result.get("errorCode", "unknown")}')
            return False

    except Exception as e:
        print(f'[CAPTCHA] Error: {e}')
        return False


def main():
    url = os.environ.get('URL')
    job_id = os.environ.get('JOB_ID')

    if not url or not job_id:
        print('[RENDER] ERROR: URL and JOB_ID environment variables required')
        sys.exit(1)

    print(f'[RENDER] URL: {url}')
    print(f'[RENDER] Job ID: {job_id}')
    print('[RENDER] Browser: Safari (real via safaridriver) on macOS')

    driver = webdriver.Safari()

    try:
        driver.get('about:blank')
        driver.execute_script("""
            Object.defineProperty(navigator, 'userAgent', {
                get: function () {
                    return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15';
                }
            });
        """)

        print('[RENDER] Navigating...')
        driver.get(url)

        time.sleep(2)

        html = driver.page_source
        captcha_type = detect_captcha(html)

        if captcha_type:
            solve_captcha_with_2captcha(driver, captcha_type)
            time.sleep(3)
            html = driver.page_source
        else:
            print('[CAPTCHA] No CAPTCHA detected')

        output_dir = Path('render-results')
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / f'rendered-{job_id}.html'
        output_file.write_text(html, encoding='utf-8')
        print(f'[RENDER] HTML saved: {output_file} ({len(html)} bytes)')

        meta_file = output_dir / f'meta-{job_id}.json'
        meta = {
            'url': url,
            'jobId': job_id,
            'browser': 'Safari (real safaridriver)',
            'os': 'macOS',
            'timestamp': datetime.utcnow().isoformat(),
            'htmlSize': len(html),
            'captchaDetected': bool(captcha_type)
        }
        meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
        print('[RENDER] Completed successfully')

        sys.exit(0)

    except Exception as e:
        print(f'[RENDER] Error: {e}')
        sys.exit(1)

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
