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
  #"16.0.0"
]
NAME_LIST_PATH = "/storage/emulated/0/qpython/python代码/uni/unicode快闪/NameList/"

for version in tqdm.tqdm(UNICODE_VERSIONS):
    url = f"https://www.unicode.org/Public/{version}/ucd/NamesList.txt"
    r = requests.get(url)
    open(os.path.join(NAME_LIST_PATH, f"{version}.txt"), "w").write(r.text)
