import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt

# =======================
# Sehifenin nastroykasi
# =======================
st.set_page_config(
    page_title='OMID Store',
    page_icon='omid icon.png',
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# OMID Store \n Bu hesabat FAB şirkətlər qrupu üçün hazırlanmışdır."
    }
)

css_header = """
<style>
    th {
       color: black;
       font-weight: bold;
    }
    
    [data-testid="stHeader"] { display: none; }
    [class="viewerBadge_link__qRIco"] { display: none; }
/*
    [data-testid="stElementToolbar"] { display: none; }
*/
    button[title="View fullscreen"] { visibility: hidden; }
</style>
<script>
        var config = {
            showTips: {
                valType: 'boolean',
                dflt: true,
                description: [
                    'Determines whether or not tips are shown while interacting',
                    'with the resulting graphs.'
                ].join(' ')
            }
        };
</script>

<title>OMID Store</title>
<meta name="description" content="FAB Şirkətlər Qrupu" />
"""
st.markdown(css_header, unsafe_allow_html=True)

# =======================
# Exceldən məlumat oxuma
# =======================
file_path = "Omid Data Shop.xlsx"
df = pd.read_excel(file_path, sheet_name='Sale')
store_info = pd.read_excel(file_path, sheet_name='Store')

# Tarixi çevirmək
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
store_info['OpenDate'] = pd.to_datetime(store_info['OpenDate'], errors='coerce')
df = df.dropna(subset=['Date'])

# Sahe Acilis tarixi
df = df.merge(store_info, on='Store', how='left')

# =======================
# Sidebar filterlər
# =======================
st.sidebar.header("OMID Store")

butun_magazalar = st.sidebar.checkbox("Bütün mağazalar", value=True)

if butun_magazalar:
    selected_store = "Bütün"
    stores = sorted(df['Store'].unique().tolist())
    selected_stores_false = st.sidebar.multiselect("Mağaza seçin",stores,disabled=True, placeholder='Mağaza seçin', label_visibility='collapsed')
else:
    stores = sorted(df['Store'].unique().tolist())
    selected_store = st.sidebar.multiselect("Mağaza seçin",stores,placeholder='Mağaza seçin', label_visibility='collapsed', default=['Rəcəbli', 'Xutor', 'Dərnəgül', 'Şərq B.'])

if not selected_store:
    st.warning("⚠️ Mağaza seçin!")
    st.stop()
else:
    pass

min_date = df['Date'].min().to_pydatetime()
max_date = df['Date'].max().to_pydatetime()

date_list = sorted(df['Date'].unique().tolist())

last_year_start = dt.datetime(dt.datetime.today().year - 1, 1, 1)

date_range = [min_date,max_date]

date_range = st.sidebar.select_slider(
    "Tarix",
    options=date_list,
    value=(last_year_start, max_date),
    format_func=lambda x: x.strftime("%Y-%m")  # YYYY-MM format
    
)

# Filter data
date_filtered_df = df[(df['Date'] >= date_range[0]) & (df['Date'] <= date_range[1])]


# Butun magaza yoxsa tek magaza
if selected_store == "Bütün":
    filtered_df = date_filtered_df.copy()   
    chart_df = date_filtered_df.groupby("Date", as_index=False)['Sale'].sum()
else:
    filtered_df = date_filtered_df[date_filtered_df['Store'].isin(selected_store)]
    chart_df = filtered_df.groupby("Date", as_index=False)['Sale'].sum()


# Tarixi ardıcıl sortlamaq
chart_df = chart_df.sort_values("Date").reset_index(drop=True)    

chart_df['MonthYear'] = chart_df['Date'].dt.strftime('%b %Y')
chart_df['SaleFormatted'] = chart_df['Sale'].apply(lambda x: f"{int(x):,}".replace(",", " "))

# =======================
#Trend Analiz (Satış + Ortalama)
# =======================
st.header("📊 Trend Analiz (Satış + Ortalama)", divider='rainbow', anchor=False)
chart_df['MA3'] = chart_df['Sale'].rolling(3).mean()
chart_df['MA6'] = chart_df['Sale'].rolling(6).mean()

fig_trend = px.line(chart_df, x='MonthYear', y='Sale', markers=True,
                    color_discrete_sequence=[px.colors.qualitative.Dark24[3]],
                    labels={'Sale': 'Satış Məbləği', 'MonthYear': 'Ay / İl'})

