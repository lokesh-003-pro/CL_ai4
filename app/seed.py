from . import db
from .models import Question

def Q(module, cat, diff, text, options=None, answer=None, exp=None, kw=None, dom="General Graduate Placement"):
    return Question(module=module, category=cat, difficulty=diff, text=text, options=options, answer=answer, explanation=exp, keywords=kw, domain=dom)

SAMPLES = [
 Q("aptitude","Quantitative","easy","What is 15% of 240?",["24","30","36","40"],2,"0.15 x 240 = 36."),
 Q("aptitude","Quantitative","medium","A train 120 m long passes a pole in 6 s. Its speed in km/h is?",["60","72","80","90"],1,"120/6 = 20 m/s = 72 km/h."),
 Q("aptitude","Quantitative","hard","If x + 1/x = 3, what is x^2 + 1/x^2?",["5","7","9","11"],1,"Squaring gives x^2 + 2 + 1/x^2 = 9, so 7."),
 Q("aptitude","Logical","easy","Find the next number: 2, 6, 12, 20, ?",["28","30","32","36"],1,"Differences grow by 2: +4, +6, +8, +10 gives 30."),
 Q("aptitude","Logical","medium","All roses are flowers. Some flowers fade quickly. Which is certain?",["All roses fade quickly","Some roses fade quickly","No rose fades quickly","None of these is certain"],3,"The statements do not link roses to fading."),
 Q("aptitude","Verbal","easy","Choose the synonym of 'brief'.",["Long","Short","Heavy","Loud"],1,"Brief means short."),
 Q("aptitude","Verbal","medium","Pick the correctly spelt word.",["Occurence","Occurrence","Ocurrence","Occurance"],1,"Occurrence has double c and double r."),
 Q("hr","Introduction","easy","Tell me about yourself.",kw="education,skills,experience,goal"),
 Q("hr","Behavioral","medium","Describe a time you worked in a team to solve a problem.",kw="team,problem,role,result"),
 Q("hr","Behavioral","medium","Tell me about a conflict you resolved.",kw="conflict,listened,solution,result"),
 Q("hr","Motivation","easy","Why should we hire you?",kw="skills,value,learn,company"),
 Q("gd","Technology","medium","Will AI create more jobs than it removes?",kw="automation,skills,jobs,productivity"),
 Q("gd","Education","medium","Should online learning replace classroom teaching?",kw="access,interaction,cost,quality"),
 Q("gd","Environment","medium","Is electric transport the answer to urban pollution?",kw="emissions,battery,infrastructure,cost"),
 Q("tech","SQL","easy","What is the difference between WHERE and HAVING?",kw="filter,group,aggregate,rows",dom="Software Developer"),
 Q("tech","OOP","easy","Explain polymorphism with an example.",kw="overriding,overloading,interface,method",dom="Software Developer"),
 Q("tech","DBMS","medium","What are the ACID properties?",kw="atomicity,consistency,isolation,durability",dom="Software Developer"),
 Q("tech",'Python',"medium",'Explain the difference between a list and a tuple in Python.',kw='mutable,immutable,performance,hashable',dom='Python Developer'),
 Q("tech",'Python',"medium",'What are decorators and when would you use them?',kw='function,wrapper,logging,reuse',dom='Python Developer'),
 Q("tech",'Java',"medium",'Explain the difference between an interface and an abstract class.',kw='multiple,inheritance,default,abstract',dom='Java Developer'),
 Q("tech",'Java',"medium",'How does garbage collection work in Java?',kw='heap,unreachable,memory,jvm',dom='Java Developer'),
 Q("tech",'JavaScript',"medium",'What is the difference between let, const and var in JavaScript?',kw='scope,hoisting,reassign,block',dom='Frontend Developer'),
 Q("tech",'CSS',"medium",'Explain the CSS box model.',kw='margin,border,padding,content',dom='Frontend Developer'),
 Q("tech",'APIs',"medium",'What is a REST API and what are the common HTTP methods?',kw='get,post,put,delete,stateless',dom='Backend Developer'),
 Q("tech",'Security',"medium",'How do you prevent SQL injection?',kw='parameterized,validate,orm,escape',dom='Backend Developer'),
 Q("tech",'Data cleaning',"medium",'How do you handle missing values in a dataset?',kw='remove,impute,mean,median,context',dom='Data Analyst'),
 Q("tech",'Charts',"medium",'What is the difference between a bar chart and a histogram?',kw='categorical,continuous,bins,distribution',dom='Data Analyst'),
 Q("tech",'Machine learning',"medium",'What is overfitting and how can you reduce it?',kw='training,validation,regularization,cross-validation',dom='Data Scientist / ML Engineer'),
 Q("tech",'Machine learning',"medium",'Explain precision and recall.',kw='false positive,false negative,precision,recall',dom='Data Scientist / ML Engineer'),
 Q("tech",'Testing',"medium",'What is the difference between smoke testing and regression testing?',kw='build,stable,existing,changes',dom='QA / Testing Engineer'),
 Q("tech",'Testing',"medium",'How do you write a good bug report?',kw='steps,expected,actual,severity',dom='QA / Testing Engineer'),
 Q("tech",'DevOps',"medium",'What is CI/CD and why is it useful?',kw='integration,delivery,automation,pipeline',dom='Cloud / DevOps'),
 Q("tech",'Containers',"medium",'Explain the difference between a container and a virtual machine.',kw='kernel,isolation,lightweight,hypervisor',dom='Cloud / DevOps'),
 Q("tech",'Security basics',"medium",'What is the difference between authentication and authorization?',kw='identity,permission,login,access',dom='Cybersecurity'),
 Q("tech",'Security basics',"medium",'Explain phishing and how to defend against it.',kw='email,link,awareness,mfa',dom='Cybersecurity'),
 Q("tech",'SQL',"medium",'What is the difference between INNER JOIN and LEFT JOIN?',kw='matching,all rows,null,left table',dom='SQL / Database Developer'),
 Q("tech",'DBMS',"medium",'What is database normalization?',kw='redundancy,anomaly,normal form,tables',dom='SQL / Database Developer'),
 Q("tech",'Data structures',"medium",'What is the difference between an array and a linked list?',kw='contiguous,pointer,insertion,access',dom='Software Developer'),
 Q("tech",'Projects',"medium",'Describe a project you are proud of and the challenge you solved.',kw='project,challenge,role,result',dom='General Graduate Placement'),
 Q("tech",'Learning',"medium",'How do you learn a new technology quickly?',kw='documentation,practice,project,mentor',dom='General Graduate Placement'),
]

def seed():
    """Adds any sample question that is missing, so it is safe to run again."""
    have = {q.text for q in Question.query.all()}
    new = [q for q in SAMPLES if q.text not in have]
    if new:
        db.session.add_all(new)
        db.session.commit()
    return len(new)
