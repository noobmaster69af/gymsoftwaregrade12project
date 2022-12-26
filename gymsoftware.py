import mysql.connector as con, os, pandas as pd, datetime as dt, csv, time
from prettytable import PrettyTable
from datetime import date as dat
from email_validator import validate_email, EmailNotValidError

mcwd = os.getcwd()  # variable holds the path of current working directory
fddir = os.path.join(mcwd, 'FeeDetails')  # variable holds the path to the directory FeeDetails
fdcsvdir = os.path.join(fddir, 'fee_details.csv')  # variable holds the path to fee_details.csv
today=dat.today()
mydb = con.connect(host='localhost', user='root', password='tiger')  # trying to establish a connection to mysql server
mc = mydb.cursor()

def displayfeedefaulters():
    try:
        df = pd.read_csv(fdcsvdir)
        # Filter the DataFrame to include only rows where the subscription_status is 'expired'
        expired_subscribers = df.loc[df['SubscriptionStatus'] == 'expired']
        # Check if the DataFrame is empty
        if not expired_subscribers.empty:
            # Print the DataFrame if it is not empty
            expired_subscribers.index = expired_subscribers.index + 1
            print(expired_subscribers)
        else:
            print('\nNo fee defaulters')
        home_page()
    except:
        print('No data')
        home_page()


def set_date(payment_frequency):
    """Set paid date and next payment date"""
    # Get the current date1
    current_date = dat.today()
    duedate = ''
    if payment_frequency == 'Monthly':
        # Calculate 1 month from the current date
        month_from_now = current_date + dt.timedelta(days=30)
        duedate = month_from_now
    elif payment_frequency == 'Quarterly':
        # Calculate 3 months from the current date
        three_months_from_now = current_date + dt.timedelta(days=90)
        duedate = three_months_from_now
    elif payment_frequency == 'Half Yearly':
        # Calculate 6 months from the current date
        six_months_from_now = current_date + dt.timedelta(days=180)
        duedate = six_months_from_now
    elif payment_frequency == 'Yearly':
        # Calculate 1 year from the current date
        one_year_from_now = current_date + dt.timedelta(days=365)
        duedate = one_year_from_now
    return current_date, duedate


def pay_fees(name=None, phno=None):
    if name is None and phno is None:
        while True:
            ch = int(input('''Search client by 
1.name
2.phone number
enter your choice: '''))
            if ch == 1:
                while True:
                    cname = input("Enter the client's full name: ").lower().strip('"').strip("'")
                    # if name is less than 2 characters long, responds the user with an error message
                    if len(cname) < 2:
                        print('pls enter a valid name!')
                        continue
                    break
                updcsv("Name", 'SubscriptionStatus', cname, 'Active')
                setduedate(name)
                break
            elif ch == 2:
                while True:
                    # trying to take phone number as input
                    try:
                        phno = int(input('Enter the client phone number: '))
                        # if the length phone number input is not 10 digits, responds to the user with an error message
                        if len(str(phno)) != 10:
                            print('please enter a valid phone number!')
                            continue
                    # if failed due to an invalid input, responds to the user with an error message
                    except:
                        print('please enter a valid phone number!')
                    break
                updcsv('PhoneNo', 'SubscriptionStatus', phno, 'Active')
                setduedate(phno=phno)

    elif name is not None and phno is None:
        updcsv('Name', 'SubscriptionStatus', name, 'Active')
        setduedate(name)
    elif phno is not None and name is None:
        updcsv('PhoneNo', 'SubscriptionStatus', phno, 'Active')
        setduedate(phno=phno)
    else:
        updcsv('Name', 'SubscriptionStatus', name, 'Active')
        setduedate(name)


def setduedate(name=None, phno=None):
    dup = False
    df = pd.read_csv('fee_details.csv')
    if name and phno is not None:
        pf = searchforpf('Name', name)
    elif name is not None:
        pf = searchforpf('Name', name)
        x = df.loc[df["Name"] == name, "PhoneNo"]
        for i in x:
            phno = i
    elif phno is not None:
        pf = searchforpf('PhoneNo', phno)
        x = df.loc[df['PhoneNo'] == phno, "Name"]
        for i in x:
            name = i
    # opens the csv file and sets the bool value for dup as true if duplicate found
    with open('fee_details.csv', 'r') as file:
        reader = csv.reader(file)
        read_data = [i for i in reader]
        for i in read_data:
            if i[0] == name and i[1] == phno:
                dup = True
            else:
                pass
    # if name a phone number already exist, just updates the paid date and due date for the specific client
    # used in paying fee function
    if dup:
        paid_date, due_date = set_date(pf)
        df.loc[df['Name'] == name, "PaidDate"] = paid_date
        df.loc[df['Name'] == name, "DueDate"] = due_date
        df.to_csv('fee_details.csv', index=False)


def feedefaulters():
    try:
        df = pd.read_csv(fdcsvdir)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.options.display.width = None
        # Convert the DueDate column to datetime objects
        df['DueDate'] = pd.to_datetime(df['DueDate'], format='%Y-%m-%d')
        # Convert the DueDate column to date objects
        df['DueDate'] = df['DueDate'].apply(lambda x: x.date())
        # Update the SubscriptionStatus column for rows where the DueDate is less than the current date
        df.loc[df["DueDate"] < dat.today(), 'SubscriptionStatus'] = 'expired'
        # Convert the DueDate column back to strings
        df['DueDate'] = df['DueDate'].astype(str)
        # Write the updated DataFrame back to the CSV file
        df.to_csv(fdcsvdir, index=False)
    except Exception as e:
        print(e)
        return