fig_trend.add_scatter(x=chart_df['MonthYear'], y=chart_df['MA3'], mode='lines', name='Son 3 ay Ortalama',
                      line=dict(color=px.colors.qualitative.Dark24[6]))
                      
fig_trend.add_scatter(x=chart_df['MonthYear'], y=chart_df['MA6'], mode='lines', name='Son 6 ay Ortalama',
                      line=dict(color=px.colors.qualitative.Dark24[21]))
fig_trend.update_layout(height=500, xaxis_tickangle=-45,legend=dict(itemdoubleclick=False))
fig_trend.update_traces(hovertemplate='Ay / İl: %{x}<br>Satış: %{customdata}',
                        customdata=chart_df['SaleFormatted'])
st.plotly_chart(fig_trend, use_container_width=True)

# =======================
#Aylıq dəyişmə (%)
# =======================
st.header("📊 Mağaza satışlarının aylıq dəyişimi", divider='rainbow', anchor=False)
chart_df['MoM_Change'] = chart_df['Sale'].pct_change() * 100
chart_df['MoMFormatted'] = chart_df['MoM_Change'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")

fig_growth = px.bar(chart_df, x='MonthYear', y='MoM_Change', text='MoMFormatted',
                    color='MoM_Change', color_continuous_scale='rdylgn',
                    labels={'MoMFormatted': 'Dəyişmə', 'MonthYear': 'Ay / İl'})
fig_growth.update_layout(
    height=400, xaxis_tickangle=-45,
    yaxis_title="Dəyişmə (%)", coloraxis_showscale=False,
    legend=dict(itemdoubleclick=False)
    )
# Hover yalnız MoMFormatted göstərsin
fig_growth.update_traces(
    hovertemplate='Ay / İl: %{x}<br>Dəyişmə: %{text}'
)
st.plotly_chart(fig_growth, use_container_width=True)


# =======================
#Bir mağazanın orta satışı
# =======================
st.header("📊 Bir mağazanın orta satışı", divider='rainbow', anchor=False)
filtered_df['Month'] = filtered_df['Date'].dt.month
seasonality = filtered_df.groupby('Month')['Sale'].mean().reset_index()
seasonality['SaleFormatted'] = seasonality['Sale'].apply(lambda x: f"{int(x):,}".replace(",", " "))
fig_season = px.bar(seasonality, x='Month', y='Sale', text='SaleFormatted',
                    labels={'SaleFormatted':'Orta Satış', 'Month':'Ay'})
fig_season.update_layout(yaxis_title="Orta Satış",
                         legend=dict(itemdoubleclick=False)
                         )
fig_season.update_traces(
    marker_color='crimson',
    hovertemplate='Ay: %{x}<br>Orta Satış: %{text}'
)
st.plotly_chart(fig_season, use_container_width=True)


# =======================
#TOP Mağazalar
# =======================
if selected_store != "aBütün":
    st.header("📊 TOP Mağazalar", divider='rainbow', anchor=False)
    store_ranking = filtered_df.groupby('Store')['Sale'].sum().sort_values(ascending=False).reset_index()
    store_ranking['SaleFormatted'] = store_ranking['Sale'].apply(lambda x: f"{int(x):,}".replace(",", " "))
    fig_rank = px.bar(store_ranking, x='Sale', y='Store', orientation='h', text='SaleFormatted',
                      labels={'Sale':'Satış Məbləği','Store':'Mağaza'})
    fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}, height=500,legend=dict(itemdoubleclick=False))
    fig_rank.update_traces(
        marker_color='crimson',
        hovertemplate='Mağaza: %{y}<br>Satış:  %{x:,.0f}<extra></extra>'
    )
    st.plotly_chart(fig_rank, use_container_width=True)

# =======================
#Mağaza payı
# =======================
    st.header("📊 Mağazaların ümumi satışdakı payı", divider='rainbow', anchor=False)
    total_sales = filtered_df.groupby('Store')['Sale'].sum().reset_index()
    total_sales['Share'] = total_sales['Sale'] / total_sales['Sale'].sum() * 100
    total_sales['ShareFormatted'] = total_sales['Share'].apply(lambda x: f"{x:.2f}%")
    fig_contrib = px.pie(total_sales, values='Sale', names='Store', hover_data=['ShareFormatted'],
                         labels={'Sale':'Satış Məbləği','Store':'Mağaza', 'ShareFormatted':'Pay'})
    fig_contrib.update_traces(textposition='inside', textinfo='percent+label')
    fig_contrib.update_layout(legend=dict(itemdoubleclick=False))
    st.plotly_chart(fig_contrib, use_container_width=True)

