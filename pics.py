import json, time, requests, os, shutil, urllib3
from datetime import datetime
from termcolor import colored
http = urllib3.PoolManager()
def get_url(id, key, attempts=10):
    url = f'https://stablediffusionapi.com/api/v3/fetch/{id}'
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({'key': key})
    for i in range(attempts):
        time.sleep(3)
        response = json.loads(requests.request("POST", url, headers=headers, data=payload).text)
        if response['status'] == 'processing':
            print('processing')
        elif response['status'] == 'success':
            print('images processed')
            return response['status'], response['output']
    return response['status'], None

def download(urls, path, timestamp, prompt, addr=None):
    print('downloading images')
    if addr:
        dir_name = f'{timestamp}_{datetime.fromtimestamp(timestamp).strftime("%d%B%Y")}_{addr}'
    else:
        dir_name = f'{timestamp}_{datetime.fromtimestamp(timestamp).strftime("%d%B%Y")}'
    fullpath = os.path.join(path, dir_name)
    try:
        os.mkdir(fullpath)
    except FileNotFoundError:
        os.mkdir(path)
        os.mkdir(fullpath)
    try:
        for i in range(len(urls)):
            with open(f'{fullpath}/image_{i}.png', 'wb') as out:
                r = http.request('GET', urls[i], preload_content=False)
                shutil.copyfileobj(r, out)
        with open(f'{fullpath}/prompt.txt', 'w') as file:
            file.write(prompt)
    except Exception as error:
        print('[', colored('ERROR', 'red'), '] download failed :', error)
        return False
    else:
        print('[', colored('OK', 'green'), '] download completed successfully')
        return True
