""" 
Updated by: 
"""
import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

load_dotenv()
now = datetime.now()
DATE_TODAY = now.strftime("%m%d%Y")
RESULTS_PATH = "comparison_results/"

class Compare:
    def __init__(self, firstenv, secondenv, inputFile):
        self.firstenv = firstenv.lower()
        self.secondenv = secondenv.lower()

        self.input_file = inputFile if inputFile != '' else "InputFile.xlsx"

        self.api_key_mapping = {'dev': {'key': os.getenv("dev_key"), 'url': os.getenv("dev_url")},
                   'qa': {'key': os.getenv("qa_key"), 'url': os.getenv("qa_url")},
                   'uat': {'key': os.getenv("uat_key"), 'url': os.getenv("uat_url")},
                   'prod': {'key': os.getenv("prod_key"), 'url': os.getenv("prod_url")}}
        self.outputpath = "comparison_results"

        #kpi df
        self.kpi_df = []
        self.total_elems = [] #{kpi: kpi_name, total_elements: total}
    
    def set_output_path(self,outputpath):
        self.outputpath = outputpath
        
    def get_key_url(self, env):
        try:
            envi_map = self.api_key_mapping[env]
            url = envi_map['url']
            key = envi_map['key']
            return key, url 
        except KeyError as e:
            exit("Environment not defined")

    def compare_values(self):
        input_file_df = pd.read_excel(self.input_file, sheet_name="Mapping")
        not_matching_lst = []
        not_matching_columns = ["company", "api", "kpi", "remarks", "firstenv", "secondenv"]
        not_matching_df = pd.DataFrame(columns=not_matching_columns)
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        first_api_key, first_url = self.get_key_url(self.firstenv)
        second_api_key, second_url = self.get_key_url(self.secondenv)

        outputs = []
        resultsMismatch = []
        for index, row in input_file_df.iterrows():
            company = row["company"]
            payload = row["payload"]
            api = row["api"]
            kpis_lst = row["kpis"].lstrip("[").rstrip("]").replace("\"", "").replace(" ", "").split(",")
            first_headers = {
                'x-api-key': first_api_key,
                'Content-Type': 'application/json'
            }
            first_response = requests.request("POST", "{}{}".format(first_url, row["base_path"]), headers=first_headers,
                                              data=payload, verify=False)
            converted_first_response = first_response.text.encode('utf8')

            second_headers = {
                'x-api-key': second_api_key,
                'Content-Type': 'application/json'
            }
            second_response = requests.request("POST", second_url + row["base_path"], headers=second_headers,
                                               data=payload, verify=False)
            converted_second_response = second_response.text.encode('utf8')
            if bool(converted_first_response):
                json_first_response_dict = json.loads(converted_first_response)
            else:
                json_first_response_dict = {}
                msg = " No Data found in {} for {} api".format(self.firstenv, api)
                print(msg)
                mismatch = [company, 'N/A', "API: {}".format(api), 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', msg]
                outputs.append(mismatch)

            if bool(converted_second_response):
                json_second_response_dict = json.loads(converted_second_response)
            else:
                json_second_response_dict = {}
                msg = " No Data found in {} in {} api ".format(self.secondenv, api)
                print(msg)
                mismatch = [company, 'N/A', "API: {}".format(api), 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', msg]
                outputs.append(mismatch)
            print("========={}=={}=={}=========".format(row["company"], row["api"], row["kpis"]))

            kpi_in_first = False
            kpi_in_second = False
            msg = ""
            if api in ("VCM_WACC", "VCM_Default", "VCM_TargetEV"):
                if isinstance(json_first_response_dict, dict):
                    json_first_response_dict = [json_first_response_dict]
                if isinstance(json_second_response_dict, dict):
                    json_second_response_dict = [json_second_response_dict]
            if len(kpis_lst) > 0:
                firstItemKPI = kpis_lst[0]
                if firstItemKPI == "":
                    self.compare_data(company, api, json_first_response_dict, json_second_response_dict)
                    tally = []
                    self.count_elements(json_first_response_dict, tally)
                    total_tally = sum(tally)
                    self.total_elems.append({'kpi':api,'total_elems':total_tally})
                else:
                    for kpi in kpis_lst:
                        kpi_in_first = kpi in json_first_response_dict
                        kpi_in_second = kpi in json_second_response_dict
                        if kpi_in_first and kpi_in_second:
                            self.compare_data(company, kpi, json_first_response_dict[kpi], json_second_response_dict[kpi])
                            tally = []
                            self.count_elements(json_first_response_dict[kpi], tally)
                            total_tally = sum(tally)
                            self.total_elems.append({'kpi':kpi,'total_elems':total_tally})
                        else:
                            if not kpi_in_first:
                                msg = "{} key not found in {} ".format(kpi, self.firstenv)
                            if not kpi_in_second:
                                msg = "{} response cannot be found in {}. Kindly check also the payload, it might be the kpi is not included.".format(kpi, self.secondenv)

                            mismatch = [company, 'N/A', kpi, 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', msg]

                            outputs.append(mismatch)
            else:
                # no kpi names on the response but has data
                # compare the data results
                if json_first_response_dict and json_second_response_dict:
                    self.compare_data(company, api, json_first_response_dict, json_second_response_dict)


        if len(outputs) > 0:
            self.writeToExcel(outputs, "Errors", 'other errors')

    def count_elements(self, data, tally):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    self.count_elements(value, tally)
                elif isinstance(value, list):
                    self.count_elements(value, tally)
                else:
                    tally.append(1)
        elif isinstance(data, list):
            for value in data:
                if isinstance(value, dict):
                    self.count_elements(value, tally)
                elif isinstance(value, list):
                    self.count_elements(value, tally)
                else:
                    tally.append(1)
        else:
            tally.append(1)

    def writeToExcel(self, datalist, filename, kpi, is_segment=False):
        companyid_or_seg_label = 'CompanyID' if not is_segment else 'Segment'
        filename = "{}/{}-{}-{}.xlsx".format(self.outputpath, filename, self.firstenv, self.secondenv)
        cols = ['CompanyName', companyid_or_seg_label, 'KPI', 'Key', 'Type1', 'Type2', 'Value1',
                                    'Value2', 'Remarks']
        df1 = pd.DataFrame(datalist,
                           columns=cols)
        df1 = df1.sort_values('Key', ascending=False).drop_duplicates(keep='first')
        df1.to_excel(filename)
        if kpi == 'other errors':
            print("Generated report for other errors found. Filename: {} ".format(filename))
        else:
            print("Generated report for {} mismatches. Filename: {} ".format(kpi, filename))

        self.kpi_df.append({"KPI":kpi, "ERROR_COUNT": df1.shape[0]})

    def getKPI(self):
        return self.kpi_df

    def compute_percentage_errors(self):

        percentage_score = []
        for er_kpi in self.kpi_df:
            kpi = er_kpi['KPI']
            num_errors = er_kpi['ERROR_COUNT']
            total_n = 0
            for n_tot in self.total_elems:
                if kpi == n_tot['kpi']:
                    total_n+=n_tot['total_elems']
            if total_n > 0:
                percentage = (num_errors/total_n)*100
                percentage_score.append({'kpi':kpi, 'percentage':percentage, 'error_count':num_errors, 'tot_elems':total_n})
        return percentage_score

    def getTotalElementsPerCo(self):
        return self.total_elems

    def compare_data(self, company, kpi_name, data1, data2):
        """
        compare data
        :param kpi_name:
        :param kp1data:
        :param kpi2data:
        :return: output: list of dic

        """
        num_matches = 0

        output = []
        print("Comparing kpi: {} ...  ".format(kpi_name))
        is_segment = False
        len_diff = False
        if len(data1) == len(data2):
            for da in data1:
                for ca in data2:
                    if 'companyId' in da and da['companyId'] == ca['companyId']:
                        try:
                            data = self.compare_item(company, da['companyId'], kpi_name, da, ca)
                            if len(data) > 0:
                                output.append(data)

                        except KeyError as e:
                            msg = '{} field is not found either on the {} or {}'.format(str(e), self.firstenv, self.secondenv)
                            mismatch = [[company, da['companyId'], kpi_name, str(e), 'N/A', 'N/A', 'N/A', 'N/A',msg]]
                            output.append(mismatch)
                    elif 'segment' in da and da['segment'] == ca['segment']:
                        print("comparing segments")
                        try:
                            is_segment = True
                            data = self.compare_item(company, da['segment'], kpi_name, da, ca)
                            if len(data) > 0:
                                output.append(data)
                        except KeyError as e:
                            # print(" Key not Found: {}".format(str(e)))
                            msg = '{} field is not found either on the {} or {}'.format(str(e), self.firstenv, self.secondenv)
                            mismatch = [[company, da['segment'], kpi_name, str(e), 'N/A', 'N/A', 'N/A', 'N/A',msg]]
                            output.append(mismatch)
                    elif 'xf_company_id' in da and da['xf_company_id'] == ca['xf_company_id']:
                        try:
                            data = self.compare_item(company, da['xf_company_id'], kpi_name, da, ca)
                            if len(data) > 0:
                                output.append(data)
                        except KeyError as e:
                            # print(" Key not Found: {}".format(str(e)))
                            msg = '{} field is not found either on the {} or {}'.format(str(e), self.firstenv, self.secondenv)
                            mismatch = [[company, da['xf_company_id'], kpi_name, str(e), 'N/A', 'N/A', 'N/A', 'N/A',msg]]
                            output.append(mismatch)
        else:
            mismatch = [company, 'N/A', kpi_name, 'N/A', 'N/A', 'N/A', str(len(data1)), str(len(data2)),
                        'Data size does not matched']
            output.append(mismatch)
            len_diff = True

        newOuts = []

        for out in output:
            for ou in out:
                newOuts.append(ou)
        fileName = "{}-{}".format(company, kpi_name)

        if len_diff:
            newOuts = [newOuts]

        if len(newOuts) > 0:

            self.writeToExcel(newOuts, fileName, kpi_name, is_segment=is_segment)
        else:
            print('No mismatches found on {}.'.format(kpi_name))
        return output

    def deep_compare(self, company, companyid_or_segment, kpi, item1, item2, outputs):
        if isinstance(item1, list):
            for idx, subitem in enumerate(item1):
                if isinstance(subitem, list) or isinstance(subitem, dict):
                    self.deep_compare(company, companyid_or_segment, kpi, subitem, item2[idx], outputs)
                else:
                    if subitem != item2[idx]:
                        mismatch = [company, companyid_or_segment, kpi, subkey, str(type(subitem)),
                                    str(type(item2[idx])), str(subitem), str(item2[idx]), 'data mismatched']
                        outputs.append(mismatch)
                  

        elif isinstance(item1, dict):
            for subkey, subvalue in item1.items():
                subtype1 = type(subvalue)
                subtype2 = type(item2[subkey])
                subvalue1 = subvalue
                subvalue2 = item2[subkey]
                if isinstance(subvalue1, list):
                    len1 = len(subvalue1)
                    len2 = len(subvalue2)
                    for idx, value in enumerate(subvalue1):
                        item1 = value
                       
                        if idx < len(subvalue2):
                             item2 = subvalue2[idx]
                        if isinstance(item1, dict):
                            self.deep_compare(company, companyid_or_segment, kpi, item1, item2, outputs)
                        else:
                            if subvalue1 != subvalue2:
                                mismatch = [company, companyid_or_segment, kpi, subkey, str(subtype1), str(subtype2),
                                            str(subvalue1), str(subvalue2), 'data mismatched']
                                outputs.append(mismatch)
                elif isinstance(subvalue1, dict):
                    self.deep_compare(company, companyid_or_segment, kpi, subvalue1, subvalue2, outputs)
                else:
                    if subvalue1 != subvalue2:
                        mismatch = [company, companyid_or_segment, kpi, subkey, str(subtype1), str(subtype2),
                                    str(subvalue1), str(subvalue2), 'data mismatched']
                        outputs.append(mismatch)
    
        else:
            if item1 != item2:
                mismatch = [company, companyid_or_segment, kpi, subkey, str(type(item1)), str(type(item2)), str(item1),
                            str(item2), 'data mismatched']
                outputs.append(mismatch)

    def compare_item(self, company, companyid_or_segment, kpi_name, item1, item2):
        output = []
        nested_outs = []
        news_dic_outs = []
      
        for key, value in item1.items():
            if item1[key] != item2[key]:
                type1 = type(item1[key])
                type2 = type(item2[key])
                if isinstance(item1[key], list):
                    item1data = item1[key]
                    item2data = item2[key]
                    lendata1 = len(item1data)
                    lendata2 = len(item2data)
                    if lendata1 == lendata2:
                        for index, ditem in enumerate(item1data):
                            subitem1 = ditem
                            subitem2 = item2data[index]
                            self.deep_compare(company, companyid_or_segment, kpi_name, subitem1, subitem2, nested_outs)
                    else:
                        mismatch = [company, companyid_or_segment, kpi_name, key, 'N/A', 'N/A', len(item1), len(item2),
                                    'Data size does not matched']
                        output.append(mismatch)
                elif isinstance(item1[key], dict):
                    subitem1 = item1[key]
                    subitem2 = item2[key]
                    for subkey, subvalue in subitem1.items():
                        subtype1 = type(subitem1[subkey])
                        subtype2 = type(subitem2[subkey])
                        subvalue1 = subitem1[subkey]
                        subvalue2 = subitem2[subkey]
                        if subvalue1 != subvalue2:
                            self.deep_compare(company, companyid_or_segment, kpi_name, subitem1, subitem2,
                                              news_dic_outs)
                else:
              
                    mismatch = [company, companyid_or_segment, kpi_name, key, str(type1), str(type2), str(item1[key]),
                                str(item2[key]), 'data mismatched']
                    output.append(mismatch)
              
        output = output + nested_outs + news_dic_outs
        return output
