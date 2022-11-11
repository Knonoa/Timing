import os
import json
import logging
import smtplib
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Timing(FileSystemEventHandler):
    def __init__(self):
        super(Timing, self).__init__()
        # 任务加载相关
        self._watch_path = "Task/task.json"

        # 日志文件
        logging.basicConfig(filename='logger.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.log = logging.getLogger()
        self.log.setLevel(level=logging.INFO)
        self.log.info("Start Auto Spider")

        # 定时任务相关
        self.scheduler = BlockingScheduler()
        self.start_time = datetime.now()
        self.scheduler.add_job(self.print_time, 'cron', hour='0-23', minute="30")
        self.job_dict = {}
        self.job_dict_id = {}
        self.task_dict = self.load_task()
        self.update_job_dict()
        self.scheduler.add_listener(self.send_mail, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # 邮箱配置
        self.date_style = "%Y-%m-%d"
        self.mail_host = 'smtp.exmail.qq.com'
        self.mail_port = 465
        self.mail_user = '邮箱'
        self.mail_pass = '邮箱密钥'
        self.mail_sender = "发信人"
        self.mail_default_subject = "定时任务"
        self.mail_default_debug = ['默认收信人']
        self.mail_default_msg = """
                    <p>技术支持：</p>
                    <p>人工智能护发素</p>
                    """

    def on_closed(self, event):
        self.task_dict = self.load_task()

    def update_job_dict(self):
        jobs = self.scheduler.get_jobs()
        new_job_dict = {}
        new_job_dict_id = {}
        for job in jobs:
            new_job_dict[job.name] = {
                'id': job.id,
                'check_time': datetime.now()
            }
            new_job_dict_id[job.id] = job.name

        self.job_dict = new_job_dict
        self.job_dict_id = new_job_dict_id
        self.log.info(self.job_dict)

    def load_task(self):
        if os.path.exists(self._watch_path):
            with open(self._watch_path, 'r', encoding='UTF-8') as f:
                load_dict = json.load(f)

            load_job_name = []
            for job in load_dict:
                job = load_dict[job]
                job_func = job['Job']
                job_name = job_func
                job_path = job['Path']
                job_time_hour = job['JobTime']['hour']
                job_time_minute = job['JobTime']['minute']
                load_job_name.append(job_name)

                if job_name not in self.job_dict.keys():
                    job_import = "from {} import {}".format(".".join(job_path.replace(".py", "").split("/")), job_func)
                    exec(job_import)
                    self.scheduler.add_job(eval(job_func), 'cron', hour=job_time_hour, minute=job_time_minute)
                    self.log.info("{} add job {}".format(job_import, job_func))

            for add_job_name in self.job_dict.keys():
                if add_job_name == "Timing.print_time":
                    continue
                if add_job_name not in load_job_name:
                    add_jog_id = self.job_dict[add_job_name]['id']
                    self.scheduler.remove_job(add_jog_id)
                    self.log.info("remove job {}, id={}".format(add_job_name, add_jog_id))

            self.update_job_dict()

            return load_dict
        else:
            self.log.info("{} not exists".format(self._watch_path))

    def print_time(self):
        now = datetime.now()
        self.log.info("当前时间:{} 已运行:{}".format(now.strftime("%Y-%m-%d %H-%M-%S"), now - self.start_time))

    def send_mail(self, event):
        job_name = self.job_dict_id[event.job_id]

        if self.task_dict is None:
            return
        if job_name not in self.task_dict.keys():
            return
        if 'mail' not in self.task_dict[job_name]:
            return

        mail_receivers = self.task_dict[job_name]['mail']['receivers'] if "receivers" in self.task_dict[job_name]['mail'] else self.mail_default_debug
        mail_debug = self.task_dict[job_name]['mail']['debug'] if "debug" in self.task_dict[job_name]['mail'] else self.mail_default_debug
        mail_msg = self.task_dict[job_name]['mail']['msg'] if "msg" in self.task_dict[job_name]['mail'] else self.mail_default_msg
        mail_subject = self.task_dict[job_name]['mail']['subject'] if "subject" in self.task_dict[job_name]['mail'] else self.mail_default_subject

        message = MIMEMultipart()
        message.attach(MIMEText(mail_msg, 'html', 'utf-8'))
        message['From'] = Header("Timing定时任务<{}>".format(self.mail_user), 'utf-8')  # 发送者
        message['To'] = Header("timing<zhaobiao@placeholder.com>", 'utf-8')  # 接收者

        job_return = event.retval

        send_success = False
        if job_return:
            file_path, file_len = job_return

            if os.path.exists(file_path):
                message['Subject'] = Header("{} {} 获取数据{}条".format(mail_subject, datetime.now().strftime(self.date_style), file_len), 'utf-8')
                msg_xlsx = MIMEApplication(open(file_path, 'rb').read())
                msg_xlsx.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                message.attach(msg_xlsx)

                try:
                    smtpObj = smtplib.SMTP_SSL(self.mail_host, self.mail_port)
                    smtpObj.login(self.mail_user, self.mail_pass)
                    smtpObj.sendmail(self.mail_sender, mail_receivers, message.as_string())
                    self.log.info("邮件发送成功 {} to {}".format(self.mail_sender, ", ".join(mail_receivers)))
                    smtpObj.quit()
                    send_success = True
                except smtplib.SMTPException as e:
                    self.log.error("无法发送邮件 {}".format(e))
                    message['Subject'] = Header("{} {} 发送邮件失败 {}".format(mail_subject, datetime.now().strftime(self.date_style), e), 'utf-8')
            else:
                message['Subject'] = Header("{} {} {}文件不存在".format(mail_subject, datetime.now().strftime(self.date_style), file_path), 'utf-8')
        else:
            message['Subject'] = Header("{} {} 任务无返回值".format(mail_subject, datetime.now().strftime(self.date_style)), 'utf-8')

        if not send_success:
            try:
                smtpObj = smtplib.SMTP_SSL(self.mail_host, self.mail_port)
                smtpObj.login(self.mail_user, self.mail_pass)
                smtpObj.sendmail(self.mail_sender, mail_debug, message.as_string())
                self.log.info("debug邮件发送成功 {} to {}".format(self.mail_sender, ", ".join(mail_receivers)))
                smtpObj.quit()
            except smtplib.SMTPException as e:
                self.log.error("debug邮件无法发送 {}".format(e))

    def run(self):
        self.scheduler.start()


if __name__ == '__main__':
    test = Timing()

    observer = Observer()
    observer.schedule(test, path=test._watch_path, recursive=False)  # recursive递归的
    observer.start()

    print('scheduler start')
    test.run()