def autoupage():
    """Checks dob of all clients and updated age"""
    try:
        mc.execute('use GymClientData')
        # Read the clients table
        mc.execute('SELECT * FROM c_data')
        x = mc.fetchall()
        # Iterate over the rows in the table
        for i in x:
            name, dob, age = i[1], i[2], i[3]
            # Convert the DOB to a datetime object
            dob = dt.datetime.strptime(dob.strftime('%Y-%m-%d'), '%Y-%m-%d')
            # Get the current date
            today = dat.today()
            # Calculate the current age
            current_age = today.year - dob.year
            # Check if the client's birthday has occurred this year
            if (today.month, today.day) >= (dob.month, dob.day):
                # Check if the age has changed since the last update
                if age != current_age:
                    # Update the age in the table
                    mc.execute(f"UPDATE c_data SET age = {current_age} WHERE name = '{name}'")
                else:
                    pass
        # Commit the changes to the database
        mydb.commit()
    except con.Error as err:
        # Handle any errors that occur while connecting to the database or executing the query
        print(f'An error occurred: {err}')


def c_name():
    """Takes name as input and returns it"""
    while True:
        cname = input("Enter the client's full name: ").lower().strip('"').strip("'")
        # if name is less than 2 characters long, responds the user with an error message
        if len(cname) < 2:
            print('pls enter a valid name!')
            continue
        return cname


def c_dobandc_age():
    """Takes Date of Birth as input from user and uses it to calculate the age and returns both dob and age"""
    while True:
        # trying to take dob as input
        try:
            x = input('Enter the dob of the client as YYYY-MM-DD: ').split('-')
            year, month, date = [int(x[0]), int(x[1]), int(x[2])]
            cdob = dt.datetime(year, month, date)
            today = dat.today()
            one_or_zero = ((today.month, today.day) < (cdob.month, cdob.day))
            year_difference = today.year - cdob.year
            age = year_difference - one_or_zero
            return str(cdob), age
        # if failed due to an invalid date input, responds to the user with an error message
        except:
            print('Please enter a valid date!')
            continue


def c_gender():
    """Serves as an interface to select gender and returns it"""
    while True:
        # trying to take gender as an input
        try:
            ch = input('''Enter client's gender
(M)Male
(F)Female
(N)Do not prefer to say
Your choice: ''').upper()
            if ch not in ['M', 'F', 'N']:
                raise ValueError
            return ch
        # if failed due to an invalid input, responds to the user with an error message
        except ValueError:
            print('Please enter a valid option!')


def c_address():
    """Takes input of address and returns it"""
    postcode=''
    while True:
        # trying to take street address,city,state and postcode as input and returns them
        try:
            street = input("Enter the client street address: ")
            city = input('Enter the client city name: ')
            state = input('Enter the client state: ')
            if street or city or state =='':
                print("address values cannot be null!!!")
                continue
            while True:
                # trying to take postcode as input
                try:
                    postcode = int(input('Enter the client POSTCODE: '))
                # if failed due to an invalid input, responds to the user with an error message
                except ValueError:
                    print('Postcode should only contain numbers!!!')
                # if the post code input is not 6 digits, responds to the user with an error message
                if len(str(postcode)) != 6:
                    print('Postcode should contain exactly 6 digits!!!')
                    continue
                return street, city, state, str(postcode)
        # if failed due to an invalid input, responds to the user with an error message
        except ValueError:
            print('Please enter valid input!!!')


def c_phno():
    """Takes input of phone number and return it"""
    while True:
        # trying to take phone number as input
        try:
            phno = int(input('Enter the client phone number: '))
            # if the length phone number input is not 10 digits, responds to the user with an error message
            if len(str(phno)) != 10:
                print('please enter a valid phone number!')
                continue
            return phno
        # if failed due to an invalid input, responds to the user with an error message
        except:
            print('please enter a valid phone number!')


def c_email():
    """Takes input of email address, verifies that the email address is valid and returns it"""
    while True:
        # trying to take email as input and validate it
        try:
            email = input('Enter the client email: ')
            v = validate_email(email)
            email = v["email"]
            return email
        # if failed due to an invalid input, responds to the user with an error message
        except EmailNotValidError as e:
            print(str(e))


def c_emergencycontact():
    """Takes input of name and phone number of the client's emergency contact and returns it"""
    while True:
        ecname = input("Enter the client's emergency contact full name: ")
        # if name is less than 2 characters long, responds the user with an error message
        if len(ecname) < 2:
            print('pls enter a valid name!')
            continue
        # trying to take phone number as input
        try:
            ecphno = int(input("Enter the client's emergency contact phone number: "))
            # if the length phone number input is not 10 digits, responds to the user with an error message
            if len(str(ecphno)) != 10:
                print('please enter a valid phone number!')
                continue
            return ecname, ecphno
        # if failed due to an invalid input, responds to the user with an error message
        except ValueError:
            print('please enter a valid phone number!')


def payment_frequency(M, Q, H, Y):
    """Serves as an interface to set the payment frequency that the customer has chosen"""
    while True:
        # trying to take the payment frequency as input
        try:
            pf = int(input(f'''Select payment frequency
1.Monthly {M}
2.Quarterly {Q}
3.Half Yearly {H}
4.Yearly {Y}
Your choice: '''))
            if pf not in [1, 2, 3, 4]:
                print('Please enter a valid option!!!')
                continue
            return pf
        # if failed due to an invalid input, responds to the user with an error message
        except ValueError:
            print('Please enter a valid option!!!')


def set_fees(pf, M, Q, H, Y):
    """Sets payment frequency based on the payment frequency"""
    if pf == 1:
        fees = M
        pfname = 'Monthly'
    elif pf == 2:
        fees = Q
        pfname = 'Quarterly'
    elif pf == 3:
        fees = H
        pfname = 'Half Yearly'
    elif pf == 4:
        fees = Y
        pfname = 'Yearly'
    return fees, pfname


