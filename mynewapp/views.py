import os
import requests
from bs4 import BeautifulSoup
from django.shortcuts import render
from django.http import HttpResponse
from urllib.parse import urljoin
import urllib3
from mynewproject.settings import BASE_DIR
import fitz  # PyMuPDF
import pandas as pd
import shutil
import re
import spacy
import pandas as pd
import numpy as np
from django.http import FileResponse, Http404
from django.conf import settings
import shutil
from .forms import ChangeExcel
from django.views.decorators.csrf import csrf_exempt



# Suppress only the single InsecureRequestWarning from urllib3 needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@csrf_exempt
def index(request):
    
    return render(request, 'index.html')



def read_pdf_to_excel():
    download_dir = os.path.join(BASE_DIR, 'downloads')
    pdf_filename = os.path.join(download_dir, 'todays-pdf.pdf')

    if os.path.exists(pdf_filename):
        pdf_document = fitz.open(pdf_filename)
        text = []

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            blocks = page.get_text("blocks")
            for block in blocks:
                text.append(block[4])  # Extracting the text from each block

        # Save the extracted text to an Excel file, each block in a new row
        data = {'Content': text}
        df = pd.DataFrame(data)
        excel_filename = 'todays-pdf-extracted.xlsx'
        excel_path = os.path.join(download_dir, excel_filename)
        df.to_excel(excel_path, index=False)





def fill_roznama_file_function(total_roznama_data):
    download_dir = os.path.join(BASE_DIR, 'downloads')

    # Define source and destination paths
    src = os.path.join(download_dir, 'ROZNAMA_DATE_ORIGINAL_COPY1.xlsx')
    dest = os.path.join(download_dir, 'ROZNAMA_DATE_ORIGINAL_COPY2.xlsx')

    try:
        shutil.copy(src, dest)
        print(f"File copied successfully from {src} to {dest}")
    except IOError as e:
        print(f"Unable to copy file. {e}")

    filename = os.path.join(download_dir, 'ROZNAMA_DATE_ORIGINAL_COPY2.xlsx')

    # Read the Excel file
    df = pd.read_excel(filename)
    rowindex = None
    column_names = []

    for i in range(0, 15):
        # Get the row
        row = df.iloc[i]
        myflag = False

        # Loop through each cell in the row
        for col_name, cell_value in row.items():
            # Split the cell content into words
            words = str(cell_value).lower().split()
            
            # Check for required column names and add them to column_names list
            if 'case' in words and 'number' in words:
                column_names.append(col_name)
                myflag = True
            elif 'party' in words and 'name' in words:
                column_names.append(col_name)
                myflag = True
            elif 'stage' in words:
                column_names.append(col_name)
                myflag = True
            elif 'coram' in words:
                column_names.append(col_name)
                myflag = True
            elif 'roznama' in words:
                column_names.append(col_name)
                myflag = True
        
        if myflag:
            rowindex = i
            break

    if rowindex is not None and column_names:
        # Identify the case_num column index
        case_num_col = column_names[0]  # Assuming the first column is 'case number'

        if 'Bombay High Court at Bench Nagpur' in df.columns:
            numeric_sr_no = pd.to_numeric(df['Bombay High Court at Bench Nagpur'], errors='coerce')
            max_sr_no = numeric_sr_no.max()
            if pd.isna(max_sr_no):
                max_sr_no = 0
        else:
            max_sr_no = 0
            df.insert(0, 'Bombay High Court at Bench Nagpur', pd.Series(dtype='int'))

        for idx, item in enumerate(total_roznama_data):
            case_num = item['case_num']
            if case_num is not None and (df[case_num_col] == case_num).any():
                print(f"Case number {case_num} already exists. Skipping insertion.")
                continue

            while rowindex < len(df):
                rowindex += 1
                # Check if the case_num cell is empty
                if pd.isna(df.at[rowindex, case_num_col]) or df.at[rowindex, case_num_col] == '':
                    df.at[rowindex, 'Bombay High Court at Bench Nagpur'] = max_sr_no + idx + 1
                    k = 0

                    for key, value in item.items():
                        if k < len(column_names):
                            # Insert the value in the cell located at rowindex and column_names[k]
                            df.at[rowindex, column_names[k]] = value
                            k += 1
                    
                    # Insert an empty row after filling the data
                    empty_row = {col: np.nan for col in df.columns}
                    df = pd.concat([df.iloc[:rowindex+1], pd.DataFrame([empty_row]), df.iloc[rowindex+1:]]).reset_index(drop=True)
                    break

        # Save the updated DataFrame back to Excel
        df.to_excel(filename, index=False)
        excel_path = os.path.join(download_dir, filename)

        # os.system(f'start excel "{excel_path}"')
        print(f"Inserted values from total_roznama_data at available rows starting from row {rowindex - len(total_roznama_data) + 1}.")
        return True
    else:
        print("Required columns not found.")
        return False
   


