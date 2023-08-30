import csv, os, re

#"LIBRARY" portion:
class courseData:
    def __init__(self) -> None:
        self.courseComps = []
        self.title = ''
        self.courseNumber = int()
        self.subject = ''
    def courseMatch(self, courseTitleStr) -> bool:
        self.matched = str(self.courseNumber) in courseTitleStr and self.subject.lower() in courseTitleStr.lower()
        return self.matched
    def __repr__(self) -> str:
        return f'''Course: {" ".join([self.subject,self.courseNumber]):>8} | Course Title: {self.title:30} |\n{'-'*100}\n{self.courseComps}\n'''
    def __str__(self) -> str:
        return self.__repr__()

class sectionData(courseData):
    def __init__(self) -> None:
        courseData.__init__(self)
        self.sectionID = ''
        self.matched = False
    def dictionary(self):
        csvFormattedDict = {}
        csvFormattedDict['Course'] = f'{self.subject} {self.courseNumber} {self.sectionID}'
        csvFormattedDict['Title'] = self.title
        for num,_competency in enumerate(self.courseComps): #"num+1" is below so that our output starts at 1 in the CSV export
            csvFormattedDict[f"Competency {num+1}"] = _competency.competency
            csvFormattedDict[f"Competency {num+1} nearest match:"] = _competency.nearestCompetencyPercentage
            csvFormattedDict[f"Competency {num+1} match %:"] = f'{(100-(_competency.minPercentLD*100)):.0f}'
        return csvFormattedDict
    def courseMatch(self, courseTitleStr,documentText=None) -> bool:
        #for courseTitleDigitsList: getting longest consecutive sequence of digits
        #replace all non-digits with a space ' '
        #then, resplit that new string into a list of integers based on the spaces
        #convert to integers, remove spaces
        #so 'COM 1812 8-16-2014' -> [1812,8,16,2014]
        courseTitleDigitsList = ''.join([(char) if char.isdigit() else ' ' for char in courseTitleStr]).split(' ')
        while '' in courseTitleDigitsList: courseTitleDigitsList.remove('')
        courseTitleDigitsList = [int(number) for number in courseTitleDigitsList]
        matched = int(self.courseNumber) in courseTitleDigitsList and self.subject.lower() in courseTitleStr.lower()
        if matched: self.matched = True
        if documentText is not None and matched: self.massTextCompComparison(documentText)
        return matched
    def massTextCompComparison(self,text):
        #print("RUNNING MASS TEXT COMPARISON")
        #I thought it was better to have this take BOTH a list of strings and a single long string
        try: text = stripCompetencies(text)
        except: pass
        for line in text: self.inlineCompetencyComparison(line)
    def inlineCompetencyComparison(self,compareString):
        #the "compareCompetency" method below takes care of keeping our best string
        for _competency in self.courseComps: 
            _competency.compareCompetency(compareString)

class competency():
    def __init__(self,competency_string) -> None:
        self.competency = competency_string
        self.nearestCompetencyPercentage = ''
        self.nearestCompetencyRawDistance = ''
        self.minLD = -1
        self.minPercentLD = -1.1
    def __repr__(self) -> str:
        return f'{self.competency} --> {self.nearestCompetencyPercentage}  | FIDELITY: {(100-(self.minPercentLD*100)):.0f}%\n'
    def __str__(self) -> str:
        return self.__repr__()
    def compareCompetency(self,compareString): #I think we can make this tighter later
        LevDistance = self.levenshtein_distance(compareString)
        LDPercent = LevDistance/len(self.competency)
        if LevDistance < self.minLD or self.minLD == -1: 
            self.minLD = LevDistance
            self.nearestCompetencyRawDistance = compareString
        if LDPercent < self.minPercentLD or self.minPercentLD == -1.1:
            self.minPercentLD = LDPercent
            self.nearestCompetencyPercentage = compareString
        #if LDPercent < .2: print(f'\"{self.competency}\" against --> \n \"{compareString}\"\nPercentage of Characters requiring change: {(LDPercent*100):.0f}%')
    def levenshtein_distance(self,compareString,originalString=None) -> int():
        t = compareString.lower()
        if originalString is None: s = self.competency.lower()
        m = len(s)
        n = len(t)
        d = [[0] * (n + 1) for i in range(m + 1)]  

        for i in range(1, m + 1):
            d[i][0] = i

        for j in range(1, n + 1):
            d[0][j] = j
        
        for j in range(1, n + 1):
            for i in range(1, m + 1):
                if s[i - 1] == t[j - 1]:
                    cost = 0
                else:
                    cost = 1
                d[i][j] = min(d[i - 1][j] + 1,      # deletion
                            d[i][j - 1] + 1,      # insertion
                            d[i - 1][j - 1] + cost) # substitution   
        #print(f'LEVENSHTEIN CALCULATION RESULTS: {d[m][n]}')
        return d[m][n]


