# 📚 RAG Document Assistant

A simple AI tool to upload PDF files and ask questions about their content. It uses **Retrieval-Augmented Generation (RAG)** to give accurate answers based only on your document.

---

## 🌟 What This App Does

1. **Reads PDFs**: Upload any PDF book or document.
2. **Splits & Stores**: Breaks text into smaller chunks and converts them into smart vector embeddings using **Chroma DB**.
3. **Smart Search**: Finds the most relevant parts of the document when you ask a question.
4. **Accurate AI Answers**: Generates answers using AI (OpenAI / Mistral) based strictly on your PDF content.

---

## 🚀 How to Run

### 1. Create & Activate Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Add API Keys
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

### 4. Start the App

#### Web Interface (Streamlit):
```bash
streamlit run app.py
```

#### Terminal / CLI:
```bash
python main.py
```

---

## 📁 Project Files

* `app.py` - Web app interface built with Streamlit.
* `main.py` - Interactive command-line chat tool.
* `create_database.py` - Script to process PDFs into the vector database.
* `chroma_db/` - Folder storing your document embeddings.
* `document loaders/` - Folder containing sample PDFs.
