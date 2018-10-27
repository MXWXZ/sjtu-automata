# AutoElect
![Language](https://img.shields.io/badge/Language-Python3-red.svg)![License](https://img.shields.io/badge/License-GPL--3.0-yellow.svg)

**注意！此版本为BETA版，未经过严格测试，可能存在BUG，如有问题请提交[issue](https://github.com/MXWXZ/AutoElect/issues)**

上海交通大学抢课脚本\
协议分析：<https://github.com/MXWXZ/AutoElect/blob/master/Protocol analysis.md>

## 使用脚本你可以做到
:heavy_check_mark: 无人值守自动抢课\
:heavy_check_mark: 并发抢课提升成功率\
~~:heavy_check_mark: 卡时间准时抢课（暂不开放）~~

## 使用脚本你不能做到
:x: 违反选课规则选课\
:x: 提高您的网速\
:x: 保证一定可以抢到课

## 系统测试优先度
运行环境：Python 3(.7)

Linux >> Windows >> ~~macOS=0（没钱无测试）~~

## 参数说明
使用：`python autoelect.py [-OPTIONS]`

|参数|长参数形式|说明|
|:--:|:--:|:--:|

## 一些说明
1. 为了尽量减少第三方库的使用，本脚本并未集成且也不会集成验证码识别的功能

## 二次开发
1. 安全考虑，任何二次开发不允许自行询问或保存Jaccount用户名/密码，需要登陆请调用`Login`函数
