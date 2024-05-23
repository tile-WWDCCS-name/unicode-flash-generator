# Unicode快闪生成

## 准备
1. 安装git、python、ffmpeg、openssl。
2. 克隆此仓库后切换到文件夹中。
3. 执行以下代码以安装python库。
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install tqdm
pip install pillow
pip install fontTools
```
## 生成
### 通过Unicode码位范围生成
```bash
python uni-flash.py 15 -rang 0 20
```
**十六进制不区分大小写。**

其表示生成从U+0000-U+0020的Unicode快闪（含首尾），帧率为15fps。
### 使用自定义字体
```bash
python uni-flash.py 15 -rang 0 20 -fonts a.ttf
```
**只支持ttf或otf格式的非位图字体。**

其表示优先使用a.ttf字体，若a.ttf无法显示则使用默认字体。

也可以使用多个字体，如：
```bash
python uni-flash.py 15 -rang 0 20 -fonts a.ttf c.ttf b.ttf
```
其表示优先使用a.ttf字体，若a.ttf无法显示则使用c.ttf字体，若c.ttf字体也无法显示则使用b.ttf字体，若a.ttf、c.ttf、b.ttf字体均无法显示则使用默认字体。
### 通过.txt文件生成
```bash
python uni-flash.py 15 -from_file 1.txt
```
其表示从1.txt文件中获取将要快闪的字符。

如果1.txt文件的内容是
```text
1,2,3,4,4E00,9FFE
```
**十六进制不区分大小写。**

则表示快闪U+1、U+2、U+3、U+4、U+4E00、U+9FFE六个字符。
### 通过自定义字体生成
```bash
python uni-flash.py 15 -from_font -fonts a.ttf c.ttf b.ttf
```
表示快闪的字符将是a.ttf、c.ttf、b.ttf中所有有字形的字符。
### 更多帮助
用`python uni-flash.py -h`查看更多帮助。

## 问题
### AttributeError
如抛出`AttributeError： 'NoneType' object has no attribute 'palette'`错误，请尝试加上`-no_dynamic`参数。
### OSError
如抛出`OSError: raster overflow`错误，请尝试以下方式：
- 使用内存更大的设备。
- 分段生成。
- 使用更低的分辩率。