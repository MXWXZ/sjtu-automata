# Protocol analysis
Jaccount 登陆&选课协议分析

## Jaccount认证
### 登录界面
地址：[GET] `http://jaccount.sjtu.edu.cn/jaccount/jalogin?sid=xxx9&returl=xxx&se=xxx`\
参数：`sid` `returl` `se`猜测为接入单位的密钥和识别码之类，returl应该为登陆后的返回地址，有CSRF防护为加密数据\
返回：登录界面

地址：[GET] `https://jaccount.sjtu.edu.cn/jaccount/captcha?xxx`\
参数：时间戳+随机数\
返回：验证码图片（每次访问会刷新！）

### 认证
地址：[POST] `https://jaccount.sjtu.edu.cn/jaccount/ulogin`\
参数：
- `sid`: 登录界面中的sid
- `returl`: 登录界面中的returl
- `se`: 登录界面中的se
- `user`: 登陆用户名
- `pass`: 密码
- `captcha`: 验证码

返回：
- 用户名/密码/验证码错误302登录界面且出现错误提示
- 验证成功设置`JAVisitedSites`和`JAAuthCookie`，然后302回到先前指定地址完成认证
- Cookie有效期为会话级

## Electsys
### 登陆
地址：[GET] `http://electsys.sjtu.edu.cn/edu/login.aspx`\
返回：302重定向
- 存在未注销session则由Jaccount接入平台执行注销操作，并且两次302到`http://electsys.sjtu.edu.cn/edu/logerror.aspx?message=xxx`显示错误页面。
- 正常请求则跳转到Jaccount认证

### 阅读声明
地址：[GET]/[POST] `http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=1/2/3`\
参数：
- `xklc`：1为海选，2为抢选，3为第三轮
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数
- `CheckBox1`：on为选中“我已阅读”
- `btnContinue`：固定值`%E7%BB%A7%E7%BB%AD`（继续）

返回：
- 选课时间未到返回错误页面`http://electsys.sjtu.edu.cn/edu/messagePage.aspx?message=xxx`
- 选课时间到进入选课页面