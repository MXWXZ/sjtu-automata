# AutoElect
![Version](https://img.shields.io/badge/Version-0.1.0-blue.svg) ![Language](https://img.shields.io/badge/Language-Python3-red.svg) ![License](https://img.shields.io/badge/License-GPL--3.0-yellow.svg)

**注意！此版本为BETA版，未经过严格测试，可能存在BUG，如有问题请提交[issue](https://github.com/MXWXZ/AutoElect/issues)**

上海交通大学抢课脚本\
协议分析：<https://github.com/MXWXZ/AutoElect/blob/master/Protocol%20analysis.md>

## 使用脚本你可以做到
:heavy_check_mark: 无人值守自动抢课\
:heavy_check_mark: 并发抢课提升成功率\
~~:heavy_check_mark: 卡时间准时抢课（暂不开放）~~

## 使用脚本你不能做到
:x: 违反选课规则选课\
:x: 提高您的网速\
:x: 保证一定可以抢到课

## 系统环境测试程度
最佳支持：Ubuntu 18.04 LTS with Python 3.6.7

Linux > Windows >> ~~macOS=0（没钱无测试）~~

## 安装
    
    pip3 install colorama requests Pillow click pytesseract tenacity
    git clone https://github.com/MXWXZ/AutoElect.git
    cd AutoElect

### [可选]验证码自动识别
Windows可以不装，Linux如无图形界面且无法通过其他方式打开`captcha.jpeg`文件需要安装。\
**未安装则每抢成功一门课都需要手动登陆，如需抢多个课则不能实现无人值守！**

Ubuntu 18.04：

    sudo apt install tesseract-ocr libtesseract-dev

其他版本/发行版/Windows等自行看文档：https://github.com/tesseract-ocr/tesseract/wiki
    
## 简单使用说明
**注意：经过测试网页先登录再打开软件可以同时选课。**
部分课无法选到

## 参数说明
使用：`python3 autoelect.py [-OPTIONS]`

|参数|长参数形式|说明|
|:--:|:--:|:--:|

## 高级用法

## FAQ
1. 出现错误`Unhandled response! Retrying...`\
一般这种情况都是教务网卡了，如果较长时间一直出现，请重新运行脚本，如果问题依旧，请提交issue。