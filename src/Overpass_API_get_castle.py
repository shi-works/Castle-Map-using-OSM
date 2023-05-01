import requests
import json
import csv
import datetime


def get_center_point(element):
    lat, lon = 0, 0
    if 'geometry' in element:
        lat_sum = sum([coord['lat'] for coord in element['geometry']])
        lon_sum = sum([coord['lon'] for coord in element['geometry']])
        lat = lat_sum / len(element['geometry'])
        lon = lon_sum / len(element['geometry'])
    return lat, lon


# 現在の日付を取得し、ファイル名に追加する
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
output_filename_csv = f'japan_castles_{current_date}.csv'
output_filename_json = f'japan_castles_{current_date}.json'

# Overpass APIからデータを取得する
query = '''
[out:json][timeout:25];
area["ISO3166-1"="JP"]->.japan;
(
  node["historic"="castle"](area.japan);
  way["historic"="castle"](area.japan);
  relation["historic"="castle"](area.japan);
);
out body;
>;
out skel qt;
'''

overpass_url = "http://overpass-api.de/api/interpreter"
response = requests.get(overpass_url, params={'data': query})
data = response.json()
print(data)

# node_id_to_name: keyがnode_idでvalueがwayまたはrelationのnameタグ
node_id_to_name = {}

for element in data['elements']:
    if 'tags' in element:
        name = element['tags'].get('name', '')
        if element['type'] == 'way':
            for node in element['nodes']:
                node_id_to_name[node] = name
        elif element['type'] == 'relation':
            for member in element['members']:
                if member['type'] == 'node':
                    node_id_to_name[member['ref']] = name

# JSONデータを解析し、CSV形式に変換する
with open(output_filename_csv, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['id', 'name', 'latitude', 'longitude', 'type', 'castle_type']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for element in data['elements']:
        lat, lon = 0, 0
        name = element['tags'].get('name', '') if 'tags' in element else ''
        castle_type = element['tags'].get(
            'castle_type', '') if 'tags' in element else ''

        if element['type'] == 'node':
            lat, lon = element['lat'], element['lon']
            # wayまたはrelationからのnameを追加
            if element['id'] in node_id_to_name:
                name = node_id_to_name[element['id']]
        elif element['type'] in ['way', 'relation']:
            lat, lon = get_center_point(element)

        writer.writerow({
            'id': element['id'],
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'type': element['type'],
            'castle_type': castle_type
        })

print(f"CSVファイル({output_filename_csv})にデータを出力しました。")

# 取得したJSONデータをそのままJSONファイルに書き込む
with open(output_filename_json, 'w', encoding='utf-8') as jsonfile:
    json.dump(data, jsonfile, ensure_ascii=False, indent=2)

print(f"JSONファイル({output_filename_json})にデータを出力しました。")