def fill_roznama_excel():
    download_dir = os.path.join(BASE_DIR, 'downloads')
    filename = os.path.join(download_dir, 'Court_Case_info_format_Davane_sir.xlsx')

    # Read the Excel file
    df = pd.read_excel(filename)

    # Get the first row
    first_row = df.iloc[0]
    colname = None

    # Loop through each cell in the first row
    for col_name, cell_value in first_row.items():
        # Split the cell content into words
        words = str(cell_value).lower().split()
        # print("Column:", col_name)
        # Check if the words 'application' and 'number' are in the list
        if 'application' in words and 'number' in words:
            colname = col_name
            # print("Matched Column:", col_name)
            break


    
    def reformat_numbers(numbers_list):
        formatted_numbers = []
        pattern = re.compile(r'(\d+)/(\d+)')

        for num in numbers_list:
            match = pattern.search(num)
            if match:
                formatted_num = f"O.A.{match.group(1)}/{match.group(2)}"
                formatted_numbers.append(formatted_num)

        return formatted_numbers



    # Initialize a dictionary to store the extracted data
    extracted_data = {}

    if colname:
        # Read the entire column and drop any NaN values
        column_data = df[colname].dropna().tolist()
        # Store the data in the dictionary
        extracted_data['application_numbers'] = column_data[2:]  # Skip header

        extracted_data['application_numbers'] = reformat_numbers(extracted_data['application_numbers'])
    


    # Extracting second excel application numbers #todays-downloaded-pdf
    filename1 = os.path.join(download_dir, 'todays-pdf-extracted.xlsx')

    # Read the Excel file
    df1 = pd.read_excel(filename1)

    # Initialize a list to store extracted data
    extracted_data1 = []
    courthallA_extracted_data = {}
    courthallB_extracted_data = {}
    courthallRC_extracted_data = {}
    flag_courthall = None
    flag_stage = None

    courthallA_extracted_data['order_matters'] = []
    courthallA_extracted_data['hearing_party_matters'] = []
    courthallA_extracted_data['pronouncement_of_orders'] = []
    courthallA_extracted_data['admission_matters'] = []

    courthallB_extracted_data['order_matters'] = []
    courthallB_extracted_data['hearing_party_matters'] = []
    courthallB_extracted_data['pronouncement_of_orders'] = []
    courthallB_extracted_data['admission_matters'] = []

    courthallRC_extracted_data['order_matters'] = []
    courthallRC_extracted_data['hearing_party_matters'] = []
    courthallRC_extracted_data['pronouncement_of_orders'] = []
    courthallRC_extracted_data['admission_matters'] = []

    # Loop through each row in the DataFrame
    for i, row in df1.iterrows():
        # Loop through each cell in the row
        for col_name, cell_value in row.items():
            # Convert cell value to a string
            cell_chars = list(str(cell_value))
            # print("*********************************\n\n\n\n*******************",cell_chars)

            if 'court hall a' in ''.join(cell_chars).lower():
                # print("A*********************************\n\n\n\n*******************",''.join(cell_chars).lower())
                flag_courthall = "courthallA"
            elif 'court hall b' in ''.join(cell_chars).lower():
                # print("B*********************************\n\n\n\n*******************",''.join(cell_chars).lower())
                flag_courthall = "courthallB"
            elif 'registrar chamber' in ''.join(cell_chars).lower():
                # print("B*********************************\n\n\n\n*******************",''.join(cell_chars).lower())
                flag_courthall = "registrarchamber"

            if 'order matters' in ''.join(cell_chars).lower():
                # print("A*********************************\n\n\n\n*******************",''.join(cell_chars).lower())
                flag_stage = "order_matters"
            elif 'hearing party matters' in ''.join(cell_chars).lower():
                # print("B*********************************\n\n\n\n*******************",''.join(cell_chars).lower())
                flag_stage = "hearing_party_matters"
            elif 'pronouncement of orders' in ''.join(cell_chars).lower() or 'pronouncement of order' in ''.join(cell_chars).lower():
                # print("B*********************************\n\n\n\n*******************",''.join(cell_chars).lower())
                flag_stage = "pronouncement_of_orders"
            elif 'admission matters' in ''.join(cell_chars).lower():
                # print("B*********************************\n\n\n\n*******************",''.join(cell_chars).lower())
                flag_stage = "admission_matters"
                

            

            # print('cell_chars')
            if 'O' in cell_chars and '.' in cell_chars and 'A' in cell_chars and '/' in cell_chars:
                # If condition is met, add the cell value to the list
                split_lists = ''.join(cell_chars).split('\n')
    
                # Extract non-empty parts
                parts = [part for part in split_lists if part.strip()]

                pattern = re.compile(r'O\.A\.\s*\d+/\d+')
                matched_parts = [part for part in parts if pattern.search(part)]
                
                # print(matched_parts)
                if len(matched_parts) >= 1:
                    extracted_data1.append(str(matched_parts[0]))
                    if flag_stage is not None:
                        if flag_courthall == 'courthallA':
                            courthallA_extracted_data[flag_stage].append(str(matched_parts[0]))
                        elif flag_courthall == 'courthallB':
                            courthallB_extracted_data[flag_stage].append(str(matched_parts[0]))
                        elif flag_courthall == 'registrarchamber':
                            courthallRC_extracted_data[flag_stage].append(str(matched_parts[0]))

                break  # Break the inner loop once "O.A." is found in the row



    

    # Store the extracted data in the dictionary

    # extracted_data['roznama_application_numbers'] = extracted_data1
    extracted_data['roznama_application_numbers'] = reformat_numbers(extracted_data1)

    extracted_data['courthallA_extracted_data'] = {}
    extracted_data['courthallB_extracted_data'] = {}
    extracted_data['courthallRC_extracted_data'] = {}

    def reformat_courthall_data(courthall_data):
        for stage, numbers in courthall_data.items():
            courthall_data[stage] = reformat_numbers(numbers)
        return courthall_data

    extracted_data['courthallA_extracted_data'] = reformat_courthall_data(courthallA_extracted_data)
    extracted_data['courthallB_extracted_data'] = reformat_courthall_data(courthallB_extracted_data)
    extracted_data['courthallRC_extracted_data'] = reformat_courthall_data(courthallRC_extracted_data)

    # print(extracted_data)



    
    def normalize_number(num):
        return num.strip()

    normalized_roznama = set(normalize_number(num) for num in extracted_data['roznama_application_numbers'])
    normalized_application = set(normalize_number(num) for num in extracted_data['application_numbers'])

    # Find common numbers
    common_numbers = normalized_application.intersection(normalized_roznama)

    # print("Common Numbers:")
    # print(common_numbers)


    extracted_data['common_numbers'] = common_numbers


    if len(common_numbers) == 0:
        extracted_data['err'] = "Application Numbers Not Matched...!"
        # return render(request, "roznama_updated.html", extracted_data)
        return extracted_data



    # Load the spaCy model
    nlp = spacy.load('en_core_web_sm')
    
    # pn = []
    total_roznama_data = []
    for num in common_numbers:
        case_num = num


        party_names = []
        roznama_data = {}
        
        
        # Loop through each row in the DataFrame
        for i, row in df1.iterrows():
            # Loop through each cell in the row
            for col_name, cell_value in row.items():
                # Convert cell value to a string
                cell_chars = list(str(cell_value))            

                if 'O' in cell_chars and '.' in cell_chars and 'A' in cell_chars and '/' in cell_chars:
                    split_lists = ''.join(cell_chars).split('\n')
                    parts = [part for part in split_lists if part.strip()]
                    pattern = re.compile(r'O\.A\.\s*\d+/\d+')
                    matched_parts = [part for part in parts if pattern.search(part)]
                    
                    # print(parts)
                    # print(matched_parts)
                    matched_parts = reformat_numbers(matched_parts)
                    if case_num not in matched_parts:
                        # print("case num not matched",case_num, matched_parts)
                        break

                    # print("matched",case_num, matched_parts)


                    # current_index = row.index
                    # print(parts)
                    # print(i)
                    # print("j")
                    if len(parts) >= 2:
                        # print('jj')
                        # check the next item in matched parts list if matched as person then take that name in list of party name
                        try:
                            for m in range(1,len(parts)):
                                # doc = nlp(str(matched_parts[m]))
                                # for ent in doc.ents:
                                #     if ent.label_ == 'PERSON':
                                #         party_names.append(ent.text)
                                #         print("party names: ",party_names)
                                
                                party_names.append(parts[m])
                                # print("party names: ",party_names, case_num)

                        except Exception as e:
                            print(e)
                        
                        # nextline = df.iloc[i+1]
                        # print("nextline",nextline)
                        # check the next cell if that also contains name then add it to partynames list
                        # further_cell_value = row.iloc[k]
                        # doc = nlp(str(further_cell_value))
                        # for ent in doc.ents:
                        #     if ent.label_ == 'PERSON':
                        #         party_names.append(ent.text)
                        #         print("party names: ",party_names)

                    else:
                        try:
                            # i = current_index+1
                            j=i+1
                            # print("hi")
                            while True:
                                further_cell_value = df1.iloc[j]
                                # doc = nlp(str(further_cell_value))
                                # for ent in doc.ents:
                                #     if ent.label_ == 'PERSON':
                                        # party_names.append(ent.text)
                                        # print("party names: ",party_names)
                                party_names.append(further_cell_value)
                                # print("party names1: ",party_names, case_num)
                                # print(further_cell_value)

                                pname = None
                                        
                                doc = nlp(str(further_cell_value))
                                for ent in doc.ents:
                                    if ent.label_ == 'PERSON':
                                        pname = ent.text
                                    # print("pname",pname)
                                    # print("party names1: ",party_names, case_num)

                                if pname != None:
                                    break


                                j+=1
                            
                        
                            party_names = list(party_names[1])
                        except Exception as e:
                            print(e)
                    # print("h")
                    break  # Break the inner loop once "O.A." is found in the row
                
        # pn.append(party_names)  
        extracted_data['party_names'] = party_names

        #stage and coram finding
        mystage = None
        mycoram = None
        for x, y in extracted_data['courthallA_extracted_data'].items():
            # print(x, y)
            if case_num in y:
                mystage = x
                mycoram = "COURT HALL A"
                break
        
        for x, y in extracted_data['courthallB_extracted_data'].items():
            # print(x, y)
            if case_num in y:
                mystage = x
                mycoram = "COURT HALL B"
                break

        for x, y in extracted_data['courthallRC_extracted_data'].items():
            # print(x, y)
            if case_num in y:
                mystage = x
                mycoram = "COURT HALL RC"
                break


        filename2 = os.path.join(download_dir, 'Court_Case_info_format_Davane_sir.xlsx')

        # Read the Excel file
        df2 = pd.read_excel(filename2)

        # Get the first row
        first_row = df2.iloc[0]
        colname = None
        next_column_value = None

        # Loop through each cell in the first row
        for col_name, cell_value in first_row.items():
            # Split the cell content into words
            words = str(cell_value).lower().split()
            # print("Column:", col_name)
            # Check if the words 'application' and 'number' are in the list
            if 'application' in words and 'number' in words:
                colname = col_name
                # print("Matched Column:", col_name)
                break

            
        

        # Initialize a variable to store the row index if found
        matched_row_index = None
        
        if colname:
            target_column_name = colname
            search_value = case_num


            # Traverse the column and find the matching item
            for index, cell_value in df2[target_column_name].items():
                # print("Cellvalue.......",cell_value)
                pattern = re.compile(r'(\d+)/(\d+)')
                
                cell_value = str(cell_value).strip()
                # for num in numbers_list:
                match = pattern.search(cell_value)
                formatted_num = ''
                if match:
                    formatted_num = f"O.A.{match.group(1)}/{match.group(2)}"
                
                if formatted_num == search_value:
                    matched_row_index = index
                    break

            # Check if a matching row was found
            if matched_row_index is not None:

                first_row = df2.iloc[0]
                colname1 = None

                # Loop through each cell in the first row
                for col_name, cell_value in first_row.items():
                    # Split the cell content into words
                    words = str(cell_value).lower().split()
                    # print("Column:", col_name)
                    # Check if the words 'application' and 'number' are in the list
                    if 'remark' in words and 'status' in words and 'brief' in words:
                        colname1 = col_name
                        # print("Matched Column:", col_name)
                        break

                if colname1 is not None:
                    # Specify the column name you want to traverse
                    next_column_name = colname1


                    # Get the value of the further column in the matched row
                    next_column_value = df2.at[matched_row_index, next_column_name]
                    print(f"Matched row index: {matched_row_index}")
                    print(f"Value in the next column: {next_column_value}")
            else:
                print(f"No match found for value: {search_value}")
        else:
            print("Column of application number not found")

        # print("********************************")
        # print(case_num)
        # print(party_names[0])
        # print(mystage)
        # print(mycoram)
        roznama_desc = next_column_value
        # print(roznama_desc)
        # print("********************************")

        roznama_data['case_num'] = case_num
        roznama_data['party_names'] = party_names[0]
        roznama_data['mystage'] = mystage
        roznama_data['mycoram'] = mycoram
        roznama_data['roznama_desc'] = roznama_desc

        total_roznama_data.append(roznama_data)
        
    
    
    # extracted_data['pn'] = pn
    extracted_data['roznama_data'] = total_roznama_data


    res = fill_roznama_file_function(total_roznama_data)

    if res == True:    
        extracted_data['message'] = "Task Completed Successfully!"
    else:
        extracted_data['err'] = "Something went wrong..!\n Required Columns Not found in roznama excel"

    # return render(request, "roznama_updated.html", extracted_data)
    return extracted_data



