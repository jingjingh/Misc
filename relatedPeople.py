__authors__ = "jingjing"

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv
import re

RHS_CLASS = "div.kno-ecr-pt"
TN_CLASS = "div.kltat"
WEB_DRIVER_TIMEOUT = 10
SECTION_NAME = "People also search for"
IMG_SELECTOR = '//img[starts-with(@id,"kximg")]'
RHS_TIMEOUT_CONDITION = EC.visibility_of_element_located((By.CSS_SELECTOR, RHS_CLASS))
IMG_TIMEOUT_CONDITION = EC.visibility_of_element_located((By.XPATH, IMG_SELECTOR))
CSV_FIELD_NAMES = ['name', 'degree']

# Returns a set of results from 'People Also Search For' for a given name.
def getRelatedNamesByName(name):
	driver = webdriver.Firefox()
	result = set()
	try:
		wait = WebDriverWait(driver, 20)
		driver.get("http://google.com");   
		inputElement = driver.find_element_by_name("q");
		inputElement.send_keys(name);
		driver.find_element_by_name("btnG").click()

		# Navigate to an HTML section that contains all 'People Also Search For' results.
		WebDriverWait(driver, WEB_DRIVER_TIMEOUT).until(RHS_TIMEOUT_CONDITION)

	  	if driver.find_element_by_css_selector(RHS_CLASS).text == name:
			driver.find_element_by_link_text(SECTION_NAME).click();
			WebDriverWait(driver, WEB_DRIVER_TIMEOUT).until(IMG_TIMEOUT_CONDITION);
			nameElems = driver.find_elements_by_css_selector(TN_CLASS);
			result = removeHtmlTags(nameElems)
	except NoSuchElementException:
		result = set()
	except TimeoutException:
		result = set()
	finally:
		driver.quit()

	return result

# Remove html tags for each item in the set
def removeHtmlTags(elems):
	result = set()
	for elem in elems:
		elem = elem.get_attribute("innerHTML")
		result.add(''.join(re.split('</?[a-z]+>', elem)))
	return result

# Get related people to maxDegree [0,) of person with name.
# Returns map{deg:set(names)}
def getRelatedNamesUpToDegree(name, maxDegree):
	nameSet = set([name])
	nameToRelatedNamesMap = {}
	degreeSoFar = 0
	degreeToNameMap = {0:{name}}
	while nameSet and degreeSoFar < maxDegree:
		namesForCurrentDeg = set()
		degreeSoFar += 1
		for name in nameSet:
			# Avoid rescraping.
			if name not in nameToRelatedNamesMap.keys():
				nameToRelatedNamesMap[name] = getRelatedNamesByName(name)
				namesForCurrentDeg = namesForCurrentDeg.union(nameToRelatedNamesMap[name])
		namesForCurrentDeg = namesForCurrentDeg.difference(nameToRelatedNamesMap.keys())
		nameSet = namesForCurrentDeg
		degreeToNameMap[degreeSoFar] = namesForCurrentDeg
	return degreeToNameMap

# Save degree-to-names degDict into a CSV with filename.
def saveToCsv(degDict, fileName):
	with open(fileName, 'w') as csvFile:
		writer = csv.DictWriter(csvFile, fieldnames = CSV_FIELD_NAMES)
		for i in degDict.keys():
			for j in degDict[i]:
				writer.writerow({'name': j.encode('utf-8'), 'degree': str(i)})
	csvFile.close()

def main(personName, maxDegree, csvFilename):
	relatedNames = getRelatedNamesUpToDegree(personName, maxDegree)
	saveToCsv(relatedNames, csvFilename)

main("Mark Zuckerberg", 3, "mark.csv")