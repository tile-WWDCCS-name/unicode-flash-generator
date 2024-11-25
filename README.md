# Unicode快闪生成器

这是一个 Python 工具，用于生成 Unicode 字符的快闪视频。它允许用户通过多种方式选择字符，支持自定义字体，并提供灵活的视频参数设置。

## 特性

- 完全支持 Unicode16.0.0；
- 支持通过 Unicode 码位范围、文本文件或字体文件生成字符序列；
- 自定义字体支持，可设置多个字体及其优先级；
- 可调节的视频参数（帧率、分辨率等）；
- 进度条显示；
- 可选的背景音乐；
- 灵活的字符过滤选项。

## 准备

1. 确保您的系统已安装以下依赖：
   - `Python 3.x`;
   - `FFmpeg`.
  
   使用命令：

   ```bash
   apt install python ffmpeg
   ```
 
   及Python第三方库：
   - `pillow`;
   - `tqdm`;
   - `fonttools`;
   - `opencv-python`;
   - `numpy`.
   
   使用命令：

   ```bash
   pip install pillow tqdm fonttools opencv-python numpy
   ```

   若您在安装opencv-python或numpy时遇到错误，请尝试：

   ```bash
   apt install opencv-python python-numpy
   ```

2. 克隆此仓库：

   ```bash
   git clone https://github.com/tile-WWDCCS-name/unicode-flash-generator
   cd unicode-flash-generator
   ```

## 使用方法

### 基本用法

生成从 U+0000 到 U+002F 的 Unicode 快闪视频，帧率为 15fps：

```bash
python uni_flash.py 15 -rang 0 2F
```

> 十六进制不区分大小写。

### 添加音乐

若您想为生成的视频添加音乐，一般运行：

```bash
python add_audio.py
```

即可，这将会在当前目录下生成一个带音乐的`with_audio.mp4`文件。

> 请在视频生成完成后运行，并确保您没有重命名生成的视频，同时`UFM.mp3`存在。

若您想更改音乐或输出文件路径等，请使用参数：
- `-vp`, `--video_path`: 待添加音乐的视频文件的路径；
- `-ap`, `--audio_path`: 音乐文件的路径；
- `-op`, `--output_path`: 输出文件的路径。


### 使用自定义字体

使用一个或多个自定义字体：

```bash
python uni_flash.py 15 -rang 0 20 -fonts a.ttf b.otf c.ttf
```

> 只支持ttf或otf格式的非位图字体。

字体优先级按输入顺序降低。如果所有自定义字体都无法显示某个字符，将使用默认字体。

### 从文本文件中生成

从文本文件中获取将要快闪的字符：

```bash
python uni_flash.py 15 -ftf 1.txt
```

若1.txt中写着：

```
1234，abc,互相,0123
```

则表示快闪`1234，abc,互相,0123`十六个字符。

### 从编码列表文件生成

通过一个写着Unicode编码（不带0x的十六进制数，多个编码间用「,」分隔）的文件获取将要快闪的字符：

```bash
python uni_flash.py 15 -fcf 1.txt
```

若1.txt中写着：

```
1,2,3,4,4E00,9FFE,E0020
```

> 十六进制不区分大小写。

则表示快闪`U+0001、U+0002、U+0003、U+00004、U+4E00、U+9FFE、U+E0020`六个字符。

### 从字体文件生成

使用指定字体文件中所有有字形的字符作为将要快闪的字符：

```bash
python uni_flash.py 15 -ff -fonts a.ttf b.otf c.ttf
```
### 更多选项

查看所有可用选项：

```bash
python uni_flash.py -h
```

## 高级设置

Unicode 快闪生成器提供了多种高级设置选项，让您能够精细控制视频的生成过程和最终效果。以下是详细的参数说明：

### 视频参数

- `-wt`, `--width`: 设置视频宽度（默认 1920 像素）
  例：`python uni_flash.py 15 -rang 0 100 -wt 1280`

- `-ht`, `--height`: 设置视频高度（默认 1080 像素）
  例：`python uni_flash.py 15 -rang 0 100 -ht 720`

- `-bh`, `--bar_height`: 设置顶部进度条高度（默认 36 像素）
  例：`python uni_flash.py 15 -rang 0 100 -bh 50`

### 字符选择和过滤

- `-sng`, `--skip_no_glyph`: 跳过在所有自定义字体中都没有字形的字符。这一般用于生成某字体的快闪视频。
  例：`python uni_flash.py 15 -rang 0 1000 -fonts custom.ttf -sng`

- `-sl`, `--skip_long`: 跳过在`U+323B0~U+DFFFF` 范围内的字符。这个范围中均为未定义字符，跳过它们可以显著减少生成（全Unicode快闪的）时间。
  例：`python uni_flash.py 15 -rang 0 FFFFF -sl`

- `-su`, `--skip_undefined`: 跳过未定义字符、非字符和代理字符等。这可以确保只显示有效的 Unicode 字符。
  例：`python uni_flash.py 15 -rang 0 FFFFF -su`

- `-shu`, `--show_undefined`: 展示在自定义字体中有字形的未定义字符、非字符、代理字符等。这个选项可以用来检查字体中的特殊字符。
  例：`python uni_flash.py 15 -ff -fonts custom.ttf -shu`

### 字体选择

- `-um`, `--use_mlst`: 使用 MonuLast (典迹末境) 字体作为最后的备选字体。
  例：`python uni_flash.py 15 -rang 0 1000 -um`

- `-ul`, `--use_last`: 使用 LastResort (最后手段) 字体作为最后的备选字体。
  例：`python uni_flash.py 15 -rang 0 1000 -ul`

### 私用区字符

- `-sp`, `--show_private`: 展示在字体中有字形的私用区字符。这对于包含自定义字符的字体特别有用。
  例：`python uni_flash.py 15 -ff -fonts custom.ttf -sp`

### 组合使用

您可以组合多个高级设置选项来精确控制视频生成过程。例如：

```
python uni_flash.py 15 -rang 0 FFFF -wt 1280 -ht 720 -bh 40 -fonts custom1.ttf custom2.ttf -sng -sl
```

这个命令将生成一个 1280x720 分辨率的视频，进度条高度为40像素，使用两个自定义字体，跳过没有在所有自定义字体中都没有字形的字符和在`U+323B0~U+DFFFF`范围内的字符。

某些选项可能会相互影响或冲突。例如，`-su` 和 `-shu` 是互斥的，不能同时使用。在使用这些高级选项时，请仔细考虑它们的组合效果，以获得最佳的视频生成结果。

## 更新ToolFiles（此功能暂未完善）

直接使用`make`命令即可。