# =======================
# Satış məhsuldarlığı (m² üzrə)
# =======================
    st.header("📊 Satış məhsuldarlığı (m² üzrə)", divider='rainbow', anchor=False)
    filtered_df['SalePerArea'] = filtered_df['Sale'] / filtered_df['Area']
    area_perf = filtered_df.groupby('Store')['SalePerArea'].mean().apply(lambda x: f"{x:.2f}").reset_index()
    fig_area = px.bar(area_perf, x='SalePerArea', y='Store', orientation='h',
                      labels={'SalePerArea':'Satış / m²','Store':'Mağaza'})
    fig_area.update_traces(marker_color='crimson')  # Qırmızı rəng
    fig_area.update_layout(height=500, yaxis={'categoryorder':'total ascending'},legend=dict(itemdoubleclick=False))
    st.plotly_chart(fig_area, use_container_width=True)

# =======================
# Mağazanın sahəsi və yaşı ilə Satışların Əlaqəsi
# =======================
    st.header("📊 Mağazların Sahə - Yaş - Satış əlaqəsi", divider='rainbow', anchor=False)
    today = pd.to_datetime("today")
    store_info['AgeYears'] = ((today - store_info['OpenDate']).dt.days / 365).round(1)
    store_sales = filtered_df.groupby('Store')['Sale'].sum().reset_index()
    store_sales = store_sales.merge(store_info[['Store','AgeYears','Area']], on='Store', how='left')
    fig_age_sales = px.scatter(store_sales, x='AgeYears', y='Sale',
                               size='Area', color='Area',
                               color_continuous_scale='reds',
                               hover_data=['Store'],
                               labels={'AgeYears':'Mağaza yaşı','Sale':'Satış', 'Area':'Sahə'})
    # Format y oxunu boşluqlu minliklə göstərmək
    fig_age_sales.update_layout(
        yaxis=dict(
            tickformat=',',  # minliklə ayırır
            tickprefix='',   # prefix olmasın
            separatethousands=True  # 7 124 689 kimi göstərsin
        ),
        legend=dict(itemdoubleclick=False)
    )
    
    # Hoverda da eyni format
    fig_age_sales.update_traces(
        hovertemplate='Mağaza: %{customdata[0]}<br>Satış: %{y:,.0f}<br>Yaş: %{x} il<br>Sahə: %{marker.size}'
    )
    st.plotly_chart(fig_age_sales, use_container_width=True)
    
    # =======================
    # Köhnə və yeni mağazaların satışda payı
    # =======================
    st.header("📊 Köhnə və yeni mağazaların satışı", divider='rainbow', anchor=False)
    # Yeni mağazalar: 2020 və sonrası açılmış mağazalar
    new_stores = store_info[store_info['OpenDate'] >= pd.Timestamp('2020-01-01')]['Store']
    # Yeni və köhnə mağazaların satışlarını ayır
    new_store_sales = filtered_df.groupby('Date')['Sale'].sum()
    old_store_sales = filtered_df[~filtered_df['Store'].isin(new_stores)].groupby('Date')['Sale'].sum()
    # Köhnə mağazaların siyahısı
    st.text("Köhnə mağazalar: " + ", ".join(filtered_df[~filtered_df['Store'].isin(new_stores)]['Store'].unique().tolist()))
    # Müqayisə üçün DataFrame
    compare_df = pd.DataFrame({
        'Date': new_store_sales.index,
        'Yeni Mağazalar': new_store_sales.values,
        'Köhnə Mağazalar': old_store_sales.reindex(new_store_sales.index, fill_value=0).values
    })
    # Çizgi chart
    fig_new = px.line(
        compare_df,
        x='Date',
        y=['Yeni Mağazalar','Köhnə Mağazalar'],
        labels={'value':'Satış', 'Date':'Tarix'},
        color_discrete_sequence=['#FF4D4D','#FF9900']  # qırmızı tonlar
    )
    fig_new.update_layout(
        legend_title_text='',
        legend=dict(itemdoubleclick=False),
        xaxis=dict(
            tickformat="%b %Y",  # ay + il, gün göstərilmir
            dtick="M1"           # ay intervalı
            )
    )
    
    fig_new.data[0].update(
    hovertemplate="Yeni Mağazalar<br>Tarix: %{x|%B %Y}<br>Satış: %{y:,.0f}<extra></extra>"
    )
    fig_new.data[1].update(
        hovertemplate="Köhnə Mağazalar<br>Tarix: %{x|%B %Y}<br>Satış: %{y:,.0f}<extra></extra>"
    )

    st.plotly_chart(fig_new, use_container_width=True)
    