def package_selection(name, phno):
    """Serves as an interface to select a package and set fees according to package and payment frequency"""
    while True:
        # trying to take package as input
        try:
            subtype = int(input('''Select a Package
1.Weight Training
2.Cardio
3.Crossfit
4.Full Pass
5.Personal Training
Your choice: '''))
            if subtype == 1:
                M, Q, H, Y = 'Rs 1200', 'Rs 3200', 'Rs 6500', 'Rs 13400'
                pf = payment_frequency(M, Q, H, Y)
                fees, pfname = set_fees(pf, M, Q, H, Y)
                p = 'Weight Training'
            elif subtype == 2:
                M, Q, H, Y = 'Rs 1500', 'Rs 4200', 'Rs 8500', 'Rs 16800'
                pf = payment_frequency(M, Q, H, Y)
                fees, pfname = set_fees(pf, M, Q, H, Y)
                p = 'Cardio'
            elif subtype == 3:
                M, Q, H, Y = 'Rs 1000', 'Rs 2700', 'Rs 5500', 'Rs 11000'
                pf = payment_frequency(M, Q, H, Y)
                fees, pfname = set_fees(pf, M, Q, H, Y)
                p = 'Crossfit'
            elif subtype == 4:
                M, Q, H, Y = 'Rs 2300', 'Rs 6600', 'Rs 13300', 'Rs 26500'
                pf = payment_frequency(M, Q, H, Y)
                fees, pfname = set_fees(pf, M, Q, H, Y)
                p = 'Full Pass'
            elif subtype == 5:
                M, Q, H, Y = 'Rs 5000', 'Rs 13500', 'Rs 27500', 'Rs 55000'
                pf = payment_frequency(M, Q, H, Y)
                fees, pfname = set_fees(pf, M, Q, H, Y)
                p = 'Personal Training'
            else:
                print('Please enter a valid option!!!')
                continue
            break
        except ValueError:
            print("Please enter a valid option!!!")
    # checks csv files for duplicate files
    dup = dupcheck(name, p, pfname, fees, str(phno))
    return dup


def dupcheck(name, p, pfname, fees, phno):
    """Checks for duplicate values in the csv files"""
    dup = False
    # opens the csv file and sets the bool value for dup as true if duplicate found
    with open('fee_details.csv', 'r') as file:
        reader = csv.reader(file)
        read_data = [i for i in reader]
        for i in read_data:
            if i[0] == name and i[4] == phno:
                dup = True
            else:
                pass
    # if no duplicate value is found, opens file in inputs the values
    paydate,duedate=set_date(pfname)
    if not dup:
        with open('fee_details.csv', 'a', newline='') as file:
            writer = csv.writer(file, escapechar='\n')
            writer.writerow([name, p, pfname, fees, phno,'Active',paydate,duedate])
    return dup


def fsg():  # abbreviation for fee system generator
    """Generates the necessary files and directories need to store the fee details file"""
    # makes sure that FeeDetails does not exist in CurrentWorkingDirectory
    if not os.path.exists('FeeDetails'):
        # trying to make the directory
        try:
            os.mkdir(fddir)
        # passes if File already exists
        except FileExistsError:
            pass
    # changes directory into the FeeDetails
    os.chdir(fddir)
    headerListcsv = ['Name', 'Package', 'PaymentFrequency', 'Amount', 'PhoneNo','SubscriptionStatus',"PaidDate", "DueDate"]
    add_headercsv = False
    # just creates the fee_details.csv file
    with open('fee_details.csv', 'a'):
        pass
    # checks if the csv file contains header
    with open('fee_details.csv', 'r') as file:
        reader = csv.reader(file)
        read_data = [i for i in reader]
        if len(read_data) == 0:
            add_headercsv = True
    # adds headers to csv file it does not already exist
    with open('fee_details.csv', 'a', newline='') as file:
        writer = csv.writer(file, escapechar='\n')
        # checks if add_header is true or not
        if add_headercsv:
            writer.writerow(headerListcsv)


def Startup():
    """Serves as a startup page welcoming the user and displays time and date"""
    print(f'''WELCOME
{dt.datetime.now().strftime("%H:%M:%S")}\t\t{dt.datetime.today().strftime("%d:%b:%Y")}''')
    fsg()
    autoupage()
    feedefaulters()
    home_page()


def home_page():
    """Serves as a homepage interface"""
    # trying to take input as options for what the user wants to do
    while True:
        try:
            ch = int(input('''\nHOME PAGE
1.ADD NEW CLIENT DETAILS
2.UPDATE CLIENT DETAILS
3.VIEW CLIENT DETAILS
4.PAY FEES
5.DISPLAY FEE DEFAULTERS
0.Exit
Enter your choice: '''))
            if ch == 1:
                newcustomerdata()
            elif ch == 2:
                updatec_data()
            elif ch == 3:
                displayc_data()
            elif ch==4:
                pay_fees()
            elif ch==5:
                displayfeedefaulters()
            elif ch == 0:
                print('Logging off!')
                time.sleep(2)
                exit()
            else:
                print('Please enter a valid option!!!')
                continue
            break
        # if failed due to an invalid input, responds to the user with an error message
        except ValueError:
            print('Please enter a valid option!!!')


def newcustomerdata():
    """Acts as an interface for adding new customer data into the mysql database and fee_details.csv file"""
    while True:
        print('\nNEW CUSTOMER DETAILS')
        name = c_name()
        dob, age = c_dobandc_age()
        gender = c_gender()
        street, city, state, zipcode = c_address()
        address = street + ',' + city + ',' + state + ',' + zipcode
        phno = c_phno()
        email = c_email()
        ecname, ecphno = c_emergencycontact()
        emergency_contact = ecname + '  ' + str(ecphno)
        dup = package_selection(name, phno)
        # if duplicate entry is detected, responds to the user with an error message
        if dup:
            print('Duplicate entry detected!!!')
            continue
        pay_fees(name,phno)
        # create the databse GymClientData if it does not already exist
        mc.execute('create database if not exists GymClientData')
        # selects the database
        mc.execute('use GymClientData')
        # create the table c_data if it does not already exist
        mc.execute('''create table if not exists c_data (client_id int NOT NULL AUTO_INCREMENT,name varchar(30),dob date,age int,gender varchar(1),address varchar(1000),
                   phno bigint,email varchar(45),emergency_contact varchar(100),PRIMARY KEY(client_id)) AUTO_INCREMENT=101''')
        # trying to insert the given data into the database
        try:
            mc.execute(
                f"insert into c_data (name,dob,age,gender,address,phno,email,emergency_contact) values('{name}','{dob}',{age},'{gender}','{address}',{phno},'{email}','{emergency_contact}')")
        # if failed due to an invalid input, responds to the user with an error message
        except con.Error as er:
            print(er)
            continue
        # saves all the changes permanently into the database
        mydb.commit()
        # asks the user where they would like to continue adding data or not
        ex = input('do you want to continue adding data?(y/n) >').lower()
        if ex == 'y':
            continue
        else:
            break

    home_page()


