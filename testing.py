import vin, vininfo, qrcode, json, os, requests, time, sys
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# with open('information.txt', 'r') as information:
#     for line in information.readlines():
#         if line.lower().startswith('user:'):
#             user = line.lower().split('user:')[1].strip()
#         elif line.lower().startswith('password:'):
#             password = line.lower().split('password:')[1].strip()
#         elif line.lower().startswith('ip:'):
#             ip = line.lower().split('ip:')[1].strip()
#         elif line.lower().startswith('port:'):
#             port = line.lower().split('port:')[1].strip()

def test(event=None, context=None):
    item = event['EventType']
    if item == 'get_vin':
        func_call = get_vin(event, context)
    if item == 'random_vin':
        func_call = random_vin(event, context)
    return func_call

def get_vin(event=None, context=None):
    table = boto3.resource('dynamodb').Table('VinInfo')
    make = ""
    model = ""
    year = ""
    
    if 'make' in event:
        make = event['make']
    if 'model' in event:
        model = event['model']
    if 'year' in event:
        year = event['year']
    
    makeq = None
    modelq = None
    yearq = None
    if make:
        makeq = Key('Makes').eq(make)
    if model:
        modelq = Key('Models').eq(model)
    if year:
        yearq = Key('Years').eq(str(year))
    
    if makeq:
        if modelq:
            if yearq:
                items = table.query(KeyConditionExpression=makeq & modelq & yearq)
            else:
                items = table.query(KeyConditionExpression=makeq & modelq)
        else:
            items = table.query(KeyConditionExpression=makeq)
    else:
        items = table.scan()
        items = items['Items']
        items = [item['Makes'] for item in items]
        
    return items

def random_vin(event=None, context=None):
    table = boto3.resource('dynamodb').Table('VinInfo')
    v = vin.getRandomVin()
    
    decodev = vininfo.Vin(v)
    
    base_url = 'https://vpic.nhtsa.dot.gov/api/vehicles'
    
    try:
        for year in decodev.years:
            
            r = requests.get(base_url + '/DecodeVin/{0}?format=json&modelyear={1}'.format(v, year))
            json_data = r.json()
            for item in json_data['Results']:
                if item['Variable'] == 'Make':
                    # makes_json['Value'] = item1['Value']
                    # make = item1['Value']
                    make = item['Value']
                elif item['Variable'] == 'Model':
                    model = item['Value']
                    if not model:
                        model = make
            
            # items = table.get_item(Key={
            #     'Makes': make,
            #     'Models': model,
            #     'Years': str(year)
            # })
            try:
                
                # items = table.query(KeyConditionExpression=Key('Makes').eq(make) & Key('Models').eq(model) & Key('Years').eq(year))
                items = table.get_item(Key={
                    'Makes': make,
                    'Models': model,
                    'Years': year,
                    'Vins': v
                })
            except ClientError as e:
                print(e.response['Error'])
                table.put_item(Item={
                    'Makes': make,
                    'Models': model,
                    'Years': year,
                    'Vins': v
                })
            else:
                print(items, ' is items')
            
    except requests.exceptions.ConnectionError:
        return 'Request Timedout'
    
    # decodev.country, decodev.manufacturer, decodev.region, decodev.years
    

# db = client['Vins']

# import vi

# l = ['hi']

# Gens a value error

# print(l.index('hi1'))

# base_url = 'https://vpic.nhtsa.dot.gov/api/vehicles'

# if not os.path.isfile(os.path.join(os.getcwd(), 'makes.json')):
#     tmp_file = open(os.path.join(os.getcwd(), 'makes.json'), 'w+')
#     tmp_file.close()

# try:
#     make_obj = json.load(open('makes.json', 'r'))
# except json.JSONDecodeError:
#     make_obj = {
#         'Makes': [],
#         'Vins': []
#     }

# def new_json(make_obj, v, decodev):
#     make_obj['Vins'].append([v])
#     # decodev = vininfo.Vin(v)
#     makes_json = {
#         'Value': '',
#         'Models': []
#     }
#     models_json = {
#         'Value': '',
#         'Years': []
#     }
    
#     for year in decodev.years:
#         years_json = {
#             "Value": year,
#             'Vins': []
#         }
#         try:
            
#             r = requests.get(base_url + '/DecodeVin/{0}?format=json&modelyear={1}'.format(v, year))
#             if r.status_code == 200:
                
