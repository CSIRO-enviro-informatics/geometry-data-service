import psycopg2

conn = psycopg2.connect(dbname = 'gis', host='127.0.0.1', port="25432", user = 'jon',password= 'jon')
cur = conn.cursor()

query = 'select id, dataset, ST_AsGeoJSON(geom) from combined_geoms where id = \'10604112630\';'
cur.execute(query).fetchone()
(id,dataset,geojson) = cur.fetchone()

print(id)
print(dataset)
print(geojson)
