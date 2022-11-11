# 定时任务

## 目录结构

```
.
|-- Readme.md
|-- Task
|   -- task.json
|-- Timing.py
|-- logger.log
|-- requirements.txt
```

Task目录下存放需要定时执行的任务文件

task.json用来配置任务

Timing.py为主程序

## 如何运行

```
pip install -r requirements.txt
```

```
python Timing.py
```

运行` Timing.py`文件后，定时任务框架开始运行，并实时监控`Task/task.json`

## 添加任务

> 添加任务不需要重启Timing.py

1.在调试好任务后，将任务放置于该项目目录下，如放置在`Task/`目录下

2.修改配置文件前，需要将代码中 `import 自定义方法` 和 `文件引用方式` 修改为 `以该项目为根目录的import方式` 和`以该项目为根目录的文件引用方式` 

例如：

​	Spider 任务调试时：` from util.utils import *`

​	将Spider任务放置与`Task`目录下后，目录结构为

```
Task
|-- JS
|   `-- mafengs_xsing.js
|-- ZhaoBiao
|   |-- GGZY.py
|   |-- Mafengs.py
|   |-- Zhaobiao.py
`-- util
    `-- utils.py
```

​	所以需要修改为 `from Task.Spider.util.utils import *`

​	对文件的引用相同

3. 在完成以上修改后，需要修改`Task/task.json`

```
{
  "Task1": { // 注意！：需要与下方“Job”的值相同
    "Path": "",  // 必填，为文件方法的py文件路径
    "Job": "Task1", // 必填，为方法名
    "JobTime": {
      "hour": "", // 必填 是apscheduler定时任务的 小时 触发
      "minute": "" // 必填 是apscheduler定时任务的 分钟 触发
    },
    "mail": { // 必填 用于配置发送邮箱
      "receivers": [], // 选填 为收信人 默认为Timing类中默认的debug邮箱
      "debug": [], // 选填 当发件失败时发送报错信息 默认为Timing类中默认的debug邮箱
      "msg": "", // 选填 为邮件的正文内容 默认为Timing类中的msg
      "subject": "" // 选填 为新建的标题开头 默认为“定时任务”
    }
  },
  "Task2": {
	...
  }
}
```

​	修改完成后保存，即可在log中看到 

​	`Added job "Task1" to job store "default"`

## 删除任务

 在`Task/task.json`中删除对应任务即可

## 任务格式要求

如果需要挂载一个任务，那么这个任务应该是一个 `def` 而不是一个 `class` 或 `类内的方法`

方法应该返回一个含有两个元素的元组 `(邮件附件路径（目前仅支持xlsx/xls）, 获取到的信息条数)`
