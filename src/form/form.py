#These are things like text elements, password fields, radio buttons
class Input:
    def __init__(self, desc, type, name):
        self.type = type
        self.name = name
        self.desc = desc
    
    def __str__(self):
        return "<span class='form_desc'>{desc}</span><input type='{type}' name='{name}'/>".format(desc=self.desc, type=self.type, name=self.name)

#Drop down select
class DropDown:
    #options needs to be an iterable of dictionaries with the keys: 'key' and 'display_string'
    def __init__(self, desc, name, options):
        self.desc = desc
        self.name = name
        self.options = options
        
    def __str__(self):
        optionHtmls = ["<option value='{key}'>{opt}</option>".format(key=option['key'], opt=option['display_string']) for option in self.options]
        return "<span class='form_desc'>{desc}</span><select name='{name}'>".format(desc=self.desc, name=self.name) + "".join(optionHtmls) + "</select>"
        
class SubmitButton:
    def __init__(self, desc):
        self.desc = desc
    
    def __str__(self):
        return "<input type='submit' value='{desc}' />".format(desc=self.desc)
        
#Aids in creating webforms
class Form:
    def __init__(self, action, method):
        if not action:
            self.action = ""
        if not method:
            self.method = ""
        
        self.action = action
        self.method = method
        self.elements = list()
    
    def addTextField(self, desc, name):
        input = Input(desc=desc, type="text", name=name)
        self.elements.append(input)
        return self
    
    def addPasswordField(self, desc, name):
        input = Input(desc=desc, type="password", name=name)
        self.elements.append(input)
        return self
    
    def addDropDown(self, desc, name, options):
        dropdown = DropDown(desc=desc, name=name, options=options)
        self.elements.append(dropdown)
        return self
        
    def addSubmitButton(self, desc):
        input = SubmitButton(desc=desc)
        self.elements.append(input)
        return self

    def __str__(self):
        return "<form action='{action}' method='{method}'>".format(action=self.action, method=self.method) + "".join([str(elem) for elem in self.elements]) + "</form>"