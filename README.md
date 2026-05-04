# 🎙️ Hệ Thống Kiểm Tra Phát Âm PRO (Trung & Anh)

Đây là ứng dụng Web hỗ trợ luyện tập và chấm điểm phát âm tiếng Trung (chuẩn HSK 3.0) và tiếng Anh (trình độ B1) dựa trên trí tuệ nhân tạo. Ứng dụng mô phỏng các phần mềm học ngôn ngữ chuyên nghiệp với khả năng phân tích lỗi sai chi tiết đến từng âm tiết/thanh điệu.

## ✨ Tính Năng Nổi Bật

- **🔍 Soi lỗi chính xác:** Phát hiện sai âm, sai thanh điệu (tiếng Trung) bằng Pinyin, sử dụng OpenAI Whisper.
- **🗣️ Giọng đọc AI bản xứ:** Tích hợp Microsoft Edge TTS, hỗ trợ nghe mẫu ở tốc độ thường và chậm (Nữ/Nam).
- **📝 Đa chế độ nhập liệu:** Nhập bằng tay, đọc bằng mic, hoặc nhập hàng loạt qua file Excel (`.xlsx` / `.csv`).
- **🗂️ Từ điển & Góp ý tùy biến:** Tự động phân tích Hán Việt, dịch nghĩa câu (Google Translate), đưa ra lời khuyên sửa lỗi dựa trên file `.csv` có thể mở rộng.
- **🧹 Tối ưu hệ thống:** Quản lý cache âm thanh thông minh, tự động dọn rác qua mỗi phiên làm việc.

## 🛠️ Cài Đặt

**1. Yêu cầu hệ thống:**
- Python 3.8 trở lên.
- Có kết nối Internet (để tải thư viện và gọi AI Voice/Dịch thuật).

**2. Tạo môi trường ảo (Khuyến nghị):**

python -m venv venv
# Windows:
.\venv\Scripts\activate
# MacOS/Linux:
source venv/bin/activate

**3. Cài đặt thư viện:**
Tạo file requirements.txt và chạy lệnh cài đặt:Bashpip install -r requirements.txt
(Danh sách các thư viện cần thiết trong requirements.txt bao gồm: streamlit, streamlit-mic-recorder, openai-whisper, pypinyin, hanziconv, deep-translator, pandas, openpyxl, edge-tts, asyncio)📂 Cấu Trúc Thư Mục ChuẩnĐể ứng dụng hoạt động trơn tru nhất với âm thanh phản hồi, hãy thiết lập thư mục theo cấu trúc sau:Plaintext├── app.py                # File mã nguồn chính
├── requirements.txt      # Danh sách thư viện
├── feedback.csv          # File cấu hình lời khuyên sửa lỗi
├── vocab.csv             # File từ điển tự định nghĩa (Hán Việt & Nghĩa)
├── sounds/               # Thư mục chứa hiệu ứng âm thanh (Bạn tự tải MP3)
│   ├── perfect.mp3       # Hiệu ứng khi đạt 100 điểm
│   ├── good.mp3          # Hiệu ứng trên 50 điểm
│   └── bad.mp3           # Hiệu ứng dưới 50 điểm
└── tts_cache/            # (App tự tạo) Nơi lưu trữ cache giọng đọc AI

📝 Định Dạng File Dữ Liệu
1. File feedback.csv: 
error_code,message
tone_1,Thanh 1 (Ngang): Cố gắng giữ giọng cao và đều.
wrong_pinyin,Bạn phát âm sai vần hoặc phụ âm.
english_wrong,Chú ý phát âm rõ ending sounds nhé!
missing,Bạn đã đọc thiếu từ này!
2. File vocab.csv: 
word,hanviet,meaning
你,Nễ,Bạn / Mày / Ngài
好,Hảo,Tốt / Khỏe / Hay
3. File Excel Đề Thi (bode.xlsx)
Yêu cầu bắt buộc: Dòng đầu tiên (Header) phải có chứa cột tên là Cau_Hoi.
Cau_Hoi
你好
I should study every day

🚀 Cách Chạy Ứng Dụng

Mở Terminal tại thư mục chứa dự án và chạy lệnh: streamlit run app.py
Trình duyệt sẽ tự động mở ứng dụng tại địa chỉ http://localhost:8501.

Phát triển bởi Hoàng Văn Thạch - Phục vụ mục tiêu chinh phục HSK 3.0 & B1.

BY THACHDEV