def displayfull():
    """Displays the entire database and all the contents of the fee_details file"""
    # trying to access the database and take data from the table
    try:
        mc.execute('use GymClientData')
        mc.execute("SELECT * FROM c_data")
    # if failed, responds to the user with an error message
    except con.Error as er:
        print('Error occured!!!> ', er.msg)
    # trying to take all the data from the cursor object into a variable
    try:
        result = mc.fetchall()
    # if failed, responds to the user with an error message
    except con.Error as er:
        print("Error> ", er)
    # create as table using the pretty table module
    Table = PrettyTable(
        ['client_id', 'name', 'dob date', 'age', 'gender', 'address', 'phno', 'email', 'emergency_contact'])
    # trying to add all the data in the result variable into the table
    try:
        for i in result:
            Table.add_row([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]])
    # if failed, responds to the user with an error message
    except:
        print('Error')
    print(f'\n--Client Data--\n\n{Table}')
    # reads the csv file using pandas module and turns it into a dataframe
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.options.display.width = None
    bruh = pd.read_csv(fdcsvdir)
    # changing index to start from 1 else starts from 0
    bruh.index = bruh.index + 1
    print(f'\n\n--Package and Fee Data--\n\n{bruh}\n\n')
    home_page()


def displayspecific():
    """Serves as an interface to display the data of specific customers"""
    while True:
        try:
            colname = int(input('''By which column do you want to search?
1. name
2. phno
Enter your choice: '''))
            if colname == 1:
                while True:
                    x = input('Enter name to be searched: ')
                    # trying to display the data for the given name
                    try:
                        mc.execute('use GymClientData')
                        mc.execute(f"select * from c_data where name='{x}'")
                        result = mc.fetchall()
                        if result == []:
                            print(f'No Client info found for the name {x}!!!')
                            continue
                        Table = PrettyTable(
                            ['client_id', 'name', 'dob date', 'age', 'gender', 'address', 'phno', 'email',
                             'emergency_contact'])
                        for i in result:
                            Table.add_row([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]])
                        print(f'\n--Client Data--\n\n{Table}')
                        bruh = pd.read_csv(fdcsvdir)
                        bruh.index = bruh.index + 1
                        result = bruh[bruh['Name'] == x]
                        print(f'\n\n--Package and Fee Data--\n\n{result}\n\n')
                        break
                    # if failed due to an invalid input, responds to the user with an error message
                    except con.Error as er:
                        print(er.msg)
            elif colname == 2:
                while True:
                    # trying to take phone number as input to conduct search for data
                    try:
                        phno = int(input("Enter phone number to be searched: "))
                        if len(str(phno)) != 10:
                            print('please enter a valid phone number!')
                            continue
                    # if failed due to an invalid input, responds to the user with an error message
                    except ValueError:
                        print('please enter a valid phone number!')
                    # trying to display data for given phone number
                    try:
                        mc.execute('use GymClientData')
                        mc.execute(f"select * from c_data where phno={phno}")
                        result = mc.fetchall()
                        if result == []:
                            print(f'No Client info found for the phone number {phno}!!!')
                            continue
                        Table = PrettyTable(
                            ['client_id', 'name', 'dob date', 'age', 'gender', 'address', 'phno', 'email',
                             'emergency_contact'])
                        for i in result:
                            Table.add_row([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]])
                        print(f'\n--Client Data--\n\n{Table}')
                        bruh = pd.read_csv(fdcsvdir)
                        bruh.index = bruh.index + 1
                        result = bruh[bruh['PhoneNo'] == phno]
                        print(f'\n\n--Package and Fee Data--\n\n{result}\n\n')
                        break
                    # if failed due to an invalid input, responds to the suer with an error message
                    except con.Error as er:
                        print(er.msg)
                        continue
            else:
                raise ValueError
        # if failed due to an invalid input, responds to the user with an error message
        except ValueError:
            print('Please enter a valid option!')
            continue
        # asks user whether they would like to continue displaying more data
        ex = input('do you want to continue?(y/n) >').lower()
        if ex == 'y':
            continue
        else:
            home_page()
        break


def displayc_data():
    """Serves as an interface for the user to choose whether they want to display the entire database or
    just data of a specific cusomter"""
    print('\nDISPLAY CUSTOMER DATA')
    # trying to take the user's choice for displaying data as input
    try:
        fullorspecific = int(input(
            'Do you want to display entire table(enter 0) or just the details of a specific customer(enter 1)? >'))
    # if failed due to an invalid input, responds to the user with an error message
    except ValueError:
        print('Enter valid option!')
        displayc_data()
    if fullorspecific == 0:
        displayfull()
    elif fullorspecific == 1:
        displayspecific()


