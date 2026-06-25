import re


#                                             Authenticate User                                            #
############################################################################################################
def name_valid(name):
    if name.isalpha() and len(name) > 1:
        return True
    else:
        return False

def password_valid(pass1):
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
	
	# compiling regex
    pat = re.compile(reg)
	
	# searching regex				
    mat = re.search(pat, pass1)
	
	# validating conditions
    if mat:
        return True
    else:
        return False

def password_check(password1, password2):
    if password1 == password2:
        return True
    else : 
        return False



def authentication(first_name, last_name, pass1, pass2):
    if name_valid(first_name) == False:
        return "Invalid First Name"           
    elif name_valid(last_name) == False:
            return "Invalid Last Name"
    elif password_valid(pass1) == False:
        return "Password Should be in Proper Format. (eg. Password@1234)"
    elif password_check(pass1, pass2) == False:
        return "Password Not Matched"
    else:
        return "success"

def comp_name_valid(name):
    if all(char.isalpha() or char.isspace() for char in name) and len(name) > 1:
        return True
    else:
        return False
    
def is_valid_indian_mobile_number(phone_number):
    # Check if the phone number is a string of 10 digits
    if len(phone_number) == 10 and phone_number.isdigit():
        # Check if the first digit is 7, 8, or 9
        if phone_number[0] in ['7', '8', '9']:
            return True
    return False

def authenticatio2(first_name,contact, pass1, pass2):
    if comp_name_valid(first_name) == False:
        return "Invalid Company Name"           
    elif is_valid_indian_mobile_number(contact) == False:
        return "Invalid Contact Number"
    elif password_valid(pass1) == False:
        return "Password Should be in Proper Format. (eg. Password@1234)"
    elif password_check(pass1, pass2) == False:
        return "Password Not Matched"
    else:
        return "success"