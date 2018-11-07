"""
Written by Niqui O'Neill
This script requires unicodecsv to be installed
This script allows the users to download metadata from nuxeo and place it either in a google
spreadsheet or tsv file.
it also allows for metadata to be downloaded from the collection or item level
it also asks if all headers should be downloaded or if the empty items should not be downloaded
Nuxeo has to be installed for this script to work
"""
import os
import sys
import argparse
import unicodecsv as csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pynux import utils


def main(args=None):
    '''Parse command line arguments.'''
    parser = argparse.ArgumentParser(
        description='''This script exports metadata from Nuxeo to a local TSV file or to a Google
                       Sheets spreadsheet.''')
    parser.add_argument(
        'path', nargs=1, help='Nuxeo path')
    parser.add_argument(
        '--object-level', action='store_true', help='get metadata for parent objects only')
    parser.add_argument(
        '--item-level', action='store_true', help='''get metadata including child items of complex
                                                  objects''')
    parser.add_argument(
        '--all-headers', action='store_true', help='''include headers for fields that do not contain
                                                   data''')
    parser.add_argument(
        '--url', type=str, required=False, help='Google Sheets URL')
    parser.add_argument(
        '--outfile', type=str, required=False, help='local file path to write out to')

    # print help if no args given
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # parse
    if args is None:
        args = parser.parse_args()

    if args.object_level:
        if args.url:
            try:
                google_object(args.path[0], args.url, args.all_headers)
            except:
                print("""\n*********\nWriting to Google document did not work.
                      Make sure that Google document has been shared with API key email address""")
        else:
            obj = object_level(args.path[0], args.all_headers)
            with open(args.outfile, "wb") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=obj['fieldnames'], delimiter="\t")
                writer.writeheader()
                for row in obj['data']:
                    writer.writerow(row)
    if args.item_level:
        if args.url:
            try:
                google_item(args.path[0], args.url, args.all_headers)
            except:
                print("""\n*********\nWriting to Google document did not work.
                      Make sure that Google document has been shared with API key email address""")
        else:
            item = item_level(args.path[0], args.all_headers)
            with open(args.outfile, "wb") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=item['fieldnames'], delimiter="\t")
                writer.writeheader()
                for row in item['data']:
                    writer.writerow(row)


def get_metadata(single_path, all_headers):
    """Get metadata for a single Nuxeo item or object, return as dict."""
    metadata = {}
    get_title(metadata, single_path)
    get_filepath(metadata, single_path)
    get_type(metadata, single_path, all_headers)
    get_alt_title(metadata, single_path, all_headers)
    get_identifier(metadata, single_path, all_headers)
    get_local_identifier(metadata, single_path, all_headers)
    get_campus_unit(metadata, single_path, all_headers)
    get_date(metadata, single_path, all_headers)
    get_publication(metadata, single_path, all_headers)
    get_creator(metadata, single_path, all_headers)
    get_contributor(metadata, single_path, all_headers)
    get_format(metadata, single_path, all_headers)
    get_description(metadata, single_path, all_headers)
    get_extent(metadata, single_path, all_headers)
    get_language(metadata, single_path, all_headers)
    get_temporal_coverage(metadata, single_path, all_headers)
    get_transcription(metadata, single_path, all_headers)
    get_access_restrictions(metadata, single_path, all_headers)
    get_rights_statement(metadata, single_path, all_headers)
    get_rights_status(metadata, single_path, all_headers)
    get_copyright_holder(metadata, single_path, all_headers)
    get_copyright_info(metadata, single_path, all_headers)
    get_collection(metadata, single_path, all_headers)
    get_related_resource(metadata, single_path, all_headers)
    get_source(metadata, single_path, all_headers)
    get_subject_name(metadata, single_path, all_headers)
    get_place(metadata, single_path, all_headers)
    get_subject_topic(metadata, single_path, all_headers)
    get_form_genre(metadata, single_path, all_headers)
    get_provenance(metadata, single_path, all_headers)
    get_physical_location(metadata, single_path, all_headers)
    return metadata