# =======================
# Train vs Test hesablaması
# =======================

st.header("📊 Real və Potensial Mağaza Satışları", divider='rainbow', anchor=False)

# Merge with store_info (TT, RatioIncome, RatioArea, City, MainCity)
sales_tt = date_filtered_df.copy(deep=True)

# Train mağazalar (real satış) lazim deyil
train_sales = sales_tt[sales_tt['TestTrain'] == 'Train'].groupby(['Date','MainCity'])['Sale'].sum().reset_index()


# MainCity üzrə ümumi Train satışları
maincity_sales = sales_tt[sales_tt['TestTrain'] == 'Train'].groupby(['Date','MainCity'])['Sale'].sum().reset_index()

sales_tt["Potential"] = None

# Yeni Potential Cedveli yaradiriq
sales_tt.loc[sales_tt["TestTrain"] == "Train", "Potential"] = sales_tt["Sale"]

city_sales_renamed = maincity_sales.rename(columns={"MainCity": "CenterCity", "Sale": "CitySale"})

sales_tt = sales_tt.merge(
    city_sales_renamed,
    on=["Date", "CenterCity"],
    how="left"
)

sales_tt.loc[sales_tt["TestTrain"] == "Test", "Potential"] = sales_tt["CitySale"] * sales_tt["RatioIncome"] * sales_tt["RatioArea"]


if selected_store == "Bütün":
    real_sales_chart = sales_tt.groupby("Date", as_index=False)['Sale'].sum()
    potential_sales_chart = sales_tt.groupby("Date", as_index=False)['Potential'].sum()
else:
    real_sales_chart = sales_tt[sales_tt['Store'].isin(selected_store)].groupby("Date", as_index=False)['Sale'].sum()
    potential_sales_chart = sales_tt[sales_tt['Store'].isin(selected_store)].groupby("Date", as_index=False)['Potential'].sum()
    

fig_potential = px.line(real_sales_chart, x='Date', y='Sale', markers=True,
                        color_discrete_sequence=[px.colors.qualitative.Dark24[3]],
                        labels={'Sale': 'Real Satış', 'Date': 'İl - Ay'}
                        )
fig_potential.update_traces(
    hovertemplate="İl - Ay: %{x|%B %Y}<br>Real Satış: %{y:,.0f}<extra></extra>"
)
fig_potential.add_scatter(x=potential_sales_chart['Date'], y=potential_sales_chart['Potential'],
                          mode='lines+markers', name='Potensial Satış',
                          line=dict(color=px.colors.qualitative.Dark24[6]),
                          hovertemplate="İl - Ay: %{x|%B %Y}<br>Potensial Satış: %{y:,.0f}<extra></extra>")
                      
fig_potential.update_layout(height=500, xaxis_tickangle=-45,legend=dict(itemdoubleclick=False),
                            xaxis=dict(
                                tickformat="%b %Y",  # ay + il, gün göstərilmir
                                dtick="M1"           # ay intervalı
                                )
                            )

st.plotly_chart(fig_potential, use_container_width=True)


html_string = """
<script>
setTimeout(function() {
    document.querySelectorAll('.modebar-btn[data-title="Download plot as a png"]').forEach(el => el.title = "Şəkil kimi yüklə"); 
    document.querySelectorAll('.modebar-btn[data-title="Zoom"]').forEach(el => el.title = "Miqyas");
    document.querySelectorAll('.modebar-btn[data-title="Pan"]').forEach(el => el.title = "Gəz");
    document.querySelectorAll('.modebar-btn[data-title="Zoom in"]').forEach(el => el.title = "Yaxınlaşdır");
    document.querySelectorAll('.modebar-btn[data-title="Zoom out"]').forEach(el => el.title = "Uzaqlaşdır");
    document.querySelectorAll('.modebar-btn[data-title="Autoscale"]').forEach(el => el.title = "Avtomatik Ölçü");
    document.querySelectorAll('.modebar-btn[data-title="Reset axes"]').forEach(el => el.title = "Yenilə");
    document.querySelectorAll('.modebar-btn[data-title="Fullscreen"]').forEach(el => el.title = "Tam ekran");
}, 5000);
</script>
"""

# st.markdown deyil, st.components.v1.html istifadə et

st.components.v1.html(html_string, height=0)

