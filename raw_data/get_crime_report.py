import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

''' Find all links to CompStat reports on the NHPD home page, get the link,
    and download the raw PDF report to the directory for further processing
'''

url = "https://www.newhavenct.gov/gov/depts/nhpd/compstat_reports.htm"
page = requests.get(url,verify=False)
soup = BeautifulSoup(page.content, 'html.parser')

# Begin extraction
reports = soup.find_all("a", class_="fbFileName",href=True)
for report in reports:
    raw_report_name = report.find(class_="compare-this").text.split()
    # Get the weekly reports
    if (len(raw_report_name) > 1) and (raw_report_name[1].lower() == 'weekly'):
        # extract date and format nicely
        date = raw_report_name[-6:]
        start_date = ' '.join([date[0][:3],date[1],date[5]])
        end_date = ' '.join([date[3][:3],date[4],date[5]])
        start = datetime.strptime(start_date, '%b %d %Y').strftime('%Y-%m-%d')
        end = datetime.strptime(end_date, '%b %d %Y').strftime('%Y-%m-%d')
        # save PDF to file
        report_name = 'NewHavenCrime_'+start+'_to_'+end+'.pdf'
        report_link = report['href']
        report_url = "https://www.newhavenct.gov/"+report_link
        report_response = requests.get(report_url,verify=False)
        with open(report_name, 'wb') as f:
            f.write(report_response.content)
