# sjtu-automata
![Version](https://img.shields.io/badge/Version-0.1.4-blue.svg) ![Language](https://img.shields.io/badge/Language-Python3-red.svg) ![License](https://img.shields.io/badge/License-GPL--3.0-yellow.svg)

**注意！此版本为BETA版，未经过严格测试，可能存在BUG，如有问题请提交[issue](https://github.com/MXWXZ/AutoElect/issues)**

上海交通大学抢课脚本\
协议分析：<https://github.com/MXWXZ/sjtu-automata/blob/master/Protocol%20analysis.md>

## 使用脚本你可以做到
:heavy_check_mark: 无人值守自动抢课\
~~:heavy_check_mark: 并发抢课提升成功率（测试版不支持）~~\
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
Windows可以不装，Linux如无图形界面且无法通过其他方式打开`captcha.jpeg`文件需要安装。\
~~**未安装则每抢成功一门课都需要手动登陆，如需抢多个课则不能实现无人值守！**~~\
仅针对海选，测试发现抢选提交后不会登出，因此可以实现无人值守。

Ubuntu 18.04：

    sudo apt install tesseract-ocr libtesseract-dev

其他版本/发行版/Windows等自行看文档：https://github.com/tesseract-ocr/tesseract/wiki
    
## 简单使用说明
**注意：经过测试网页先登录再打开软件可以同时登陆，但是任何一边提交选课后将会导致所有登陆失效。**\
**请在海选是确认命令行参数是否正确，以免出现选课失败的情况**

本例详细解释请看本文最后的栗子

海选，使用OCR，选修-个性化-ES002课程-000002老师：

    autoelect -o -r 1 -e 2/gridModule$ctl02$radioButton/ES002/000002

`2`为选修，`gridModule$ctl02$radioButton`为组别（个性化），`ES002`为课号，`000002`为教师号。参数获取方式见下文。

需要选多门课只要在后面再加上`-e xxxx`的参数就行了。

## 抢课说明
- 程序运行后选课将会自动进行，如果失败自动重试，如果课程已满将自动等待并且定时刷新，直到抢成功或者用户退出为止
- 测试版不支持多线程抢课，请等正式版稳定后再使用
- 可以提前开上程序，如果没有开放选课将会自动等待并定时刷新，可以节省登陆的时间
- 延时数如果调的太低会被ban30s，请酌情设置或使用默认参数

## 参数说明
### CLI
使用：`autoelect [OPTIONS]`

|参数|长参数形式|说明|
|:--:|:--:|:--:|
|-v|--version|显示版本|
|-i|--interact|交互模式（忽略其他选项）|
||--no-update|关闭更新检查|
|-r|--round|指定选课轮数（1/2/3），默认为2|
|-o|--ocr|使用OCR识别验证码|
||--print-cookie|打印登陆cookie|
||--delay-elect|人数未满检查频率（默认15s）|
||--delay-login|选课开放检查频率（默认15s）|
|-e|--elect|选课，可以使用多个，参数见下|
|-l|--list-teacher|列出教师，参数见下|
|-h|--help|显示帮助|

选课参数：课程类型/课程组别（必修课无此项）/课号/教师ID
- 课程类型：1为必修，2为选修，3为通识，4为任选
- 课程组别：请通过交互模式查看，必修课无组别，跳过这项即可
- 课号：课号，如`AV001`
- 教师ID：通过交互模式或者`-l`查看

列出教师参数：课程类型/课程组别/课号
- 同上

### 交互模式
指定`-i`参数进入交互模式，命令说明：

|命令|参数|说明|
|:--:|:--:|:--:|
|back||返回上级，只允许在选中课号后使用|
|cd|课程类型/课程组别/课号|选中不同项目，空格分割可以连续执行|
|cookie||打印cookie|
|elect|[教师编号] [人数未满检查频率（默认15s）]|选课|
|help||显示帮助|
|login|[选课轮数] [0/1是否采用OCR] [选课开放检查频率（默认15s）]|登陆|
|ls||列出当前信息|
|quit||退出|
|update||检查更新|
|version||显示版本|

## 栗子

例如下面这个选课流程，**注意//后面的内容为后期注释，实际使用不要添加！！！**\
所有数据经过处理不包含用户信息，但是流程是一样的

```
(AutoElect)> login 1 1  // 登陆，海选，使用OCR
[Warning] Only one session was permitted at the same time. Do NOT login on other browsers!
[Info] Login to your JAccount:
Username: 9S        // JAccount用户名 9S
Password(no echo):  // 输入你的密码，注意是没有回显的
[Info] Login successful!
[Info] Elect round 1 is available!
(9S)$ ls     // 查看必修课
      CID	Name
      MO001	长者语录
      MO002	动物寿命研究
      MO003	唱诗班
(9S)$ cd 2   // 切换选修课
(9S)$ ls     // 查看选修课
      		CGP			Name
      gridModule$ctl02$radioButton	个性化教育
(9S)$ cd gridModule$ctl02$radioButton    // 切换到个性化教育
(9S)$ ls     // 查看个性化教育
      CID	Name
      ES001	Steam入门
      ES002	电子竞技导论
(9S)$ cd ES001  // 切换到ES001
(9S ES001)$ ls  // 查看老师
      TID	Name
      000001	G胖
(9S ES001)$ back   // 返回（只能在查看老师后使用）     
(9S)$ ls    // 查看个性化教育
      CID	Name
      ES001	Steam入门
      ES002	电子竞技导论
(9S)$ cd ES002  // 切换到ES002
(9S ES002)$ ls  // 查看老师
      TID	Name
      000002	IG.WXZ
(9S ES002)$ elect 000002    // 选课，自动提交
[Info] Selecting teacher...(1/2)
[Info] Submitting...(2/2)
[Info] Elect OK~ You are logged out!
[Warning] Your username and password will be remembered until you quit.
(AutoElect)> quit   // 退出
```

相对应的，只要确定了CGP/TID的值，即可使用下面的命令直接选课：

    autoelect -o -r 1 -e 2/gridModule$ctl02$radioButton/ES002/000002

其中`-o`为使用OCR，`-r 1`为海选，`-e`指定为选课模式，`2/gridModule$ctl02$radioButton/ES002/000002`就是上面我们`cd`指令执行的参数和教师编号