def object_level(path, all_headers):
    nx = utils.Nuxeo()
    data = []
    for nx_object in nx.children(path):
        data2 = get_metadata(nx_object, all_headers)
        data.append(data2)

    # ensures that File path, Title and Type are the first three rows
    fieldnames = ['File path', 'Title', 'Type']
    for data2 in data:
        for key, value in data2.items():
            if key not in fieldnames:
                fieldnames.append(key)

    return {'fieldnames': fieldnames, 'data': data}


def item_level(path, all_headers):
    nx = utils.Nuxeo()
    data = []
    for nx_object in nx.children(path):
        for nx_item in nx.children(nx_object['path']):
            data2 = get_metadata(nx_item, all_headers)
            data.append(data2)

    # ensures that File path, Title and Type are the first three rows
    fieldnames = ['File path', 'Title', 'Type']
    for data2 in data:
        for key, value in data2.items():
            if key not in fieldnames:
                fieldnames.append(key)

    return {'fieldnames': fieldnames, 'data': data}

def google_object(path, url, all_headers):
    obj = object_level(path, all_headers)
    nx = utils.Nuxeo()
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    with open("temp.csv", "wb") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=obj['fieldnames'])
        writer.writeheader()
        for row in obj['data']:
            writer.writerow(row)
    with open("temp.csv", encoding="utf8") as tempfile:
        sheet = tempfile.read() + '\n'
    sheet_id = client.open_by_url(url).id
    client.import_csv(sheet_id, sheet)
    client.open_by_key(sheet_id).sheet1.update_title(
        "nuxeo_object_%s" % nx.get_metadata(path=path)['properties']['dc:title'])
    os.remove("temp.csv")


def google_item(path, url, all_headers):
    item = item_level(path, all_headers)
    nx = utils.Nuxeo()
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'client_secret.json', scope)
    client = gspread.authorize(creds)
    with open("temp.csv", "wb") as csvfile:  # creates temporary csv file
        writer = csv.DictWriter(csvfile, fieldnames=item['fieldnames'])
        writer.writeheader()
        for row in item['data']:
            writer.writerow(row)
    with open("temp.csv", encoding="utf8") as tempfile:  # opens and reads temporary csv file
        sheet = tempfile.read() + '\n'
    sheet_id = client.open_by_url(url).id
    client.import_csv(sheet_id, sheet)  # writes csv file to google sheet
    client.open_by_key(sheet_id).sheet1.update_title(
        "nuxeo_item_%s" % nx.get_metadata(path=path)['properties']['dc:title'])
    os.remove("temp.csv")  # removes temporary csv

# Functions for getting individual metatdata elements, called by get_metadata()
def get_title(data2, item):  # gets title
    data2['Title'] = item['properties']['dc:title']


def get_filepath(data2, item):  # gets path
    data2['File path'] = item['path']


# gets type, inputs are dictionary (data2), nuxeo (item), all_headers input
def get_type(data2, item, all_headers):
    if item['properties']['ucldc_schema:type']:
        data2['Type'] = item['properties']['ucldc_schema:type']
    elif all_headers:
        data2['Type'] = ''


def get_alt_title(data2, item, all_headers):
    altnumb = 0
    if (isinstance(item['properties']['ucldc_schema:alternativetitle'], list)
            and item['properties']['ucldc_schema:alternativetitle']):
        while altnumb < len(item['properties']['ucldc_schema:alternativetitle']):
            numb = altnumb + 1
            name = 'Alternative Title %d' % numb
            data2[name] = item['properties'][
                'ucldc_schema:alternativetitle'][altnumb]
            altnumb += 1
    elif all_headers:
        data2['Alternative Title 1'] = ''


def get_identifier(data2, item, all_headers):
    if item['properties']['ucldc_schema:identifier']:
        data2['Identifier'] = item['properties']['ucldc_schema:identifier']
    elif all_headers:
        data2['Identifier'] = ''


def get_local_identifier(data2, item, all_headers):
    locnumb = 0
    if (isinstance(item['properties']['ucldc_schema:localidentifier'], list)
            and item['properties']['ucldc_schema:localidentifier']):
        while locnumb < len(item['properties']['ucldc_schema:localidentifier']):
            numb = locnumb + 1
            name = 'Local Identifier %d' % numb
            data2[name] = item['properties'][
                'ucldc_schema:localidentifier'][locnumb]
            locnumb += 1
    elif all_headers:
        data2['Local Identifier 1'] = ''


