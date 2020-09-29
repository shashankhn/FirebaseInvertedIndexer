# -*- coding: utf-8 -*-
"""
Step 1: Get the metadata from Information schema
Step 2: Write the data to .csv files """


import sys
import mysql.connector
import json
import csv
import os
import glob
import requests
import re

baseURL = "https://fir-dm-project.firebaseio.com/"

#baseURL= "https://project1-23012.firebaseio.com/"
SLASH = '/'
INDEX = 'index'
json_suffix_invert = 'index.json'
json_suffix_pk = 'pkrelation.json'
json_suffix_fk = 'fkrelation.json'
pk_string = "PKcollated"


#Function to load the database contents as CSV fike
def load_data_to_csv(db):
   

    table_list = []
    mydb = get_connection(db);
    cur = mydb.cursor()
    

    query1 = ("SELECT table_name FROM information_schema.tables WHERE table_schema = '"+db+"'")
    
    cur.execute(query1)
   
         
    for (table_name) in cur:
      table_list.append(''.join(table_name))
      csv_file_name = ''.join(table_name)+".csv";
      f = open(csv_file_name,'w')
      f.close()
      
      
    for table in table_list:   
       query2 = ("select column_name from information_schema.columns where table_schema = '"+db+"'"+" and table_name = '"+table+"' ORDER BY ORDINAL_POSITION")
       cur.execute(query2)
       f = open(table+".csv",'w')
       header = "# "
       for (col_name) in cur:
         header += ''.join(col_name)+", "
       f.write(header.rstrip()[:-1])
       f.write('\n')
       f.close()
       
       
    for table in table_list:   
       query3 = ("select * from "+db+"."+table)
       cur.execute(query3)
       rows = cur.fetchall()
       f = open(table+".csv",'a')
       for row in rows:
         f.write(', '.join( to_string(s) for s in row) + '\n')

def to_string(obj):
    if obj is None:
        return "NULL"
    else:
        return "'"+str(obj)+"'"
         

def get_connection(db):
    mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    passwd='Samartha$123',
    database=db
        )
    return mydb;


def get_col_names(csv):
    with open(csv) as f:
      first_line = f.readline()
    cols = first_line.split(", ");
    cols[0] = cols[0][2:]
    cols[-1] = cols[-1].replace('\n','')
    return cols


def load_CSVdata_by_columns(path, col_names,file_name,db):
    # load data from csv file into json format
    res_data = []
    json_arr = []
    with open(path, 'rb') as f:  
        text = f.read().decode('latin-1')  
    converted_text = text.replace("'", '"')  
    data = converted_text.splitlines()
    for l in  csv.reader(data, quotechar='"', delimiter=',',quoting=csv.QUOTE_ALL, skipinitialspace=True):
      res_data.append(l)
    for lis in res_data:
      res = {col_names[i]: lis[i] for i in range(len(col_names))} 
      json_arr.append(res)
    json_arr.remove(json_arr[0])
    
    if(len(get_prim_key(db, file_name))>1):
      pk_list = get_prim_key(db, file_name)
      for element in json_arr:
        pk_value = ""
        for k,v in element.items():
          for elem in pk_list:
            if k == elem:
              pk_value += v+"|"
        element[pk_string] =  pk_value[:-1]
        
    json_arr_m = json.dumps(json_arr)
    return  json_arr_m 


def upload_data(url, data, suffix, tips='data'):
    try:
        putResponse = requests.put(url + suffix, data)
        if putResponse.status_code == 200:
            print("Uploaded {} Successfully".format(tips))
        else:
            print("Upload data failed, Reason: {}".format(putResponse.text))
    except:
      print("Upload {} failed".format(tips))
      
def query_data(json_suffix):
	getURL = baseURL + json_suffix
	response = requests.get(getURL)
	return json.loads(response.text)


#Utility function
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#Utility function   
def trim_value(s):
  return re.sub(r'[^\w\s]', " ", s)   


