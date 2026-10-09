"""
Example of Data Annotation
"""
import os
import random
from http import HTTPStatus
import dashscope
from dashscope import Generation

from dotenv import load_dotenv


SYSTEM_PROMPT_ANNOTATION = """阅读裁判文书并整理输入文本为JSON文件

参考示例：
```json
{
    "案件类型": "刑事二审",
    "文书ID": "https://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/index.html?docId=4L13DrbIdEyrO+PdrhByLSgGw9VtktdXJmVsQJcxz/GLT82ysZ5c3pO3qNaLMqsJ4UFMIzGyFfSA75RjT0hR56NibXaty3AlQnAaCY17r5RLkd9HkIpdnF/iB5V94QSv",
    "案件名称一": "梁玮轩交通肇事二审刑事附带民事判决书",
    "案件名称二": "新疆生产建设兵团第八师中级人民法院",
    "案件编号": "（2020）兵08刑终44号",
    "裁判日期": "2020-08-05",
    "法院名称": "新疆生产建设兵团第八师中级人民法院",
    "肇事人": "梁玮轩",
    "性别": "男",
    "出生日期": "35973",
    "民族": "汉",
    "文化程度": "空",
    "户籍所在地": "空",
    "案发时间": "43476",
    "车辆品牌和车型": "新C0×警“长城”牌小型普通客车",
    "事故发生地": "空",
    "酒精": "有",
    "伤亡数量": "0",
    "驾照实习期开始": "43138",
    "驾驶实习期结束": "空",
    "驾照类型(A or C)": "C",
    "实习期类型（A2 or C1）": "空",
    "经济损失": "1385133.76",
    "撤销案件号": "空",
    "维持案件号": "空"
}

要求：
1. 如样例所示：
    - 所有字段都为字符串，数字同样
    - 如果一个字段在法律文书中并不存在，请填`无`
2. 仅给出json结果即可
"""


load_dotenv('../.env')
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
dashscope.api_key = dashscope_api_key


def summarize():
    with open('sample.txt') as f:
        user_prompt = f.read()
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT_ANNOTATION},
        {'role': 'user', 'content': user_prompt}
    ]
    response = Generation.call(
        # turbo不可用，max长度不够
        model="qwen-max-longcontext", messages=messages,
        # 设置随机数种子seed，如果没有设置，则随机数种子默认为1234
        seed=random.randint(1, 10000),
        # 将输出设置为"message"格式
        result_format='message'
    )
    if response.status_code == HTTPStatus.OK:
        content = response["output"]["choices"][0]["message"]["content"]
        return content
    else:
        raise Exception('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code, response.code, response.message))


if __name__ == "__main__":
    result = summarize()
    print(result)
