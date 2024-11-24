import requests
import tqdm
import os

UNICODE_VERSIONS = [
  "4.1.0",
  "5.0.0",
  "5.1.0",
  "5.2.0",
  "6.0.0",
  "6.1.0",
  "6.2.0",
  "6.3.0",
  "7.0.0",
  "8.0.0",
  "9.0.0",
  "10.0.0",
  "11.0.0",
  "12.0.0",
  "12.1.0",
  "13.0.0",
  "14.0.0",
  "15.0.0",
  "15.1.0",
  "16.0.0"
]
CUR_FOLDER = os.path.dirname(__file__)
NAME_LIST_PATH = os.path.join(os.path.dirname(CUR_FOLDER), 'NamesList')

for version in tqdm.tqdm(UNICODE_VERSIONS):
    if os.path.exists(os.path.join(os.path.dirname(CUR_FOLDER), 'NamesList', f'{version}.txt')):
        continue
    url = f"https://www.unicode.org/Public/{version}/ucd/NamesList.txt"
    r = requests.get(url)
    open(os.path.join(NAME_LIST_PATH, f'{version}.txt'), 'w').write(r.text)