inverted_index = {}
fks = {}
pk = {}
      

#Utility function
def flush_index():
  inverted_index.clear()  

def flush_pk_relation():
  pk.clear()  
  
def flush_fk():
  fks.clear()


#Function to create inverted index
def create_index(data,table,pk):
    for data_record in data:
        pk_val = {}
        for key in pk:
          pk_val[key] = data_record[key]
        for k,v in data_record.items():
            v = trim_value(v)
            
            for word in v.lower().split():
                if word is not None and not(word == ""):
                  if word in inverted_index:
                      inverted_index[word].append({"TABLE" : table , "COLUMN" : k, "pk" : pk_val})
                  else:
                      inverted_index[word] = [{"TABLE" : table , "COLUMN" : k, "pk" : pk_val}]

def get_prim_key(db, table):
    pks = []
    mydb = get_connection(db);
    cur = mydb.cursor()
    query1 = ( "SHOW KEYS FROM "+table+" WHERE Key_name = 'PRIMARY'")
    cur.execute(query1)
    tup = cur.fetchall()
    for elem in tup:
      pks.append(''.join(elem[4]))
    return pks
    
def truncate_db(url):
	try:
		delResponse = requests.delete(url+".json")
		if delResponse.status_code == 200:
			print("Truncated firebase Successfully")
		else:
			print("Truncate DB failed, Reason: {}".format(delResponse.text))
	except:
		print("Truncate DB failed")
        

        
def pop_pk(db):
  mydb = get_connection(db);
  cur = mydb.cursor()
  query1 = ("SELECT table_name FROM information_schema.tables WHERE TABLE_TYPE = 'BASE TABLE' AND table_schema = '"+db+"'")
  cur.execute(query1)
  for (table_name) in cur:
    pk[''.join(table_name)] = get_prim_key(db,''.join(table_name))
 

       


def create_fk_relation(file,db):
    mydb = get_connection(db);
    cur = mydb.cursor()
    query1 = ( "SELECT TABLE_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE REFERENCED_TABLE_SCHEMA ='"+db+"'AND REFERENCED_TABLE_NAME ='"+file+"'") 
    cur.execute(query1)
    tup = cur.fetchall()
    for elem in tup:
      if ''.join(elem[0]) not in fks:
        fks[''.join(elem[0])] = []
      fks[''.join(elem[0])].append(elem[1])
      
      

if __name__ == "__main__":
    assert len(sys.argv[1]) > 1, "Please input a valid database name"
    db = sys.argv[1]
    node = sys.argv[2]  
   
    #print("truncating firebase ....")
    path = os.path.abspath(os.getcwd())
    os.chdir(path)
    test = os.listdir(path)
    for item in test:
      if item.endswith(".csv"):
        os.remove(os.path.join(path, item))
    load_data_to_csv(db) 
    csv_files = glob.glob('*.{}'.format('csv'))
    flush_index()
    flush_fk()
    flush_pk_relation()
    pop_pk(db)
    for file in csv_files:
      print(file)
      file_name = file[0:file.find('.')]
      fileContent = load_CSVdata_by_columns( file, get_col_names(file),file_name,db)
      json_suffix = node+"/"+file_name+".json"
      upload_data(baseURL, fileContent,json_suffix,tips='json' )
      create_fk_relation(file_name,db)
      #upload_data(baseURL, fileContent,json_suffix,tips='json' )
      jsonData = query_data(json_suffix)
     # createUpload_Pk(jsonData,file_name,get_prim_key(db, file_name),node)
      create_index(jsonData, file_name,get_prim_key(db, file_name))
    upload_data(baseURL,json.dumps(inverted_index),node+"/"+json_suffix_invert, tips='index')
    upload_data(baseURL,json.dumps(fks),node+"/"+json_suffix_fk, tips='index')
    upload_data(baseURL,json.dumps(pk),node+"/"+json_suffix_pk, tips='index')

   