def updatec_data():
    """Serves as an interface to update data of the customers"""
    print('\nUPDATE CUSTOMER DATA')
    mc.execute('use GymClientData')
    while True:
        # trying to take the user's choice as input
        try:
            colname = int(input('''By which column do you want to search?
1. client_id
2. name
Enter your choice: '''))
            if colname == 1:
                # displays the table as the user might not properly know the customer id
                try:
                    mc.execute('use GymClientData')
                    mc.execute("SELECT * FROM c_data")
                except con.Error as er:
                    print('Error occured!!!> ', er.msg)
                try:
                    result = mc.fetchall()
                except con.Error as er:
                    print("Error> ", er)
                Table = PrettyTable(
                    ['client_id', 'name', 'dob date', 'age', 'gender', 'address', 'phno', 'email', 'emergency_contact'])
                try:
                    for i in result:
                        Table.add_row([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]])
                except:
                    print('Error')
                print(f'\n--Client Data--\n\n{Table}')
                searchval = []
                while True:
                    # trying to take the customer id for which the user wants to update data for
                    try:
                        cid = int(input('Enter client_id you want to update the values of: '))
                    # if failed due to an invalid input, responds to the user with an error message
                    except:
                        print('Invalid input!!!')
                        continue
                    # trying to retrieve data from the table and csv file
                    try:
                        mc.execute(f'select * from c_data where client_id={cid}')
                        result = mc.fetchall()
                        if result == []:
                            print(f'No Client info found for the id {cid}!!!')
                            continue
                        Table = PrettyTable(
                            ['client_id', 'name', 'dob date', 'age', 'gender', 'address', 'phno', 'email',
                             'emergency_contact'])
                        for i in result:
                            Table.add_row([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]])
                        mc.execute(f'select name from c_data where client_id={cid}')
                        for i in mc.fetchone():
                            searchval.append(i)
                        searchname = searchval[0]
                        print(f'\n--Client Data--\n\n{Table}')
                        bruh = pd.read_csv(fdcsvdir)
                        bruh.index = bruh.index + 1
                        result = bruh[bruh['Name'] == searchname]
                        print(f'\n\n--Package and Fee Data--\n\n{result}\n\n')
                    # if failed, responds to the user with an error message
                    except con.Error as er:
                        print(er.msg)
                    break
                while True:
                    # asks what the user wants to update
                    upvalue = int(input('''What do you want to update?
1.name
2.dob 
3.gender
4.address
5.phone no
6.email
7.emergency_contact
8.package
9.payment frequency
enter option: '''))
                    if upvalue == 1:
                        while True:
                            # trying to take updated name as input
                            try:
                                cname = input("Enter the client's full name(updated): ")
                                if len(cname) < 2:
                                    raise ValueError
                            # if failed due to an invalid input, responds to the user with an error message
                            except ValueError:
                                print('Invalid value')
                                continue
                            break
                        # updates the data in the database and csv file
                        updcsv('Name', 'Name', searchname, cname)
                        mc.execute(f"update c_data set name='{cname}' where client_id={cid}")
                        print(f'Name successfully updated as {cname} for client_id {cid}')
                        mydb.commit()
                    elif upvalue == 2:
                        while True:
                            # trying to dob as input and calculating the age automatically
                            try:
                                x = input('Enter the dob of the client as YYYY-MM-DD(updated): ').split('-')
                                year, month, date = [int(x[0]), int(x[1]), int(x[2])]
                                cdob = dt.datetime(year, month, date)
                                c = str(cdob)
                                today = dat.today()
                                one_or_zero = ((today.month, today.day) < (cdob.month, cdob.day))
                                year_difference = today.year - cdob.year
                                age = year_difference - one_or_zero
                            # if failed due to an invalid input, responds to the user with an error message
                            except:
                                print('Please enter a valid date!')
                                continue
                            break
                        # updates the data in the database and csv file
                        mc.execute(f"update c_data set age={age},dob='{c}' where client_id={cid}")
                        print(f'DOB and age successfully updated as {c} and {age} respectively for client_id {cid}')
                        mydb.commit()
                    elif upvalue == 3:
                        while True:
                            # trying to take gender as an input
                            try:
                                ch = input('''Enter updated client gender(updated)
(M)Male
(F)Female
(N)Do not prefer to say
Your choice: ''').upper()
                                if ch not in ['M', 'F', 'N']:
                                    raise ValueError
                            # if failed due to an invalid input, responds to the user with an error message
                            except ValueError:
                                print('Please enter a valid option!')
                                continue
                            break
                        # updates the data in the database and csv file
                        mc.execute(f"update c_data set gender='{ch}' where client_id={cid}")
                        print(f'Gender successfully updated as {ch} for client_id {cid}')
                        mydb.commit()
                    elif upvalue == 4:
                        while True:
                            # trying to take address as the input
                            try:
                                street = input("Enter the client street address(updated): ")
                                city = input('Enter the client city name(updated): ')
                                state = input('Enter the client state(updated): ')
                                if street or city or state == '':
                                    print("address values cannot be null!!!")
                                    continue
                                while True:
                                    # trying to take postcode as an input
                                    try:
                                        postcode = int(input('Enter the client ZIPCODE(updated): '))
                                    # if failed due to an invalid input, responds to the user with an error message
                                    except ValueError:
                                        print('Invalid values entered')
                                        continue
                                    # if the postcode does not contain 6 digits, responds to the user with error message
                                    if len(str(postcode)) != 6:
                                        print('Zipcode/Postcode should contain exactly 6 digits!!!')
                                        continue
                                    else:
                                        address = street + ',' + city + ',' + state + ',' + str(postcode)
                                        break
                            # if failed due to an invalid input, responds to the user with an error message
                            except ValueError:
                                print('Invalid values entered!!!')
                                continue
                            break
                        # updates the data in the database and csv file
                        mc.execute(f"update c_data set address='{address}' where client_id={cid}")
                        print(f'Address successfully updated as {address} for client_id {cid}')
                        mydb.commit()
                    elif upvalue == 5:
                        while True:
                            # trying to take phone number as input
                            try:
                                phno = int(input('Enter the client phone number(updated): '))
                                if len(str(phno)) != 10:
                                    print('Phone number should only be 10 digits long')
                                    continue
                            # if failed due to an invalid input, responds to the user with an error message
                            except ValueError:
                                print('please enter a valid phone number!')
                                continue
                            break
                        # updates the data in the database and csv file
                        updcsv('Name', 'PhoneNo', searchname, phno)
                        mc.execute(f"update c_data set phno={phno} where client_id={cid}")
                        print(f'Phone number successfully updated as {phno} for client_id {cid}')
                        mydb.commit()
                    elif upvalue == 6:
                        while True:
                            # takes email address as input
                            email = input('Enter the client updated email(updated): ')
                            # trying to validate the email address
                            try:
                                v = validate_email(email)
                                email = v["email"]
                            # if failed due to an invalid input, responds to the user with an error message
                            except EmailNotValidError as e:
                                print(str(e))
                                continue
                            break
                        # updates the data in teh database and csv file
                        mc.execute(f"update c_data set email='{email}' where client_id={cid}")
                        print(f'Email address successfully updated as {email} for client_id {cid}')
                        mydb.commit()
                    elif upvalue == 7:
                        while True:
                            # takes name of emergency contact as in input
                            ecname = input("Enter the client's emergency contact full name(updated): ")
                            if len(ecname) < 2:
                                print('pls enter a valid name!')
                                continue
                            while True:
                                # trying to take emergency contact phone number as input
                                try:
                                    phno = int(input("Enter the client's emergency contact phone number(updated): "))
                                    if len(str(phno)) != 10:
                                        print('please enter a valid phone number!')
                                        continue
                                # if failed due to an invalid input, responds to the user with an error message
                                except ValueError:
                                    print('please enter a valid phone number!')
                                    continue
                                emergency_contact = ecname + '  ' + str(phno)
                                break
                            break
                        # updates the data in teh database and csv file
                        mc.execute(f"update c_data set emergency_contact='{emergency_contact}' where client_id={cid}")
                        print(f'Emergency contact successfully updated as {emergency_contact} for client_id {cid}')
                        mydb.commit()
                    elif upvalue == 8:
                        # updates the data in the csv file as package info is only contained in the csv file
                        updcsv('Name', 'Package', searchname)
                    elif upvalue == 9:
                        # updates the data in the csv file as payment frequency info is only contained in the csv file
                        updcsv('Name', 'PaymentFrequency', searchname)
                    else:
                        print('Please enter a valid option!!!')
                        continue
                    break
                    # asks the user whether they would like to continue updating data or not
                ex = input('do you want to continue?(y/n) >').lower()
                if ex == 'y':
                    continue
                else:
                    home_page()
            if colname == 2:
                while True:
                    # trying to take name as input to update the data in the table
                    try:
                        name = input('Enter name you want to update the values of: ')
                    # if failed due to an invalid input, responds to the user with an error message
                    except:
                        print('Invalid input!!!')
                        continue
                    # trying to retrive the data from the database and csv file based on the name given
                    try:
                        mc.execute(f"select * from c_data where name='{name}'")
                        result = mc.fetchall()
                        if result == []:
                            print(f'No Client info found for the name {name}!!!')
                            continue
                        Table = PrettyTable(
                            ['client_id', 'name', 'dob date', 'age', 'gender', 'address', 'phno', 'email',
                             'emergency_contact'])
                        for i in result:
                            Table.add_row([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]])
                            print(f'\n--Client Data--\n\n{Table}')
                            searchname = i[1]
                        bruh = pd.read_csv(fdcsvdir)
                        bruh.index = bruh.index + 1
                        result = bruh[bruh['Name'] == searchname]
                        print(f'\n\n--Package and Fee Data--\n\n{result}\n\n')
                    # if failed due to an invalid input, responds to the user with an error message
                    except con.Error as er:
                        print(er.msg)
                        continue
                    break
                # asks what the user wants to update
                upvalue = int(input('''What do you want to update?
1.name
2.dob 
3.gender
4.address
5.phno
6.email
7.emergency_contact
8.package
9.PaymentFrequency
enter option: '''))
                if upvalue == 1:
                    while True:
                        # trying to take the updated customer id as input
                        try:
                            cname = input("Enter the client's full name(updated): ")
                            if len(cname) < 2:
                                raise ValueError
                        # if failed due to an invalid input, responds to the user with an error message
                        except ValueError:
                            print('Invalid value')
                            continue
                        break
                    # updates the data in the database and csv file
                    updcsv('Name', 'Name', name, cname)
                    mc.execute(f"update c_data set name='{cname}' where name='{name}'")
                    print(f'Name successfully updated as {cname} for client_name {name}')
                    mydb.commit()
                elif upvalue == 2:
                    while True:
                        # trying to take the updated dob as input and calculate the age automatically
                        try:
                            x = input('Enter the dob of the client as YYYY-MM-DD(updated): ').split('-')
                            year, month, date = [int(x[0]), int(x[1]), int(x[2])]
                            cdob = dt.datetime(year, month, date)
                            c = str(cdob)
                            today = dat.today()
                            one_or_zero = ((today.month, today.day) < (cdob.month, cdob.day))
                            year_difference = today.year - cdob.year
                            age = year_difference - one_or_zero
                        # if failed due to an invalid input, responds to the user with an error message
                        except:
                            print('Please enter a valid date!')
                            continue
                        break
                    # updates the data in the database and csv file
                    mc.execute(f"update c_data set age={age},dob='{c}' where name='{name}'")
                    print(f'DOB and age successfully updated as {c} and {age} respectively client_name {name}')
                    mydb.commit()
                elif upvalue == 3:
                    while True:
                        # trying to take gender as input
                        try:
                            ch = input('''Enter updated client gender(updated)
(M)Male
(F)Female
(N)Do not prefer to say
Your choice: ''').upper()
                            if ch not in ['M', 'F', 'N']:
                                raise ValueError
                        # if failed due to an invalid input, responds to the user with an error message
                        except ValueError:
                            print('Please enter a valid option!')
                            continue
                        break
                    # updates the data in the database and csv file
                    mc.execute(f"update c_data set gender='{ch}' where name='{name}'")
                    print(f'Gender successfully updated as {ch} for client_name {name}')
                    mydb.commit()
                elif upvalue == 4:
                    while True:
                        # trying to take updated address as input
                        try:
                            street = input("Enter the client street address(updated): ")
                            city = input('Enter the client city name(updated): ')
                            state = input('Enter the client state(updated): ')
                            if street or city or state == '':
                                print("address values cannot be null!!!")
                                continue
                            while True:
                                try:
                                    zipcode = int(input('Enter the client ZIPCODE(updated): '))
                                except ValueError:
                                    print('Invalid values entered')
                                    continue
                                if len(str(zipcode)) != 6:
                                    print('Zipcode/Postcode should contain exactly 6 digits!!!')
                                    continue
                                else:
                                    address = street + ',' + city + ',' + state + ',' + str(zipcode)
                                    break
                        # if failed due to an invalid input, responds to the user with an error message
                        except ValueError:
                            print('Invalid values entered!!!')
                            continue
                        break
                    # updates the data in the database and csv file
                    mc.execute(f"update c_data set address='{address}' where name='{name}'")
                    print(f'Address successfully updated as {address} for client_name {name}')
                    mydb.commit()
                elif upvalue == 5:
                    while True:
                        # trying to take phone number as input
                        try:
                            phno = int(input('Enter the client phone number: '))
                            if len(str(phno)) != 10:
                                print('Phone number should only be 10 digits long')
                                continue
                        # if failed due to an invalid input, responds to the user with an error message
                        except ValueError:
                            print('please enter a valid phone number!')
                            continue
                        break
                    # updates the data in the database and csv file
                    updcsv('Name', 'PhoneNo', name, phno)
                    mc.execute(f"update c_data set phno={phno} where name='{name}'")
                    print(f'Phone number successfully updated as {phno} for client_name {name}')
                    mydb.commit()
                elif upvalue == 6:
                    while True:
                        # takes email address as input
                        email = input('Enter the client email(updated): ')
                        # validates email address
                        try:
                            v = validate_email(email)
                            email = v["email"]
                        # if failed due to an invalid input, responds to the user with an error message
                        except EmailNotValidError as e:
                            print(str(e))
                            continue
                        break
                    # updates the data in the database and csv file
                    mc.execute(f"update c_data set email='{email}' where name='{name}'")
                    print(f'Email address successfully updated as {email} for client_name {name}')
                    mydb.commit()
                elif upvalue == 7:
                    while True:
                        # takes the updated emergency contact name as input
                        ecname = input("Enter the client's emergency contact full name(updated): ")
                        if len(ecname) < 2:
                            print('pls enter a valid name!')
                            continue
                        while True:
                            # trying to take the updated emergency contact phone number as input
                            try:
                                phno = int(input("Enter the client's emergency contact phone number(updated): "))
                                if len(str(phno)) != 10:
                                    print('please enter a valid phone number!')
                                    continue
                            # if failed due to an invalid input, responds to the user with an error message
                            except ValueError:
                                print('please enter a valid phone number!')
                                continue
                            emergency_contact = ecname + '  ' + str(phno)
                            break
                        break
                    # updates the data in the database and csv file
                    mc.execute(f"update c_data set emergency_contact='{emergency_contact}' where name='{name}'")
                    print(f'Emergency contact successfully updated as {emergency_contact} for client_name {name}')
                    mydb.commit()
                elif upvalue == 8:
                    # updates the data in the csv file as the package info is only contained in the csv file
                    updcsv('Name', 'Package', name)
                elif upvalue == 9:
                    # updates the data in the csv file as the payment frequency is only contained in the csv file
                    updcsv('Name', 'PaymentFrequency', name)
            else:
                print('Please enter a valid option!!!')
                updatec_data()
        # if failed due to an invalid input, responds to the user with an error message
        except ValueError:
            print('Please enter a valid option!!!')
            continue
        ex = input('Do you want to continue updating data?(y/n) >').lower()
        if ex == 'y':
            continue
        else:
            break
    home_page()


