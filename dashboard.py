import streamlit as st
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import calendar
import plotly.express as px
from plotly_calplot import calplot



def main():
    st.title("실시간 농산물 가격 조회 서비스")

    # 사이드바
    st.sidebar.header("필터링 옵션")

    # 지역 선택
    region = st.sidebar.selectbox(
        "지역을 선택하세요:",
        [
            "강릉", "고양", "광주", "김해", "대구", "대전", "부산", "서울",
            "성남", "세종", "수원", "순천", "안동", "용인", "울산", "인천",
            "전주", "제주", "창원", "천안", "청주", "춘천", "포항"
        ]
    )

    # 날짜 선택
    date = st.sidebar.date_input(
        "날짜를 선택하세요:",
        datetime.today()
    )

    # 작물 선택
    crop = st.sidebar.selectbox(
        "작물을 선택하세요:",
        ["쌀", "콩", "고구마", "감자", "사과", "배", "딸기", "토마토", "배추", "무", "양파", "마늘", "고추"]
    )

    # 선택한 값 출력 (디버깅용)
    st.write("선택한 지역:", region)
    st.write("선택한 날짜:", date)
    st.write("선택한 작물:", crop)


    data = pd.read_csv(f'output/{region}/price_{crop}.csv')

    # selected_date = pd.to_datetime(date)
    selected_date = '2024-10-28'
    filtered_data = data[data['date'] == selected_date]
    print(filtered_data)

    if not filtered_data.empty:
        dpr1_value = filtered_data['dpr1'].iloc[0]  # 선택한 날짜의 dpr1 값
        st.write(f"오늘의 {region} 지역 {crop} 소매 가격은 {dpr1_value}입니다.")
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
    st.write("### Daily Prices by Date (2024)")
    st.plotly_chart(fig)
if __name__ == '__main__':
    main()