#                 json_data = r.json()
                # for item1 in json_data['Results']:
                #     if item1['Variable'] == 'Make':
                #         makes_json['Value'] = item1['Value']
                #         make = item1['Value']
                #     elif item1['Variable'] == 'Model':
                #         model = item1['Value']
                #         if not model:
                #             model = make
                #         models_json['Value'] = model
                        
#                         years_json['Vins'].append(v)
#                         # models_json['Years'].append(years_json)
#                 # vin_json_obj['Years'].append(years_json)
#                 if make_obj['Makes']:
#                     for item in make_obj['Makes']:
#                         if item['Value'] == make:
#                             if item['Models']:
#                                 for models in item['Models']:
#                                     if models['Value'] == model:
#                                         if models['Years']:
#                                             for year1 in models['Years']:
#                                                 if year1['Value'] == year:
#                                                     try:
#                                                         index = year1['Vins'].index(v)
#                                                     except ValueError:
#                                                         if not years_json['Vins']:
#                                                             years_json['Vins'].append(v)
#                                                 else:
#                                                     models_json['Years'].append(years_json)
#                                         else:
#                                             models_json['Years'].append(years_json)
#                             else:
#                                 if not years_json['Vins']:
#                                     years_json['Vins'].append(v)
#                                 models_json['Years'].append(years_json)
#                         else:
#                             if not years_json['Vins']:
#                                 years_json['Vins'].append(v)
#                             models_json['Years'].append(years_json)
#                     makes_json['Models'].append(models_json)
#                 else:
#                     if not years_json['Vins']:
#                         years_json['Vins'].append(v)
#                     models_json['Years'].append(years_json)
#                     makes_json['Models'].append(models_json)
#                 return ('Completed', makes_json)
#                 # return ("Completed", make, model, years_json)
#         except requests.exceptions.ConnectionError:
#             # return ("Connection Error", 0, 0, 0)
#             return ('Connection Error', make_obj['Makes'])

# qr = qrcode.QRCode(
#     version=1,
#     error_correction=qrcode.constants.ERROR_CORRECT_H,
#     box_size=10,
#     border=4
# )

# qr.add_data('some data')
# qr.make(fit=True)

# img = qr.make_image()

# img.save('testing.png')
# i = 0
# while i < 381:
#     print(i)
#     v = vin.getRandomVin()
#     # print(v)
#     decodev = vininfo.Vin(v)
#     index = None
#     if make_obj['Vins']:
#         for item in make_obj['Vins']:
#             try:
#                 index = make_obj['Vins'].index(v)
#             except ValueError:
#                 pass
        
#         if not index:
#             new_js = ("", make_obj['Makes'])
#             tries = 1
#             while not new_js[0] == "Completed":
#                 # new_js = new_json(make_obj, v, decodev)
#                 makes_json = new_js[1]
#                 if tries == 10:
#                     print('Error: Got a connection error 10 times in a row.')
#                     sys.exit()
#                 if new_js[0] == "Completed":
#                     make_obj['Makes'].append(makes_json)
#                     tries = 0
#                     break
#                 elif new_js[0] == "Connection Error":
#                     time.sleep(5)
#                     tries += 1
#     else:
#         new_js = ("", make_obj['Makes'])
#         tries = 1
#         while not new_js[0] == "Completed":
#             # new_js = new_json(make_obj, v, decodev)
#             makes_json = new_js[1]
#             if tries == 10:
#                 print('Error: Got a connection error 10 times in a row.')
#                 sys.exit()
#             # if new_js[0] == "Completed":
#                 # make_obj['Makes'].append(makes_json)
#                 # tries = 0
#                 # break
#             elif new_js[0] == "Connection Error":
#                 time.sleep(5)
#     i += 1
# with open('makes.json', 'w') as json_file:
#     json.dump(make_obj, json_file, indent=4)
# print(json.dumps(make_obj, indent=4))

# print(json_obj)
# qr = qrcode.QRCode(
#     version=1,
#     error_correction=qrcode.constants.ERROR_CORRECT_H,
#     box_size=10,
#     border=4
# )

# qr.add_data("{0} {1}\n".format(v, vin.isValidVin(v)))
# qr.add_data("{0} {1} {2} {3}\n".format(decodev.country, decodev.manufacturer, decodev.region, decodev.years))
# qr.make(fit=True)

# img = qr.make_image()

# img.save('qrcode.png')