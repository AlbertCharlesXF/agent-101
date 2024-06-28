# 示例:执行代码并获取代码执行结果
import sys
import io
import re
from datetime import datetime
from tools.llm_api import *
import contextlib
from tools.text2jupyter import *

# 定义一个全局变量字典
global_vars = {}

# Prompt:写代码:一次输出,非思维链
def get_coding_prompt(question):
    coding_prompt = f'''
# 你的角色
具有十年经验的代码专家

# 你的任务
根据用户的需求,撰写高质量、可执行的Python代码

# 用户问题
---
{question}
---

# 工作流
1. 写代码之前,首先考虑写代码的时候会出现什么问题,需要用到什么库,然后分点列举； 
2. 考虑上述所有问题,给出撰写代码的步骤；
3. 根据上述步骤,直接给出所有代码；

# 要求
- 你要尽可能考虑代码的最佳实践
- 你要尽可能详细地输出,不需要担心token限制
- 代码要符合强迫症的需求,尽可能美观,舒适
- 尽可能将可以封装的代码进行封装
- 每次回答前都务必深呼吸,一步步思考、推理,然后给出详细的、符合语境和对应专业的解答。
- 你必须尽可能确保你的代码能一次执行成功,确保代码的正确性
- 你的Python代码必须以```python开头,以```结束
- 如果问题包含数据,请按照用户的具体情况设计虚拟的不超过一万条的数据,方便运行测试
- 中文字符显示问题,你需要增加以下代码:
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
'''
    return coding_prompt

# prompt: 优化代码
def get_coding_optimization_prompt(question):
    coding_optimization_prompt = f'''
# 你的角色
具有十年经验的代码专家

# 你的任务
根据用户的需求,优化用户提供的Python代码

# 用户问题
{question}

# 要求
-优化目前的最新代码从以下三个角度:
    1. 哪里可以提升运行速度？
    2. 可以从哪些地方丰富代码,考虑更多因素？
    3. 代码整体风格是否可以更加好看,美观。
- 你要尽可能考虑代码的最佳实践
- 你要尽可能详细地输出,不需要担心token限制
- 代码要符合强迫症的需求,尽可能美观,舒适
- 尽可能将可以封装的代码进行封装
- 每次回答前都务必深呼吸,一步步思考、推理,然后给出详细的、符合语境和对应专业的解答。
- 你必须尽可能确保你的代码能一次执行成功,确保代码的正确性
- 你的Python代码必须以```python开头,以```结束

'''
    return coding_optimization_prompt

# prompt: 提供用户的问题、当前撰写的代码和当前代码的报错,让agent纠错
def get_coding_correction_prompt(question, code, error):
    coding_correction_prompt = f'''
# 你的角色
具有十年经验的代码专家

# 你的任务
根据用户的问题和提供的Python代码,找出其中的错误并加以纠正

# 用户问题
---
{question}
---

# 当前代码
---
{code}
---

# 当前代码出现的错误提示
---
{error}
---

# 你的工作流
1. 首先,仔细阅读用户提供的Python代码和报错信息,找出代码中的错误,并写出可能的原因；
2. 然后,根据上述分析,给出完整的、修正后的代码；

# 要求
- 你要尽可能考虑代码的最佳实践
- 你要尽可能详细地输出,不需要担心token限制
- 代码要符合强迫症的需求,尽可能美观,舒适
- 尽可能将可以封装的代码进行封装
- 每次回答前都务必深呼吸,一步步思考、推理,然后给出详细的解答。
- 你必须尽可能确保你的代码能一次执行成功,确保代码的正确性
- 你在最后必须将python代码从import到结束完整输出,代码必须以```python开头,以```结束

'''
    return coding_correction_prompt

# tool: 提取Python代码
def extract_python_code(text):
    # 定义用于匹配Python代码块的正则表达式
    pattern = re.compile(r'```python(.*?)```', re.DOTALL)
    # 使用findall()方法找到所有匹配的Python代码块
    pycode_list = pattern.findall(text)
    # 合并所有Python代码为一个字符串
    pycode = "\n".join(pycode_list)
    return pycode
    