@csrf_exempt
def return_roznama(request):
    ##return file as response
            
    download_dir = os.path.join(BASE_DIR, 'downloads')
    filename = os.path.join(download_dir, 'ROZNAMA_DATE_ORIGINAL_COPY2.xlsx')
    # file_path = request.GET.get('path')
    # Ensure file_path is provided
    if not filename:
        return Http404("File path not specified")
    
    full_path = os.path.join(download_dir, filename)
    
    # Check if the file exists
    if not os.path.exists(full_path):
        raise Http404("File does not exist")
    
    # Return the file as a response
    try:
        response = FileResponse(open(full_path, 'rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_path)}"'
        return response
    except Exception as e:
        return Http404(f"Error: {str(e)}")


@csrf_exempt
def fetch_and_download_pdf(request):
    try:
        # base_url = 'https://mat.maharashtra.gov.in/1081/Board-Display'  #base url provided to find pdfs url
        # response = requests.get(base_url, verify=False)  # Disable SSL verification
        # soup = BeautifulSoup(response.text, 'html.parser')
        # anchor = soup.find(id='SitePH_DataList1_HyperLink3_0')
        # if anchor and anchor['href']:
        #     pdf_url = anchor['href']
        #     full_pdf_url = urljoin(base_url, pdf_url)  # Join the base URL with the relative URL

        #     print(full_pdf_url)

            
        #     download_dir = os.path.join(BASE_DIR,'downloads')
        #     if not download_dir:
        #         os.makedirs(download_dir, exist_ok=True)

        #     # Download the PDF
        #     pdf_response = requests.get(full_pdf_url, verify=False)  # Disable SSL verification
        #     pdf_filename = 'downloads/todays-pdf.pdf'
        #     with open(pdf_filename, 'wb') as f:
        #         f.write(pdf_response.content)
                

        #     print("done")
        #     # Render the success page

        #     read_pdf_to_excel()
            exdata = fill_roznama_excel()
            if exdata is None:
                print("exdata was none")
                return render(request, 'pdf_downloaded.html', {'err': 'Opps..! Something Went Wrong, Error Occured..!, Cant extract data'})

            print(exdata)

            return render(request, 'pdf_downloaded.html', exdata)
    except Exception as e:
        print(e)
        return render(request, 'pdf_downloaded.html', {'err': 'Opps..! Something Went Wrong, Error Occured..!'})
    else:
        return render(request, 'pdf_downloaded.html', {'err': 'PDF Not Founded On Website, Something went wrong'})





@csrf_exempt
def change_caseinfo_excelfile(request):
    mydic = {}
    if request.method == 'POST':
        try:
            form = ChangeExcel(request.POST, request.FILES)
            if form.is_valid():
                myfile = request.FILES['file']
                download_dir = os.path.join(settings.BASE_DIR, 'downloads')
                # Ensure the downloads directory exists
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                # Save the file
                file_path = os.path.join(download_dir, 'Court_Case_info_format_Davane_sir.xlsx')
                with open(file_path, 'wb+') as destination:
                    for chunk in myfile.chunks():
                        destination.write(chunk)
            
            mydic['msg']='Excel File Changed Successfully..!'
        except Exception as e:
            print(e)
            mydic['err'] = 'Oops..! Something Went Wrong'



        return render(request,'index.html',mydic)
    else:
        form = ChangeExcel()
        return render(request,'change_court_excel.html',{'form': form})
    
