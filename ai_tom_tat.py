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
# CẤU HÌNH API KEY TỪ KÉT SẮT
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color:#004B87;'>⚙️ CẤU HÌNH HỆ THỐNG</h3>", unsafe_allow_html=True)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        st.success("✅ Đã kết nối Chìa khóa VIP an toàn.")
        st.info("🚀 Cấu hình: Gemini 1.5 Flash (Hỗ trợ File Mắt thần).")
    except Exception:
        api_key = None
        st.error("⚠️ Lỗi: Không tìm thấy chìa khóa API trong Két sắt!")

# ==========================================
# HEADER VÀ GIAO DIỆN CHÍNH
# ==========================================
st.markdown("<h1 class='main-title'>🤖 TRỢ LÝ AI TÓM TẮT VĂN BẢN</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Giải pháp đọc và xử lý tài liệu thông minh dành cho Cán bộ, Chuyên viên</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("**📂 CÁCH 1: Tải lên file tài liệu (Hỗ trợ Mắt thần)**")
    file_tai_len = st.file_uploader("Hỗ trợ: PDF (kể cả bản Scan ảnh), Word (.docx), Text (.txt)", type=["pdf", "docx", "txt"])
    
    st.markdown("**📝 CÁCH 2: Dán văn bản thủ công**")
    van_ban_goc = st.text_area("", height=120, placeholder="Dán nội dung vào đây nếu không có file...")

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
# LOGIC XỬ LÝ AI
# ==========================================
if nut_xu_ly:
    if not api_key:
        st.error("⚠️ Hệ thống đang thiếu chìa khóa VIP.")
    elif file_tai_len is None and not van_ban_goc.strip():
        st.warning("⚠️ Đồng chí chưa cung cấp file hay văn bản nào!")
    else:
        with st.spinner("🤖 Trợ lý AI đang thu thập dữ liệu..."):
            hop_le = True
            file_duoc_upload_len_ai = None
            noidung_van_ban_goc = ""
            
            # --- XỬ LÝ FILE ---
            if file_tai_len is not None:
                file_ext = file_tai_len.name.split('.')[-1].lower()
                
                # NẾU LÀ PDF: NÉM LÊN CHO MẮT THẦN ĐỌC SCAN
                if file_ext == 'pdf':
                    st.info("🔎 Đang nạp file PDF vào hệ thống Mắt thần Google...")
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(file_tai_len.getvalue())
                            duong_dan_tam = tmp_file.name
                        
                        file_duoc_upload_len_ai = genai.upload_file(duong_dan_tam)
                        os.remove(duong_dan_tam)
                    except Exception as e:
                        st.error(f"❌ Lỗi tải file lên máy chủ Google: {e}")
                        hop_le = False
                        
                # NẾU LÀ WORD: ĐỌC CHỮ CHO NHANH
                elif file_ext == 'docx':
                    try:
                        doc = docx.Document(file_tai_len)
                        noidung_van_ban_goc = "\n".join([para.text for para in doc.paragraphs])
                    except Exception as e:
                        st.error("❌ Lỗi khi đọc file Word.")
                        hop_le = False
                elif file_ext == 'txt':
                    noidung_van_ban_goc = file_tai_len.getvalue().decode("utf-8")
            else:
                noidung_van_ban_goc = van_ban_goc

            # --- GỌI AI NHẢ CHỮ LIVE ---
            if hop_le:
                try:
                    # Chốt cứng model mạnh nhất
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    if "Tóm tắt" in che_do:
                        loi_dan = "Bạn là chuyên viên tổng hợp của cơ quan Đảng. Hãy đọc và tóm tắt cốt lõi tài liệu trong 3-5 câu súc tích. Văn phong trang trọng."
                    elif "Ý chính" in che_do:
                        loi_dan = "Bạn là chuyên viên tổng hợp. Đọc tài liệu và trích xuất luận điểm, ý chính bằng gạch đầu dòng rõ ràng."
                    else:
                        loi_dan = "Lập dàn ý chi tiết (I, II, III, 1, 2, 3...) cho tài liệu này. Bao quát toàn bộ nội dung."

                    noi_dung_gui_di = [loi_dan]
                    if file_duoc_upload_len_ai: 
                        noi_dung_gui_di.append(file_duoc_upload_len_ai)
                    if noidung_van_ban_goc: 
                        noi_dung_gui_di.append(f"\n\nVĂN BẢN:\n{noidung_van_ban_goc}")

                    st.markdown("---")
                    st.markdown("<h3 style='color: #10b981;'>✨ KẾT QUẢ XỬ LÝ TỪ AI:</h3>", unsafe_allow_html=True)
                    khung_ket_qua = st.empty()
                    van_ban_hoan_thanh = ""
                    
                    # Truyền dữ liệu và bật nhả chữ Live
                    response = model.generate_content(noi_dung_gui_di, stream=True)
                    for chunk in response:
                        van_ban_hoan_thanh += chunk.text
                        khung_ket_qua.markdown(f"<div class='result-box'>{van_ban_hoan_thanh}</div>", unsafe_allow_html=True)
                    
                    # Xóa file PDF bảo mật sau khi xử lý xong
                    if file_duoc_upload_len_ai:
                        try: genai.delete_file(file_duoc_upload_len_ai.name)
                        except: pass
                        
                except Exception as e:
                    st.error(f"❌ Có lỗi mạng trong quá trình gọi AI. (Chi tiết: {str(e)})")

st.markdown("<br><hr><p style='text-align:center; color:#94a3b8; font-size: 0.85rem;'>Phát triển bởi Ngạc Văn Tuấn</p>", unsafe_allow_html=True)
