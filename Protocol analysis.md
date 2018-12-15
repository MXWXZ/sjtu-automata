# Protocol analysis
Jaccount 登陆&选课协议分析

注：参数中所有中文实际传输均需要UrlEncode

## Jaccount认证
### 登录界面
地址：[GET] `http://jaccount.sjtu.edu.cn/jaccount/jalogin?sid=xxx9&returl=xxx&se=xxx`\
参数：
- `sid`：验证参数
- `returl`：登陆后的返回地址，CSRF防护
- `se`：验证参数

返回：
- 登录界面

地址：[GET] `https://jaccount.sjtu.edu.cn/jaccount/captcha?xxx`\
参数：
- 时间戳+随机数

返回：
- 验证码图片（每次访问会刷新！）

### 认证
地址：[POST] `https://jaccount.sjtu.edu.cn/jaccount/ulogin`\
参数：
- `sid`：登录界面中的sid
- `returl`：登录界面中的returl
- `se`：登录界面中的se
- `user`：登陆用户名
- `pass`：密码
- `captcha`：验证码
- `v`：空

返回：
- 用户名/密码/验证码错误302登录界面且出现错误提示
- 验证成功设置`JAVisitedSites`和`JAAuthCookie`，然后302回到先前指定地址完成认证
- Cookie有效期为会话级

## Electsys
- **由于选课系统设计极其SB，API参数通用性很低，部分参数含义未知。故本文档所列内容为一般情况下的参数，如有遗漏请告知。自动化处理最好通过解析返回网页action属性获取参数。**
- **由于ASP存在`__EVENTVALIDATION`验证，选课必须严格按照顺序走，缺漏步骤或者少/错参数（即使是一个）均有可能导致选课失败或出现不可预料结果，故AutoElect将尽可能按照参数严格进行。**

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
地址：[POST] `http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=1/2/3`\
GET参数：
- `xklc`：1为海选，2为抢选，3为第三轮

POST参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数
- `CheckBox1`：on为选中“我已阅读”
- `btnContinue`：定值`继续`

POST返回：
- 选课时间未到返回错误页面`http://electsys.sjtu.edu.cn/edu/messagePage.aspx?message=xxx`
- 选课时间到进入选课页面

### 选课界面地址
- 必修课地址（默认）：`http://electsys.sjtu.edu.cn/edu/student/elect/speltyRequiredCourse.aspx`
- 选修课地址：`http://electsys.sjtu.edu.cn/edu/student/elect/speltyLimitedCourse.aspx `
- 通识课地址：`http://electsys.sjtu.edu.cn/edu/student/elect/speltyCommonCourse.aspx`
- 任选课地址：`http://electsys.sjtu.edu.cn/edu/student/elect/outSpeltyEP.aspx`

### 主界面跳转
地址：[POST] `当前界面地址`\
参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数

// 下面是3个没有协作没有review的码农的做法，大家不要学习\
- 从必修跳转到其他需附加（转到哪就加那个）：
    - `SpeltyRequiredCourse1$btnXxk`：定值`限选课`
    - `SpeltyRequiredCourse1$btnTxk`：定值`通识课`
    - `SpeltyRequiredCourse1$btnXuanXk`：定值`任选课`
    - `SpeltyRequiredCourse1$btnYtk`：定值`新生研讨课`

- 从选修/通识跳转到其他需附加；
    - `btnBxk`：定值`必修课`
    - `btnXxk`：定值`限选课`
    - `btnTxk`：定值`通识课`
    - `btnXuanXk`：定值`任选课`
    - `btnYtk`：定值`新生研讨课`

    和以下三项：
    - `__EVENTARGUMENT`：空
    - `__LASTFOCUS`：空
    - `__EVENTTARGET`：空

- 从任选跳转到其他需附加：
  - `OutSpeltyEP1$btnBxk`：定值`必修课`
  - `OutSpeltyEP1$btnXuanXk`：定值`限选课`
  - `OutSpeltyEP1$btnTxk`：定值`通识课`
  - `OutSpeltyEP1$btnYtk`：定值`新生研讨课`

返回：
- 跳转到其他页面

### 选修/通识/任选课打开二级菜单
地址：[POST] `当前界面地址`\
参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数

