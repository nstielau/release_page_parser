import os
import re

from bs4 import BeautifulSoup
from jira import JIRA
import requests


release_page_url = "https://amd64.ocp.releases.ci.openshift.org/releasestream/4-dev-preview/release/4.12.0-ec.5"
release_page = requests.get(release_page_url)

soup = BeautifulSoup(release_page.content, "html.parser")
list_items = soup.find_all("li")

jira_ids = []
for li in list_items:
    children = li.find_all('a')    
    if len(children) == 2:
        text = children[0].text
        if re.search("^[A-Z]+-\d+", text) and not re.search("OCPBUGS", text):
            jira_ids.append(text)


url = "http://issues.redhat.com"
jira = JIRA(url, token_auth=(os.environ['JIRA_TOKEN']))

parents = {}
print("Gettign list of changes with parents: ", end=" ")
for jid in jira_ids:
    issue = jira.issue(jid)
    epic_link = issue.get_field('customfield_12311140')
    parent_link = issue.get_field('customfield_12313140')
    print(jid, end=",", flush=True)

    plink = epic_link or parent_link
    if plink:
        if not parents.get(plink):
            parents[plink] = []   
        parents[plink].append(jid)
print()


nodes = {}
print("Nesting parents")
for jid in parents:
    item = jira.issue(jid)

    epic_link = item.get_field('customfield_12311140')
    parent_link = item.get_field('customfield_12313140')
    plink = epic_link or parent_link

    if plink:
        print(plink, end=", ", flush=True)
        parent = jira.issue(plink)
        if not plink in nodes:
            nodes[plink] = {}
        nodes[plink][jid] = {}
    else:
        nodes[jid] = {}
print()

def recursive_print(parent_dict, spacing = ""):
    if len(parent_dict) == 0:
        print()
        return
    for jira_id in parent_dict:
        item = jira.issue(jira_id)
        print(spacing + item.get_field("issuetype").name + " " + jira_id + ": " + item.get_field("summary"))
        recursive_print(parent_dict[jira_id], spacing + "    ")


print()
print("Changes by parent")
recursive_print(nodes)