def updcsv(searchcolname, upvalcolname, searchval=None, upval=None):
    """Serves to update the data in the csv file"""
    df = pd.read_csv('fee_details.csv')
    df.index += 1
    colnames = []
    for i in df.columns:
        colnames.append(i)
    if searchcolname not in colnames:
        print('Given search column name does not exist in the DataFrame')
        return
    elif upvalcolname not in colnames:
        print('Given update column name does not exist in the DataFrame')
        return
    if searchcolname == 'Name':
        outseaname = 'name'
    elif searchcolname == 'PhoneNo':
        outseaname = 'phone number'
    if upvalcolname == 'Name':
        outupname = 'name'
    elif upvalcolname == 'Package':
        outupname = 'package'
    elif upvalcolname == 'PaymentFrequency':
        outupname = 'payment frequency'
    elif upvalcolname == 'PhoneNo':
        outupname = 'phone number'
    elif upvalcolname == 'Paid':
        outupname = 'Paid'
    ValList = []
    DfName = df[searchcolname]
    for i in DfName:
        ValList.append(i)
    while True:
        if searchval == None:
            searchval = input(f'Enter client {outseaname} you want to change {outupname} of: ')
            pass
        if searchval == '':
            print(f"{outseaname} field cannot be left blank")
            continue
        elif searchval not in ValList:
            print(f'{outseaname} not found!!!')
            continue
        elif upvalcolname == 'Name':
            df.loc[df[searchcolname] == searchval, upvalcolname] = upval
            df.to_csv('fee_details.csv', index=False)
            print("\n", df.loc[df[upvalcolname] == upval], "\n")
            break
        elif upvalcolname == 'Package':
            package, fees = updcsvpackage_selection(searchcolname, upvalcolname, searchval)
            df.loc[df[searchcolname] == searchval, upvalcolname] = package
            df.loc[df[searchcolname] == searchval, 'Amount'] = fees
            df.to_csv('fee_details.csv', index=False)
            print("\n", df.loc[df[searchcolname] == searchval], "\n")
            print('Data updated successfully\n\n')
            break
        elif upvalcolname == 'PaymentFrequency':
            paymentfrequency, fees = updcsvpackage_selection(searchcolname, upvalcolname, searchval)
            df.loc[df[searchcolname] == searchval, upvalcolname] = paymentfrequency
            df.loc[df[searchcolname] == searchval, 'Amount'] = fees
            df.to_csv('fee_details.csv', index=False)
            print("\n", df.loc[df[searchcolname] == searchval], "\n")
            print('Data updated successfully\n\n')
            break
        elif upvalcolname == 'PhoneNo':
            df.loc[df[searchcolname] == searchval, upvalcolname] = upval
            df.to_csv('fee_details.csv', index=False)
            print("\n", df.loc[df[searchcolname] == searchval], "\n")
            break
        elif upvalcolname == 'SubscriptionStatus':
            df.loc[df[searchcolname] == searchval, upvalcolname] = upval
            df.to_csv('fee_details.csv', index=False)
            break


