import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import docx
import tempfile
import os

# ==========================================
# CẤU HÌNH TRANG & GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Trợ lý AI TGDV", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .main-title { color: #004B87; font-weight: 900; text-align: center; text-transform: uppercase; margin-bottom: 5px; font-size: 2.2rem; }
    .sub-title { text-align: center; color: #64748b; font-size: 1rem; margin-bottom: 30px; font-style: italic; }
    .stButton > button { background-color: #C8102E; color: white; font-weight: bold; border-radius: 8px; padding: 10px 20px; width: 100%; border: none; transition: 0.3s; }
    .stButton > button:hover { background-color: #a00c24; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(200,16,46,0.2); }
    .result-box { background-color: #ffffff; border-left: 5px solid #10b981; padding: 20px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); font-size: 1.05rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ---- GHI LƯỢT TRUY CẬP ----
if "da_ghi_truy_cap" not in st.session_state:
    try:
        _sb = create_client(
            "https://qqzsdxhqrdfvxnlurnyb.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFxenNkeGhxcmRmdnhubHVybnliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2MjY0NjAsImV4cCI6MjA5MTIwMjQ2MH0.H62F5zYEZ5l47fS4IdAE2JdRdI7inXQqWG0nvXhn2P8"
        )
        _sb.table("thong_ke_truy_cap").insert({"ten_app": "Trợ lý AI Tóm tắt"}).execute()
        st.session_state["da_ghi_truy_cap"] = True
    except Exception:
        pass

# ==========================================
# CẤU HÌNH API KEY (TỪ KÉT SẮT)
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color:#004B87;'>⚙️ CẤU HÌNH HỆ THỐNG</h3>", unsafe_allow_html=True)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ Trợ lý AI đã kết nối an toàn với Két sắt bí mật.")
        genai.configure(api_key=api_key) # Cấu hình luôn ở đây
    except Exception:
        api_key = None
        st.error("⚠️ Lỗi: Không tìm thấy chìa khóa API trong hệ thống!")
        
    st.markdown("---")
    st.markdown("💡 **Gợi ý sử dụng:**<br>1. Tải lên file Word (.docx) hoặc PDF (hỗ trợ cả bản Scan).<br>2. Chọn chế độ Xử lý và bấm Thực hiện.", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================
st.markdown("<h1 class='main-title'>🤖 TRỢ LÝ AI TÓM TẮT VĂN BẢN</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Giải pháp đọc và xử lý tài liệu thông minh dành cho Cán bộ, Chuyên viên</p>", unsafe_allow_html=True)

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("**📂 CÁCH 1: Tải lên file tài liệu**")
    file_tai_len = st.file_uploader("Hỗ trợ: PDF (bản Scan có dấu đỏ/chữ ký), Word (.docx), Text (.txt)", type=["pdf", "docx", "txt"])
    
    st.markdown("**📝 CÁCH 2: Dán văn bản thủ công**")
    van_ban_goc = st.text_area("", height=140, placeholder="Dán nội dung vào đây nếu không có file...")

with col2:
    st.markdown("**🎯 Chọn Yêu cầu Xử lý:**")
    che_do = st.radio(
        "AI sẽ giúp bạn làm gì?",
        ("📑 Tóm tắt siêu ngắn (Lấy ý cốt lõi trong 3-5 câu)", 
         "📋 Trích xuất Ý chính (Gạch đầu dòng các luận điểm)", 
         "🗺️ Lập Dàn ý chi tiết (Trình bày cấu trúc I, II, III...)")
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    nut_xu_ly = st.button("🚀 BẮT ĐẦU ĐỌC VÀ XỬ LÝ")

# ==========================================
# XỬ LÝ LOGIC AI (HỖ TRỢ VISION ĐỌC SCAN)
# ==========================================
if nut_xu_ly:
    if not api_key:
        st.error("⚠️ Hệ thống đang thiếu chìa khóa. Vui lòng kiểm tra lại thiết lập Secrets.")
    elif file_tai_len is None and not van_ban_goc.strip():
        st.warning("⚠️ Đồng chí chưa tải file lên hoặc chưa dán văn bản nào!")
    else:
        with st.spinner("🤖 Hệ thống đang chuẩn bị dữ liệu..."):
            
            hop_le = True
            file_duoc_upload_len_ai = None
            noidung_van_ban_goc = ""
            
            # 1. XỬ LÝ FILE NẾU CÓ TẢI LÊN
            if file_tai_len is not None:
                file_ext = file_tai_len.name.split('.')[-1].lower()
                
                # NẾU LÀ FILE PDF (SCAN HOẶC CHỮ) -> NÉM THẲNG CHO GOOGLE
                if file_ext == 'pdf':
                    st.info("🔎 Đang dùng Mắt thần AI để soi toàn bộ bản Scan PDF...")
                    try:
                        # Ghi tạm file ra ổ cứng máy chủ
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(file_tai_len.getvalue())
                            duong_dan_tam = tmp_file.name
                        
                        # Upload file trực tiếp lên kho chứa của Gemini
                        file_duoc_upload_len_ai = genai.upload_file(duong_dan_tam)
                        
                        # Xóa file tạm trên máy chủ cho nhẹ
                        os.remove(duong_dan_tam)
                    except Exception as e:
                        st.error(f"❌ Lỗi khi tải file PDF lên AI: {e}")
                        hop_le = False
                        
                # NẾU LÀ FILE WORD/TXT -> VẪN ĐỌC CHỮ NHƯ BÌNH THƯỜNG CHO NHANH
                elif file_ext == 'docx':
                    try:
                        doc = docx.Document(file_tai_len)
                        noidung_van_ban_goc = "\n".join([para.text for para in doc.paragraphs])
                        st.info("✅ Đã đọc xong dữ liệu từ file Word.")
                    except Exception as e:
                        st.error(f"❌ Lỗi khi đọc file Word: {e}")
                        hop_le = False
                elif file_ext == 'txt':
                    noidung_van_ban_goc = file_tai_len.getvalue().decode("utf-8")
                    st.info("✅ Đã đọc xong dữ liệu Text.")
            
            # Nếu không có file thì lấy chữ dán ở ô
            else:
                noidung_van_ban_goc = van_ban_goc

            # 2. BẮT ĐẦU YÊU CẦU AI PHÂN TÍCH VÀ NHẢ CHỮ LIVE
            if hop_le:
                try:
                    # Gọi Model 1.5 Flash VIP
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Chuẩn bị lời dặn dò (Prompt)
                    if "Tóm tắt" in che_do:
                        loi_dan = "Bạn là một chuyên viên tổng hợp tài liệu chuyên nghiệp của cơ quan Đảng. Hãy đọc tài liệu đính kèm và tóm tắt lại những nội dung cốt lõi nhất một cách cực kỳ ngắn gọn, súc tích trong khoảng 3 đến 5 câu. Giữ văn phong trang trọng, nghiêm túc."
                    elif "Ý chính" in che_do:
                        loi_dan = "Bạn là một chuyên viên tổng hợp tài liệu chuyên nghiệp. Hãy đọc tài liệu đính kèm và trích xuất ra các luận điểm, ý chính quan trọng nhất. Trình bày dưới dạng các gạch đầu dòng rõ ràng, dễ hiểu. Bỏ qua các từ ngữ rườm rà."
                    else:
                        loi_dan = "Bạn là một thư ký xuất sắc. Hãy đọc tài liệu đính kèm và lập một dàn ý chi tiết theo cấu trúc phân cấp (I, II, III... rồi đến 1, 2, 3...). Dàn ý phải bao quát toàn bộ nội dung của văn bản, các tiêu đề phải ngắn gọn, toát lên được ý chính của từng phần."

                    # Gom nguyên liệu gửi cho AI (Bao gồm File Scan PDF và Lời dặn dò)
                    noi_dung_gui_di = [loi_dan]
                    if file_duoc_upload_len_ai:
                        noi_dung_gui_di.append(file_duoc_upload_len_ai)
                    if noidung_van_ban_goc:
                        noi_dung_gui_di.append(f"\n\nVĂN BẢN:\n{noidung_van_ban_goc}")

                    st.markdown("---")
                    st.markdown("<h3 style='color: #10b981;'>✨ KẾT QUẢ XỬ LÝ TỪ AI:</h3>", unsafe_allow_html=True)
                    
                    # Tạo khung trống để chữ chạy ra từ từ
                    khung_ket_qua = st.empty()
                    van_ban_hoan_thanh = ""
                    
                    # GỌI API CHẾ ĐỘ STREAMING
                    response = model.generate_content(noi_dung_gui_di, stream=True)
                    
                    for chunk in response:
                        van_ban_hoan_thanh += chunk.text
                        khung_ket_qua.markdown(f"<div class='result-box'>{van_ban_hoan_thanh}</div>", unsafe_allow_html=True)
                    
                    # Dọn dẹp: Xóa file PDF khỏi kho Google sau khi đọc xong để bảo mật
                    if file_duoc_upload_len_ai:
                        try:
                            genai.delete_file(file_duoc_upload_len_ai.name)
                        except Exception:
                            pass
                        
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Có lỗi mạng xảy ra trong quá trình kết nối với AI. (Chi tiết: {error_msg})")

# Footer
st.markdown("<br><hr><p style='text-align:center; color:#94a3b8; font-size: 0.85rem;'>Phát triển bởi Ngạc Văn Tuấn - Tích hợp AI Google Gemini 1.5</p>", unsafe_allow_html=True)
