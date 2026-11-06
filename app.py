import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
import numpy as np

# ตั้งค่าหน้าเว็บ Streamlit (ซ่อน Sidebar ตั้งแต่เริ่มต้น และใช้แบบ Wide)
st.set_page_config(page_title="Chiang Mai Coffee Atlas", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------
# 1. Custom CSS สำหรับปรับหน้าตาให้เป็นสไตล์ Editorial / Storytelling
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');

html, body, [class*="css"]  {
    font-family: 'Prompt', sans-serif !important;
}

/* ซ่อนเมนูหลักของ Streamlit เพื่อความคลีน */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* สไตล์หัวเรื่อง (Hero Section) */
.hero-title {
    font-size: 3.5rem;
    font-weight: 600;
    color: #2c3e50;
    line-height: 1.2;
    margin-bottom: 0px;
}
.hero-subtitle {
    font-size: 1.3rem;
    color: #7f8c8d;
    font-weight: 300;
    margin-top: 10px;
    margin-bottom: 30px;
}
.hero-highlight {
    color: #d35400; /* สีส้มกาแฟ */
}

/* สไตล์แท็กหมวดหมู่ */
.section-tag {
    font-size: 0.85rem;
    color: #95a5a6;
    letter-spacing: 1.5px;
    font-weight: 500;
    text-transform: uppercase;
    margin-bottom: -10px;
}
.section-title {
    font-size: 2.2rem;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 25px;
}

/* สไตล์กล่องข้อมูลสรุป */
.story-box {
    background-color: #ffffff;
    padding: 25px;
    border-radius: 12px;
    border: 1px solid #eeeeee;
    border-left: 6px solid #d35400;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    margin-bottom: 20px;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: 600;
    color: #2c3e50;
    line-height: 1.1;
}
.metric-unit {
    font-size: 1.1rem;
    color: #7f8c8d;
    font-weight: 400;
}
.metric-label {
    font-size: 1rem;
    color: #95a5a6;
    font-weight: 500;
    margin-bottom: 5px;
}
.highlight-text {
    font-size: 1.2rem;
    color: #d35400;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# โหลดข้อมูล
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_name = "กาแฟ เชียงใหม่_2.xlsx"
    try:
        df = pd.read_excel(file_name)
        num_cols = [
            'จำนวนเกษตรกร(ครัวเรือน)', 'เนื้อที่เพาะปลูก/เนื้อที่ยืนต้น(ไร่)', 
            'เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)', 'ปริมาณผลผลิตปีปัจจุบัน(ตัน)', 
            'การกระจายภายในจังหวัด(ตัน)', 'การกระจายภายนอกจังหวัด(ตัน)'
        ]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'อำเภอ' in df.columns: df['อำเภอ'] = df['อำเภอ'].astype(str).str.strip()
        if 'ตำบล' in df.columns: df['ตำบล'] = df['ตำบล'].astype(str).str.strip()
        if 'สินค้า' in df.columns: df['สินค้า'] = df['สินค้า'].astype(str).str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.error("ไม่พบไฟล์ 'กาแฟ เชียงใหม่_2.xlsx' หรือไฟล์มีปัญหา")
    st.stop()

# ---------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------
st.markdown('<div class="section-tag">THE COFFEE LANDSCAPE</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">เชียงใหม่<span class="hero-highlight">ในทุกเมล็ดกาแฟ.</span></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">สำรวจต้นทางของกาแฟ ผ่านผู้คน พื้นที่ และผลผลิต</div>', unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------------
# FILTERS (แสดงแนวนอนแทน Sidebar)
# ---------------------------------------------------------
col_f1, col_f2, col_f3 = st.columns(3)

amphoe_list = ['ทุกอำเภอ'] + sorted(df['อำเภอ'].unique().tolist())
selected_amphoe = col_f1.selectbox("📍 เลือกอำเภอ", amphoe_list)

filtered_df = df if selected_amphoe == 'ทุกอำเภอ' else df[df['อำเภอ'] == selected_amphoe]

tambon_list = ['ทุกตำบล'] + sorted(filtered_df['ตำบล'].unique().tolist())
selected_tambon = col_f2.selectbox("🏡 เลือกตำบล", tambon_list)

if selected_tambon != 'ทุกตำบล':
    filtered_df = filtered_df[filtered_df['ตำบล'] == selected_tambon]

product_list = ['ทุกสายพันธุ์'] + sorted(filtered_df['สินค้า'].unique().tolist())
selected_product = col_f3.selectbox("☕ เลือกสายพันธุ์", product_list)

if selected_product != 'ทุกสายพันธุ์':
    filtered_df = filtered_df[filtered_df['สินค้า'] == selected_product]

if filtered_df.empty:
    st.warning("ไม่มีข้อมูลตามเงื่อนไขที่เลือก")
    st.stop()

st.write("")
st.write("")

# ---------------------------------------------------------
# SECTION 01: MAP & STORY
# ---------------------------------------------------------
st.markdown('<div class="section-tag">01 / EXPLORE THE ORIGIN</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">ให้แผนที่เล่าเรื่องพื้นที่</div>', unsafe_allow_html=True)

col_map, col_story = st.columns([2.5, 1])

with col_story:
    area_name = "จังหวัดเชียงใหม่"
    if selected_tambon != 'ทุกตำบล': area_name = f"ต.{selected_tambon} อ.{selected_amphoe}"
    elif selected_amphoe != 'ทุกอำเภอ': area_name = f"อ.{selected_amphoe}"
    
    st.markdown(f"<div style='font-size:1.1rem; color:#7f8c8d; margin-bottom: 10px;'>YOUR SELECTED AREA</div>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='margin-top:0; color:#2c3e50;'>{area_name}</h2>", unsafe_allow_html=True)
    
    t_farm = filtered_df['จำนวนเกษตรกร(ครัวเรือน)'].sum()
    t_area = filtered_df['เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)'].sum()
    t_prod = filtered_df['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'].sum()
    
    st.markdown(f"""
    <div class="story-box">
        <div class="metric-label">ปริมาณผลผลิต</div>
        <div class="metric-value">{t_prod:,.2f} <span class="metric-unit">ตัน</span></div>
    </div>
    <div class="story-box">
        <div class="metric-label">เนื้อที่ให้ผล</div>
        <div class="metric-value">{t_area:,.0f} <span class="metric-unit">ไร่</span></div>
    </div>
    <div class="story-box">
        <div class="metric-label">เกษตรกร</div>
        <div class="metric-value">{t_farm:,.0f} <span class="metric-unit">ครัวเรือน</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    if selected_amphoe == 'ทุกอำเภอ' and t_prod > 0:
        top_area = filtered_df.groupby('อำเภอ')['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'].sum().idxmax()
        top_val = filtered_df.groupby('อำเภอ')['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'].sum().max()
        st.markdown("<br><div class='metric-label'>พื้นที่ที่น่าจับตา ✳</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='highlight-text'>อ.{top_area} ({top_val:,.1f} ตัน)</div>", unsafe_allow_html=True)

with col_map:
    @st.cache_data
    def get_geojson():
        url = "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/geojson/thailand-tambons.geojson"
        try:
            geo_data = requests.get(url).json()
            geo_data['features'] = [f for f in geo_data['features'] if f['properties'].get('ADM1_TH') == 'เชียงใหม่']
            return geo_data
        except:
            return None

    geo_json_data = get_geojson()
    if geo_json_data:
        map_df = filtered_df.groupby(['อำเภอ', 'ตำบล'], as_index=False)['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'].sum()
        
        m = folium.Map(location=[18.7953, 98.9620], zoom_start=8, tiles="cartodbpositron") # ใช้แผนที่สีสว่างมินิมอล
        
        folium.Choropleth(
            geo_data=geo_json_data,
            name='ปริมาณผลผลิต',
            data=map_df,
            columns=['ตำบล', 'ปริมาณผลผลิตปีปัจจุบัน(ตัน)'],
            key_on='feature.properties.ADM3_TH',
            fill_color='YlOrBr', # ใช้โทนสีเหลือง-ส้ม-น้ำตาล (คล้ายสีกาแฟ)
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='ปริมาณผลผลิต (ตัน)',
            nan_fill_color='#f4f4f4'
        ).add_to(m)

        for feature in geo_json_data['features']:
            t_name = feature['properties'].get('ADM3_TH')
            match = map_df[map_df['ตำบล'] == t_name]
            if not match.empty:
                feature['properties']['production'] = f"{match.iloc[0]['ปริมาณผลผลิตปีปัจจุบัน(ตัน)']:,.2f} ตัน"
            else:
                feature['properties']['production'] = "-"

        folium.GeoJson(
            geo_json_data,
            style_function=lambda x: {'fillColor': '#00000000', 'color': '#2c3e50', 'weight': 0.3},
            tooltip=folium.GeoJsonTooltip(fields=['ADM2_TH', 'ADM3_TH', 'production'], aliases=['อำเภอ:', 'ตำบล:', 'ผลผลิต:'])
        ).add_to(m)
        
        st_folium(m, width="100%", height=500, returned_objects=[])

st.write("")
st.write("")
st.write("")

# ---------------------------------------------------------
# SECTION 02: THE STORY BEHIND THE NUMBERS
# ---------------------------------------------------------
st.markdown('<div class="section-tag">02 / THE STORY BEHIND THE NUMBERS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">จากเมล็ดกาแฟ สู่ภาพรวมของพื้นที่</div>', unsafe_allow_html=True)

col_c1, col_c2 = st.columns(2)
coffee_colors = ['#8D6E63', '#D35400', '#A1887F', '#5D4037'] # โทนสีกาแฟมินิมอล

with col_c1:
    st.markdown("#### VARIETY PROFILE: หลากสายพันธุ์ ในพื้นที่เดียว")
    if 'สินค้า' in filtered_df.columns:
        variety_df = filtered_df.groupby('สินค้า', as_index=False)['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'].sum()
        variety_df = variety_df[variety_df['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'] > 0]
        if not variety_df.empty:
            fig_var = px.pie(variety_df, values='ปริมาณผลผลิตปีปัจจุบัน(ตัน)', names='สินค้า', hole=0.6,
                             color_discrete_sequence=coffee_colors)
            fig_var.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
            fig_var.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_var, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลสายพันธุ์ในพื้นที่นี้")

with col_c2:
    st.markdown("#### FROM FARM TO MARKET: ผลผลิตเดินทางไปที่ไหน")
    in_prov = filtered_df['การกระจายภายในจังหวัด(ตัน)'].sum()
    out_prov = filtered_df['การกระจายภายนอกจังหวัด(ตัน)'].sum()
    market_df = pd.DataFrame({'ตลาด': ['ภายในจังหวัด', 'ภายนอกจังหวัด'], 'ปริมาณ': [in_prov, out_prov]})
    market_df = market_df[market_df['ปริมาณ'] > 0]
    
    if not market_df.empty:
        fig_mkt = px.pie(market_df, values='ปริมาณ', names='ตลาด', hole=0.6,
                         color_discrete_sequence=['#2c3e50', '#e67e22'])
        fig_mkt.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
        fig_mkt.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_mkt, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลการกระจายสินค้าในพื้นที่นี้")

st.write("")
st.write("")

# ---------------------------------------------------------
# SECTION 03: A CLOSER LOOK
# ---------------------------------------------------------
st.markdown('<div class="section-tag">03 / A CLOSER LOOK</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">เปรียบเทียบพื้นที่</div>', unsafe_allow_html=True)

# จัดเตรียมตารางโชว์ข้อมูลแบบคัดเฉพาะส่วนที่สำคัญ
display_df = filtered_df.groupby(['อำเภอ', 'ตำบล'], as_index=False).agg({
    'จำนวนเกษตรกร(ครัวเรือน)': 'sum',
    'เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)': 'sum',
    'ปริมาณผลผลิตปีปัจจุบัน(ตัน)': 'sum'
})

display_df.rename(columns={
    'จำนวนเกษตรกร(ครัวเรือน)': 'เกษตรกร (ครัวเรือน)',
    'เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)': 'เนื้อที่ให้ผล (ไร่)',
    'ปริมาณผลผลิตปีปัจจุบัน(ตัน)': 'ผลผลิต (ตัน)'
}, inplace=True)

# คำนวณผลผลิตเฉลี่ยต่อไร่ (กก. / ไร่)
display_df['ก.ก. / ไร่'] = np.where(
    display_df['เนื้อที่ให้ผล (ไร่)'] > 0,
    (display_df['ผลผลิต (ตัน)'] * 1000) / display_df['เนื้อที่ให้ผล (ไร่)'],
    0
).round(2)

st.dataframe(display_df, use_container_width=True, hide_index=True)
st.caption("* ข้อมูลผลผลิตเฉลี่ยแปลงหน่วยเป็น กิโลกรัมต่อไร่ เพื่อให้ง่ายต่อการเปรียบเทียบ")