def get_campus_unit(data2, item, all_headers):
    campnumb = 0
    if (isinstance(item['properties']['ucldc_schema:campusunit'], list)
            and item['properties']['ucldc_schema:campusunit']):
        while campnumb < len(item['properties']['ucldc_schema:campusunit']):
            numb = campnumb + 1
            name = 'Campus/Unit %d' % numb
            data2[name] = item['properties']['ucldc_schema:campusunit'][campnumb]
            campnumb += 1
    elif all_headers:
        data2['Campus/Unit 1'] = ''


def get_date(data2, item, all_headers):
    datenumb = 0
    if (isinstance(item['properties']['ucldc_schema:date'], list)
            and item['properties']['ucldc_schema:date']):
        while datenumb < len(item['properties']['ucldc_schema:date']):
            numb = datenumb + 1
            try:
                name = 'Date %d' % numb
                if item['properties']['ucldc_schema:date'][datenumb]['date']:
                    data2[name] = item['properties'][
                        'ucldc_schema:date'][datenumb]['date']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Date %d Type' % numb
                if item['properties']['ucldc_schema:date'][datenumb]['datetype']:
                    data2[name] = item['properties'][
                        'ucldc_schema:date'][datenumb]['datetype']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Date %d Inclusive Start' % numb
                if item['properties']['ucldc_schema:date'][datenumb]['inclusivestart']:
                    data2[name] = item['properties']['ucldc_schema:date'][
                        datenumb]['inclusivestart']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Date %d Inclusive End' % numb
                if item['properties']['ucldc_schema:date'][datenumb]['inclusiveend']:
                    data2[name] = item['properties'][
                        'ucldc_schema:date'][datenumb]['inclusiveend']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Date %d Single' % numb
                if item['properties']['ucldc_schema:date'][datenumb]['single']:
                    data2[name] = item['properties'][
                        'ucldc_schema:date'][datenumb]['single']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            datenumb += 1
    elif all_headers:
        data2['Date 1'] = ''
        data2['Date 1 Type'] = ''
        data2['Date 1 Inclusive Start'] = ''
        data2['Date 1 Inclusive End'] = ''
        data2['Date 1 Single'] = ''


def get_publication(data2, item, all_headers):
    pubnumb = 0
    if (isinstance(item['properties']['ucldc_schema:publisher'], list)
            and item['properties']['ucldc_schema:publisher']):
        while pubnumb < len(item['properties']['ucldc_schema:publisher']):
            numb = pubnumb + 1
            name = 'Publication/Origination Info %d' % numb
            data2[name] = item['properties']['ucldc_schema:publisher'][pubnumb]
            pubnumb += 1
    elif all_headers:
        data2['Publication/Origination Info 1'] = ''


def get_creator(data2, item, all_headers):
    creatnumb = 0
    if (isinstance(item['properties']['ucldc_schema:creator'], list)
            and item['properties']['ucldc_schema:creator']):
        while creatnumb < len(item['properties']['ucldc_schema:creator']):
            numb = creatnumb + 1
            try:
                name = 'Creator %d Name' % numb
                if item['properties']['ucldc_schema:creator'][creatnumb]['name']:
                    data2[name] = item['properties'][
                        'ucldc_schema:creator'][creatnumb]['name']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Creator %d Name Type' % numb
                if item['properties']['ucldc_schema:creator'][creatnumb]['nametype']:
                    data2[name] = item['properties'][
                        'ucldc_schema:creator'][creatnumb]['nametype']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Creator %d Role' % numb
                if item['properties']['ucldc_schema:creator'][creatnumb]['role']:
                    data2[name] = item['properties'][
                        'ucldc_schema:creator'][creatnumb]['role']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Creator %d Source' % numb
                if item['properties']['ucldc_schema:creator'][creatnumb]['source']:
                    data2[name] = item['properties'][
                        'ucldc_schema:creator'][creatnumb]['source']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Creator %d Authority ID' % numb
                if item['properties']['ucldc_schema:creator'][creatnumb]['authorityid']:
                    data2[name] = item['properties'][
                        'ucldc_schema:creator'][creatnumb]['authorityid']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            creatnumb += 1
    elif all_headers:
        data2['Creator 1 Name'] = ''
        data2['Creator 1 Name Type'] = ''
        data2['Creator 1 Role'] = ''
        data2['Creator 1 Source'] = ''
        data2['Creator 1 Authority ID'] = ''


