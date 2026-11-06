import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
import json
import numpy as np

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="Dashboard กาแฟ เชียงใหม่", layout="wide")
st.title("☕ Interactive Dashboard: วิเคราะห์ข้อมูลการปลูกกาแฟ จังหวัดเชียงใหม่")

# 1. โหลดและทำความสะอาดข้อมูล
@st.cache_data
def load_data():
    file_name = "กาแฟ เชียงใหม่_2.xlsx"
    try:
        df = pd.read_excel(file_name)
    except FileNotFoundError:
        st.error(f"ไม่พบไฟล์ข้อมูล '{file_name}' กรุณาอัปโหลดไฟล์ไว้ในโฟลเดอร์เดียวกับ app.py")
        return pd.DataFrame()
    
    num_cols = [
        'จำนวนเกษตรกร(ครัวเรือน)', 'เนื้อที่เพาะปลูก/เนื้อที่ยืนต้น(ไร่)', 
        'เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)', 'ปริมาณผลผลิตปีปัจจุบัน(ตัน)', 
        'การกระจายภายในจังหวัด(ตัน)', 'การกระจายภายนอกจังหวัด(ตัน)', 'ปริมาณผลผลิตปีถัดไป(ตัน)'
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'อำเภอ' in df.columns and 'ตำบล' in df.columns:
        df['อำเภอ'] = df['อำเภอ'].astype(str).str.strip()
        df['ตำบล'] = df['ตำบล'].astype(str).str.strip()
    
    if 'เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)' in df.columns and 'ปริมาณผลผลิตปีปัจจุบัน(ตัน)' in df.columns:
        df['ผลผลิตต่อไร่(ตัน/ไร่)'] = np.where(
            df['เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)'] > 0, 
            df['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'] / df['เนื้อที่ เก็บเกี่ยว/เนื้อที่ให้ผล(ไร่)'], 
            0
        )
    return df

df = load_data()
if df.empty:
    st.stop()

# 2. Slicer/Filter
st.sidebar.header("🔍 กรองข้อมูล (Filters)")
amphoe_list = df['อำเภอ'].unique().tolist()
selected_amphoe = st.sidebar.multiselect("เลือกอำเภอ", amphoe_list, default=amphoe_list)

if selected_amphoe:
    filtered_df_for_tambon = df[df['อำเภอ'].isin(selected_amphoe)]
else:
    filtered_df_for_tambon = df

tambon_list = filtered_df_for_tambon['ตำบล'].unique().tolist()
selected_tambon = st.sidebar.multiselect("เลือกตำบล", tambon_list, default=tambon_list)

filtered_df = df[
    (df['อำเภอ'].isin(selected_amphoe)) & 
    (df['ตำบล'].isin(selected_tambon))
]

if filtered_df.empty:
    st.warning("ไม่มีข้อมูลสำหรับพื้นที่ที่เลือก")
    st.stop()

# 3. KPI Cards
st.subheader("📊 สรุปข้อมูลภาพรวม (KPIs)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("จำนวนเกษตรกร (ครัวเรือน)", f"{filtered_df['จำนวนเกษตรกร(ครัวเรือน)'].sum():,.0f}")
col2.metric("เนื้อที่เพาะปลูก (ไร่)", f"{filtered_df['เนื้อที่เพาะปลูก/เนื้อที่ยืนต้น(ไร่)'].sum():,.2f}")
col3.metric("ปริมาณผลผลิต (ตัน)", f"{filtered_df['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'].sum():,.2f}")
col4.metric("ผลผลิตเฉลี่ยต่อไร่ (ตัน/ไร่)", f"{filtered_df['ผลผลิตต่อไร่(ตัน/ไร่)'].mean():,.2f}")

st.markdown("---")

# 4. แผนที่ Folium Map
st.subheader("🗺️ แผนที่แสดงปริมาณผลผลิตแยกตามพื้นที่")
@st.cache_data
def get_geojson():
    url = "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/geojson/thailand-tambons.geojson"
    try:
        response = requests.get(url)
        geo_data = response.json()
        cm_features = [f for f in geo_data['features'] if f['properties'].get('ADM1_TH') == 'เชียงใหม่']
        geo_data['features'] = cm_features
        return geo_data
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูล GeoJSON ได้: {e}")
        return None

geo_json_data = get_geojson()
if geo_json_data:
    map_df = filtered_df.groupby(['อำเภอ', 'ตำบล']).agg({
        'ปริมาณผลผลิตปีปัจจุบัน(ตัน)': 'sum',
        'จำนวนเกษตรกร(ครัวเรือน)': 'sum'
    }).reset_index()

    m = folium.Map(location=[18.7953, 98.9620], zoom_start=8, tiles="cartodbpositron")
    folium.Choropleth(
        geo_data=geo_json_data,
        name='ปริมาณผลผลิต',
        data=map_df,
        columns=['ตำบล', 'ปริมาณผลผลิตปีปัจจุบัน(ตัน)'],
        key_on='feature.properties.ADM3_TH',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='ปริมาณผลผลิต (ตัน)'
    ).add_to(m)

    for feature in geo_json_data['features']:
        tambon_name = feature['properties'].get('ADM3_TH')
        match = map_df[map_df['ตำบล'] == tambon_name]
        if not match.empty:
            feature['properties']['production'] = f"{match.iloc[0]['ปริมาณผลผลิตปีปัจจุบัน(ตัน)']:,.2f} ตัน"
        else:
            feature['properties']['production'] = "ไม่มีข้อมูล"

    folium.GeoJson(
        geo_json_data,
        style_function=lambda x: {'fillColor': '#ffffff00', 'color': 'black', 'weight': 0.5},
        tooltip=folium.GeoJsonTooltip(fields=['ADM2_TH', 'ADM3_TH', 'production'], aliases=['อำเภอ:', 'ตำบล:', 'ผลผลิต:'])
    ).add_to(m)
    
    st_folium(m, width=1000, height=500)

st.markdown("---")

# 5. Charts
col_c1, col_c2 = st.columns(2)
with col_c1:
    st.subheader("📈 เปรียบเทียบปริมาณผลผลิต (ตัน)")
    bar_data = filtered_df.groupby('อำเภอ', as_index=False)['ปริมาณผลผลิตปีปัจจุบัน(ตัน)'].sum().sort_values(by='ปริมาณผลผลิตปีปัจจุบัน(ตัน)', ascending=False)
    fig_bar = px.bar(bar_data, x='อำเภอ', y='ปริมาณผลผลิตปีปัจจุบัน(ตัน)', color='อำเภอ', text_auto='.2s')
    st.plotly_chart(fig_bar, use_container_width=True)

with col_c2:
    st.subheader("🍩 สัดส่วนการกระจายสินค้า")
    in_prov = filtered_df['การกระจายภายในจังหวัด(ตัน)'].sum()
    out_prov = filtered_df['การกระจายภายนอกจังหวัด(ตัน)'].sum()
    pie_data = pd.DataFrame({'ประเภท': ['ภายใน', 'ภายนอก'], 'ปริมาณ': [in_prov, out_prov]})
    fig_pie = px.pie(pie_data, names='ประเภท', values='ปริมาณ', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with st.expander("📄 ดูข้อมูลดิบ"):
    st.dataframe(filtered_df)