def stripCompetencies(ccomps):
    ccomps = ccomps.replace('Course Competencies','')
    ccomps = ccomps.replace('Upon completion of this course, the student can','')
    ccomps = ccomps.replace('Â','')
    ccomps = re.sub(r'\d+\. ', '', ccomps)
    ccomps = re.sub(r'^(.*(competencies|outcomes).*:.*\n)', '', ccomps, flags=re.IGNORECASE | re.MULTILINE)
    for line in ccomps: line.strip()
    ccomps = re.sub(r'\n(?=\n|\s)', '', ccomps)
    if ccomps[:1] == '\n': ccomps = ccomps.replace('\n','',1)
    ccomps = ccomps.splitlines(keepends=False)
    if ' ' in ccomps: ccomps.remove(' ')
    return ccomps

#"FUNCTIONAL" portion

#grab some environment variables
envDict = {}
with open('.env') as envFile:
    homepath = os.path.expanduser('~')
    for line in envFile:
        if line[0] != "#": 
            key, value = line.strip().split('=')
            value = value.replace('~',homepath)
            envDict[key.strip()] = value.strip()

[print(f'{key}: {envDict[key]}') for key in envDict]

#get our CSV file as list of dictionaries
sectionsSource = envDict['sectionsSource']
with open(sectionsSource,'r',encoding='ISO-8859-1') as csvFile: #encoding is required for many CSV files
    csvData = [row for row in csv.DictReader(csvFile)]

#now we generate a list of sectionData() objects, with courseCompetencies stripped of newlines and other content
sectionDataList = []
for row in csvData:
    newSection = sectionData()
    newSection.term = row['Term']
    newSection.title = row['Title']
    newSection.subject, newSection.courseNumber, newSection.sectionID = row['Name'].split(' ')
    print(f'{newSection.subject},{newSection.courseNumber},{newSection.sectionID}')
    newSection.courseNumber = ''.join([char for char in newSection.courseNumber if char in ('0','1','2','3','4','5','6','7','8','9')])
    courseComps = stripCompetencies(row['Course Competencies Content'])
    [newSection.courseComps.append(competency(_competency)) for _competency in courseComps if _competency.strip() != '']
    sectionDataList.append(newSection)

#this is a function for grabbing info from a word document in the form of a tuple: ('document title (no extension)','document text (stripped)')
import zipfile
import xml.dom.minidom
def grabDocInfo(documentDirectory) -> ('title','docText'):
    #doc = open(documentDirectory,encoding='ISO-8859-1')
    #doc.read()
    #https://github.com/nmolivo/tesu_scraper/blob/master/Python_Blogs/01_extract_from_MSWord.ipynb
    #specific to extracting information from word documents
    document = zipfile.ZipFile(documentDirectory)
    #document.namelist()
    uglyXml = xml.dom.minidom.parseString(document.read('word/document.xml')).toprettyxml(indent='  ')
    text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
    prettyXml = text_re.sub('>\g<1></', uglyXml)
    text = re.findall(r'<w:t>(.*?)</w:t>',prettyXml)
    docDir = documentDirectory.split('\\')
    docTitle = docDir[-1].replace('.docx','')
    return (docTitle,text)

x = 'Identify elements of the oral communication process/model.'
y = '1.	Identify elements of the oral communication process/model.'
z = '1.	Identify elements of the oral communication process and/or model.'
a = 'dentify elements of the oral communication processmodel'

#trawling our docx files and grabbing their text content, along with titles
sourceDir = envDict['courseDirectory']
os.chdir(sourceDir)
dir = os.listdir(sourceDir)
dir = [item for item in dir if item.__contains__('.docx')]
print(f'Documents to examine from {envDict["courseDirectory"]}: {dir}')
allDocuments = tuple([grabDocInfo(file) for file in dir])

#go through the tuple we made and all sections imported from CSV file
#if the document info matches the sectionData, run a mass course competency comparison. 
#this data is retained in each section
for section in sectionDataList:
    for title,doc in allDocuments:
        section.courseMatch(title,documentText=doc)

temp = [sect.__str__() for sect in sectionDataList if sect.matched]
with open(envDict['reportOutput'].replace(".csv",".txt"),'wa+') as txtfile:
    txtfile.write(';'.join(temp))

'''with open(envDict['reportOutput'],'w') as csvFile: #encoding is required for many CSV files
    #this is terrible, but it works fine for getting our columnNames right
    fieldnames = []
    fieldnames1 = [f"Competency {i}" for i in range(1,300)]
    fieldnames2 = [f"Competency {i} nearest match:" for i in range(1,300)]
    fieldnames3 = [f"Competency {i} match %:" for i in range(1,300)]
    for i in range(len(fieldnames1)):
        fieldnames.append(fieldnames1[i])
        fieldnames.append(fieldnames2[i])
        fieldnames.append(fieldnames3[i])
    fieldnames.insert(0,'Course')
    fieldnames.insert(0,'Title')
    print(fieldnames)
    writer = csv.DictWriter(csvFile,fieldnames=fieldnames)
    writer.writeheader()
    #[writer.writerow(sectionObject.dictionary()) for sectionObject in sectionDataList]
    for s in sectionDataList:
        print(s.dictionary())
        try: writer.writerow(s.dictionary())
        except UnicodeEncodeError:
            newDict = {key:value.encode('utf-8') for key,value in s.dictionary().items()}
            writer.writerow(newDict)'''