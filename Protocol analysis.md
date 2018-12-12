# Protocol analysis
Jaccount 登陆&选课协议分析

## Jaccount认证
### 登录界面
地址：[GET] `http://jaccount.sjtu.edu.cn/jaccount/jalogin?sid=xxx9&returl=xxx&se=xxx`\
参数：`sid` `returl` `se`猜测为接入单位的密钥和识别码，`returl`为登陆后的返回地址，有CSRF防护为加密数据\
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
- **由于选课系统设计极其SB，API参数通用性很低，部分参数为薛定谔的参数。故本文档所列内容为一般情况下，单次实验中出现频率较高的，比较重要的参数，如有遗漏请告知。自动化处理最好通过解析返回网页action属性获取参数。**
- **由于ASP存在`__EVENTVALIDATION`验证，因此可能无法通过直接向接口提交绕过部分操作，故AutoElect采用全程模拟的方法进行。**

### 登陆
地址：[GET] `http://electsys.sjtu.edu.cn/edu/login.aspx`\
返回：302重定向
- 存在未注销session则由Jaccount接入平台执行注销操作，并且两次302到`http://electsys.sjtu.edu.cn/edu/logerror.aspx?message=xxx`显示错误页面。
- 正常请求则跳转到Jaccount认证

### 主界面
地址：[GET] `http://electsys.sjtu.edu.cn/edu/student/sdtMain.aspx`\
返回：登陆后主界面
- 需要包含登陆cookie，否则302跳转回`http://electsys.sjtu.edu.cn/edu/`


### 阅读声明
地址：[GET]/[POST] `http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=1/2/3`\
GET参数：
- `xklc`：1为海选，2为抢选，3为第三轮

POST参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数
- `CheckBox1`：on为选中“我已阅读”
- `btnContinue`：固定值`%E7%BB%A7%E7%BB%AD`（继续）

GET返回：
- 阅读声明界面

POST返回：
- 选课时间未到返回错误页面`http://electsys.sjtu.edu.cn/edu/messagePage.aspx?message=xxx`
- 选课时间到进入选课页面

### 课程列表
必修课地址：[GET]/[POST] `http://electsys.sjtu.edu.cn/edu/student/elect/speltyRequiredCourse.aspx`\
限选课地址：[GET]/[POST] `http://electsys.sjtu.edu.cn/edu/student/elect/speltyLimitedCourse.aspx`\
通识课地址：[GET]/[POST] `http://electsys.sjtu.edu.cn/edu/student/elect/speltyCommonCourse.aspx`\
任选课地址：[GET]/[POST] `http://electsys.sjtu.edu.cn/edu/student/elect/outSpeltyEP.aspx`\
新生研讨课：TODO: 非新生待完善

#### 课程安排POST
通用POST参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数
- `myradiogroup`：课号

必修课POST参数：
- `SpeltyRequiredCourse1%24lessonArrange`：固定值`%E8%AF%BE%E7%A8%8B%E5%AE%89%E6%8E%92`（课程安排）

限选/通识POST参数：
- `__EVENTTARGET`：ASPX参数
- `__EVENTARGUMENT`：ASPX参数
- `__LASTFOCUS`：ASPX参数
- `gridModule%24ctl02%24radioButton`：固定值`radioButton`
- `lessonArrange`：固定值`%E8%AF%BE%E7%A8%8B%E5%AE%89%E6%8E%92`（课程安排）

任选课POST参数：
- `OutSpeltyEP1$dpYx`：固定值`01000`
- `OutSpeltyEP1$dpNj`：年级届数
- `OutSpeltyEP1$lessonArrange`：固定值`%E8%AF%BE%E7%A8%8B%E5%AE%89%E6%8E%92`（课程安排）

GET返回：
- 课程列表

POST返回：
- 均302跳转到课程安排查询界面

#### 选课提交POST
参数：
- 相应课程安排的除课号、固定值`radioButton`、固定值`%E8%AF%BE%E7%A8%8B%E5%AE%89%E6%8E%92`外的POST参数
- `btnSubmit`/`OutSpeltyEP1$btnSubmit`：固定值`%E9%80%89%E8%AF%BE%E6%8F%90%E4%BA%A4`（选课提交）

返回：
- 302跳转到选课提交


### 课程安排查询
地址：[GET]/[POST] `http://electsys.sjtu.edu.cn/edu/lesson/viewLessonArrange.aspx?kcdm=xxx&xklx=xxx&redirectForm=xxx&yxdm=&nj=xxx&kcmk=xxx&txkmk=xxx&tskmk=xxx`\
GET参数：
- `kcdm`：课号，如`AV001`
- `xklx`：选课类型，`%e5%bf%85%e4%bf%ae`（必修） `%e9%99%90%e9%80%89`（限选） `%e9%80%9a%e8%af%86`（通识） `%e9%80%9a%e9%80%89`（通选/任选）
- `redirectForm`：相应课程列表的页面文件，如`speltyRequiredCourse.aspx`
- `yxdm`：未知参数，必修无此项，限选/通识为空，任选为`01000`（只测试了几个）
- `nj`：年级届数，如`1926`
- `kcmk`：未知参数，必修/通识/任选为`-1`，限选为`h1904%20%20%20%20%20`（未广泛测试，不确定，似乎写`-1`也没问题）
- `txkmk`：未知参数，为固定值`-1`
- `tskmk`：仅通识课存在此项，810为人文学科，820为社会科学，830为自然科学，840为工程科学与技术

GET返回：
- 课程安排，教师列表

POST参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数
- `myradiogroup`：6位数字，推测为教师编号
- `LessonTime1$btnChoose`：固定值`%E9%80%89%E5%AE%9A%E6%AD%A4%E6%95%99%E5%B8%88`（选定此教师）

POST返回：
- 302跳转到课程列表界面
- POST提交即选定此教师

### 选课提交
地址：[GET] `http://electsys.sjtu.edu.cn/edu/student/elect/electSubmit.aspx?redirectForm=speltyCommonCourse.aspx&yxdm=xxx&nj=xxx&kcmk=xxx&tskmk=xxx`

参数：
- `redirectForm`：提交之前所在的课程列表页面文件，如`speltyRequiredCourse.aspx`
- `yxdm`：同课程安排查询参数
- `nj`：同课程安排查询参数
- `kcmk`：同课程安排查询参数
- `tskmk`：同课程安排查询参数

返回：
- 选课成功界面
- 自动登出系统（服务端登出，无法拦截）