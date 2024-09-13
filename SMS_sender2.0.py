import threading
import time
import tkinter as tk
from tkinter import messagebox

import requests


# 发送短信的函数
def send_sms(api_id, api_key, to, body) :
    url = f"https://www.riserphone.com/sms-api/v1/{api_id}/send-sms/{api_key}"
    headers = {
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {
        "to" : to,
        "body" : body
    }

    try :
        response = requests.post(url, headers=headers, data=data, timeout=15)  # 添加超时检测
        response.raise_for_status()  # 检查是否有HTTP错误

        # 打印响应状态码和内容以进行调试
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        # 检查响应是否成功
        if response.status_code == 200 :
            return True
        else :
            return False
    except requests.exceptions.Timeout :
        print(f"发送短信超时: {to}")
        return False
    except requests.exceptions.RequestException as e :
        print(f'请求出错：{e}')
        return False


# 全局变量，用于控制手动停止
stop_sending = False


# 停止发送的函数
def stop_program() :
    global stop_sending
    stop_sending = True
    print('发送已手动终止')


# 批量发送短信任务的线程函数
def send_sms_thread(api_id, api_key, to_number, body_list, interval) :
    global stop_sending
    success_count = 0
    fail_count = 0

    # 字典记录每个号码已经发送的内容
    sent_messages = {number.stips() : [] for number in to_number}

    for i, number in enumerate(to_number) :
        if stop_sending :
            messagebox.showinfo('停止', '发送已手动停止')
            break

        number = number.strip()  # 去除手机号前后的空格
        body = body_list[i % len(body_list)]  # 话术循环

        # 检查是否重复发送话术
        if body in sent_messages[number] :
            print(f'跳过{number}，因为改号码已经接收到相同的短信内容：{body}')
            continue

        # 发送短信
        if send_sms(api_id, api_key, number, body) :
            success_count += 1
            sent_messages[number].append(body)  # 记录已发送的话术
            print(f"短信发送到 {number} 成功，话术: {body}")
        else :
            fail_count += 1
            print(f"短信发送到 {number} 失败，跳过此号码")
            # 终止改号码的发送，跳过这个号码的后续发送
            continue

        # 设置发送间隔为11秒
        time.sleep(interval)

    if not stop_sending :
        messagebox.showinfo("发送完成", f"成功发送: {success_count}条，失败: {fail_count}条")


# 创建GUI窗口的函数
def create_window() :
    def submit() :
        global stop_sending
        stop_sending = False  # 在每次发送前重置停止标志

        api_id = entry_api_id.get()
        api_key = entry_api_key.get()
        to_numbers = entry_to.get("1.0", "end-1c").split("\n")  # 用逗号分隔多个手机号
        body_list = entry_body.get("1.0", "end-1c").split("\n")  # 从Text控件中获取多行文本

        # 输入校验
        if not api_id or not api_key :
            messagebox.showwarning('输入错误', 'API ID和API Key不能为空！')
            return
        if not to_numbers or not body_list :
            messagebox.showwarning('输入错误', '请确保输入至少一个手机号和一个短信内容！')
            return

        # 验证手机号码格式
        invalid_numbers = [number for number in to_numbers if not number.strip().startswith("+")]
        if invalid_numbers :
            messagebox.showwarning('输入错误', f'以下手机号格式无效：{"，".join(invalid_numbers)}')
            return

        # 设置发送时间间隔为11秒
        interval = 11

        # 创建线程来发送短信
        threading.Thread(target=send_sms_thread, args=(api_id, api_key, to_numbers, body_list, interval)).start()

    # 创建主窗口
    window = tk.Tk()
    window.title("批量短信发送器")
    window.geometry("600x800")

    # API ID
    label_api_id = tk.Label(window, text="API ID:")
    label_api_id.grid(row=0, column=0, padx=10, pady=10)
    entry_api_id = tk.Entry(window)
    entry_api_id.grid(row=0, column=1, padx=10, pady=10)

    # API Key
    label_api_key = tk.Label(window, text="API Key:")
    label_api_key.grid(row=1, column=0, padx=10, pady=10)
    entry_api_key = tk.Entry(window, show="*")  # 隐藏API Key输入
    entry_api_key.grid(row=1, column=1, padx=10, pady=10)

    # 接收手机号的提示
    label_to = tk.Label(window, text="接收手机号 (换行分隔):")
    label_to.grid(row=2, column=0, padx=10, pady=10)

    # 添加滚动条
    scroll_bar = tk.Scrollbar(window)
    scroll_bar.grid(row=2, column=2, sticky='ns', padx=2)

    # 接收手机号输入框（100行）
    entry_to = tk.Text(window, height=20, width=40, yscrollcommand=scroll_bar.set)  # 多行文本框
    entry_to.grid(row=2, column=1, padx=10, pady=10)

    # 连接滚动条和文本框
    scroll_bar.config(command=entry_to.yview)

    # 短信内容提示
    label_body = tk.Label(window, text="短信内容(换行分隔）:")
    label_body.grid(row=3, column=0, padx=10, pady=10)

    # 创建一个框架用于放置滚动条和Text控件
    body_frame = tk.Frame(window)
    body_frame.grid(row=3, column=1, padx=10, pady=10)

    # 添加滚动条
    scroll_bar_body = tk.Scrollbar(body_frame)
    scroll_bar_body.grid(row=3, column=2, sticky='ns', padx=2)

    # 短信内容输入框
    entry_body = tk.Text(window, height=25, width=40, yscrollcommand=scroll_bar_body.set)  # 多行文本框
    entry_body.grid(row=3, column=1, padx=10, pady=10)

    # 连接滚动条和内容输入框
    scroll_bar_body.config(command=entry_body.yview)

    # 提交按钮
    submit_button = tk.Button(window, text="发送", command=submit, bg='blue', fg='white', padx=10, pady=10,
                              cursor="spider", width=10)
    submit_button.grid(row=4, column=0, columnspan=2, pady=10)

    # 停止按钮
    stop_button = tk.Button(window, text='停止', command=stop_program, bg='red', fg='white', padx=10, pady=10,
                            cursor="spider", width=10)
    stop_button.grid(row=4, column=8, columnspan=8, pady=10)

    # 启动窗口主循环
    window.mainloop()


# 启动GUI窗口
create_window()
