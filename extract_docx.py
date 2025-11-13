# 提取Word文档内容
# 需要安装python-docx库
from docx import Document
import os

def extract_docx_text(docx_path):
    doc = Document(docx_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

if __name__ == "__main__":
    docx_file = "量化投研 Web 平台大模型 Prompt-3.docx"
    if os.path.exists(docx_file):
        text = extract_docx_text(docx_file)
        with open("docx_extracted.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("内容已提取到 docx_extracted.txt")
    else:
        print("未找到Word文档")
