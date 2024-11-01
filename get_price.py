import requests
import pandas as pd
import chardet
from urllib.parse import quote_plus, urlencode
from datetime import datetime, timedelta
import os
import pytz
import json
from tqdm import tqdm
import numpy as np

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

    # print(today.strftime('%Y-%m-%d'))
    # cert_key = '50c892c3-9a7b-4c46-81e1-c9cc776f476c&'

    # start_date = datetime(2024, 1, 1)
    # end_date = datetime.today()
    # date_range = pd.date_range(start=start_date, end=end_date)

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
                print(js)

                # 'data'와 'item' 키 존재 여부를 검사하고 데이터프레임 생성
                if 'data' in js and isinstance(js['data'], dict) and 'item' in js['data']:
                    each_data = pd.DataFrame(js['data']['item'])
                    each_data['date'] = today
                    # print(f"{each_data}=each_data")
                    each_data.to_csv(f"{output_folder}/total.csv", mode='w', index=False)
                    print('저장완료')

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
            data[col] = data[col].str.replace(',', '').astype(float)  # 쉼표 제거 후 float 변환
            # data[col] = data[col].astype(str).str.replace(',', '').astype(float)

            # dpr3_rate와 dpr4_rate 계산 (기준은 dpr1)
        for i in range(3, 7):
            rate_column = f'dpr{i}_rate'  # 새로운 rate 칼럼 이름 생성
            data[rate_column] = ((data['dpr1'] - data[f'dpr{i}']) / data['dpr1']) * 100

        data.to_csv(f'./output/{region_name}/total.csv')

        # 증가율과 감소율 데이터 프레임 분리

if __name__ == '__main__':
    main()
