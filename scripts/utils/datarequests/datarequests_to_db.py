from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import codecs
from geonode.datarequests.models import DataRequestProfile
import re
import os
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def _is_in(aString, aList):
    for a in aList:
        if a in aString:
            return True
    return False


def parse_datarequest_csv(csv_path):

    if not os.path.isfile(csv_path):
        print '{0} file not found! Exiting.'.format(csv_path)
        exit(1)

    # with codecs.open(csv_path, 'r', 'utf-8') as open_file:
    with open(csv_path, 'r') as open_file:
        first_line = True
        request_list = []
        counter = 1
        for line in open_file:

            # print '#' * 80

            if first_line:
                first_line = False
                continue

            tokens = line.strip().split('|')
            if len(tokens) <= 1:
                continue

            try:
                _id = tokens[0].strip()  # int
                orig_name = tokens[1].strip()
                institution = tokens[2].strip()
                agency = tokens[3].strip()
                position = tokens[4].strip()
                email = tokens[5].strip()
                contact_num = tokens[6].strip()  # int or string
                organization = tokens[7].strip()
                request_date = tokens[8].strip()  # mm/dd/yyyy
                date_received_by_dream = tokens[9].strip()
                data_requested = tokens[10].strip()
                action_related = tokens[11].strip()  # int
                action_id = tokens[12].strip()
                actions = tokens[13].strip()
                date_provided = tokens[14].strip()
                supporting_document = tokens[15].strip()
                remarks = tokens[16].strip()
                status = tokens[17].strip()
                overall_status = tokens[18].strip()
                assigned_person = tokens[19].strip()
                audit = tokens[20].strip()
                # legend,agency column excluded being empty

                # print counter, _id, orig_name

                ## Get first, middle and last name ##

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

                # print '1: name:', repr(name)

                # If multiple requesters, only get the first name
                if (';' not in name and ((',' in name and ' and ' in name) or
                                         name.count(',') > 1)):
                    # print 'Case 1'
                    name = name.split(',')[0].strip()
                elif '/' in name:
                    # print 'Case 2'
                    name = name.split('/')[0].strip()
                elif ';' in name and 'and' in name:
                    # print 'Case 3'
                    name = name.split(';')[0].strip()
                    tokens = name.split(',')
                    last_name = tokens[0].strip()
                    first_name = tokens[1].strip()
                elif ' and ' in name:
                    # print 'Case 4'
                    name = name.split('and')[0].strip()

                # print '2: name:', repr(name)
                # print '2: first_name:', repr(first_name)
                # print '2: middle_initial:', repr(middle_initial)
                # print '2: last_name:', repr(last_name)

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
                        # print 'Case 7'
                        middle_initial = tokens[middle_id]
                        first_name = ' '.join(tokens[:middle_id])
                        last_name = ' '.join(tokens[middle_id + 1:])
                    else:
                        if ',' in name:
                            # print 'Case 5'
                            for i in range(len(tokens)):
                                if ',' in tokens[i]:
                                    split_id = i
                                    break
                        elif _is_in(name, suffixes):
                            # print 'Case 6'
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

                # print '3: tokens:', repr(tokens)
                # print '3: first_name:', repr(first_name)
                # print '3: middle_initial:', repr(middle_initial)
                # print '3: last_name:', repr(last_name)

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
                           remarks, status, overall_status, assigned_person,
                           audit, organization)

                profile_object = DataRequestProfile(first_name=str(first_name),
                                                    middle_name=str(
                                                        middle_initial),
                                                    last_name=str(last_name),
                                                    organization=str(
                                                        institution),
                                                    email=str(email),
                                                    contact_number=contact_num,
                                                    additional_remarks=remarks)
                profile_object.save()
                print 'Profile: ', profile_object.first_name, profile_object.last_name
                counter += 1

            except Exception:
                print traceback.print_exc()
                exit(1)
                # print _id
                # print 'length chars', name_length_chars
                # print '* First name: ', first_name
                # print '* Middle name: ', middle_name
                # print '* Last name: ', last_name

#csv_path = 'data_request_list.csv'
csv_path = raw_input('CSV complete file path:')
parse_datarequest_csv(csv_path)

