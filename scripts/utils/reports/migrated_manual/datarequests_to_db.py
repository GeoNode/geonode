from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import codecs
from geonode.datarequests.models import DataRequestProfile
import re
import os
import traceback
from datetime import datetime
<<<<<<< HEAD
=======
import regex
>>>>>>> master

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def _is_in(aString, aList):
    for a in aList:
        if a in aString:
            return True
    return False


def set_name(orig_name):
    first_name = ''
    middle_initial = ''
    last_name = ''

    name = orig_name.strip()
    # Remove text in parenthesis
    name = re.sub(r'\([a-zA-Z0-9 ]+\)', '', name).strip()
    # Remove titles
    titles = ['Ms', 'Mr', 'Dr', 'Engr', 'Hon',
              'Prof', 'For', 'Sec', 'Atty']
    for title in titles:
        name = re.sub(r'' + title + '[\. ]{1}', '', name).strip()
    # Remove suffixes
    suffixes = ['PhD', 'Ph.D']
    for suffix in suffixes:
        name = re.sub(r'' + suffix + '[\.]*$', '', name).strip()
    # Remove last character if it is a comma
    if name[len(name) - 1] == ',':
        name = name[:-1].strip()
    # Remove double spaces
    name = name.replace('  ', ' ')

<<<<<<< HEAD
    # print '1: name:', repr(name)
=======
    print '1: name:', repr(name)
>>>>>>> master

    # If multiple requesters, only get the first name
    if (';' not in name and ((',' in name and ' and ' in name) or
                             name.count(',') > 1)):
<<<<<<< HEAD
        # print 'Case 1'
        name = name.split(',')[0].strip()
    elif '/' in name:
        # print 'Case 2'
        name = name.split('/')[0].strip()
    elif ';' in name and 'and' in name:
        # print 'Case 3'
=======
        print 'Case 1'
        name = name.split(',')[0].strip()
    elif '/' in name:
        print 'Case 2'
        name = name.split('/')[0].strip()
    elif ';' in name and 'and' in name:
        print 'Case 3'
>>>>>>> master
        name = name.split(';')[0].strip()
        tokens = name.split(',')
        last_name = tokens[0].strip()
        first_name = tokens[1].strip()
    elif ' and ' in name:
<<<<<<< HEAD
        # print 'Case 4'
        name = name.split('and')[0].strip()

    # print '2: name:', repr(name)
    # print '2: first_name:', repr(first_name)
    # print '2: middle_initial:', repr(middle_initial)
    # print '2: last_name:', repr(last_name)
=======
        print 'Case 4'
        name = name.split('and')[0].strip()

    print '2: name:', repr(name)
    print '2: first_name:', repr(first_name)
    print '2: middle_initial:', repr(middle_initial)
    print '2: last_name:', repr(last_name)

    # mayor entries
    tokens = name.split()
    if len(tokens) == 1 and tokens[0].lower() == 'mayor':
        print 'MAYOR ENTRY'
        first_name = 'Mayor'
>>>>>>> master

    # Finally get the first and last name
    suffixes = ['Sr', 'Jr', 'II', 'III']
    if first_name == '':
        tokens = name.split()

        # 326

        # Try, finding the middle initial
        middle_id = None
        for i in range(len(tokens)):
            if '.' in tokens[i] and len(tokens[i]) == 2:
                middle_id = i

        if middle_id:
<<<<<<< HEAD
            # print 'Case 7'
=======
            print 'Case 7'
>>>>>>> master
            middle_initial = tokens[middle_id]
            first_name = ' '.join(tokens[:middle_id])
            last_name = ' '.join(tokens[middle_id + 1:])
        else:
            if ',' in name:
<<<<<<< HEAD
                # print 'Case 5'
=======
                print 'Case 5'
>>>>>>> master
                for i in range(len(tokens)):
                    if ',' in tokens[i]:
                        split_id = i
                        break
            elif _is_in(name, suffixes):
<<<<<<< HEAD
                # print 'Case 6'
=======
                print 'Case 6'
