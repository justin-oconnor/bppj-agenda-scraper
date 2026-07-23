# Imports libraries
import os
import csv
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

# Sets up the URL and headers for the request
url = 'https://www.bossierparishla.gov/police-jury/meetings-and-agendas/upcoming-meeting-agenda'
headers = {'User-Agent': f'Justin O\'Connor / The Advocate - {os.environ["WORK_EMAIL"]}'}

# Makes the request and turns the html into soup for parsing
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

# Finds the list of agendas and extracts the title and link for each agenda
rows = []
ul = soup.find('ul', class_='DocumentDownload')
if ul is None:
    raise ValueError('Could not find list. The page structure has likely changed.')

for link in ul.find_all('a', href=True):
    href = link['href']
    if '.pdf' in href.lower():
        for span in link.find_all('span'):
            span.decompose()

        title = link.get_text(strip=True)

        if href.startswith('/'):
            href = 'https://www.bossierparishla.gov' + href

        rows.append({'Title': title, 'Link': href})


# Writes the extracted data to a CSV file
with open('bppj-agendas.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Title', 'Link'])
    writer.writeheader()
    writer.writerows(rows)

# Checks for new agendas by comparing the current list of links to a previously saved list of seen links
seen_file = 'seen_links.csv'

seen_links = set()
if os.path.exists(seen_file):
    with open(seen_file, 'r', encoding='utf-8') as f:
        seen_links = set(line.strip() for line in f)

new_rows = [row for row in rows if row['Link'] not in seen_links]

if new_rows:
    print(f'Found {len(new_rows)} new agenda(s):')
    for row in new_rows:
        print(f" - {row['Link']}")

    with open(seen_file, 'a', encoding='utf-8') as f:
        for row in new_rows:
            f.write(row['Link'] + '\n')
else:
    print('No new agendas found.')

# Sends an email notification if new agendas are found
if new_rows:
    body = 'New Bossier Parish Police Jury agenda(s) found:\n\n'
    for row in new_rows:
        body += f"{row['Title']}\n{row['Link']}\n\n"

    msg = MIMEText(body)
    msg['Subject'] = f'New BPPJ Agenda(s) - {len(new_rows)} found'
    msg['From'] = os.environ['PERSONAL_EMAIL']
    msg['To'] = os.environ['WORK_EMAIL']

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(os.environ['PERSONAL_EMAIL'], os.environ['PERSONAL_EMAIL_PASSWORD'])
        server.send_message(msg)

    print(f'Email sent - {len(new_rows)} new agenda(s).')
else:
    print('No new agendas - no email sent.')