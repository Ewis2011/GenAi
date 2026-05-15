# 🗺️ Cartographer Assistant

AI co-pilot for map design and Egyptian GIS standards.

## Features

- **Vision Analysis**: Upload map screenshots for critique.
- **Multi-Provider**: Use Gemini or OpenRouter (Claude/GPT).
  ![Alternative Text](/imgs/1.png)
- **Synchronized Export**: Download full chat history as Markdown.
  ![Alternative Text](/imgs/4.png)
- **Quick Prompts**: One-click Egypt GIS common tasks.
  ![Alternative Text](/imgs/3.png)

## 🛠️ Installation & Setup

### 1. Clone the Repository

- git clone -b AI https://github.com/Ewis2011/GenAi.git
- cd GenAi

### 2. Install Dependencies

pip install -r requirements.txt

### 3. Configure API Keys

Create a file named .env in the project root and add your keys:
'GOOGLE_API_KEY' or 'OPENROUTER_API_KEY'

### 4. Run the Application

```bash
streamlit run app.py
```
