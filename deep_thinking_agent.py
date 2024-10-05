import re
from tools.llm_api import *
from tools.code_interpreter import *
from tools.json_tool import *
from tools.system_operations import SystemOperations as so
from tools.pdf_reader import *
from tools.search_bing import *
from tools.function_call_toolbox import extract_params_to_json, get_func_name

from prompts.deep_thinking_agent_prompts import SERIES_INTENTION_RECOGNITION_SYSTEM_PROMPT, DEEP_THINKING_AGENT_PROMPT, DEEP_THINKING_AGENT_PROMPT_o1, TASK_DELEGATION_PROMPT, REFLECTION_PROMPT, ELABORATE_DEEP_THINK_PROMPT, ELABORATE_DEEP_THINK_PROMPT_CODING, GET_TASK_NAME_PROMPT

from prompts.deep_thinking_agent_prompts import EXAMPLE_CONTENT_WRITING

class DeepThinkingAgent:
    """
    深度思考智能体
    """
    def __init__(self, main_model, tool_model, flash_model):
        self.main_model = main_model
        self.tool_model = tool_model
        self.flash_model = flash_model

        self.tool_conversations = [{"role": "system", "content": SERIES_INTENTION_RECOGNITION_SYSTEM_PROMPT}]
        # 创建文件夹deep_think_files
        self.file_path = "deep_think_files"
        so.create_folder(self.file_path)
        # coding聊天记录
        self.coding_conversations = [{"role": "system", "content": "You must follow my instructions."}]

    
    def deep_think(self, question):
        self.deep_think_conversation = [{"role": "system", "content": "你需要尽可能详细回答我的问题。"}]
        prompt = DEEP_THINKING_AGENT_PROMPT.format(question=question)
        self.deep_think_conversation.append({"role": "user", "content": prompt})
        ans = ""
        for char in get_llm_answer_converse(self.deep_think_conversation, model=self.main_model):
            ans += char
            yield char
        yield "\n"
        self.deep_think_conversation.append({"role": "assistant", "content": ans})
        self.deep_think_conversation.append({"role": "user", "content": "继续"})
        ans = ""
        for char in get_llm_answer_converse(self.deep_think_conversation, model=self.main_model):
            yield char
            ans += char
        yield "\n"
        self.deep_think_conversation.append({"role": "assistant", "content": ans})
        # 最终整合
        prompt = '''根据上述所有回答，整合出解决这个问题的逐步方案，分点做详细描述'''
        self.deep_think_conversation.append({"role": "user", "content": prompt})
        ans = ""
        for char in get_llm_answer_converse(self.deep_think_conversation, model=self.main_model):
            ans += char
            yield char
        
        self.deep_think_result = ans
        return self.deep_think_result
    
    def deep_think_o1(self, question):
        self.deep_think_conversation = [{"role": "system", "content": "你需要尽可能详细回答我的问题。"}]
        prompt = DEEP_THINKING_AGENT_PROMPT_o1.format(question=question)
        self.deep_think_conversation.append({"role": "user", "content": prompt})
        
        ans_time = 1
        ans = ""
        while "[END]" not in ans:
            print(f"===第{ans_time}次思考===")
            yield "=" * 30 + "\n"
            ans = ""
            for char in get_llm_answer_converse(self.deep_think_conversation, model=self.main_model):
                ans += char
                yield char
            yield "\n"
            self.deep_think_conversation.append({"role": "assistant", "content": ans})
            step_prompt = """
继续下一步。
# 参考长文输出格式
{EXAMPLE_CONTENT_WRITING}
---

# 注意
- 如果是最终方案，你只需要输出一个经过优化后的最终的解决方案, 并且在最后加上[END]提示，表示你的回答全部结束
- 最终方案需要包含所有的步骤，以及每个步骤的详细描述，包含问题和每个步骤的细节，具有可操作性
"""
            step_prompt = step_prompt.format(EXAMPLE_CONTENT_WRITING=EXAMPLE_CONTENT_WRITING)
            self.deep_think_conversation.append({"role": "user", "content": step_prompt})
            yield "\n"
            ans_time += 1
            
        pattern = r"```markdown(.*?)```"
        self.deep_think_result = re.findall(pattern, ans, re.DOTALL)[0]
        text_to_jupyter(self.deep_think_result, "deep_think_o1")
        return self.deep_think_result

    # 反思模块
    def reflect_steps(self, question, deepthink_result):
        prompt = REFLECTION_PROMPT.format(question=question, deepthink_result=deepthink_result)

        ans = ""
        for char in get_llm_answer(prompt, model=self.main_model):
            ans += char
            print(char, end="", flush=True)
        print()
        pattern = r"```markdown(.*?)```"
        deep_think_result = re.findall(pattern, ans, re.DOTALL)[0]
        return deep_think_result

    # 根据question为任务取名
    def get_task_name(self, question):
        prompt = GET_TASK_NAME_PROMPT.format(question=question)
        ans = ""
        for char in get_llm_answer(prompt, model=self.flash_model):
            ans += char
            print(char, end="", flush=True)
        print()
        name = get_json(ans)["task_name"]
        return name
    
    def get_task_type(self, task):
        """
        区分是什么类型的任务，需要输出的是什么类型的结果：
        代码、文本、图片、表格、其他
        - 如果是代码，则需要详细输出完整的代码，需要将任务分配给代码智能体
        """
        prompt = TASK_DELEGATION_PROMPT.format(task=task)
        ans = ""
        for char in get_llm_answer(prompt, self.flash_model):
            print(char, end="", flush=True)
            ans += char
        print()
        task_type = get_json(ans)["task_type"]
        return task_type   
    
    def elaborate_deep_think(self, question):
        # 提取深度思考的结果
        prompt = ELABORATE_DEEP_THINK_PROMPT.format(question=question, deep_think_result=self.deep_think_result)
        
        self.conversations = [{"role": "system", "content": "你必须按照我的要求回答问题。"}]
        self.conversations.append({"role": "user", "content": prompt})
        ans = ""
        step = 1
        
        elaborated_result = ""
        while "[END]" not in ans:
            yield "=" * 30 + "\n"
            ans = ""
            for char in get_llm_answer_converse(self.conversations, model=self.main_model):
                ans += char
                yield char
            yield "\n"
            self.conversations.append({"role": "assistant", "content": ans})
            self.conversations.append({"role": "user", "content": "继续下一步"})
            step += 1
            elaborated_result += ans + "\n"

        # 保存到txt文件
        date = so.get_current_date()
        task_name = self.get_task_name(question)
        file_name = f"{self.file_path}/{task_name}_{date}.txt"
        so.save_text_to_file(elaborated_result, file_name)
        
        jupyter_name = f"{self.file_path}/{task_name}_{date}"
        text_to_jupyter(elaborated_result, jupyter_name)
        
    def elaborate_deep_think_coding(self, question):
        # 提取深度思考的结果
        prompt = ELABORATE_DEEP_THINK_PROMPT_CODING.format(question=question, deep_think_result=self.deep_think_result)
        
        self.conversations = [{"role": "system", "content": "你必须按照我的要求回答问题。"}]
        self.conversations.append({"role": "user", "content": prompt})
        ans = ""
        step = 1
        
        elaborated_result = ""
        while "[END]" not in ans:
            print(f"===第{step}步===")
            ans = ""
            for char in get_llm_answer_converse(self.conversations, model=self.main_model):
                ans += char
                yield char
            yield "\n"
            self.conversations.append({"role": "assistant", "content": ans})
            self.conversations.append({"role": "user", "content": "判断是否完成了所有步骤的内容，如果没有，则继续下一步。如果已经完成，则发送[END]"})
            step += 1
            elaborated_result += ans

        # 保存到txt文件
        date = so.get_current_date()
        task_name = self.get_task_name(question)
        file_name = f"{self.file_path}/{task_name}_{date}.txt"
        so.save_text_to_file(elaborated_result, file_name)
        
        jupyter_name = f"{self.file_path}/{task_name}_{date}"
        text_to_jupyter(elaborated_result, jupyter_name)

    def work_flow(self, question):
        for char in self.deep_think_o1(question):
            yield char
        yield "\n"
        task_type = self.get_task_type(question)
        if task_type == "coding":
            for char in self.elaborate_deep_think_coding(question):
                yield char
            yield "\n"
        else:
            for char in self.elaborate_deep_think(question):
                yield char
            yield "\n"
