# Safari Browser Renderer with 2captcha

Renderizza pagine web usando **Safari reale** (via Selenium safaridriver) su macOS con risoluzione automatica di CAPTCHA via 2captcha.

Non usa approssimazioni WebKit — Safari è il vero browser Apple, controllato via safaridriver su macOS runner.

## Setup

```bash
pip3 install selenium requests
```

## GitHub Secret

Configura il secret `TWOCAPTCHA` con la tua API key 2captcha.

## Uso

Triggerizza il workflow con:
- `url`: URL da renderizzare
- `job_id`: ID univoco del job

Il rendering restituisce:
- `rendered-{job_id}.html`: HTML renderizzato
- `meta-{job_id}.json`: Metadati (browser, OS, timestamp, CAPTCHA status)

## Tecnologie

- Selenium WebDriver (real Safari via safaridriver)
- macOS runner GitHub Actions
- 2captcha per CAPTCHA solving
- Python 3
