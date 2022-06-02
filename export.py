#!/usr/bin/python3

import sys, json
from datetime import datetime

if __name__ == "__main__":
	if (not (len(sys.argv) == 2)):
		print("Usage: ./export.py <month>/<year>")
		exit(1)
	with open('planning.json', 'r') as f:
		data = json.load(f)
		result = {}
		for key in data:
			date = datetime.strptime(key, "%d/%m/%Y")
			if (date.month == int(sys.argv[1].split('/')[0]) and date.year == int(sys.argv[1].split('/')[1])):
				result.update({key: data[key]})
		print(json.dumps(result))
