import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import PyPDF2
import docx
import io

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
    except Exception:
        api_key = None
        st.error("⚠️ Lỗi: Không tìm thấy chìa khóa API trong hệ thống!")
        
    st.markdown("---")
    st.markdown("💡 **Gợi ý sử dụng:**<br>1. Tải lên file Word (.docx) hoặc PDF.<br>2. Hoặc Copy nội dung dán vào ô.<br>3. Chọn chế độ Tóm tắt và bấm Thực hiện.", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================
st.markdown("<h1 class='main-title'>🤖 TRỢ LÝ AI TÓM TẮT VĂN BẢN</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Giải pháp đọc và xử lý tài liệu thông minh dành cho Cán bộ, Chuyên viên</p>", unsafe_allow_html=True)

# ==========================================
# HÀM ĐỌC NỘI DUNG TỪ FILE
# ==========================================
def doc_noi_dung_file(file):
    text = ""
    try:
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif file.name.endswith('.docx'):
            doc = docx.Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif file.name.endswith('.txt'):
            text = file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
    return text

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("**📂 CÁCH 1: Tải lên file tài liệu (Tối ưu nhất)**")
    file_tai_len = st.file_uploader("Hỗ trợ định dạng: Word (.docx), PDF (.pdf), Text (.txt)", type=["pdf", "docx", "txt"])
    
    st.markdown("**📝 CÁCH 2: Dán văn bản thủ công**")
    van_ban_goc = st.text_area("", height=180, placeholder="Nếu không có file, hãy dán nội dung vào đây...")

with col2:
    st.markdown("**🎯 Chọn Yêu cầu Xử lý:**")
    che_do = st.radio(
        "AI sẽ giúp bạn làm gì?",
        ("📑 Tóm tắt siêu ngắn (Lấy ý cốt lõi trong 3-5 câu)", 
         "📋 Trích xuất Ý chính (Gạch đầu dòng các luận điểm)", 
         "🗺️ Lập Dàn ý chi tiết (Trình bày cấu trúc I, II, III...)")
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    nut_xu_ly = st.button("🚀 BẮT ĐẦU ĐỌC VÀ XỬ LÝ")

# ==========================================
# XỬ LÝ LOGIC AI
# ==========================================
if nut_xu_ly:
    if not api_key:
        st.error("⚠️ Hệ thống đang thiếu chìa khóa. Vui lòng kiểm tra lại thiết lập Secrets.")
    else:
        # Lấy nội dung: Ưu tiên file tải lên, nếu không có thì lấy text ở ô dán
        noidung_can_xu_ly = ""
        if file_tai_len is not None:
            with st.spinner("⏳ Đang trích xuất văn bản từ file..."):
                noidung_can_xu_ly = doc_noi_dung_file(file_tai_len)
        else:
            noidung_can_xu_ly = van_ban_goc
            
        if not noidung_can_xu_ly.strip():
            st.warning("⚠️ Bạn chưa tải file lên hoặc chưa dán văn bản nào!")
        else:
            with st.spinner("🤖 Trợ lý AI đang phân tích dữ liệu..."):
                try:
                    genai.configure(api_key=api_key)
                    model_name = 'gemini-pro' 
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            model_name = m.name
                            if 'flash' in model_name: 
                                break 
                    
                    model = genai.GenerativeModel(model_name)
                    
                    if "Tóm tắt" in che_do:
                        prompt = f"Bạn là một chuyên viên tổng hợp tài liệu chuyên nghiệp của cơ quan Đảng. Hãy đọc đoạn văn bản sau và tóm tắt lại những nội dung cốt lõi nhất một cách cực kỳ ngắn gọn, súc tích trong khoảng 3 đến 5 câu. Giữ văn phong trang trọng, nghiêm túc.\n\nVĂN BẢN CẦN TÓM TẮT:\n{noidung_can_xu_ly}"
                    elif "Ý chính" in che_do:
                        prompt = f"Bạn là một chuyên viên tổng hợp tài liệu chuyên nghiệp. Hãy đọc đoạn văn sau và trích xuất ra các luận điểm, ý chính quan trọng nhất. Trình bày dưới dạng các gạch đầu dòng rõ ràng, dễ hiểu. Bỏ qua các từ ngữ rườm rà.\n\nVĂN BẢN CẦN TRÍCH XUẤT:\n{noidung_can_xu_ly}"
                    else:
                        prompt = f"Bạn là một thư ký xuất sắc. Hãy đọc tài liệu sau và lập một dàn ý chi tiết theo cấu trúc phân cấp (I, II, III... rồi đến 1, 2, 3...). Dàn ý phải bao quát toàn bộ nội dung của văn bản, các tiêu đề phải ngắn gọn, toát lên được ý chính của từng phần.\n\nVĂN BẢN CẦN LẬP DÀN Ý:\n{noidung_can_xu_ly}"
                    
                    response = model.generate_content(prompt)
                    
                    st.markdown("---")
                    st.markdown("<h3 style='color: #10b981;'>✨ KẾT QUẢ XỬ LÝ TỪ AI:</h3>", unsafe_allow_html=True)
                    st.markdown(f"<div class='result-box'>{response.text}</div>", unsafe_allow_html=True)
                    
               except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower():
                        st.warning("⚠️ Lỗi quá tải: Tài liệu của đồng chí tải lên quá dài (vượt quá giới hạn đọc 200 trang/lần) hoặc hệ thống đang có nhiều người dùng. Vui lòng cắt bớt độ dài tài liệu hoặc đợi 1 phút sau rồi bấm lại nhé!")
                    else:
                        st.error(f"❌ Có lỗi mạng xảy ra trong quá trình kết nối với AI. (Chi tiết: {error_msg})")

# Footer
st.markdown("<br><hr><p style='text-align:center; color:#94a3b8; font-size: 0.85rem;'>Phát triển bởi Ngạc Văn Tuấn - Tích hợp trí tuệ nhân tạo Google Gemini</p>", unsafe_allow_html=True)
