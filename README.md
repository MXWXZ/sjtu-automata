# sjtu-automata
![Version](https://img.shields.io/badge/Version-0.2.0-blue.svg) ![Language](https://img.shields.io/badge/Language-Python3-red.svg) ![License](https://img.shields.io/badge/License-GPL--3.0-yellow.svg)

**注意！此版本为BETA版，未经过严格测试，可能存在BUG，如有问题请提交[issue](https://github.com/MXWXZ/AutoElect/issues)**

上海交通大学抢课脚本\
V2协议分析：<https://github.com/MXWXZ/sjtu-automata/blob/master/Protocol%20analysis%20v2.md>

## 使用脚本你可以做到
:heavy_check_mark: 无人值守自动抢课\
:heavy_check_mark: 并发抢课提升成功率\
:heavy_check_mark: 卡时间准时抢课

## 使用脚本你不能做到
:x: 违反选课规则选课\
:x: 提高您的网速\
:x: 保证一定可以抢到课

## 系统环境测试程度
最佳支持：Ubuntu 18.04 LTS with Python 3.6.7

Linux > Windows >> ~~macOS=0（没钱无测试）~~

## 安装
    
    pip3 install sjtu-automata

## 升级

    pip3 install sjtu-automata --upgrade

### [可选]验证码自动识别
Windows可以不装，Linux如无图形界面且无法通过其他方式打开`captcha.jpeg`文件需要安装。

Ubuntu 18.04：

    sudo apt install tesseract-ocr libtesseract-dev

其他版本/发行版/Windows等自行看文档：https://github.com/tesseract-ocr/tesseract/wiki
    
## 简单使用说明
1. 查看课号：想选的课“教学班”一栏最后6位数字即为唯一课号
2. 查看课程类型：主修课为0，通识课为1，通选课为2（更多需要请提交issue）
3. 使用命令选课，例如选择主修课，课号123456，通识课，课号234567，不使用ocr：

        autoelect 0 123456 1 234567

    注：程序运行过程中输入`s`可以查看选课状态

## 抢课说明
- **本程序所有操作均保证当前课程不会减少，即无论你是否已经选上课、无论是否人满等各种情况都不会影响已选课程。换言之，无论何时均保证课程只多不少，重复提交不会影响当前课表。**
- 程序运行后选课将会自动进行，如果失败自动重试，如果课程已满将自动等待并且定时刷新，直到抢成功或者用户退出为止
- 可以提前开上程序，如果没有开放选课将会自动等待并定时刷新，可以节省登陆的时间
- 所有指定的课程会同时进行选课，每个课程可占一个或多个线程进行选课增加成功率（多线程一般在网卡的时候才有必要）

## 参数说明
### CLI
使用：`autoelect [OPTIONS] [CLASSTYPE-CLASSID]`

|参数|长参数形式|说明|
|:--:|:--:|:--:|
|-v|--version|显示版本|
||--no-update|关闭更新检查|
|-o|--ocr|使用OCR识别验证码|
||--print-cookie|打印登陆cookie|
|-d|--delay|两次尝试选课间隔（默认1s）|
|-n|--number|每个课程的线程数（默认为1）|
|-h|--help|显示帮助|

- `CLASSTYPE`和`CLASSID`成对出现，可以出现多对同步进行，但至少有一对
- `CLASSTYPE`：主修课为0，通识课为1，通选课为2（更多需要请提交issue）
- `CLASSID`：“教学班”一栏最后6位数字