from genderize import Genderize, GenderizeException
import csv
import sys
import os.path
import time
import argparse
import logging
import requests

import jpyhelper as jpyh

from shutil import copyfile

def genderize(args):
    print(args)

    #File initialization
    dir_path = os.path.dirname(os.path.realpath(__file__))

    logging.basicConfig(filename=dir_path + os.sep + "log.txt", level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logger=logging.getLogger(__name__)

    ofilename, ofile_extension = os.path.splitext(args.output)

    #ofile = ofilename + "_" + time.strftime("%Y%m%d-%H%M%S") + ".csv"
    ofile = ofilename + ofile_extension
    ifile = args.input

    if os.path.isabs(ifile):
        print("\n--- Input file: " + ifile)
    else:
        print("\n--- Input file: " + dir_path + os.sep + ifile)

    if os.path.isabs(ofile):
        print("--- Output file: " + ofile)
    else:
        print("--- Output file: " + dir_path + os.sep + ofile + "\n")

    #File integrity checking
    if not os.path.exists(ifile):
        print("--- Input file does not exist. Exiting.\n")
        sys.exit()

    #if not os.path.exists(os.path.dirname(ofile)):
    if not os.path.exists(ofile):
        print("--- Error! Invalid output file path. Exiting.\n")
        sys.exit()

    #Some set up stuff
    ##csv.field_size_limit(sys.maxsize)

    #Initialize API key
    if not args.key == "NO_API":
        print("--- API key: " + args.key + "\n")
        genderize = Genderize(
            user_agent='GenderizeDocs/0.0',
            api_key=args.key)
        key_present = True
    else:
        print("--- No API key provided.\n")
        key_present = False

    #Open ifile
    with open(ifile, 'r', encoding="utf8") as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        first_name = []
        inputData = []

        for row in readCSV: #Read CSV into first_name list
            if len(row) > 1:
                row[1] = row[1].strip()
                first_name.append(row[1])
            else:
                row[0] = row[0].strip()
                first_name.append(row[0])
            inputData.append(row)

        headers = inputData[0]
        inputData = inputData[1:]
        data_iterator = iter(inputData)

        if args.noheader == False:
            first_name.pop(0) #Remove header

        o_first_name = list()
        for l in first_name:
            for b in l:
                o_first_name.append(b)
        
        if args.auto == True:
            uniq_first_name = list(set(first_name))
            chunks = list(jpyh.splitlist(uniq_first_name, 10));
            print("--- Read CSV with " + str(len(first_name)) + " first_name. " + str(len(uniq_first_name)) + " unique.")
        else:
            chunks = list(jpyh.splitlist(first_name, 10));
            print("--- Read CSV with " + str(len(first_name)) + " first_name")

        print("--- Processed into " + str(len(chunks)) + " chunks")
        
        if jpyh.query_yes_no("\n---! Ready to send to Genderdize. Proceed?") == False:
            print("Exiting...\n")
            sys.exit()

        if os.path.isfile(ofile):
            if jpyh.query_yes_no("---! Output file exists, overwrite?") == False:
                print("Exiting...\n")
                sys.exit()
            print("\n")

        if args.auto == True:
            ofile = ofile + ".tmp"

        if "gender" not in headers:
            headers.append("gender")
            gender_index = headers.index("gender")
        if "probability" not in headers:
            headers.append("probability")
            prob_index = headers.index("probability")
        if "count" not in headers:
            headers.append("count")
            count_index = headers.index("count")

        response_time = [];
        gender_responses = list()
        with open(ofile, 'w', newline='', encoding="utf8") as f:
            writer = csv.writer(f)
            #writer.writerow(list(["first_name", "gender", "probability", "count"]))
            chunks_len = len(chunks)
            stopped = False

            #print(inputData)
            
            writer.writerow(headers)
            
            for index, chunk in enumerate(chunks):
                if stopped:
                    break
                success = False
                while not success:
                    try:
                        start = time.time()

                        if key_present:
                            dataset = genderize.get(chunk)
                        else:
                            dataset = Genderize().get(chunk)

                        gender_responses.append(dataset)
                        success = True
                    except GenderizeException as e:
                        #print("\n" + str(e))
                        logger.error(e)

                        #Error handling
                        if "response not in JSON format" in str(e) and args.catch == True:
                            if jpyh.query_yes_no("\n---!! 502 detected, try again?") == True:
                                success = False
                                continue
                        elif "Invalid API key" in str(e) and args.catch == True:
                            print("\n---!! Error, invalid API key! Check log file for details.\n")
                        else:
                            print("\n---!! GenderizeException - You probably exceeded the request limit, please add or purchase a API key. Check log file for details.\n")
                        stopped = True
                        break

                    response_time.append(time.time() - start)
                    print("Processed chunk " + str(index + 1) + " of " + str(chunks_len) + " -- Time remaining (est.): " + \
                        str( round( (sum(response_time) / len(response_time) * (chunks_len - index - 1)), 3)) + "s")

                    #print(dataset)
                    
                    for data in dataset:
                        next_row = next(data_iterator)
                        next_row_index = inputData.index(next_row)
                        entry_row = inputData[next_row_index]

                        entry = [data["gender"], data["probability"], data["count"]]
                        entry_row += entry
                        writer.writerow(entry_row)
                    break

            if args.auto == True:
                print("\nCompleting identical first_name...\n")
                #AUTOCOMPLETE first_name

                #Create master dict
                gender_dict = dict()
                for response in gender_responses:
                    for d in response:
                        gender_dict[d.get("name")] = [d.get("gender"), d.get("probability"), d.get("count")]
                
                #names seen
                seen_names = []

                with open(ofilename + "_auto" + ofile_extension, 'w', newline='', encoding="utf8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    for row in inputData:
                        if len(row) > 4:
                            name = row[1]
                            if name not in seen_names:
                                writer.writerow(row)
                            seen_names.append(name)
                        else:
                            name = row[0]
                            if name not in seen_names:
                                writer.writerow(row)
                            seen_names.append(name)
            
            if args.override == True:
                print("\nExercising override \n")

                with open(ofilename + "_override" + ofile_extension, 'w', newline='', encoding="utf8") as f:
                    writer = csv.writer(f)

                    #add headers
                    headers += ["female", "male"]
                    writer.writerow(headers)

                    for row in inputData:
                        gender = row[gender_index]
                        if gender == "male":
                            row += [0, 1]
                            writer.writerow(row)
                        else:
                            row += [1, 0]
                            writer.writerow(row)

            master_dict = dict()
            for response in gender_responses:
                for line in response:
                   master_dict[line.get("name")] = [line.get("gender"), line.get("probability"), line.get("count")]
            
            userResponse = True
            while userResponse == True:
                if jpyh.query_yes_no("Would you like to search the output file for the gender of a name") == False:
                    userResponse = False
                    sys.exit()
            
                sys.stdout.write("Enter a name you would like to search. \n")
                user_input = input()
                
                if user_input == '':
                    sys.stdout.write("You MUST enter a name \n")
                
                elif user_input not in master_dict:
                    sys.stdout.write("The name you entered is not in the output file \n")
                    
                    if jpyh.query_yes_no("Would you like to genderize {}?".format(user_input)) == False:
                        userResponse = False
                    
                    else:
                        if key_present:
                            api_response = genderize.get([user_input])
                        else:
                            api_response = Genderize().get([user_input])
                        for line in api_response:
                            name, gender, prob, count = line.get("name"), line.get("gender"), line.get("probability"), line.get("count")
                            print("Name: {}, Gender: {}, Probability: {}, Count: {}".format(name, gender, prob, count))

                else:
                    response = master_dict[user_input]
                    sys.stdout.write("Name: {}, Gender: {}, Probability: {}, Count: {}".format(user_input, response[0], response[1], response[2]))
                    if jpyh.query_yes_no("\nWould you like to search for another name?") == False:
                        userResponse = False

            print("Done!\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bulk genderize.io script')
    required = parser.add_argument_group('required arguments')

    required.add_argument('-i','--input', help='Input file name', required=True)
    required.add_argument('-o','--output', help='Output file name', required=True)
    parser.add_argument('-k','--key', help='API key', required=False, default="NO_API")
    parser.add_argument('-c','--catch', help='Try to handle errors gracefully', required=False, action='store_true', default=True)
    parser.add_argument('-a','--auto', help='Automatically complete gender for identical first_name', required=False, action='store_true', default=False)
    parser.add_argument('-nh','--noheader', help='Input has no header row', required=False, action='store_true', default=False)
    parser.add_argument('-OVR', '--override', help='Override default column output.', required=False, action='store_true', default=False)

    genderize(parser.parse_args())