- 选修/通识附加：
  - `__EVENTARGUMENT`：空
  - `__LASTFOCUS`：空
  - `__EVENTTARGET`：单选按钮编号，从`02`开始。选修为`gridModule$ctl02$radioButton`，必修为`gridGModule$ctl02$radioButton`
  - `上面的单选按钮编号`：定值`radioButton`

- 任选附加：
  - `OutSpeltyEP1$btnQuery`：定值`查 询`
  - `OutSpeltyEP1$dpNj`：届数
  - `OutSpeltyEP1$dpYx`：部门编号

返回：
- 科目的二级菜单

### 课程安排
地址：[POST] `当前界面地址`\
参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数
- `myradiogroup`：课号

必修课附加：
`SpeltyRequiredCourse1$lessonArrange`：定值`课程安排`

选修/通识课附加：
- `__EVENTARGUMENT`：空
- `__LASTFOCUS`：空
- `__EVENTTARGET`：空
- `二级菜单选按钮编号`：定值`radioButton`
- `lessonArrange`：定值`课程安排`

任选课附加：
- `OutSpeltyEP1$lessonArrange`：定值`课程安排`
- `OutSpeltyEP1$dpNj`：届数
- `OutSpeltyEP1$dpYx`：部门编号

返回：
- 课程的科目安排

### 选定老师
地址：[POST]`http://electsys.sjtu.edu.cn/edu/lesson/viewLessonArrange.aspx?xxx`\
GET参数（吔屎吧你）：
- `kcdm`：课号
- `xklx`：定值`必修`/`限选`/`通识`/`通选`
- `redirectForm`：定值`speltyRequiredCourse.aspx`/`speltyLimitedCourse.aspx`/`speltyCommonCourse.aspx`/`outSpeltyEp.aspx`

必修附加：
- `nj`：届数
- `kcmk`：未知参数，定值`-1`
- `txkmk`：未知参数，定值`-1`

选修附加：
- `yxdm`：空
- `kcmk`：定值`h1904     `（存疑）
- `txkmk`：未知参数，定值`-1`

通识附加：
- `yxdm`：空
- `nj`：定值`无`（存疑）
- `kcmk`：未知参数，定值`-1`
- `tskmk`：`810`为人文学科；`820`社会科学；`830`自然科学；`840`工程科学与技术

任选附加：
- `yxdm`：部门编号
- `nj`：届数
- `kcmk`：未知参数，定值`-1`
- `txkmk`：未知参数，定值`-1`

POST参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数
- `LessonTime1$btnChoose`：定值`选定此教师`
- `myradiogroup`：课程教师编号

返回：
- 当前类型主页面

### 提交选课
地址：[POST] `当前界面地址?xxx`\
GET参数：

必修附加：
- `yxdm`：空
- `nj`：届数
- `kcmk`：未知参数，定值`-1`
- `txkmk`：未知参数：定值`-1`
- `tskmk`：空

选修附加：
- `yxdm`：空
- `nj`：届数
- `kcmk`：定值`h1904     `（存疑）
- `txkmk`：未知参数，定值`-1`
- `tskmk`：空

通识附加：
- `yxdm`：空
- `nj`：定值`无`（存疑）
- `kcmk`：未知参数，定值`-1`
- `txkmk`：空
- `tskmk`：`810`为人文学科；`820`社会科学；`830`自然科学；`840`工程科学与技术

任选附加：
- `yxdm`：部门编号
- `nj`：届数
- `kcmk`：未知参数，定值`-1`
- `txkmk`：未知参数，定值`-1`
- `tskmk`：空

POST参数：
- `__VIEWSTATE`：ASPX参数
- `__VIEWSTATEGENERATOR`：ASPX参数
- `__EVENTVALIDATION`：ASPX参数

必修课附加：
- `SpeltyRequiredCourse1$Button1`：`选课提交`

选修/通识课附加：
- `__EVENTARGUMENT`：空
- `__LASTFOCUS`：空
- `__EVENTTARGET`：空
- `btnSubmit`：定值`选课提交`

任选课附加：
- `OutSpeltyEP1$btnSubmit`：定值`选课提交`
- `OutSpeltyEP1$dpNj`：届数
- `OutSpeltyEP1$dpYx`：定值`01000`

返回：
- 选课成功结果
- 服务端登出所有session，无法拦截，需要重新登录（间隔至少10s，否则会Ban 30s）