>>>>>>> master
                for i in range(len(tokens)):
                    if _is_in(tokens[i], suffixes):
                        split_id = i - 1
                        break
            else:
                split_id = -1

            # 242,252
            if tokens[split_id - 1].lower()[:2] == 'de':
                split_id -= 1
            last_name = ' '.join(tokens[split_id:])

            if len(tokens[split_id - 1]) <= 2:
                middle_initial = tokens[split_id - 1]
                first_name = ' '.join(tokens[:split_id - 1])
            else:
                first_name = ' '.join(tokens[:split_id])

    # Truncate long names
    first_name = first_name[:21]
    last_name = last_name[:21]

    return first_name, middle_initial, last_name


def parse_datarequest_csv(csv_path):
<<<<<<< HEAD

=======
    print 'Parsing CSV'
>>>>>>> master
    if not os.path.isfile(csv_path):
        print '{0} file not found! Exiting.'.format(csv_path)
        exit(1)

    # with codecs.open(csv_path, 'r', 'utf-8') as open_file:
    with open(csv_path, 'r') as open_file:
<<<<<<< HEAD
        first_line = True
        request_list = []
        counter = 1
        for line in open_file:

            # print '#' * 80
=======
        print 'Opening File'
        first_line = True
        counter = 1
        for line in open_file:

            print '#' * 80
>>>>>>> master

            if first_line:
                first_line = False
                continue

            tokens = line.strip().split('|')
<<<<<<< HEAD
=======
            # print 'T: ',tokens

>>>>>>> master
            if len(tokens) <= 1:
                continue

            try:
                _id = tokens[0].strip()
                orig_name = tokens[1].strip()
                institution = tokens[2].strip()  # this is the organization
                agency = tokens[3].strip()
                position = tokens[4].strip()
                email = tokens[5].strip()
<<<<<<< HEAD
                contact_num = tokens[6].strip()
                mailing_addr = tokens[7].strip()
                org_sub = tokens[8].strip()
                org_main = tokens[9].strip() # becomes org type as is
                request_date = datetime.strptime(
                    str(tokens[10].strip()), '%m/%d/%Y')  # .created
                date_received_by_dream = datetime.strptime(
                    str(tokens[11].strip()), '%m/%d/%Y')  # verification date key_created_date
=======
                contact_num = tokens[6].strip().replace(' ', '')
                mailing_addr = tokens[7].strip()
                org_sub = tokens[8].strip()
                org_main = str(tokens[9].strip())  # becomes org type as is

                # .created
                # has not null constraint
                # not seen in admin
                created = datetime.now()
                raw_request_date = str(tokens[10].strip())
                str_date = regex.search(
                    r'[0-9]*\/[0-9]*\/[0-9]*', raw_request_date)
                if str_date:
                    request_date = datetime.strptime(
                        str_date.group(), '%m/%d/%Y')
                    created = request_date

                # verification date key_created_date
                # it is not null constraint
                key_created_date = datetime.now()
                raw_date_received_by_dream = str(tokens[11].strip())
                print 'RAW DATE RECEIVED BY DREAM', raw_date_received_by_dream
                str_date = regex.search(
                    r'[0-9]*\/[0-9]*\/[0-9]*', raw_date_received_by_dream)
                if str_date:
                    date_received_by_dream = datetime.strptime(
                        str_date.group(), '%m/%d/%Y')
                    print 'DATE RECEIVED BY DREAM', date_received_by_dream
                    key_created_date = date_received_by_dream

>>>>>>> master
                data_requested = tokens[12].strip()
                action_related = tokens[13].strip()
                action_id = tokens[14].strip()
                actions = tokens[15].strip()
<<<<<<< HEAD
                date_provided = datetime.strptime(
                    str(tokens[16].strip()), '%m/%d/%Y')  # action date
                supporting_document = tokens[17].strip()
                remarks = tokens[18].strip()
=======

                # action date
                action_date = None
                raw_date_provided = str(tokens[16].strip())
                str_date = regex.search(
                    r'[0-9]*\/[0-9]*\/[0-9]*', raw_date_provided)
                if str_date:
                    date_provided = datetime.strptime(
                        str_date.group(), '%m/%d/%Y')
                    action_date = date_provided

                supporting_document = tokens[17].strip()
                remarks_manual = tokens[18].strip()
