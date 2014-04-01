from lxml import etree
filename = 'data/dfid-tz.xml'
doc = etree.parse(filename)

activity_ids= ['GB-1-202481','GB-1-105369','GB-1-200498','GB-1-200980','GB-1-201575','GB-1-202480','GB-1-202181','GB-1-202394','GB-1-200715']

print "Displaying DFID activities that were found to have evaluation documents."

for activity_id in activity_ids:
    activity = doc.xpath("//iati-activity[iati-identifier/text()='"+activity_id+"']")[0]
    
    print ""
    print "Title:", activity.find('title').text
    print "End planned:", activity.xpath('activity-date[@type="end-planned"]')[0].text
    print "Document:", activity.xpath("document-link[category[@code='A07']]")[0].get('url')
