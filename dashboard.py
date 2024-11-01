import streamlit as st
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import calendar
import plotly.express as px
from plotly_calplot import calplot
import requests
import chardet
from flask import Flask, request, send_file
import io
# import io

def nice_encoding(file_content):
    result = chardet.detect(file_content)
    return result['encoding']
def download_csv_from_github(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        # 바이너리 데이터를 바로 반환
        return response.content
    else:
        print(f"Failed to download file: {file_url}")
        return None

def detail_page(item):
    st.title(f"{item['name']}의 상세 페이지")
    st.write(f"가격: {item['price']}")
    st.write(f"단위: {item['unit']}")
    if st.button("뒤로 가기"):  # 뒤로 가기 버튼
        st.session_state.selected_item = None  # 선택 초기화



def main():
    st.title("실시간 농산물 가격 조회 서비스")
    st.header("오늘 가격은 어떻게 변했을까 ?")
    region = st.selectbox(
        "지역을 선택하세요:",
        ["전주", "서울", "부산"]
    )

    url = f'https://raw.githubusercontent.com/danuni29/Price_Action/refs/heads/master/output/{region}/total.csv'
    data = download_csv_from_github(url)
    # print(data)
    encod = nice_encoding(data)
    csv_data = io.BytesIO(data)
    data = pd.read_csv(csv_data, encoding=encod)

    # 비교 기간 옵션
    comparison_options = {
        "1주일 전": "dpr3",
        "2주일 전": "dpr4",
        "1달 전": "dpr5",
        "1년 전": "dpr6",
        # "연평균": "dpr7"
    }

    # 비교 기간 선택
    selected_period = st.selectbox("비교 기간을 선택하세요", list(comparison_options.keys()))
    selected_column = comparison_options[selected_period]
    st.write(f"기준 날짜(업데이트 날짜): {data['date'].iloc[0]}")

    # 증감률 계산
    rate_column = f'{selected_column}_rate'


    # 증가율과 감소율 데이터 프레임 분리 및 정렬
    increased = data[data[rate_column] > 0].sort_values(by=rate_column, ascending=False).head(5)
    decreased = data[data[rate_column] < 0].sort_values(by=rate_column).head(5)

    # 증감률 컬럼 스타일링 함수
    def style_rate(val):
        color = 'red' if val > 0 else 'blue'
        arrow = '▲' if val > 0 else '▼'
        return f'color: {color}; font-weight: bold; content: "{arrow} {val:.2f}%"'

    # Streamlit 컬럼을 이용해 양옆에 테이블 배치
    col1, col2 = st.columns(2)

    # 증가율 높은 품목
    # with col1:
    st.subheader("증가율 높은 품목")
    increased_table = increased[['item_name', 'kind_name', 'rank', 'dpr1', selected_column, rate_column]]
    increased_table = increased_table.rename(columns={
        'item_name': '품목명', 'kind_name': '품종명', 'rank': '등급', 'dpr1': '현재 가격', selected_column: '비교 기간 가격', rate_column:'증가율'
    }).reset_index(drop=True)
    increased_table.index = increased_table.index + 1
    styled_increased_table = increased_table.style.applymap(
        lambda x: 'color: red; font-weight: bold;' if isinstance(x, float) and x > 0 else '',
        subset=['증가율']
    ).format({
        '현재 가격': "{:,.0f}원",
        '비교 기간 가격': "{:,.0f}원",
        '증가율': "{:+.2f}%"
    })
    st.markdown(styled_increased_table.to_html(index=False), unsafe_allow_html=True)

    # 감소율 높은 품목
    # with col2:
    st.subheader("감소율 높은 품목")
    decreased_table = decreased[['item_name', 'kind_name', 'rank', 'dpr1', selected_column, rate_column]]
    decreased_table = decreased_table.rename(columns={
        'item_name': '품목명', 'kind_name': '품종명', 'rank': '등급', 'dpr1': '현재 가격', selected_column: '비교 기간 가격', rate_column: '감소율'
    }).reset_index(drop=True)
    decreased_table.index = decreased_table.index + 1
    styled_decreased_table = decreased_table.style.applymap(
        lambda x: 'color: blue; font-weight: bold;' if isinstance(x, float) and x < 0 else '',
        subset=['감소율']
    ).format({
        '현재 가격': "{:,.0f}원",
        '비교 기간 가격': "{:,.0f}원",
        '감소율': "{:+.2f}%"
    })
    st.markdown(styled_decreased_table.to_html(index=False), unsafe_allow_html=True)


    # -----------------------------------------------------------------------
    # 작물별 가격 확인하기

    st.header("품목별 가격 확인하기")


    # 날짜 선택
    date = st.date_input(
        "날짜를 선택하세요:",
        datetime.today()
    )
    year = date.year
    month = date.month
    day = date.day

    # 작물 선택
    crop = st.selectbox(
        "작물을 선택하세요:",
        ["갓", "건고추", "고춧가루", "깐마늘(국산)", "깻잎", "당근", "멜론", "무", "미나리", "방울토마토", "배추", "붉은고추", "브로콜리", "상추",
         "생강", "시금치", "알배기배추", "양배추", "양파", "얼갈이배추", "열무", "오이", "토마토", "파", "파프리카", "풋고추", "피망", "호박"]
    )
    # 선택한 값 출력 (디버깅용)


    # https://github.com/danuni29/Price_Action/tree/master/output
    url = f'https://raw.githubusercontent.com/danuni29/Price_Action/refs/heads/master/output/{region}/price_{crop}.csv'
    # st.write(url)
    # data = pd.read_csv(f'./output/{region}/price_{crop}.csv')
    file_data = download_csv_from_github(url)
    # print(data)
    encoding = nice_encoding(file_data)
    csv_data = io.BytesIO(file_data)
    data = pd.read_csv(csv_data, encoding=encoding)
    # print(data)
    data['date'] = pd.to_datetime(data['date'])

    selected_date = pd.to_datetime(date)
    filtered_data = data[data['date'] == selected_date]
    # print("data['date'] 타입:", data['date'].dtype)
    # print("selected_date 타입:", type(selected_date))
    print(filtered_data)

    if not filtered_data.empty:
        dpr1_value = filtered_data['dpr1'].iloc[0]
        print(dpr1_value)
        # st.write(f"{year}년 {month}월 {day}일 {region} 지역 {crop} 소매 가격은 {dpr1_value}원 입니다.")
        st.markdown(f"<span style='color: blue;'>{year}년 {month}월 {day}일 {region} 지역 {crop} 소매 가격은 {dpr1_value}원 입니다.</span>", unsafe_allow_html=True)
    else:
        st.write(f"{date}에 대한 데이터가 없습니다.")

    print(data.columns)
    data['dpr1'] = data['dpr1'].astype(str).str.replace(',', '')  # 쉼표 제거
    data['dpr1'] = pd.to_numeric(data['dpr1'], errors='coerce')  # 숫자로 변환
    # st.write(f"오늘의 {region}지역 {crop} 소매 가격은 {dpr1}입니다.")

    print(data['dpr1'])
    fig = calplot(
        data,
        x="date",
        y="dpr1",
        dark_theme=False,
        colorscale="YlOrRd"
    )

    # Streamlit에서 히트맵 출력


    if st.button("가격 히트맵 보기"):
        # 날짜 데이터를 연, 월, 일로 분리
        data['year'] = data['date'].dt.year
        data['month'] = data['date'].dt.month
        data['day'] = data['date'].dt.day

        # 히트맵 그리기
        st.write("### Daily Prices by Date (2024)")
        st.plotly_chart(fig)




if __name__ == '__main__':
    main()