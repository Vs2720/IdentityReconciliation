from django.shortcuts import render
from django.http import HttpResponse
from .models import Customer
from django.utils import timezone
from django.db.models import Q
import json

class IdentityResponse:
    def __init__(self, primaryContatctId: int, emails : list[str], phoneNumbers: list[str], secondaryContactIds : list[int]) -> None:
        self.primaryContatctId = primaryContatctId 
        self.emails = emails 
        self.phoneNumbers = phoneNumbers 
        self.secondaryContactIds = secondaryContactIds
    def to_json(self):
        return json.dumps({"contact": self.__dict__})

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} ('id : {self.primaryContactId} ',emails : {self.emails}, phoneNumbers: {self.phoneNumbers}, sids : {self.secondaryContactIds})"
    

def identify(request):
    if request.method == 'POST':
        reqBody = json.loads(request.body)
        email = reqBody["email"]
        phno = reqBody["phoneNumber"]
        if email is None and phno is None:
            return HttpResponse({'error': 'Bad request both email and phone no cannot be null'}, status=400) 
        if email is None:
            query = Q(phoneNumber=phno)
        elif phno is None:
            query = Q(email=email)
        else:
            query = Q(phoneNumber=phno) | Q(email=email)
        maybeListOfObj = Customer.objects.filter(query)
        maybeListOfObj.order_by('createdAt')
        oldestObj = None
        if not maybeListOfObj:
            return createNewEntity(phno, email)
        else:
            lkids = set([obj.linkedId for obj in maybeListOfObj])
            primaryObjectList = list(Customer.objects.filter(Q(id__in=lkids)))
            if maybeListOfObj[0].linkPrecedence == "primary":
                oldestObj = maybeListOfObj[0]
                primaryObjectList.append(oldestObj)
            secondIds = set([obj.id for obj in primaryObjectList])
            secondaryObjectList = list(Customer.objects.filter(Q(linkedId__in=secondIds)))
        customerObjectList = primaryObjectList + secondaryObjectList
        # oldestObj = None
        for obj in primaryObjectList:
            if obj.linkPrecedence == 'primary':
                if oldestObj is None:
                    oldestObj = obj 
                else:
                    if oldestObj.createdAt > obj.createdAt:
                        oldestObj = obj
        emails = {oldestObj.email}
        phnos = {oldestObj.phoneNumber}
        secondaryIds = []
        doesEmailExistInDb = False
        if email is None:
            doesEmailExistInDb = True 
        doesPhoneExistInDb = False
        if phno is None:
            doesPhoneExistInDb = True
        for obj in customerObjectList:
            phnos.add(obj.phoneNumber)
            emails.add(obj.email)
            if obj.phoneNumber == phno:
                doesPhoneExistInDb = True 
            if obj.email == email:
                doesEmailExistInDb = True
            if oldestObj.id != obj.id:
                updateCustomer(obj,oldestObj.id)
                secondaryIds.append(obj.id)
        if not doesEmailExistInDb or not doesPhoneExistInDb:
            newCust = createNewCustomer(phno,email,oldestObj.id)
            phnos.add(newCust.phoneNumber)
            emails.add(newCust.email)
            secondaryIds.append(newCust.id)
            res = IdentityResponse(oldestObj.id,list(emails),list(phnos),secondaryIds)
        else:
            res = IdentityResponse(oldestObj.id,list(emails),list(phnos),secondaryIds)
        return HttpResponse(res.to_json(), content_type="appplication/json") 
    else:
        return HttpResponse({'error': 'Method not allowed'}, status=405)
    
def createNewCustomer(phoneNo, email, lkid) -> Customer:
    newCust = Customer()
    if lkid is not None:
        newCust.linkedId = lkid 
        newCust.linkPrecedence = "secondary"
    else:
        newCust.linkedId = None
        newCust.linkPrecedence = "primary"
    newCust.phoneNumber = phoneNo
    newCust.email = email 
    newCust.createdAt = timezone.now()
    newCust.updatedAt = timezone.now()
    newCust.save()
    return newCust

def updateCustomer(obj : Customer, linkId):
    obj.linkedId = linkId
    obj.linkPrecedence = "secondary"
    obj.updatedAt = timezone.now()
    obj.save() 

def createNewEntity(phno: str, email: str):
    createRes = createNewCustomer(phno, email, None)
    res = IdentityResponse(createRes.id,[createRes.email],[createRes.phoneNumber],[])
    return HttpResponse(res.to_json(), content_type="appplication/json")