# PDF QU⚡CK - Fast & Free Online PDF Tools

**PDF QU⚡CK** is a lightweight, blazing-fast web application designed to help you manage your PDF documents securely. No registrations, no watermarks, and no limits.

[Visit PDF QU⚡CK](https://pdfquick.online)

## ✨ Features
- **Merge & Split:** Combine multiple PDFs or extract specific pages.
- **Universal Conversion:** Convert Office documents (Word, Excel, PPT) and Images to PDF, or extract text and tables from PDFs.
- **Security:** Add passwords, watermarks, or unlock your PDF files.
- **AI-Powered Analysis:** Generate executive summaries, extract key points, or translate documents seamlessly using Llama 3 (powered by Groq).
- **Privacy First:** Files are processed entirely in memory or temporary directories and instantly deleted after the task is completed.

## 🛠️ Tech Stack
- **Frontend:** Vanilla HTML5, CSS3 (Custom Dark/Light mode), and JavaScript (with i18n support for ES/EN/FR/PT).
- **Backend:** Flask (Python) & Gunicorn.
- **PDF/Office Engine:** PyMuPDF, pdfplumber, pdf2docx, ReportLab, and LibreOffice Headless.
- **AI Engine:** Groq API (Llama-3.3-70b).
- **Deployment:** Render (Dockerized Environment) + Cloudflare (DNS, Caching & Security).

## 🚀 Local Setup

1. Clone the repository:
   ```bash
   git clone [https://github.com/luisjoselares/pdf-quick.git](https://github.com/luisjoselares/pdf-quick.git)
   cd pdf-quick
Install the required dependencies (Make sure you have Python 3.11+ installed):


pip install -r requirements.txt
Set up your Environment Variables:
Create a .env file in the root directory and add your Groq API key:

Fragmento de código
GROQ_API_KEY=your_groq_api_key_here
Run the application:
python main.py

The app will be available at http://localhost:5000 or the port specified in your environment.

(Note: The Office-to-PDF conversion feature requires LibreOffice to be installed on your local machine or container to work properly).
### 5. Contribuciones y Soporte

```markdown
## ☕ Support the Project
If this tool saved you time, consider supporting the development:
- [Buy me a coffee on Ko-fi](https://ko-fi.com/ldownloader)
- **Binance Pay ID:** 422864557
