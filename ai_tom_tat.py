import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

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

# ---- GHI LƯỢT TRUY CẬP (SUPABASE) ----
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
# ---- HẾT GHI LƯỢT TRUY CẬP ----

# ==========================================
# HEADER
# ==========================================
st.markdown("<h1 class='main-title'>🤖 TRỢ LÝ AI TÓM TẮT VĂN BẢN</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Giải pháp xử lý tài liệu thông minh dành cho Cán bộ, Chuyên viên</p>", unsafe_allow_html=True)

# ==========================================
# CẤU HÌNH API KEY (Lấy từ Két sắt bảo mật)
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color:#004B87;'>⚙️ CẤU HÌNH HỆ THỐNG</h3>", unsafe_allow_html=True)
    
    # Ra lệnh cho hệ thống chui vào Két sắt (st.secrets) để lấy chìa khóa
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ Trợ lý AI đã được kết nối an toàn với bộ não Google Gemini.")
    except Exception:
        api_key = None
        st.error("⚠️ Lỗi: Không tìm thấy API Key trong Két sắt bí mật!")
        
    st.markdown("---")
    st.markdown("💡 **Gợi ý sử dụng:**<br>- Copy nội dung Đề cương, Báo cáo dài dán vào ô bên phải.<br>- Chọn chế độ Tóm tắt và bấm nút Thực hiện.", unsafe_allow_html=True)

# ==========================================
# XỬ LÝ LOGIC AI
# ==========================================
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("**📝 Dán nội dung văn bản cần xử lý vào đây:**")
    van_ban_goc = st.text_area("", height=350, placeholder="Ví dụ: Dán nội dung Báo cáo chính trị, Đề cương tuyên truyền, hoặc bất kỳ văn bản dài nào vào đây...")

with col2:
    st.markdown("**🎯 Chọn Yêu cầu Xử lý:**")
    che_do = st.radio(
        "AI sẽ giúp bạn làm gì?",
        ("📑 Tóm tắt siêu ngắn (Lấy ý cốt lõi trong 3-5 câu)", 
         "📋 Trích xuất Ý chính (Gạch đầu dòng các luận điểm)", 
         "🗺️ Lập Dàn ý chi tiết (Trình bày cấu trúc I, II, III...)")
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    nut_xu_ly = st.button("🚀 BẮT ĐẦU XỬ LÝ VĂN BẢN")

# ==========================================
# GỌI AI VÀ HIỂN THỊ KẾT QUẢ
# ==========================================
if nut_xu_ly:
    if not api_key:
        st.error("⚠️ Lỗi hệ thống: Không tìm thấy Google Gemini API Key!")
    elif not van_ban_goc.strip():
        st.warning("⚠️ Bạn chưa nhập văn bản nào để tôi xử lý cả!")
    else:
        with st.spinner("🤖 Trợ lý AI đang đọc và phân tích tài liệu... (Thường mất khoảng 3-5 giây)"):
            try:
                # Kích hoạt não bộ Gemini
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash') # Model siêu tốc độ
                
                # Tạo câu lệnh (Prompt) ép AI làm theo đúng format
                if "Tóm tắt" in che_do:
                    prompt = f"Bạn là một chuyên viên tổng hợp tài liệu chuyên nghiệp của cơ quan Đảng. Hãy đọc đoạn văn bản sau và tóm tắt lại những nội dung cốt lõi nhất một cách cực kỳ ngắn gọn, súc tích trong khoảng 3 đến 5 câu. Giữ văn phong trang trọng, nghiêm túc.\n\nVĂN BẢN CẦN TÓM TẮT:\n{van_ban_goc}"
                elif "Ý chính" in che_do:
                    prompt = f"Bạn là một chuyên viên tổng hợp tài liệu chuyên nghiệp. Hãy đọc đoạn văn sau và trích xuất ra các luận điểm, ý chính quan trọng nhất. Trình bày dưới dạng các gạch đầu dòng rõ ràng, dễ hiểu. Bỏ qua các từ ngữ rườm rà.\n\nVĂN BẢN CẦN TRÍCH XUẤT:\n{van_ban_goc}"
                else:
                    prompt = f"Bạn là một thư ký xuất sắc. Hãy đọc tài liệu sau và lập một dàn ý chi tiết theo cấu trúc phân cấp (I, II, III... rồi đến 1, 2, 3...). Dàn ý phải bao quát toàn bộ nội dung của văn bản, các tiêu đề phải ngắn gọn, toát lên được ý chính của từng phần.\n\nVĂN BẢN CẦN LẬP DÀN Ý:\n{van_ban_goc}"
                
                # Bắn yêu cầu cho AI
                response = model.generate_content(prompt)
                
                # Hiển thị kết quả
                st.markdown("---")
                st.markdown("<h3 style='color: #10b981;'>✨ KẾT QUẢ XỬ LÝ:</h3>", unsafe_allow_html=True)
                st.markdown(f"<div class='result-box'>{response.text}</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra trong quá trình kết nối với AI. Vui lòng thử lại sau. (Lỗi: {e})")

# Footer
st.markdown("<br><hr><p style='text-align:center; color:#94a3b8; font-size: 0.85rem;'>Phát triển bởi Ngạc Văn Tuấn - Tích hợp trí tuệ nhân tạo Google Gemini 1.5</p>", unsafe_allow_html=True)
