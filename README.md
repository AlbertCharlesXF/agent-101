

# Agent-101

**Agent-101** is a modular Python framework and collection of examples for building and experimenting with advanced AI agent architectures. It provides ready-to-use implementations of cognitive workflows like Deep Thinking and Chain-of-Thought (CoT), alongside domain-specific agents, autonomous code execution with self-correction, and a real-time web chat interface.

## ✨ Features

- **🧠 Deep Thinking Agent**: Implements iterative reasoning, self-reflection, and step-by-step task elaboration. Automatically decomposes complex queries into actionable plans and generates detailed markdown outputs.
- **🔗 Chain-of-Thought (CoT) Workflow**: Supports dynamic prompt generation, multi-step reasoning loops, and automatic result optimization to improve response accuracy and coherence.
- **📊 Domain-Specific Agents**: Includes a fully featured `StockAgent` that integrates web search (Bing, arXiv, CNKI), PDF extraction, data analysis, and modular financial scoring.
- **💻 Autonomous Code Interpreter**: Generates Python code, executes it in a controlled environment, catches errors, and autonomously iterates on fixes until success. Exports working scripts to Jupyter notebooks.
- **🌐 Real-Time Web Demo**: A lightweight Flask + Socket.IO chat interface with streaming responses, markdown rendering, and support for multiple LLM backends (Ollama, OpenAI, Anthropic, etc.).

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AlbertCharlesXF/agent-101.git
   cd agent-101
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-socketio flask-cors python-dotenv pandas openai anthropic ollama requests beautifulsoup4
   ```
   *(Note: Exact dependencies may vary based on your chosen LLM providers and additional libraries referenced in the `tools/` directory.)*

4. **Configure Environment Variables**
   Create a `.env` file in the project root and add your API keys & proxy settings:
   ```env
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   SNOWBALL_TOKEN=your_token_here
   HTTP_PROXY=http://your-proxy:port  # Optional
   HTTPS_PROXY=http://your-proxy:port
   ```

## 🚀 Usage

### Running the Web Chat Interface
The repository includes a pre-built web demo for real-time agent interactions:
```bash
cd agent_webpage_demo
python app.py
```
Open your browser and navigate to `http://localhost:3000`. Select your preferred model (e.g., `llama3`, `gemma2`, `qwen2`) and start chatting. Responses stream in real-time with full Markdown and code block rendering.

### Using the Deep Thinking Agent
```python
from deep_thinking_agent import DeepThinkingAgent

# Initialize with your preferred models
agent = DeepThinkingAgent(
    main_model="gpt-4o",
    tool_model="claude-3-sonnet",
    flash_model="llama-3.1-8b"
)

# Run the full workflow (deep thinking + reflection + elaboration)
question = "How to build a scalable real-time data pipeline?"
for chunk in agent.work_flow(question):
    print(chunk, end="", flush=True)
```

### Using the Chain-of-Thought Agent
```python
from free_agent.chain_of_thoughts import CoTAgent

cot = CoTAgent(model="gpt-4o", max_iter=5, use_default=True)
response = cot.get_cot_answer("Explain quantum computing in simple terms.")
```

### Running the Stock Analysis Agent
```python
from stock_ana_agent import StockAgent

agent = StockAgent("financial_analyst", model="gpt-4o")
question = "立讯精密这只股票怎么样？"
for chunk in agent.work_flow(question, tool_model="deepseek-chat", ans_model="gpt-4o"):
    print(chunk, end="", flush=True)
```

## 📁 Project Structure
```
agent-101/
├── deep_thinking_agent.py      # Core deep reasoning & reflection workflow
├── stock_ana_agent.py          # Domain-specific stock analysis agent
├── free_agent/
│   ├── chain_of_thoughts.py    # CoT implementation & prompt routing
│   └── prompts/                # Prompt templates for CoT & ToT
├── agent_webpage_demo/
│   ├── app.py                  # Flask + SocketIO backend
│   ├── templates/              # Frontend HTML/CSS/JS
│   └── tools/                  # Web-specific utilities
├── prompts/                    # Deep agent prompt templates
└── tools/                      # Shared utilities (LLM APIs, code interpreter, JSON parser, etc.)
```

## 🔧 Customization & Extensions
- **LLM Providers**: Modify `tools/llm_api.py` to support additional endpoints, custom inference servers, or different API formats.
- **Tool Integration**: Add new capabilities by extending the `tools/` directory (e.g., database connectors, API scrapers, custom file handlers).
- **Prompt Engineering**: All prompts are externalized in `.py` files under `prompts/` and `free_agent/prompts/` for easy iteration and A/B testing.

## 📝 Notes
- The codebase contains Chinese comments and documentation. Adjust language settings in prompt templates as needed.
- Ensure your LLM endpoints support streaming if you want real-time chunked output in scripts.
- The built-in code interpreter runs locally; always sandbox untrusted inputs in production environments.

## 📄 License
This project is open-source. Please refer to the `LICENSE` file for details.