def updcsvpayment_frequency(M, Q, H, Y):
    """Serves as an interface to update the payment frequency"""
    while True:
        try:
            pf = int(input(f'''Select payment frequency
1.Monthly {M}
2.Quarterly {Q}
3.Half Yearly {H}
4.Yearly {Y}
Your choice: '''))
            if pf not in [1, 2, 3, 4]:
                print('Please enter a valid option!!!')
                continue
            else:
                return pf
        except ValueError:
            print('Please enter a valid option!!!')
            continue


def updcsvset_feespf(pfname, M, Q, H, Y):
    """Serves as an interface to set the fees based on the payment frequency where the payment frequency is in text"""
    if pfname == 'Monthly':
        return M
    elif pfname == 'Quarterly':
        return Q
    elif pfname == 'Half Yearly':
        return H
    elif pfname == 'Yearly':
        return Y


def updcsvset_feespfname(pf, M, Q, H, Y):
    """Serves as an interface to set the fees based on the payment frequency where the payment frequency is in number"""
    if pf == 1:
        fees = M
        pfname = 'Monthly'
    elif pf == 2:
        fees = Q
        pfname = 'Quarterly'
    elif pf == 3:
        fees = H
        pfname = 'Half Yearly'
    elif pf == 4:
        fees = Y
        pfname = 'Yearly'
    return fees, pfname


