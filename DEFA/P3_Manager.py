#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author:    Byeongchan Jeong
@contact:   jbc0729@gmail.com
"""

import os
import sys
import csv
import json

from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

from CARPE3.READ.PDF.carpe_pdf import PDF
from CARPE3.READ.OOXML.Carpe_OOXML import OOXML
from CARPE3.READ.MS_Office.carpe_compound import Compound
from CARPE3.READ.Hancom.carpe_hwp import HWP



class READ:
    def documentFilter(self, data, file):
        es = Elasticsearch(hosts="220.73.134.142", port=9200)
        index_name = 'read'
        type_name = 'document'
        
        data.name = file[4] # 파일이름
        data.ext = file[34] # 파일 확장자
        data.parent_full_path = file[33] # parent 경로
        data.path_with_ext = file[33] + file[4] # 파일 전체 경로
        data.path = data.path_with_ext.replace('.'+data.ext, '') # 확장자 제외
        data.creation_time = datetime.fromtimestamp(file[13])
        data.last_written_time = datetime.fromtimestamp(file[11])
        data.last_access_time = datetime.fromtimestamp(file[12])
        data.original_size = file[10]
        
        data.has_exif = 'No'
        data.doc_id = file[0]
        data.doc_type = 'documents'
        data.doc_type_sub = data.ext

        work_file = file[37]

        if data.ext.lower() in 'pdf':
            return False
            with PDF(work_file) as pdf:
                pdf.parse_content()
                pdf.parse_metadata()
                try:
                    data.content = pdf.content
                    data.author = pdf.metadata[0]['Author'].decode('utf-16')
                    #data.creation_time = pdf.metadata[0]['CreationDate'].decode('utf-8')
                    #data.last_written_time = pdf.metadata[0]['ModDate'].decode('utf-8')
                    data.has_metadata = pdf.has_metadata
                    data.has_content = pdf.has_content
                    data.is_damaged = pdf.is_damaged
                    es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                    #print(data.__dict__)
                    return True
                except Exception as ex:
                    print('[Error]%s-%s'%(ex, data.name))
                    return False
        elif data.ext.lower() in 'hwp': 
            hwp = HWP(work_file)
            hwp.parse()
            try:
                data.content = hwp.content
                data.author = hwp.metaList[0]['author']
                #data.creation_time = hwp.metaList[0]['createTime']
                #data.last_written_time = hwp.metaList[0]['lastSavedTime']
                data.has_metadata = hwp.has_metadata
                data.has_content = hwp.has_content
                data.is_damaged = hwp.isDamaged
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        elif data.ext.lower() in ('doc', 'xls', 'ppt'): 
            compound = Compound(work_file) 
            compound.parse()
            try:
                data.content = compound.content
                data.author = compound.metadata['author'].decode('utf-16')
                #data.creation_time = compound.metadata['create_time']
                #data.last_written_time = compound.metadata['modified_time']
                data.has_metadata = compound.has_metadata
                data.has_content = compound.has_content
                data.is_damaged = compound.is_damaged
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        elif data.ext.lower() in ('docx', 'xlsx', 'pptx'): 
            ooxml = OOXML(work_file)
            ooxml.parse_ooxml()
            try:
                data.content = ooxml.content
                data.author = ooxml.metadata['creator']
                #data.creation_time = ooxml.metadata['created']
                #data.last_written_time = ooxml.metadata['modified']
                data.has_metadata = ooxml.has_metadata
                data.has_content = ooxml.has_content
                data.is_damaged = ooxml.is_damaged
                es.index(index=index_name, doc_type=type_name, body=data.__dict__)
                #print(data.__dict__)
                return True
            except Exception as ex:
                print('[Error]%s-%s'%(ex, data.name))
                return False
        else:
            print('NONE')
		


def run_daemon(data, file_list):
    
    try:
        if len(file_list) == 0: return False
       
        read = READ()
        f = open("out.txt", "w")

        success = 0
        failed = 0
        time1 = datetime.now()
        for file in file_list:
            if read.documentFilter(data, file):
                success += 1
            else:
                failed += 1
                f.write(file[37])		
                f.write('\n')
        f.close()				
        print('success: %d failed: %d'% (success, failed))
        time2 = datetime.now()
        print((time2-time1).seconds, 'sec')		

    except KeyboardInterrupt:
        print('error')

