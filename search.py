# -*- coding: utf-8 -*-


import json
import requests
import re
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

app= Flask(__name__)
CORS(app)

baseURL = 'https://project1-23012.firebaseio.com/'
SLASH = '/'
json_suffix_invert = 'index'
json_suffix = ".json"
wordfreq = {}

#Flask Test API
@app.route("/message", methods=["GET"])
def message():
    return "hello"

#Query firebase data
def query_data(word, db):
    getURL = baseURL + db + SLASH + json_suffix_invert + SLASH + word + json_suffix
    response = requests.get(getURL)
    return json.loads(response.text)

#Utility function
def trim_value(s):
  return re.sub(r'[^\w\s]', " ", s) 



#Utility function
def flush_word_dicts():
  wordfreq.clear()
 
 
#Count the primary keys for each word
def count_prim_key(word_d,pk):
  l = set()
  temp = []
  for elem in word_d:
    primary_key_data = elem['pk']
    pk_string = ""
    for k,v in primary_key_data.items():
      pk_string += v
    if pk_string not in l:
      l.add(pk_string)
      temp.append(elem)
  for d in temp:
    pk_string_1 = ""
    primary_key_data_1= d['pk']
    for k,v in primary_key_data_1.items():
      pk_string_1 += v+"|"
    mod_pk = pk_string_1[:-1]
    if d['TABLE']+":"+mod_pk not in wordfreq:
      wordfreq[d['TABLE']+":"+mod_pk] = 1 
    else: 
       wordfreq[d['TABLE']+":"+mod_pk] += 1
 
  
#Sort the keys
def sort_keys():
  result = []
  a1_sorted_keys = sorted(wordfreq, key=wordfreq.get, reverse=True)
  for r in a1_sorted_keys:
    result.append(r)
  return result    

#Populating primary key
def pop_pk(db):
  gets = baseURL + db + SLASH + "pkrelation" + json_suffix 
  response_1 = requests.get(gets)  
  return json.loads(response_1.text)

#Get all the related records
def get_record(result,db,pk):
  rows = []
  for elem in result:
    split_res = elem.split(':')
    table = split_res[0]
    primary_key = ""
    if len(pk[table]) > 1:
      primary_key = "PKcollated"
    else:
      for elem in pk[table]:
        primary_key += elem       
    pp =  split_res[1]
    gets = baseURL + db + SLASH + table + json_suffix + "?orderBy="+'"'+primary_key+'"'+"&equalTo="+'"'+pp+'"'
    response_1 = requests.get(gets)
    for k,v in json.loads(response_1.text).items():
      v['Table'] = table
      rows.append(v)
  return rows

#Route to get records from firebase based on ranking
@app.route('/getData', methods=['GET'])
def get_data():
    cleaned_query = trim_value(request.args.get('word'))
    db = request.args.get('db')
    keywords = ' '.join(cleaned_query.lower().split()).split(' ')
    flush_word_dicts()
    print("You are going to search database with these following keywords :", keywords)
    pk = pop_pk(db)
    not_found_count = 0
    for word in keywords:
      word_data = query_data(word,db)
      if word_data is None:
        not_found_count += 1
        continue;
      count_prim_key(word_data,pk)
    if not_found_count == len(keywords):
      return jsonify({'errorCode' : 404, 'message' : 'Route not found'})
    result = sort_keys()
    for res in result:
      print(res+"\n")
    start_time = time.time()
    final_result = get_record(result,db,pk)
    print(" The number of records fetched are are ", len(final_result))
    print("--- in %s seconds ---" % (time.time() - start_time)) 
    return jsonify(final_result)



#Main function
if __name__ == '__main__':
    app.run(debug=True)
   

	