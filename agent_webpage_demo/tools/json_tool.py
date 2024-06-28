import json
import re

def get_json(text):
    text = text.replace("\n", "").replace(" ", "").replace("：","-")
    try:
        # 尝试直接解析整个文本
        json_obj = json.loads(text)
        return json_obj
    except json.JSONDecodeError as e:
        # 正则表达式提取包含```json的整个块
        matches = re.findall(r"```json\n([\s\S]*?)\n```", text)
        if matches:
            try:
                response_json = json.loads(matches[0])
                return response_json
            except json.JSONDecodeError as e:
                print("解析错误：", e)
        else:
            matches = re.findall(r"```json([\s\S]*?)```", text)
            response_json = json.loads(matches[0])
            return response_json
            