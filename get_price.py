import requests
import chardet
from urllib.parse import quote_plus, urlencode
from datetime import datetime, timedelta
import os
import pytz
import json
import numpy as np
from twilio.rest import Client
import pandas as pd
from dashboard import download_csv_from_github, nice_encoding
import io

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    if encoding is None:
        encoding = 'euc-kr'
    return encoding

def main():

    # info_data = pd.read_csv('regions_price_selection.csv', encoding=detect_encoding('regions_price_selection.csv'))

    # product_data = pd.read_csv('product_code.csv', encoding=detect_encoding('product_code.csv'), header=1)

    # print(info_data.columns)

    # KAMIS API 기본 URL
    # api_url = "http://www.kamis.or.kr/service/price/xml.do?action=periodProductList"
    api_url = "http://www.kamis.or.kr/service/price/xml.do?action=dailyPriceByCategoryList"

    info_data = { '1101': '서울', '2100': '부산', '3511':'전주'}

    desired_timezone = pytz.timezone('Asia/Seoul')
    day = datetime.now(desired_timezone)
    today = day.strftime('%Y-%m-%d')


    # 각 지역에 대해 API 호출 파라미터를 설정하고 저장
    for region_code, region_name in info_data.items():
        # region_code = row["code"]
        # region_name = row["region"]

        # 지역별 output 폴더 경로 설정
        output_folder = f'./output/{region_name}'
        os.makedirs(output_folder, exist_ok=True)  # 폴더가 없으면 생성

        # 각 날짜에 대해 데이터를 가져옴
        # for date in tqdm(date_range, desc=f"Processing {region_name} ({region_code})"):
        #     formatted_date = date.strftime('%Y-%m-%d')
        #     print(formatted_date)

            # 파라미터 설정
        print(str(region_code))


        params = f'&{quote_plus("p_cert_key")}=50c892c3-9a7b-4c46-81e1-c9cc776f476c&' + urlencode({
            quote_plus("p_cert_id"): "2100",
            quote_plus("p_returntype"): "json",
            quote_plus("p_product_cls_code"): "01",
            quote_plus("p_item_category_code"): '200',
            quote_plus("p_country_code"): str(region_code),
            quote_plus("p_regday"): today,
            quote_plus("p_convert_kg_yn"): 'N',
        })

        # API 요청
        response = requests.get(api_url, params=params)

        # 응답 상태 코드 확인
        if response.status_code == 200:
            try:
                # JSON 데이터를 파싱하고 데이터 구조 확인
                js = json.loads(response.content)
                # print(js)

                # 'data'와 'item' 키 존재 여부를 검사하고 데이터프레임 생성
                if 'data' in js and isinstance(js['data'], dict) and 'item' in js['data']:
                    each_data = pd.DataFrame(js['data']['item'])
                    each_data['date'] = today
                    # print(f"{each_data}=each_data")
                    each_data.to_csv(f"{output_folder}/total.csv", mode='w', index=False)
                    # print('저장완료')

                else:
                    print(f"Unexpected data format for {region_name} ({region_code}) on : Skipping")


                each_data['date'] = today
                each_data['region'] = region_name  # 지역명 추가

                # item_name별로 분리하여 저장
                for item_name, group in each_data.groupby('item_name'):
                    file_name = f'price_{item_name}.csv'
                    file_path = os.path.join(output_folder, file_name)

                    # 파일이 존재하면 기존 데이터에 추가
                    if os.path.exists(file_path):
                        existing_df = pd.read_csv(file_path, encoding='utf-8-sig')
                        combined_df = pd.concat([existing_df, group], ignore_index=True)
                        print(combined_df)
                        combined_df = combined_df.drop_duplicates(subset=['date', 'region'], keep='first')
                    else:
                        combined_df = group

                    # 결합된 데이터 저장
                    combined_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                    print("저장완료")

            except json.JSONDecodeError as e:
                pass
                print(f"JSON decoding error for {region_name} ({region_code}) on : {e}")
        else:
            # pass
            print(f"Error fetching data for {region_name} ({region_code}) on : {response.status_code}")

        data = pd.read_csv(f'./output/{region_name}/total.csv')

        # dpr1, dpr3, dpr4 열에서 값이 '-'인 경우 NaN으로 변환하여 계산 가능하도록 함
        for col in ['dpr1', 'dpr3', 'dpr4', 'dpr5', 'dpr6']:
            data[col] = data[col].replace('-', np.nan)  # '-'를 NaN으로 대체
            data[col] = data[col].astype(str).str.replace(',', '').astype(float)

            # dpr3_rate와 dpr4_rate 계산 (기준은 dpr1)
        for i in range(3, 7):
            rate_column = f'dpr{i}_rate'  # 새로운 rate 칼럼 이름 생성
            data[rate_column] = ((data['dpr1'] - data[f'dpr{i}']) / data['dpr1']) * 100

        data.to_csv(f'./output/{region_name}/total.csv')
    # -----------------------------------------------------------
    # 문자 보내기
    account_sid = 'AC6e9b818ca2ffc02dc8f85b51c6447041'
    auth_token = 'b3e9fe52e754160431cd20b63ca9c134'
    client = Client(account_sid, auth_token)

    # UTF-8 인코딩 설정
    # sys.stdout.reconfigure(encoding='utf-8')

    # CSV 파일 URL
    url = 'https://raw.githubusercontent.com/danuni29/Price_Action/refs/heads/master/output/전주/total.csv'

    # CSV 파일 읽기
    # data = pd.read_csv(url)

    data = download_csv_from_github(url)
    # print(data)
    encod = nice_encoding(data)
    csv_data = io.BytesIO(data)
    data = pd.read_csv(csv_data, encoding=encod)
    print(data)

    # 최신 데이터에서 dpr1 값 추출

    tomato_data = data[data['kind_name'] == '대추방울토마토(1kg)']
    print(tomato_data)

    # Twilio를 통해 메시지 전송

    message_body = f"[토마토] 오늘 : {tomato_data['dpr1'].values[0]}원 , 저번주에 비해 {round(tomato_data['dpr3_rate'].values[0], 1)} 변화"
    message = client.messages.create(
        to="+821075503967",
        from_="+18302680093",
        body=message_body
    )
    print(message.sid)


if __name__ == '__main__':
    main()