def get_contributor(data2, item, all_headers):
    contnumb = 0
    if (isinstance(item['properties']['ucldc_schema:contributor'], list)
            and item['properties']['ucldc_schema:contributor']):
        while contnumb < len(item['properties']['ucldc_schema:contributor']):
            numb = contnumb + 1
            try:
                name = 'Contributor %d Name' % numb
                if item['properties']['ucldc_schema:contributor'][contnumb]['name']:
                    data2[name] = item['properties'][
                        'ucldc_schema:contributor'][contnumb]['name']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Contributor %d Name Type' % numb
                if item['properties']['ucldc_schema:contributor'][contnumb]['nametype']:
                    data2[name] = item['properties'][
                        'ucldc_schema:contributor'][contnumb]['nametype']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Contributor %d Role' % numb
                if item['properties']['ucldc_schema:contributor'][contnumb]['role']:
                    data2[name] = item['properties'][
                        'ucldc_schema:contributor'][contnumb]['role']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Contributor %d Source' % numb
                if item['properties']['ucldc_schema:contributor'][contnumb]['source']:
                    data2[name] = item['properties'][
                        'ucldc_schema:contributor'][contnumb]['source']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Contributor %d Authority ID' % numb
                if item['properties']['ucldc_schema:contributor'][contnumb]['authorityid']:
                    data2[name] = item['properties'][
                        'ucldc_schema:contributor'][contnumb]['authorityid']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            contnumb += 1
    elif all_headers:
        data2['Contributor 1 Name'] = ''
        data2['Contributor 1 Name Type'] = ''
        data2['Contributor 1 Role'] = ''
        data2['Contributor 1 Source'] = ''
        data2['Contributor 1 Authority ID'] = ''


def get_format(data2, item, all_headers):
    if item['properties']['ucldc_schema:physdesc']:
        data2['Format/Physical Description'] = item['properties']['ucldc_schema:physdesc']
    elif all_headers:
        data2['Format/Physical Description'] = ''


def get_description(data2, item, all_headers):
    descnumb = 0
    if (isinstance(item['properties']['ucldc_schema:description'], list)
            and item['properties']['ucldc_schema:description']):
        while descnumb < len(item['properties']['ucldc_schema:description']):
            numb = descnumb + 1
            try:
                name = "Description %d Note" % numb
                if item['properties']['ucldc_schema:description'][descnumb]['item']:
                    data2[name] = item['properties'][
                        'ucldc_schema:description'][descnumb]['item']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = "Description %d Type" % numb
                if item['properties']['ucldc_schema:description'][descnumb]['type']:
                    data2[name] = item['properties'][
                        'ucldc_schema:description'][descnumb]['type']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            descnumb += 1
    elif all_headers:
        data2['Description 1 Note'] = ''
        data2['Description 1 Type'] = ''


def get_extent(data2, item, all_headers):
    if item['properties']['ucldc_schema:extent']:
        data2['Extent'] = item['properties']['ucldc_schema:extent']
    elif all_headers:
        data2['Extent'] = ''


def get_language(data2, item, all_headers):
    langnumb = 0
    if (isinstance(item['properties']['ucldc_schema:language'], list)
            and item['properties']['ucldc_schema:language']):
        while langnumb < len(item['properties']['ucldc_schema:language']):
            numb = langnumb + 1
            try:
                name = "Language %d" % numb
                if item['properties']['ucldc_schema:language'][langnumb]['language']:
                    data2[name] = item['properties'][
                        'ucldc_schema:language'][langnumb]['language']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = "Language %d Code" % numb
                if item['properties']['ucldc_schema:language'][langnumb]['code']:
                    data2[name] = item['properties'][
                        'ucldc_schema:language'][langnumb]['code']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            langnumb += 1
    elif all_headers:
        data2['Language 1'] = ''
        data2['Language 1 Code'] = ''


