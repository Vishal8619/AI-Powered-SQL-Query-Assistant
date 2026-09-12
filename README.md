# 🤖 AI Data Assistant — Text-to-SQL Chatbot

An AI-powered chatbot that converts plain English questions 
into SQL queries and returns results with interactive charts.

## ✨ Features
- 💬 Natural language to SQL using LLaMA 3.3 70B
- 🔧 Auto error detection and self-healing SQL
- 📁 Supports SQLite, CSV, Excel and SQL files
- 📊 On-demand interactive charts
- 🧠 Conversation memory for follow-up questions
- 🔍 Auto data profiling on file upload
- 🔐 User authentication with bcrypt encryption
- 💾 Persistent chat history per user

## 🛠️ Tech Stack
| Technology | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web interface |
| Groq API | LLM provider |
| LLaMA 3.3 70B | Language model |
| SQLite | Database |
| Plotly | Charts |
| Pandas | Data processing |
| Bcrypt | Password encryption |

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-sql-chatbot.git
cd ai-sql-chatbot
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API key
Create a `.env` file:

GROQ_API_KEY=your_groq_api_key_here

Get your free API key from: https://console.groq.com

### 5. Run the app
```bash
streamlit run app.py
```

## 💡 Example Questions
- "How many customers are there?"
- "Show top 5 products by revenue"
- "Which city has the most orders?"
- "Show me a bar chart of sales by category"
- "Now filter only Electronics"

## 📁 Project Structure
ai-sql-chatbot/
├── app.py # Main Streamlit UI
├── llm.py # LLM integration
├── db.py # Database handler
├── charts.py # Chart generator
├── analyzer.py # Data profiling
├── history.py # Chat history
├── auth.py # Authentication
├── sample_db.py # Sample database
└── requirements.txt


## 🔐 Environment Variables
| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |

## 📄 License
MIT License
