import requests
import pandas as pd
import chardet
from urllib.parse import quote_plus, urlencode
from datetime import datetime, timedelta
import os
import pytz
import json

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
    today = today - timedelta(days=1)

    print(today.strftime('%Y-%m-%d'))

    params = f'&{quote_plus("p_cert_key")}=50c892c3-9a7b-4c46-81e1-c9cc776f476c&' + urlencode({
        quote_plus("p_cert_id"): "3749",
        quote_plus("p_returntype"): "json",
        quote_plus("p_product_cls_code"): "01",
        quote_plus("p_item_category_code"): '200',
        quote_plus("p_regday"): today.strftime('%Y-%m-%d'),
        quote_plus("p_convert_kg_yn"): 'N',
    })


    # API 요청
    response = requests.get(api_url, params=params)

    # 응답 상태 코드 확인
    if response.status_code == 200:
        # 응답 데이터를 텍스트로 출력 (원본 XML 데이터 확인)
        print(response.text)
    else:
        # print(response.url)
        print(f"Error: {response.status_code}")

    full_path = 'price_data.csv'
    # try:
    js = json.loads(response.content)
    each_data = pd.DataFrame(js['data']['item'])
    each_data['date'] = today
    # return each_data
    print(each_data)
    # each_data.to_csv('price_data.csv', mode='a', index=False, encoding='utf-8-sig')

    for item_name, group in each_data.groupby('item_name'):
        file_name = f'price_{item_name}.csv'
        file_path = os.path.join('./output', file_name)

        # 파일이 존재하면 전체 경로(file_path)를 확인하여 기존 데이터 불러오기
        if os.path.exists(file_path):
            existing_df = pd.read_csv(file_path, encoding=detect_encoding(file_path))

            # 기존 데이터와 새로운 데이터 결합
            combined_df = pd.concat([existing_df, group], ignore_index=True)

            # 중복된 행 제거 (date 기준으로 중복 제거)
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='first')
            print(f'중복 행 제거 후 데이터 결합 완료: {file_path}')
        else:
            combined_df = group

        # 결합된 데이터 저장
        combined_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"Data saved to {file_path}")

if __name__ == '__main__':
    main()