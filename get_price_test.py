import requests
import pandas as pd
import chardet
from urllib.parse import quote_plus, urlencode
from datetime import datetime, timedelta
import os
import pytz
import json
from tqdm import tqdm

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    if encoding is None:
        encoding = 'euc-kr'
    return encoding

def main():

    # info_data = pd.read_csv('price_regions.csv', encoding=detect_encoding('price_regions.csv'))
    # product_data = pd.read_csv('product_code.csv', encoding=detect_encoding('product_code.csv'), header=1)
    # print(info_data.columns)

    # KAMIS API 기본 URL
    # api_url = "http://www.kamis.or.kr/service/price/xml.do?action=periodProductList"
    api_url = "http://www.kamis.or.kr/service/price/xml.do?action=dailyPriceByCategoryList"


    desired_timezone = pytz.timezone('Asia/Seoul')
    today = datetime.now(desired_timezone)
    today = today - timedelta(days=10)

    # print(today.strftime('%Y-%m-%d'))

    start_date = datetime(2024, 1, 1)
    end_date = datetime.today()
    date_range = pd.date_range(start=start_date, end=end_date)

    # for date in date_range:
    #     formatted_date = date.strftime('%Y-%m-%d')
    #     print(formatted_date)
    params = f'&{quote_plus("p_cert_key")}=50c892c3-9a7b-4c46-81e1-c9cc776f476c&' + urlencode({
        quote_plus("p_cert_id"): "2100",
        quote_plus("p_returntype"): "json",
        quote_plus("p_product_cls_code"): "01",
        quote_plus("p_item_category_code"): '200',
        quote_plus("p_country_code"): '3511',
        quote_plus("p_regday"): today,
        quote_plus("p_convert_kg_yn"): 'N',
    })


    # API 요청
    response = requests.get(api_url, params=params)

    # 응답 상태 코드 확인
    if response.status_code == 200:
        try:
            # JSON 데이터를 파싱하여 데이터프레임 생성
            js = json.loads(response.content)
            print(js)
            each_data = pd.DataFrame(js['data']['item'])
            print(each_data)
            # each_data['date'] =

            # item_name별로 분리하여 저장
            for item_name, group in each_data.groupby('item_name'):
                file_name = f'price_{item_name}.csv'
                file_path = os.path.join('./output/전주', file_name)

                # 파일이 존재하면 기존 데이터에 추가
                if os.path.exists(file_path):
                    existing_df = pd.read_csv(file_path, encoding=detect_encoding(file_path))
                    combined_df = pd.concat([existing_df, group], ignore_index=True)
                    # combined_df = combined_df.drop_duplicates(subset=['date'], keep='first')
                    print(f'중복 행 제거 후 데이터 결합 완료: {file_path}')
                else:
                    combined_df = group

                # 결합된 데이터 저장
                print(combined_df)
                combined_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                print(f"Data saved to {file_path}")

        except (KeyError, TypeError, json.JSONDecodeError) as e:
            # print(f"Error processing data for {formatted_date}: {e}")
            pass
    else:
        pass
        # print(f"Error fetching data on {formatted_date}: {response.status_code}")
if __name__ == '__main__':
    main()