def get_temporal_coverage(data2, item, all_headers):
    tempnumb = 0
    if (isinstance(item['properties']['ucldc_schema:temporalcoverage'], list)
            and item['properties']['ucldc_schema:temporalcoverage']):
        while tempnumb < len(item['properties']['ucldc_schema:temporalcoverage']):
            numb = tempnumb + 1
            name = 'Temporal Coverage %d' % numb
            data2[name] = item['properties'][
                'ucldc_schema:temporalcoverage'][tempnumb]
            tempnumb += 1
    elif all_headers:
        data2['Temporal Coverage 1'] = ''


def get_transcription(data2, item, all_headers):
    if item['properties']['ucldc_schema:transcription']:
        data2['Transcription'] = item['properties']['ucldc_schema:transcription']
    elif all_headers:
        data2['Transcription'] = ''


def get_access_restrictions(data2, item, all_headers):
    if item['properties']['ucldc_schema:accessrestrict']:
        data2['Access Restrictions'] = item['properties'][
            'ucldc_schema:accessrestrict']
    elif all_headers:
        data2['Access Restrictions'] = ''


def get_rights_statement(data2, item, all_headers):
    if item['properties']['ucldc_schema:rightsstatement']:
        data2['Copyright Statement'] = item['properties'][
            'ucldc_schema:rightsstatement']
    elif all_headers:
        data2['Copyright Statement'] = ''


def get_rights_status(data2, item, all_headers):
    if item['properties']['ucldc_schema:rightsstatus']:
        data2['Copyright Status'] = item['properties'][
            'ucldc_schema:rightsstatus']
    elif all_headers:
        data2['Copyright Status'] = ''


def get_copyright_holder(data2, item, all_headers):
    rightsnumb = 0
    if (isinstance(item['properties']['ucldc_schema:rightsholder'], list)
            and item['properties']['ucldc_schema:rightsholder']):
        while rightsnumb < len(item['properties']['ucldc_schema:rightsholder']):
            numb = rightsnumb + 1
            try:
                name = 'Copyright Holder %d Name' % numb
                if item['properties']['ucldc_schema:rightsholder'][rightsnumb]['name']:
                    data2[name] = item['properties'][
                        'ucldc_schema:rightsholder'][rightsnumb]['name']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Copyright Holder %d Name Type' % numb
                if item['properties']['ucldc_schema:rightsholder'][rightsnumb]['nametype']:
                    data2[name] = item['properties'][
                        'ucldc_schema:rightsholder'][rightsnumb]['nametype']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Copyright Holder %d Source' % numb
                if item['properties']['ucldc_schema:rightsholder'][rightsnumb]['source']:
                    data2[name] = item['properties'][
                        'ucldc_schema:rightsholder'][rightsnumb]['source']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Copyright Holder %d Authority ID' % numb
                if item['properties']['ucldc_schema:rightsholder'][rightsnumb]['authorityid']:
                    data2[name] = item['properties'][
                        'ucldc_schema:rightsholder'][rightsnumb]['authorityid']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            rightsnumb += 1
    elif all_headers:
        data2['Copyright Holder 1 Name'] = ''
        data2['Copyright Holder 1 Name Type'] = ''
        data2['Copyright Holder 1 Source'] = ''
        data2['Copyright Holder 1 Authority ID'] = ''


def get_copyright_info(data2, item, all_headers):
    if item['properties']['ucldc_schema:rightscontact']:
        data2['Copyright Contact'] = item['properties'][
            'ucldc_schema:rightscontact']
    elif all_headers:
        data2['Copyright Contact'] = ''

    if item['properties']['ucldc_schema:rightsnotice']:
        data2['Copyright Notice'] = item['properties'][
            'ucldc_schema:rightsnotice']
    elif all_headers:
        data2['Copyright Notice'] = ''

    if item['properties']['ucldc_schema:rightsdeterminationdate']:
        data2['Copyright Determination Date'] = item['properties'][
            'ucldc_schema:rightsdeterminationdate']
    elif all_headers:
        data2['Copyright Determination Date'] = ''

    if item['properties']['ucldc_schema:rightsstartdate']:
        data2['Copyright Start Date'] = item['properties'][
            'ucldc_schema:rightsstartdate']
    elif all_headers:
        data2['Copyright Start Date'] = ''

    if item['properties']['ucldc_schema:rightsenddate']:
        data2['Copyright End Date'] = item['properties'][
            'ucldc_schema:rightsenddate']
    elif all_headers:
        data2['Copyright End Date'] = ''

    if item['properties']['ucldc_schema:rightsjurisdiction']:
        data2['Copyright Jurisdiction'] = item['properties'][
            'ucldc_schema:rightsjurisdiction']
    elif all_headers:
        data2['Copyright Jurisdiction'] = ''

    if item['properties']['ucldc_schema:rightsnote']:
        data2['Copyright Note'] = item['properties']['ucldc_schema:rightsnote']
    elif all_headers:
        data2['Copyright Note'] = ''


