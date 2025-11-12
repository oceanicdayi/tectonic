import obspy
from obspy.clients.fdsn import Client
import pygmt
import pandas as pd

print("PyGMT 和 ObsPy 範例程式：納斯卡板塊 (Nazca Plate)")
print("開始執行...")

# --- 1. 設定 (Settings) ---

# 設定要下載地震的區域（納斯卡板塊）
# [lon_min, lon_max, lat_min, lat_max]
REGION = [-110, -70, -60, 10]

# 設定地震時間範圍
START_TIME = obspy.UTCDateTime("2010-01-01")
END_TIME = obspy.UTCDateTime("2025-01-01")

# 最小規模
MIN_MAGNITUDE = 5.5

# 著名的歷史地震：1960 年智利（瓦爾迪維亞）大地震
# 這是歷史上儀器記錄到的最大地震
FAMOUS_EQ = {
    "lon": -73.05,
    "lat": -38.29,
    "depth": 33,
    "mag": 9.5,
    "label": "1960 Valdivia EQ (M9.5)"
}

# 輸出圖片檔案名稱
OUTPUT_FILE = "nazca_plate_map.png"

# --- 2. 獲取地震資料 (ObsPy) ---

print(f"正在從 IRIS 下載 {START_TIME.year} 至 {END_TIME.year} 的地震資料...")
try:
    client = Client("IRIS")
    catalog = client.get_events(
        starttime=START_TIME,
        endtime=END_TIME,
        minlatitude=REGION[2],
        maxlatitude=REGION[3],
        minlongitude=REGION[0],
        maxlongitude=REGION[1],
        minmagnitude=MIN_MAGNITUDE,
    )
    print(f"成功獲取 {len(catalog)} 筆地震事件。")

except Exception as e:
    print(f"錯誤：無法從 IRIS 下載資料。 {e}")
    catalog = obspy.Catalog()

# --- 3. 處理資料 (Pandas) ---

print("正在處理地震資料...")
# 將 ObsPy Catalog 轉換為 Pandas DataFrame，方便 PyGMT 使用
data = []
for event in catalog:
    try:
        origin = event.preferred_origin() or event.origins[0]
        magnitude = event.preferred_magnitude() or event.magnitudes[0]
        
        data.append({
            "lon": origin.longitude,
            "lat": origin.latitude,
            "depth": origin.depth / 1000,  # 深度從 m 轉換為 km
            "mag": magnitude.mag,
            "time": origin.time.strftime("%Y-%m-%d")
        })
    except Exception:
        # 忽略缺少必要資訊的事件
        continue

eq_df = pd.DataFrame(data)

# 載入全球火山資料並篩選
print("正在載入火山資料...")
volcano_df = pygmt.datasets.load_sample_data("world_volcanoes")
# 篩選出在我們區域內的火山
volcano_df = volcano_df[
    (volcano_df.longitude >= REGION[0]) & (volcano_df.longitude <= REGION[1]) &
    (volcano_df.latitude >= REGION[2]) & (volcano_df.latitude <= REGION[3])
]
print(f"篩選出 {len(volcano_df)} 座火山。")


# --- 4. 繪製地圖 (PyGMT) ---

print("開始使用 PyGMT 繪製地圖...")
fig = pygmt.Figure()

# 建立地震深度使用的色標 (CPT)
# 0-70km (淺), 70-300km (中), 300-700km (深)
pygmt.makecpt(
    cmap="viridis",         # 使用 'viridis' 色標
    series=[0, 700],        # 範圍 0 到 700 km
    reverse=True,           # 反轉色標，讓淺層更亮
    background=True         # 讓超出範圍的值變成透明
)

# 繪製底圖：地形 + 陰影
# 使用 02m (2-minute) 解析度的全球地形資料
# 速度較快，品質中等。若要高品質可用 '01m'
grid = pygmt.datasets.load_earth_relief(resolution="02m", region=REGION)
fig.grdimage(grid=grid, projection="M15c", frame=True, cmap="geo", shading=True)

# 繪製海岸線與國界
fig.coast(
    shorelines="1/0.5p,black",   # 海岸線 0.5p 粗, 黑色
    borders="1/0.2p,gray",       # 國界 0.2p 粗, 灰色
    water="skyblue"              # 水體顏色
)

# 加上經緯網格
fig.basemap(frame=["a", "+t納斯卡板塊 (Nazca Plate) 地震與火山活動圖"])

# 繪製火山 (紅色三角形)
fig.plot(
    x=volcano_df.longitude,
    y=volcano_df.latitude,
    style="t0.25c",              # 三角形, 0.25cm
    color="red",
    pen="0.5p,black",
    label="火山 (Volcano)"
)

# 繪製 M5.5+ 地震
# 依據 'depth' 欄位使用色標 (cmap=True)
# 依據 'mag' 欄位調整大小 (size=...)
fig.plot(
    x=eq_df.lon,
    y=eq_df.lat,
    style="c",                   # 圓形
    # 尺寸：(規模 * 0.05) cm。可自行調整比例
    size=eq_df.mag * 0.05,
    cmap=True,                   # 啟用色標 (使用上面 makecpt 的設定)
    zvalue=eq_df.depth,          # 依據深度上色
    color="white@50",            # 50% 透明度的白色
    pen="0.5p,black",
    label="M5.5+ 地震 (依深度著色)"
)

# 繪製 1960 智利大地震 (M9.5)
fig.plot(
    x=FAMOUS_EQ["lon"],
    y=FAMOUS_EQ["lat"],
    style="a0.5c",               # 星形, 0.5cm
    color="yellow",
    pen="1p,red",
    label=f"著名地震: {FAMOUS_EQ['label']}"
)

# 標註 1960 智利大地震
fig.text(
    x=FAMOUS_EQ["lon"],
    y=FAMOUS_EQ["lat"],
    text=FAMOUS_EQ['label'],
    font="10p,Helvetica-Bold,black",
    justify="LM",                # 文字在標點的左中 (Left-Middle)
    offset="0.5c/0c"             # 向右偏移 0.5cm
)

# 加上地震深度色標
fig.colorbar(
    frame=["+l地震深度", "a100", "f", "+u km"],
    position="JMR+o0.5c/0c+w7c/0.4c" # 右中位置
)

# 加上圖例
fig.legend(position="JBL+o0.5c/0.5c", box="+gwhite+p1p") # 左下角

# 儲存地圖
print(f"地圖繪製完成，儲存至 {OUTPUT_FILE}...")
fig.savefig(OUTPUT_FILE)
fig.show()

print("程式執行完畢。")