def updcsvpackage_selection(searchcolname, upvalcolnam, searchval):
    """Serves as an interface to update the package"""
    subtype = []
    askforp = False
    askforpf = False
    if upvalcolnam == 'Package':
        askforp = True
    elif upvalcolnam == 'PaymentFrequency':
        askforpf = True
    if askforp:
        while True:
            try:
                sub = int(input('''Select a Package
1.Weight Training
2.Cardio
3.Crossfit
4.Full Pass
5.Personal Training
Your choice: '''))
                if sub not in [1, 2, 3, 4, 5]:
                    print('Invalid option entered')
                else:
                    subtype.append(sub)
                    break
            except:
                print('Invalid input!!!')
    elif askforpf:
        df = pd.read_csv('fee_details.csv')
        xdf = df.loc[df[searchcolname] == searchval, 'Package']
        for i in xdf:
            if i == 'Weight Training':
                subtype.append(1)
            elif i == 'Cardio':
                subtype.append(2)
            elif i == 'Crossfit':
                subtype.append(3)
            elif i == 'Full Pass':
                subtype.append(4)
            elif i == 'Personal Training':
                subtype.append(5)
    if 1 in subtype:
        M, Q, H, Y = 'Rs 1200', 'Rs 3200', 'Rs 6500', 'Rs 13400'
        if askforpf:
            pf = updcsvpayment_frequency(M, Q, H, Y)
            fees, pfname = updcsvset_feespfname(pf, M, Q, H, Y)
            return pfname, fees
        if askforp:
            pfname = searchforpf(searchcolname, searchval)
            fees = updcsvset_feespf(pfname, M, Q, H, Y)
            p = 'Weight Training'
            return p, fees
    elif 2 in subtype:
        M, Q, H, Y = 'Rs 1500', 'Rs 4200', 'Rs 8500', 'Rs 16800'
        if askforpf:
            pf = updcsvpayment_frequency(M, Q, H, Y)
            fees, pfname = updcsvset_feespfname(pf, M, Q, H, Y)
            return pfname, fees
        if askforp:
            pfname = searchforpf(searchcolname, searchval)
            fee = updcsvset_feespf(pfname, M, Q, H, Y)
            p = 'Cardio'
            return p, fee
    elif 3 in subtype:
        M, Q, H, Y = 'Rs 1000', 'Rs 2700', 'Rs 5500', 'Rs 11000'
        if askforpf:
            pf = updcsvpayment_frequency(M, Q, H, Y)
            fees, pfname = updcsvset_feespfname(pf, M, Q, H, Y)
            return pfname, fees
        if askforp:
            pfname = searchforpf(searchcolname, searchval)
            fees = updcsvset_feespf(pfname, M, Q, H, Y)
            p = 'Crossfit'
            return p, fees
    elif 4 in subtype:
        M, Q, H, Y = 'Rs 2300', 'Rs 6600', 'Rs 13300', 'Rs 26500'
        if askforpf:
            pf = updcsvpayment_frequency(M, Q, H, Y)
            fees, pfname = updcsvset_feespfname(pf, M, Q, H, Y)
            return pfname, fees
        if askforp:
            pfname = searchforpf(searchcolname, searchval)
            fees = updcsvset_feespf(pfname, M, Q, H, Y)
            p = 'Full Pass'
            return p, fees
    elif 5 in subtype:
        M, Q, H, Y = 'Rs 5000', 'Rs 13500', 'Rs 27500', 'Rs 55000'
        if askforpf:
            pf = updcsvpayment_frequency(M, Q, H, Y)
            fees, pfname = updcsvset_feespfname(pf, M, Q, H, Y)
            return pfname, fees
        if askforp:
            pfname = searchforpf(searchcolname, searchval)
            fees = updcsvset_feespf(pfname, M, Q, H, Y)
            p = 'Personal Training'
            return p, fees
    else:
        print('Please enter a valid option!!!')
        updcsvpackage_selection(searchcolname, upvalcolnam, searchval)


def searchforpf(searchcolname, searchval):
    """Searches for the payment frequency of a customer if we are updating the package info and payment frequency is
    not given"""

    df = pd.read_csv('fee_details.csv')
    x = df.loc[df[searchcolname] == searchval, "PaymentFrequency"]
    for pf in x:
        return pf


# Starts the program
Startup()