def get_collection(data2, item, all_headers):
    collnumb = 0
    if (isinstance(item['properties']['ucldc_schema:collection'], list)
            and item['properties']['ucldc_schema:collection']):
        while collnumb < len(item['properties']['ucldc_schema:collection']):
            numb = collnumb + 1
            name = 'Collection %d' % numb
            data2[name] = item['properties']['ucldc_schema:collection'][collnumb]
            collnumb += 1
    elif all_headers:
        data2['Collection 1'] = ''


def get_related_resource(data2, item, all_headers):
    relnumb = 0
    if (isinstance(item['properties']['ucldc_schema:relatedresource'], list)
            and item['properties']['ucldc_schema:relatedresource']):
        while relnumb < len(item['properties']['ucldc_schema:relatedresource']):
            numb = relnumb + 1
            name = 'Related Resource %d' % numb
            data2[name] = item['properties'][
                'ucldc_schema:relatedresource'][relnumb]
            relnumb += 1
    elif all_headers:
        data2['Related Resource 1'] = ''


def get_source(data2, item, all_headers):
    if item['properties']['ucldc_schema:source']:
        data2['Source'] = item['properties']['ucldc_schema:source']
    elif all_headers:
        data2['Source'] = ''


def get_subject_name(data2, item, all_headers):
    subnumb = 0
    if (isinstance(item['properties']['ucldc_schema:subjectname'], list)
            and item['properties']['ucldc_schema:subjectname']):
        while subnumb < len(item['properties']['ucldc_schema:subjectname']):
            numb = subnumb + 1
            try:
                name = 'Subject (Name) %d Name' % numb
                if item['properties']['ucldc_schema:subjectname'][subnumb]['name']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjectname'][subnumb]['name']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Subject (Name) %d Name Type' % numb
                if item['properties']['ucldc_schema:subjectname'][subnumb]['name_type']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjectname'][subnumb]['name_type']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Subject (Name) %d Role' % numb
                if item['properties']['ucldc_schema:subjectname'][subnumb]['role']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjectname'][subnumb]['role']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Subject (Name) %d Source' % numb
                if item['properties']['ucldc_schema:subjectname'][subnumb]['source']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjectname'][subnumb]['source']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Subject (Name) %d Authority ID' % numb
                if item['properties']['ucldc_schema:subjectname'][subnumb]['authorityid']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjectname'][subnumb]['authorityid']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            subnumb += 1
    elif all_headers:
        data2['Subject (Name) 1 Name'] = ''
        data2['Subject (Name) 1 Name Type'] = ''
        data2['Subject (Name) 1 Role'] = ''
        data2['Subject (Name) 1 Source'] = ''
        data2['Subject (Name) 1 Authority ID'] = ''


def get_place(data2, item, all_headers):
    plcnumb = 0
    if (isinstance(item['properties']['ucldc_schema:place'], list)
            and item['properties']['ucldc_schema:place']):
        while plcnumb < len(item['properties']['ucldc_schema:place']):
            numb = plcnumb + 1
            try:
                name = 'Place %d Name' % numb
                if item['properties']['ucldc_schema:place'][plcnumb]['name']:
                    data2[name] = item['properties'][
                        'ucldc_schema:place'][plcnumb]['name']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Place %d Coordinates' % numb
                if item['properties']['ucldc_schema:place'][plcnumb]['coordinates']:
                    data2[name] = item['properties'][
                        'ucldc_schema:place'][plcnumb]['coordinates']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Place %d Source' % numb
                if item['properties']['ucldc_schema:place'][plcnumb]['source']:
                    data2[name] = item['properties'][
                        'ucldc_schema:place'][plcnumb]['source']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Place %d Authority ID' % numb
                if item['properties']['ucldc_schema:place'][plcnumb]['authorityid']:
                    data2[name] = item['properties'][
                        'ucldc_schema:place'][plcnumb]['authorityid']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            plcnumb += 1
    elif all_headers:
        data2['Place 1 Name'] = ''
        data2['Place 1 Coordinates'] = ''
        data2['Place 1 Source'] = ''
        data2['Place 1 Authority ID'] = ''


