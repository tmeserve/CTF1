import vin, vininfo, qrcode, json, os, requests, time, sys
import boto3, random
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

def test(event=None, context=None):
    return event
    params = event['headerParams']
    
    item = params['EventType']
    func_call = {
        "Error": "Nothing found in the headers!"
    }
    if item == 'get_vin':
        func_call = get_vin(params, context)
    elif item == 'random_vin':
        func_call = random_vin(params, context)
    elif item == 'decode_vin':
        func_call = decode_vin(params, context)
    elif item == 'more_details':
        func_call = more_details(params, context)
    return func_call

def get_vin(event=None, context=None):
    table = boto3.resource('dynamodb').Table('VinInfo')
    make = ""
    model = ""
    year = ""
    if 'Makes' in event:
        make = event['Makes']
    if 'Models' in event:
        model = event['Models']
    if 'Years' in event:
        year = event['Years']
    
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
                items = table.scan(FilterExpression=makeq & modelq & yearq)
                items = [item['Vins'] for item in items['Items']]
                return {
                    'vin': random.choice(items),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                }
            else:
                items = table.scan(FilterExpression=makeq & modelq)
                items = [item['Years'] for item in items['Items']]
                return {
                    'values': items,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                }
        else:
            items = table.scan(FilterExpression=makeq)
            items = [item['Models'] for item in items['Items']]
            return {
                'values': items,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
            }
    else:
        data = table.scan()
        items = data['Items']
        items = [item['Makes'] for item in items]
        itemsc = items.copy()
        toAppend = []
        for item in items:
            if item in itemsc:
                if item in toAppend:
                    continue
                toAppend.append(item)
        items = toAppend.copy()
        vins = data['Items']
        vins = [item['Vins'] for item in vins]
        vinsc = vins.copy()
        toAppend = []
        for item in vins:
            if item in vinsc:
                if item in toAppend:
                    continue
                toAppend.append(item)
        vins = toAppend.copy()
        
        vin = random.choice(vins)
        decoded = decode(vin)
        if 'Error' in decoded:
            return {
                'Error': 'Request Timedout',
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
            } 
    return {
        'values': items,
        'make': decoded['make'],
        'model': decoded['model'],
        'years': decoded['years'],
        'vin': vin,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
    }

def random_vin(event=None, context=None):
    table = boto3.resource('dynamodb').Table('VinInfo')
    
    v = vin.getRandomVin()
    data = decode(v)
    
    return data

def decode(vin):
    base_url = 'https://vpic.nhtsa.dot.gov/api/vehicles'
    
    table = boto3.resource('dynamodb').Table('VinInfo')
    
    decodev = vininfo.Vin(vin)
    
    if not decodev.verify_checksum():
        return {
            'Error': 'Invalid VIN!'
        }
    model = ""
    make = ""
    try:
        for year in decodev.years:
            
            r = requests.get(base_url + '/DecodeVin/{0}?format=json&modelyear={1}'.format(vin, year))
            json_data = r.json()
            for item in json_data['Results']:
                if item['Variable'] == 'Make':
                    make = item['Value']
                elif item['Variable'] == 'Model':
                    model = item['Value']
                    if not model:
                        model = make
            try:
                
                items = table.get_item(Key={
                    'Makes': make,
                    'Models': model,
                    'Years': str(year),
                    'Vins': vin,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                })
            except ClientError as e:
                table.put_item(Item={
                    'Makes': make,
                    'Models': model,
                    'Years': str(year),
                    'Vins': vin,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                })
                return {
                        "make": make,
                        "model": model,
                        "years": decodev.years,
                        "vin": vin,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                    }
            else:
                return {
                    "make": make,
                    "model": model,
                    "years": decodev.years,
                    "vin": vin,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                }
            
    except requests.exceptions.ConnectionError:
        return {
            'Error': 'Request Timedout',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
        }    

def decode_vin(event=None, context=None):
    if not 'vin' in event:
        return {
            'Error': 'Vin parameter was not passed in.',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
        }
    
    return decode(event['vin'])
        
def more_details(event=None, context=None):
    if not 'vin' in event:
        return {
            "Error": "Vin parameter was not passed in.",
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
        }
    
    base_url = 'https://vpic.nhtsa.dot.gov/api/vehicles'
    v = event['vin']
    print(v, ' is vin')
    
    table = boto3.resource('dynamodb').Table('VinInfo')
    
    decodev = vininfo.Vin(v)
    print(decodev.details, ' is decodev')
    if decodev.details:
        body = decodev.details.body
        engine = decodev.details.engine
        plant = decodev.details.plant
        serial = decodev.details.serial
        trans = decodev.details.transmission
    
    
    if not decodev.verify_checksum():
        return {
            'Error': 'Invalid VIN!',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
        }
    model = ""
    make = ""
    try:
        for year in decodev.years:
            
            r = requests.get(base_url + '/DecodeVin/{0}?format=json&modelyear={1}'.format(v, year))
            json_data = r.json()
            for item in json_data['Results']:
                if item['Variable'] == 'Make':
                    make = item['Value']
                elif item['Variable'] == 'Model':
                    model = item['Value']
                    if not model:
                        model = make
                elif item['Variable'] == 'Manufacturer Name':
                    manu = item['Value']
                elif item['Variable'] == 'Vehicle Type':
                    vtype = item['Value']
            # })
            try:
                
                items = table.get_item(Key={
                    'Makes': make,
                    'Models': model,
                    'Years': str(year),
                    'Vins': v,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                })
            except ClientError as e:
                table.put_item(Item={
                    'Makes': make,
                    'Models': model,
                    'Years': str(year),
                    'Vins': v,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                })
                if decodev.details:
                    return {
                        'make': make,
                        'model': model,
                        'years': decodev.years,
                        'manufacture': manu,
                        'type': vtype,
                        'body': body,
                        'engine': engine,
                        'plant': plant,
                        'serial': serial,
                        'transmission': trans,
                        'vin': v,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                    }
                return {
                    'make': make,
                    'model': model,
                    'years': decodev.years,
                    'manufacture': manu,
                    'type': vtype,
                    'vin': v,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                }
            else:
                if decodev.details:
                    return {
                        'make': make,
                        'model': model,
                        'years': decodev.years,
                        'manufacture': manu,
                        'type': vtype,
                        'body': body,
                        'engine': engine,
                        'plant': plant,
                        'serial': serial,
                        'transmission': trans,
                        'vin': v,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                    }
                return {
                    'make': make,
                    'model': model,
                    'years': decodev.years,
                    'manufacture': manu,
                    'type': vtype,
                    'vin': v,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                }
            
    except requests.exceptions.ConnectionError:
        return {
            'Error': 'Request Timedout',
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
        }