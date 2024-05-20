# Unicode快闪生成

## 准备
1. 安装git。（如果没有的话）
```bash
apt install git
```
2. 克隆此仓库后切换到文件夹中。
3. 执行`Preparations.sh`。
```bash
sh Preparations.sh
```
## 生成
### 通过Unicode码位范围生成
```bash
python uni-flash.py -rang 0 20 15
```
==十六进制不区分大小写==

其表示生成从U+0000-U+0020的Unicode快闪（含首尾），帧率为15fps。
### 使用自定义字体
```bash
python uni-flash.py -rang 0 20 15 -fonts a.ttf
```
==只支持ttf格式的非彩色字体。==

其表示优先使用a.ttf字体，若a.ttf无法显示则使用默认字体。

也可以使用多个字体，如：
```bash
python uni-flash.py -rang 0 20 15 -fonts a.ttf c.ttf b.ttf
```
其表示优先使用a.ttf字体，若a.ttf无法显示则使用c.ttf字体，若c.ttf字体也无法显示则使用b.ttf字体，若a.ttf、c.ttf、b.ttf字体均无法显示则使用默认字体。
### 通过.txt文件生成
```bash
python uni-flash.py -from_file 1.txt 15
```
其表示从1.txt文件中获取将要快闪的字符。

如果1.txt文件的内容是
```text
1,2,3,4,4e00,9FFE
```
==十六进制不区分大小写。==

则表示快闪U+1、U+2、U+3、U+4、U+4E00、U+9FFE六个字符。
### 通过自定义字体生成
```bash
python uni-flash.py -from_font 15 -fonts a.ttf c.ttf b.ttf
```
表示快闪的字符将是a.ttf、c.ttf、b.ttf中所有有字形的字符。
### 更多参数
用`python uni-flash.py -h`查看更多帮助。