>>>>>>> master
                status = tokens[19].strip()
                overall_status = tokens[20].strip()

                # legend,agency column excluded being empty

<<<<<<< HEAD
                # print counter, _id, orig_name
=======
                print counter, _id, orig_name
>>>>>>> master

                # Get first, middle and last name ##
                first_name, middle_initial, last_name = set_name(orig_name)

<<<<<<< HEAD
                # print '3: tokens:', repr(tokens)
                # print '3: first_name:', repr(first_name)
                # print '3: middle_initial:', repr(middle_initial)
                # print '3: last_name:', repr(last_name)

                # organization type
                # org_type = organization_type(org_main)


                remarks = """
                Name: {0}
                Position: {1}
                Request data: {2}
                Date received by DREAM: {3}
                Data Requested: {4}
                Action related: {5}
                Action ID: {6}
                Actions: {7}
                Date provided: {8}
                Supporting Document: {9}
                Remarks: {10}
                Status: {11}
                Overall Status: {12}
                Assigned Person: {13}
                Audit: {14}
                Organization: {15}
                """.format(orig_name, position, request_date, date_received_by_dream,
                           data_requested, action_related, action_id,
                           actions, date_provided, supporting_document,
                           remarks, status, overall_status, , organization)

=======
                print '3: tokens:', repr(tokens)
                print '3: first_name:', repr(first_name)
                print '3: middle_initial:', repr(middle_initial)
                print '3: last_name:', repr(last_name)

                # do not have field in DataRequestProfile

                remarks = """ID: {0}
Name of Requester: {16}
Agency: {1}
Position: {2}
Mailing Address: {3}
Organization-sub: {4}
Date of Request (created) :  {5}
Date Received by DREAM (Key created date): {6}
Data Requested: {7}
Action Related: {8}
Action ID: {9}
Actions: {10}
Date Provided (Action Date): {11}
Supporting Document: {12}
Remarks: {13}
Status: {14}
Overall Status: {15}""".format(_id, agency, position, mailing_addr, org_sub, raw_request_date,
                               raw_date_received_by_dream, data_requested, action_related, action_id,
                               actions, raw_date_provided, supporting_document, remarks_manual,
                               status, overall_status, orig_name)
                print 'REMARKS', remarks
>>>>>>> master
                profile_object = DataRequestProfile(first_name=str(first_name),
                                                    middle_name=str(
                                                        middle_initial),
                                                    last_name=str(last_name),
                                                    organization=str(
                                                        institution),
                                                    email=str(email),
                                                    contact_number=contact_num,
<<<<<<< HEAD
                                                    created=request_date,
                                                    key_created_date=date_received_by_dream,
                                                    date_of_action=date_provided,
                                                    additional_remarks=remarks)
=======
                                                    org_type=org_main,
                                                    additional_remarks=remarks,
                                                    key_created_date=key_created_date,
                                                    created=created,
                                                    action_date=action_date)
>>>>>>> master
                profile_object.save()
                print 'Profile: ', profile_object.first_name, profile_object.last_name
                counter += 1

            except Exception:
                print traceback.print_exc()
                exit(1)
<<<<<<< HEAD
                # print _id
                # print 'length chars', name_length_chars
                # print '* First name: ', first_name
                # print '* Middle name: ', middle_name
                # print '* Last name: ', last_name
=======
                print _id
                # print 'length chars', name_length_chars
                print '* First name: ', first_name
                # print '* Middle name: ', middle_name
                print '* Last name: ', last_name
>>>>>>> master

enable_raw_input = False
if enable_raw_input:
    csv_path = raw_input('CSV complete file path:')
    parse_datarequest_csv(csv_path)
else:
<<<<<<< HEAD
    csv_path = 'new_datarequest_list.csv'
=======
    print 'Importing ...'
    csv_path = 'scripts/utils/reports/migrated_manual/new_datarequest_list.csv'
>>>>>>> master
    parse_datarequest_csv(csv_path)