def get_subject_topic(data2, item, all_headers):
    topnumb = 0
    if (isinstance(item['properties']['ucldc_schema:subjecttopic'], list)
            and item['properties']['ucldc_schema:subjecttopic']):
        while topnumb < len(item['properties']['ucldc_schema:subjecttopic']):
            numb = topnumb + 1
            try:
                name = 'Subject (Topic) %d Heading' % numb
                if item['properties']['ucldc_schema:subjecttopic'][topnumb]['heading']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjecttopic'][topnumb]['heading']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Subject (Topic) %d Heading Type' % numb
                if item['properties']['ucldc_schema:subjecttopic'][topnumb]['headingtype']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjecttopic'][topnumb]['headingtype']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Subject (Topic) %d Source' % numb
                if item['properties']['ucldc_schema:subjecttopic'][topnumb]['source']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjecttopic'][topnumb]['source']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Subject (Topic) %d Authority ID' % numb
                if item['properties']['ucldc_schema:subjecttopic'][topnumb]['authorityid']:
                    data2[name] = item['properties'][
                        'ucldc_schema:subjecttopic'][topnumb]['authorityid']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            topnumb += 1
    elif all_headers:
        data2['Subject (Topic) 1 Heading'] = ''
        data2['Subject (Topic) 1 Heading Type'] = ''
        data2['Subject (Topic) 1 Source'] = ''
        data2['Subject (Topic) 1 Authority ID'] = ''


def get_form_genre(data2, item, all_headers):
    formnumb = 0
    if (isinstance(item['properties']['ucldc_schema:formgenre'], list)
            and item['properties']['ucldc_schema:formgenre']):
        while formnumb < len(item['properties']['ucldc_schema:formgenre']):
            numb = formnumb + 1
            try:
                name = 'Form/Genre %d Heading' % numb
                if item['properties']['ucldc_schema:formgenre'][formnumb]['heading']:
                    data2[name] = item['properties'][
                        'ucldc_schema:formgenre'][formnumb]['heading']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Form/Genre %d Source' % numb
                if item['properties']['ucldc_schema:formgenre'][formnumb]['source']:
                    data2[name] = item['properties'][
                        'ucldc_schema:formgenre'][formnumb]['source']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            try:
                name = 'Form/Genre %d Authority ID' % numb
                if item['properties']['ucldc_schema:formgenre'][formnumb]['authorityid']:
                    data2[name] = item['properties'][
                        'ucldc_schema:formgenre'][formnumb]['authorityid']
                elif all_headers:
                    data2[name] = ''
            except:
                pass
            formnumb += 1
    elif all_headers:
        data2['Form/Genre 1 Heading'] = ''
        data2['Form/Genre 1 Source'] = ''
        data2['Form/Genre 1 Authority ID'] = ''


def get_provenance(data2, item, all_headers):
    provnumb = 0
    if (isinstance(item['properties']['ucldc_schema:provenance'], list)
            and item['properties']['ucldc_schema:provenance']):
        while provnumb < len(item['properties']['ucldc_schema:provenance']):
            numb = provnumb + 1
            name = 'Provenance %d' % numb
            data2[name] = item['properties']['ucldc_schema:provenance'][provnumb]
            provnumb += 1
    elif all_headers:
        data2['Provenance 1'] = ''


def get_physical_location(data2, item, all_headers):
    if item['properties']['ucldc_schema:physlocation']:
        data2['Physical Location'] = item['properties'][
            'ucldc_schema:physlocation']
    elif all_headers:
        data2['Physical Location'] = ''

if __name__ == "__main__":
    main()