# tool: 运行代码
def run_code(code, globals=None):
    if globals is None:
        globals = {}
    globals['__name__'] = '__main__'
    output = io.StringIO()

    # 为代码的每一行添加行号
    numbered_code = ""
    lines = code.split('\n')
    for index, line in enumerate(lines, 1):
        numbered_code += f"# Line {index}\n{line}\n"

    try:
        with contextlib.redirect_stdout(output):
            exec(numbered_code, globals, globals)
            success_message = "代码执行成功\n"
            output.write(success_message)
            sys.stdout.flush()  # 确保立即刷新缓冲区内容
    except Exception as e:
        tb = e.__traceback__
        # 反向遍历堆栈找到执行代码的位置
        while tb:
            code_line = tb.tb_frame.f_lineno
            # 查找原始行号
            if code_line and code_line % 2 == 1:  # 因为行号注释和代码是成对的
                original_line = (code_line // 2) + 1
                line_content = lines[original_line - 1] if original_line <= len(lines) else "行号超出代码长度"
                break
            tb = tb.tb_next
        filename = tb.tb_frame.f_code.co_filename if tb else "未知文件"
        lineno = original_line if tb else -1
        error_message = f"代码执行出错: {str(e)}\n文件:{filename}, 行号:{lineno}, 出错代码:{line_content}\n"
        output.write(error_message)
        sys.stdout.flush()  # 确保立即刷新缓冲区内容
    finally:
        result = output.getvalue()
        output.close()
        return result
  
  
    
# tool:代码出错后,获取修改后的代码
def get_modified_code(question, pycode, result, model):
    modify_prompt = get_coding_correction_prompt(question, pycode, result)
    for char in get_llm_answer(modify_prompt, model):
        yield char


# tool: 提取Python代码,包含定界符```python
def extract_python_code_with_delimiter(text):
    # 定义用于匹配Python代码块（包括定界符）的正则表达式
    pattern = re.compile(r'(```python.*?```)', re.DOTALL)
    # 使用findall()方法找到所有匹配的Python代码块
    pycode_list = pattern.findall(text)
    # 合并所有Python代码为一个字符串
    pycode = "\n".join(pycode_list)
    return pycode


# tool:根据用户问题,执行:写代码,运行代码,出错修正/代码出错自动修正机制
def auto_code_running_modify(question, model, save_file_name="code_agent_written_codes"):
    ans = ""
    for char in get_llm_answer(get_coding_prompt(question), model):
        ans += char
        yield char
    # 提取代码
    pycode = extract_python_code(ans)
    # 当前日期
    formatted_date = datetime.now().strftime("%m-%d-%H-%M")
    # 保存文件夹名称
    save_file_name = f"{save_file_name}/{formatted_date}-stocks"
    # 保存realized_code到codes文件夹
    text_to_jupyter(pycode, save_file_name)
    result = run_code(pycode)
    print("="*100 + "\n" + result + "\n" + "="*100)
    max_try_num = 3
    try_num = 0
    while "代码执行出错" in result:
        if try_num >= max_try_num:
            break
        print(f"\n\n代码执行出错,第{try_num+1}次尝试\n")
        if try_num == 0:
            modify_code_ans = ""
            for char in get_modified_code(question, pycode, result, model):
                modify_code_ans += char
                yield char
        else:   
            modify_code_ans = ""
            for char in get_modified_code(question, modified_code, result, model):
                modify_code_ans += char
                yield char
        modified_code = extract_python_code(modify_code_ans)
        result = run_code(modified_code)
        print("="*100 + "\n" + result + "\n" + "="*100)
        try_num += 1
        time.sleep(3)
    print(result)
    # 保存pycode到jupyter
    if try_num == 0:
        # pycode前面增加```python,后面增加```
        pycode = f"```python\n{pycode}\n```"
        text_to_jupyter(pycode, save_file_name)
    else:
        # modified_code前面增加```python,后面增加```
        modified_code = f"```python\n{modified_code}\n```"
        text_to_jupyter(modified_code, save_file_name)
    print("代码执行成功,请查看代码文件夹")
    
# 测试函数
def test():
    import os 
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

    question = '''
    Create a Python script that meets the given requirements for running an LSTM model in PyTorch to predict T+1 stock price changes, keep in mind to:

    1. **Generate Virtual Stock Data**: Simulate realistic-looking stock data to be used for training.
    2. **Build the LSTM Model**: Implement an LSTM architecture using PyTorch.
    3. **Train and Test**: Train the model on the generated data, and test its performance.
    4. **Data Visualization**: Create visualizations for both the stock trends and model analysis.

    Be sure to include all necessary import statements and comments explaining the code logic. Use markdown-style headers and maintain code blocks starting with ```python.
    '''
    question = '''
    创建一个电商网站的用户行为分析案例,包括用户行为数据的获取、数据分析、用户行为预测等。

    # 要求
    - 需要创建一系列复杂的虚拟数据,包括用户行为数据、商品数据等
    - 需要使用多种数据分析方法,包括用户行为分析、用户画像分析等
    - 需要使用机器学习方法,对用户行为进行预测
    - 需要使用数据可视化方法,展示数据分析结果
    '''

    model = "mixtral-8x7b-32768"
    model = "anthropic/claude-3-haiku"
    model = "gpt-3.5-turbo"
    model = "llama3-70b-8192"
    model = "glm-4"

    reply = ""
    for char in auto_code_running_modify(question, model):
        reply += char
        print(char, end="")
    
    