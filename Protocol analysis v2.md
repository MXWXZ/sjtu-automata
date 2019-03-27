# Protocol analysis
Jaccount 登陆&选课协议分析 V2

注：参数中所有中文实际传输均需要UrlEncode

## Jaccount认证
### 登录界面
地址：`https://jaccount.sjtu.edu.cn/jaccount/jalogin?sid=xxx&client=xxx&returl=xxx&se=xxx`\
参数：
- `sid`：验证参数，接入ID号？
- `client`：验证参数，客户端？
- `returl`：登陆后的返回地址，CSRF防护
- `se`：验证参数，SK？

返回：
- 登录界面

地址：`https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid=xxx&t=xxx`\
参数：
- `uuid`：随机uuid
- `t`：时间戳

返回：
- 验证码图片（每次访问会刷新！）

### 认证
地址：`https://jaccount.sjtu.edu.cn/jaccount/ulogin`\
参数：
- `sid`：登录界面中的`sid`
- `returl`：登录界面中的`returl`
- `se`：登录界面中的`se`
- `user`：登陆用户名
- `pass`：密码
- `captcha`：验证码
- `v`：空
- `client`：登录界面中的`client`
- `uuid`：验证码uuid，不可省略
- `g-recaptcha-response`：reCaptcha参数，可省略

返回：
- 用户名/密码/验证码错误302登录界面且出现错误提示
- 验证成功设置`JAVisitedSites`和`JAAuthCookie`，然后302回到先前指定地址完成认证
- Cookie有效期为会话级

## Electsys
- **V2版选课系统很不错，不像V1版的反人类，可以直接向系统提交选课了，且容错性挺强，妈妈再也不用担心我一步一步模拟人类操作啦~**

### 登陆
地址：`http://i.sjtu.edu.cn/jaccountlogin`\
返回：302重定向
- 多次302跳转到Jaccount认证

### 主界面
地址：`http://i.sjtu.edu.cn/xtgl/index_initMenu.html?jsdm=&_t=xxx`\
参数：
- `jsdm`：未知参数，不加似乎无影响
- `_t`：应该是时间戳，不加似乎无影响

返回：登陆后主界面
- 需要包含登陆cookie

### 选课界面
V2版采用AJAX无刷新技术，比之前不知道高到哪里去了，因此除了汉语拼音命名让人不知所云外分析较为方便。

#### 无关紧要的界面元素
- 主界面：`http://i.sjtu.edu.cn/xsxk/zzxkyzb_cxZzxkYzbIndex.html?gnmkdm=N253512&layout=default&su=xxx`
- 课程显示：`http://i.sjtu.edu.cn/xsxk/zzxkyzb_cxZzxkYzbDisplay.html?gnmkdm=N253512&su=xxx`
- 已选信息：`http://i.sjtu.edu.cn/xsxk/zzxkyzb_cxZzxkYzbChoosed.html?gnmkdm=N253512&su=xxx`

GET参数：
- `gnmkdm`：菜单栏选项，`N253512`即为选课。
- `su`：学号

#### 搜索接口
地址：`http://i.sjtu.edu.cn/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html?gnmkdm=N253512&su=xxx`

POST参数：\
太多了不想列举了，没啥卵用。

#### 选课接口
地址：`http://i.sjtu.edu.cn/xsxk/zzxkyzb_xkBcZyZzxkYzb.html?gnmkdm=N253512&su=xxx`\
必须参数（经过测试可以省略的就不写了）：
- `jxb_ids`：唯一班号，教学班最后一列的6位数字
- `xkkz_id`：未知ID，和选课轮数有关，同一轮，同一课程类型为定值。
- `njdm_id`：年级ID？推测为届数。
- `zyh_id`：未知ID。

返回值：
- `{"flag":"1"}`：选课成功
- `{"flag":"0","msg":"所选教学班的上课时间与其他教学班有冲突！"}`：课程冲突
- `{}`：参数错误
- `{"flag":"-1","msg":"x,xxx,x"}`：人数已满