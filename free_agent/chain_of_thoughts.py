from tools.llm_api import * # 用于调用llm模型
from tools.json_tool import * # 用于解析json
import re

class CoTAgent:
    def __init__(self
                 , angent_name="CoTAgent"
                 , model="glm-4"
                 , temperature=0.7
                 , max_iter=10
                 , custom_cot_init_prompt=""
                 , custom_cot_final_prompt=""
                 , custom_cot_optimize_prompt=""
                 , use_default=False  # False: 使用LLM构造的提示词 True:使用已编写好的提示词
                 ):
        self.name = angent_name
        self.model = model
        self.temperature = temperature
        self.system_prompt = '''你将严格遵从我的提示.'''
        self.conversations = [{"role": "system", "content": self.system_prompt}]
        self.max_iter = max_iter
        # 定制提示词
        self.custom_cot_init_prompt = custom_cot_init_prompt
        self.custom_cot_final_prompt = custom_cot_final_prompt
        self.custom_cot_optimize_prompt = custom_cot_optimize_prompt
        self.use_default = use_default

    def generate_cot_prompt(self, question):
        """
        生成CoT的提示词
        """
        with open(f"free_agent/prompts/chain_of_thoughts/cot_prompt_generate.py", "r", encoding="utf-8") as file:
            cot_prompt_generate = file.read()
        cot_prompt_generate = cot_prompt_generate.format(question=question)
        return cot_prompt_generate
        
    def get_prompt(self, question):
        if self.use_default:
            with open(f"free_agent/prompts/chain_of_thoughts/cot_init_prompt.py", "r", encoding="utf-8") as file:
                chain_of_thought_prompt = file.read()
            chain_of_thought_prompt = chain_of_thought_prompt.format(question)
            return chain_of_thought_prompt    
        else:
            cot_prompt_guild = self.generate_cot_prompt(question)
            chain_of_thought_prompt = self.get_answer_only(cot_prompt_guild)
            chain_of_thought_prompt = re.findall(r"```markdown(.*?)```", chain_of_thought_prompt, re.S)[0]
            return chain_of_thought_prompt

    def get_answer_only(self, question):
        ans = ""
        for char in get_llm_answer(question, model=self.model):
            ans += char
            print(char, end="", flush=True)
        return ans
    
    def chat(self, conversations):
        ans = ""
        for char in get_llm_answer_converse(conversations, model=self.model, temperature=self.temperature):
            ans += char
            print(char, end="", flush=True)
        self.conversations.append({"role": "assistant", "content": ans})     
        return ans
    
    def chat_yield(self, conversations):
        for char in get_llm_answer_converse(conversations, model=self.model, temperature=self.temperature):
            yield char

    def get_cot_final_ans(self, final_iter_num=3):
        """
        获取CoT的最终回答
        """
        
        with open(f"free_agent/prompts/chain_of_thoughts/cot_final_prompt.py", "r", encoding="utf-8") as file:
            cot_final_prompt = file.read()
        cot_final_prompt = cot_final_prompt.format(self.question)
        
        self.conversations.append({"role": "user", "content": cot_final_prompt})
        
        iter_num = 0
        ans = ""
        while iter_num < final_iter_num:
            if "[END]" not in ans and iter_num == 0:
                print("\n" + "-"*50 + f"[总结]：iter {iter_num+1}"+ "-"*50 + "\n")
                ans = self.chat(self.conversations)
                iter_num += 1
            elif "[END]" not in ans and iter_num >= 1:
                self.conversations.append({"role": "user", "content": "继续"})
                ans = self.chat(self.conversations)
                iter_num += 1
            else:
                return ans

    def get_cot_answer(self, question):
        self.question = question
        cot_prompt = self.get_prompt(question)
        self.conversations.append({"role": "user", "content": cot_prompt})
        iter = 0
                
        ans = ""
        while iter <= self.max_iter:
            if "[END]" not in ans:
                print("\n" + "-"*50 + f"第{iter+1}轮对话"+ "-"*50 + "\n")
                ans = self.chat(self.conversations)
                iter += 1
                self.conversations.append({"role": "user", "content": "继续"})
            else:
                break
        ans = self.get_cot_final_ans()
        return self.conversations


           
    # 优化最终结果 
    def optimize_result(self):
        with open(f"free_agent/prompts/cot_optimize_prompt.py", "r", encoding="utf-8") as file:
            cot_optimize_prompt = file.read()
        cot_optimize_prompt = cot_optimize_prompt.format(self.question)
        
