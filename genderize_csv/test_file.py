import csv
import sys
import os.path
import requests

import jpyhelper as jpyh

if __name__ == "__main__":
    aFile = "test\genderize_test_file.csv"
    dir_path = os.path.dirname(os.path.realpath(aFile))
    checkPath = os.path.exists(os.path.dirname(dir_path))

    with open(aFile, 'r', encoding="utf8") as infile, open("output.csv", 'w') as outfile:
        writer = csv.writer(outfile, lineterminator="\n")
        reader = csv.reader(infile, delimiter=',', skipinitialspace=True)

        data = []
        row = next(reader)
        row.append("Probability")
        row.append("Count")
        data.append(row)

        for row in reader:
            row.append(row[0])
            data.append(row)

        writer.writerows(data)

    '''
    with open(aFile, 'r', encoding="utf8") as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        first_name = []
        for row in readCSV: #Read CSV into first_name list
            first_name.append(row[0])

        o_first_name = list()
        for l in first_name:
            for b in l:
                o_first_name.append(b)

        uniq_first_name = list(set(o_first_name))
        chunks = list(jpyh.splitlist(uniq_first_name, 10));
        
        theDictionary = {
            "Samson": 42,
            "Jesus": 33,
            "Clyde": 56,
            "Jehovah": 65
        }



        
        for name in theDictionary:
            print(name)
        
        for name in theDictionary:
            print(theDictionary[name])

        userResponse = True
        while userResponse == True:
            if jpyh.query_yes_no("Would you like to search the output file for the gender of a name") == False:
                userResponse = False
                sys.exit()
            
            sys.stdout.write("Enter a name you would like to search. \n")
            user_input = input()
            
            if user_input == '':
                sys.stdout.write("You MUST enter a name \n")
            
            elif user_input not in theDictionary:
                sys.stdout.write("The name you entered is not in the output file \n")
                
                if jpyh.query_yes_no("Would you like to genderize {}?".format(user_input)) == False:
                    userResponse = False
                
                else:
                    api_response = requests.get('https://api.genderize.io/',params={"name": user_input})
                    decoded = api_response.json()
                    name, gender, prob, count = decoded['name'], decoded['gender'], decoded['probability'], decoded['count']
                    print("Name: {}, Gender: {}, Probability: {}, Count: {}".format(name, gender, prob, count))

            else:
                response = theDictionary[user_input]
                sys.stdout.write("{}: {}".format(user_input, response))
                if jpyh.query_yes_no("\nWould you like to search for another name?") == False:
                    userResponse = False'''