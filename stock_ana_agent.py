from super_agent_tools.llm_api import * # llm_api：调用大模型的API
from super_agent_tools.json_tool import * # json_tool：处理json数据的工具
from super_agent_tools.code_interpreter import * # code_interpreter：代码解释器

from super_agent_tools.search_bing import * # search_bing：搜索必应
from super_agent_tools.search_arxiv import * # search_arxiv：搜索arXiv
from super_agent_tools.search_cnki import * # search_cnki：搜索知网
from super_agent_tools.text2jupyter import * # text2jupyter：文本转jupyter
from super_agent_tools.pdf_reader import *  # pdf_reader：PDF文本提取
from super_agent_tools.download_arxiv_papers import * # download_arxiv_papers：下载arXiv论文

from agents.stock_agents.stock_data import * # stock_data：股票数据
from prompts.stock_agent_prompts.ComAna_PromptTemplate import *  # prompts_js：分模块股票分析系统的所有提示词

# 获取环境中的api_key
from dotenv import load_dotenv
import os
# 加载.env文件
load_dotenv()

stock_data = StockData("stock_data")
snowball_token = os.getenv("snowball_token")

class StockAgent:
    def __init__(self, agent_name, model="glm-4", temperature=0.8):
        ball.set_token(snowball_token)
        self.agent_name = agent_name
        self.model = model
        self.temperature = temperature
        # prompt: 提取股票名称
        self.get_stock_name_prompt = self.get_prompt("prompts/stock_agent_prompts/get_stock_name_prompt.txt")
        # prompt: 判断需求
        self.cmd_judge_prompt = self.get_prompt("prompts/stock_agent_prompts/cmd_judge_prompt.txt")

        # 如果不存在files文件夹，则创建
        if not os.path.exists("files"):
            os.makedirs("files")
        # 获取files文件夹下的所有文件
        files = os.listdir("files")
        self.files = [f for f in files if f.endswith(".pdf")]
                
        # 工具选择系统
        self.tool_system_prompt = self.get_prompt("prompts/stock_agent_prompts/tools_system_prompt.txt")
        self.tool_system_prompt = self.tool_system_prompt.format(files=self.files)
        self.tool_conversations = [{"role": "system", "content": self.tool_system_prompt}]
        
        # 回答系统
        self.agent_system_prompt = '''你必须尽可能详细地回答我的问题。'''
        self.agent_conversations = [{"role": "system", "content": self.agent_system_prompt}]
        
        # 全面分析系统
        self.com_temp_conversations = []
        # 全面分析prompt
        self.comprehensive_analysis_system_prompt = self.get_prompt("prompts/stock_agent_prompts/comprehensive_analysis_system_prompt.txt")
    
    def get_prompt(self, path):
        with open(path, 'r', encoding="utf-8") as file:
            prompt = file.read()
        return prompt

    def get_stock_index_by_stockname(self, stock_name):
        stock_indexes = pd.read_excel("free_agent/stock_agent/stock_indexes.xlsx", index_col=False)
        stock_indexes["证券名称"] = stock_indexes["证券名称"].str.replace(" ", "")
        stock_indexes["indexes"] = stock_indexes["证券代码"].str[-2:] + stock_indexes["证券代码"].str[:6] 
        stock_index = stock_indexes.loc[stock_indexes["证券名称"].str.contains(stock_name), "indexes"].values[0]
        return stock_index

    # 提取股票代码
    def get_stock_index(self, question):
        get_stock_name_prompt = self.get_stock_name_prompt.format(question=question)
        ans = ""
        for char in get_llm_answer(question=get_stock_name_prompt, model="glm-4"):
            ans += char
            print(char, end="", flush=True)
        stock_name = get_json(ans)["stock_name"]
        stock_index = self.get_stock_index_by_stockname(stock_name)
        return stock_index

    # 依据聊天记录回答
    def get_answer_converse_yield(self):
        ans = ""
        for char in get_llm_answer_converse(self.stock_agent_conversations, self.model, self.temperature):
            ans += char
            yield char

    # 选择工具
    def select_tools(self, question, tool_model="deepseek-chat"):
        # prompt:工具选择注意事项
        notice = self.get_prompt("prompts/stock_agent_prompts/tool_notice.txt")
        # 根据问题及注意事项，选择工具
        tool_select_request = self.get_prompt("prompts/stock_agent_prompts/tool_select_request.txt").format(question=question, notice=notice)
        # 让大模型自主选择
        self.tool_conversations.append({"role": "user", "content": tool_select_request})
        ans = ""
        for char in get_llm_answer_converse(self.tool_conversations, tool_model, self.temperature):
            ans += char
            print(char, end='', flush=True)
        self.tool_conversations.append({"role": "assistant", "content": ans})
        tools = get_json(ans)["tools"]
        return tools

    # 全面分析工作流
    def comprehensive_analysis(self, question, model, test=False):
        stock_index = self.get_stock_index(question)
        self.com_temp_conversations.append({"role": "system", "content": self.comprehensive_analysis_system_prompt})
        stock_index = stock_index.upper()
        com_info = StockData.get_all_data(stock_index)
        # 保存com_info为json文件
        with open("files/com_info.json", "w", encoding="utf-8") as f:
            json.dump(com_info, f, ensure_ascii=False)
        if test:
            com_info = json.load(open("files/com_info.json", "r", encoding="utf-8"))
            
        for i, value in enumerate(com_info.values()):
            print(f"\n===分析第{i+1}个模块: {list(com_info.keys())[i]}===")
            additional_prompt = prompts_js[f"ComAna_PromptTemplate_{i+1}"]
            value = f"分析如下信息：\n{value}\n 注意，请尽可能详细且客观。{additional_prompt}\n # 注意\n最终需要给出一个0-100之间的评分。"
            self.com_temp_conversations.append({"role": "user", "content": value})
            ans = ""
            for char in get_llm_answer_converse(self.com_temp_conversations, model):
                ans += char
                yield char
            yield "\n\n"
            self.com_temp_conversations.append({"role": "assistant", "content": ans})
        print("\n分模块分析结束\n")    
        prompt = "继续，开始编写Python代码计算总分。"
        self.com_temp_conversations.append({"role": "user", "content": prompt})
        ans = ""
        for char in get_llm_answer_converse(self.com_temp_conversations, model=model):
            yield char
            ans += char
        yield "\n\n"
        py_code = extract_python_code(ans)
        self.com_temp_conversations.append({"role": "assistant", "content": ans})
        print("\n====================================\n")
        result = run_code(py_code, globals=globals())
        print(f"运行结果：{result}")
        # prompt:代码结果分析
        prompt = self.get_prompt("prompts/stock_agent_prompts/code_result_analysis.txt").format(result=result)
        print("\n====================================\n")
        self.com_temp_conversations.append({"role": "user", "content": prompt})
        ans = ""
        for char in get_llm_answer_converse(self.com_temp_conversations, model="glm-4-0520"):
            yield char
            ans += char
                            
    # 自主分析工作流
    def work_flow(self, question, tool_model="deepseek-chat",ans_model="glm-4-0520"):
        self.agent_conversations.append({"role": "user", "content": question})
        total_info = ""
        # 选择工具
        tools = self.select_tools(question, tool_model)
        yield "\n\n"
        print(f"需要调用工具数量：{len(tools)} \n")
        for i,tool in enumerate(tools):
            print(f"第{i+1}个工具：{tool}")
            
        for tool in tools:   
            if not tool.startswith("stock_agent.") and not tool.startswith("chat"):
                if not tool.startswith("download") and not tool.startswith("run_code"):                    
                    # arXiv搜索 下载arxiv论文 搜索CNKI 搜索必应 获取必应搜索结果 提取PDF文本
                    yield "正在执行：\n" + tool + "\n"
                    result, output = run_code_v2(tool, globals=globals())
                    total_output = str(result) + "\n" + str(output) + "\n"
                    print(f"工具运行结果部分如下：{str(total_output)[:500]}\n")
                    total_info += str(result) + "\n"   
                    
                elif tool.startswith("run_code_v2"):
                    yield "正在运行代码..."
                    # 写代码
                    self.agent_conversations.append({"role": "user", "content": question})
                    ans = ""
                    for char in auto_code_running_modify(question, self.model):
                        yield char
                        ans += char
                    total_info += ans + "\n=====================\n"   
                    
                # 汇总信息
                prompt = self.get_prompt("prompts/stock_agent_prompts/merge_info_prompt.txt")
                prompt = prompt.format(total_info=total_info,question=question,question_repeat=question)
                self.agent_conversations.append({"role": "user", "content": prompt})
                print("\n=========正式回答=========\n")
                ans = ""
                for char in get_llm_answer_converse(self.agent_conversations, ans_model):
                    yield char
                    ans += char      
                                                            
            elif tool.startswith("chat"):
                print("\n---普通聊天---\n")
                ans = ""
                for char in get_llm_answer_converse(self.agent_conversations, ans_model):
                    yield char
                    ans += char           
                self.agent_conversations.append({"role": "assistant", "content": ans})
                    
            elif tool.startswith("stock_agent"):
                ans = ""
                for char in self.comprehensive_analysis(question, model=ans_model):
                    yield char
                    ans += char
                self.agent_conversations.append({"role": "assistant", "content": ans})


if __name__ == "__main__":
    model = "gpt-4o-2024-08-06"
    stock_agent = StockAgent("stock_agent")

    question = "立讯精密这只股票怎么样？"
    for char in stock_agent.work_flow(question, tool_model="deepseek-chat",ans_model=model):
        print(char, end="", flush=True)
        
        
