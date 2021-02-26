import requests


class DingTalkClient:
    def __init__(self, url=''):
        self.url = url

    def send_to_group(self,  content, msg_type='markdown', url=''):
        data = {
            "msgtype": msg_type,
        }
        if msg_type == 'markdown':
            data["markdown"] = {"title": "提醒", "text": content}
        else:
            data["text"] = {
                "content": f'提醒：{content}'
            }
        url = url or self.url
        try:
            r = requests.post(url=url, json=data)
            r_json = r.json()
            if r_json['errcode'] == 0:
                print(f'钉钉Webhook推送成功\n通知对象：{url}\n消息内容：{content}')
                return True
            else:
                print(f"钉钉Webhook推送失败错误码\n请求url:{url}\n请求data:{data}\n请求响应:{r_json}")
                return False
        except Exception as e:
            print('发送钉钉失败', e)
            return False
