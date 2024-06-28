from openai import OpenAI
from tools.code_interpreter import *
import time  
from functools import wraps  
import pandas as pd  
from selenium.webdriver.common.by import By  
from tools.json_tool import *
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

class OllamaAgent:
    def __init__(self, model):
        self.model = model
        self.analyze_sentiment_prompt = self.get_prompt("prompt/stock_analysis_prompt.txt")
        self.driver = self.get_driver()
        self.get_stock_name_prompt = self.get_prompt("prompt/get_stock_name_prompt.txt")
        self.system_prompt = "你是股票分析专家。"
        self.conversations = [{"role": "system", "content": self.system_prompt}]
        
    def retry(retry_times=3, delay=2):
        def decorator(func):
            @wraps(func)  
            def wrapper(*args, **kwargs):
                for i in range(retry_times):  
                    try:
                        return func(*args, **kwargs)  
                    except Exception as e:
                        print(f"出错了,错误信息:{e},正在尝试第{i+1}次重新执行")  
                        time.sleep(delay)  
                print("达到最大尝试次数,仍然失败")  
                return None
            return wrapper
        return decorator

    def get_prompt(self, path):
        with open(path, 'r', encoding="utf-8") as file:
            prompt = file.read()
        return prompt
    
    def get_driver(self):
        options = Options()  
        options.add_argument('user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"')
        options.add_argument("--headless")  
        driver = webdriver.Chrome(options=options)  
        return driver
    
    @retry(retry_times=3, delay=2)  
    def get_guba_comments(self, driver, stock, page=1):
        url = "https://guba.eastmoney.com/list,{}_{}.html".format(stock, page)  
        print(url)
        driver.get(url)  # 打开网页
        comments_df = pd.DataFrame()  # 创建空的DataFrame
        for i in range(70):  # 循环70次
            try:
                element_text = driver.find_elements(By.XPATH, f'/html/body/div[1]/div[3]/div[1]/div[1]/div/ul/li[1]/table/tbody/tr[{i+1}]')[0].text  # 获取元素文本
                parts = element_text.split('\n')  
                if len(parts) == 5:  
                    read, comment_num, title, author, update_time = parts  
                    df = pd.DataFrame([[read, comment_num, title, author, update_time]], columns=[
                                    'read', 'comment_num', 'title', 'author', 'update_time'])  
                    comments_df = pd.concat([comments_df, df], axis=0)  
                else:
                    print(f"第{i+1}行数据格式不符，跳过")  
            except Exception as e:
                print(f"获取第{i+1}行数据时出错: {e}")  
        return comments_df

    def get_comment_list(self, driver, stock, page):
        print("开始获取评论....")
        comments_df = self.get_guba_comments(driver, stock, page)  
        if comments_df is not None:  
            comment_list = comments_df['title'].tolist()  
            # 计算评论标题的总字数
            total_words = sum(len(comment) for comment in comment_list) 
            print(f'总字数:{total_words}')
            return comment_list
        else:
            print("获取评论失败")  
            return []

    def get_ollama_yield(self, messages, model):
        client = OpenAI(
            base_url = 'http://localhost:11434/v1',
            api_key='ollama', 
        )

        response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
        )
        for char in response:
            yield char.choices[0].delta.content

    def get_stock_index_by_stockname(self, stock_name):
        stock_indexes = pd.read_excel("free_agent/stock_agent/stock_indexes.xlsx", index_col=False)
        stock_indexes["证券名称"] = stock_indexes["证券名称"].str.replace(" ", "")
        stock_indexes["indexes"] = stock_indexes["证券代码"].str[-2:] + stock_indexes["证券代码"].str[:6] 
        stock_index = stock_indexes.loc[stock_indexes["证券名称"].str.contains(stock_name), "indexes"].values[0]
        return stock_index

    # 提取股票代码
    def get_stock_index(self, question):
        get_stock_name_prompt = self.get_stock_name_prompt.format(question=question)
        self.conversations.append({"role": "user", "content": get_stock_name_prompt})
        ans = ""
        for char in self.get_ollama_yield(self.conversations, self.model):
            ans += char
            print(char, end="", flush=True)
        print("\n\n")
        stock_name = get_json(ans)["stock_name"]
        stock_index = self.get_stock_index_by_stockname(stock_name)
        return stock_index
    
    def analyze_sentiment(self, question, page=1):
        stock_index = self.get_stock_index(question)
        comment_list = self.get_comment_list(self.driver, stock_index, page=page)
        prompt = self.analyze_sentiment_prompt.format(question=question, comment_list=comment_list)
        self.conversations.append({"role": "user", "content": prompt})
        ans = ""
        for char in self.get_ollama_yield(self.conversations, self.model):
            print(char, end="", flush=True)
            ans += char
        print(f"\n\n总字数：{len(ans)}")
        sent = get_json(ans)["judge"]
        print(f"情感判断：{sent}")
        return ans
    
    def analyze_sentiment_yield(self, question, page=1):
        stock_index = self.get_stock_index(question)
        comment_list = self.get_comment_list(self.driver, stock_index, page=page)
        prompt = self.analyze_sentiment_prompt.format(question=question, comment_list=comment_list)
        self.conversations.append({"role": "user", "content": prompt})
        for char in self.get_ollama_yield(self.conversations, self.model):
            print(char, end="", flush=True)
            yield char

    