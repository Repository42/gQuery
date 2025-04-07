#!/usr/bin/env python3
#CREATION: 5th apr 12:30 BST
#DESCRIPTION:
# gQuery:
# 	light weight graphql querying tool.
#
#TODO
#Query managment
#	 Auto update queries drop down
#	 Load extra queries from .json
#	 Thread?

import argparse
import copy
import json
from http.cookies import SimpleCookie
import os
import requests
from tkinter import *
from tkinter import messagebox, ttk, filedialog

VER_MAJOR = 0
VER_MIN = 1
VER_PATCH = 0
VER_STRING = f"v{VER_MAJOR}.{VER_MIN}.{VER_PATCH}"

DEFAULT_QUERIES_FILE = { # will be used in next version
	"queries": [
		"introspection.graphql",
	]
}

DEFAULT_INTROSPECTION = """query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
    directives {
      name
      description

      locations
      args {
        ...InputValue
      }
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description


  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue


}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

class Functions:
	def sendRequest(self, endpoint: str, headers: dict, cookies: dict, query: dict, timeout: int): #[Status, [Data]]
		try:
			r = self.session.post(endpoint, headers = headers, cookies = cookies, timeout = timeout, json = query)

			return [True, [r.status_code, "Got cloudflare :(" if "Just a moment..." in r.text else r.json()]]
		except requests.exceptions.RequestException as Error:
			return [False, [Error]]

	def getQueries(self, queriesDir):
		queries = []

		for file in os.listdir(queriesDir):
			if file.endswith(".graphql"):
				queries.append(file)

		return queries

	def __init__(self):
		self.session = requests.Session()

class gQuery:
	def clearAll(self):
		self.responseStatus.configure(state = "normal")
		self.responseEntry.configure(state = "normal")

		self.textClear(self.cookiesEntry)
		self.textClear(self.headersEntry)
		self.textClear(self.variablesEntry)
		self.textClear(self.responseEntry)
		self.endPointVariable.set("")
		self.operationNameVar.set("")
		self.selectedQuery.set(self.queries[0])
		self.responseStatus.delete(0, "end")

		self.responseStatus.configure(state = "disabled")
		self.responseEntry.configure(state = "disabled")

	def sendQuery(self):
		errors = []

		endpoint = self.endPointVariable.get()

		if endpoint == "":
			errors.append("Endpoint must be defined!")

		selectedQuery = self.selectedQuery.get()
		operationName = self.operationNameVar.get()

		query = None

		if selectedQuery == "*FROM CURL":
			query = self.queryText
		else:
			path = f"{self.queriesDir}/{selectedQuery}"
			print(f"selected query: `{path}`")

			if os.path.exists(path):
				with open(path) as queryFile:
					query = queryFile.read()
			else:
				errors.append(f"Query path does not exist on disk: `{path}`")

		if query is not None:
			query = {
				"variables": json.loads(self.textGet(self.variablesEntry)),
				"query": query,
			}

			if operationName != "":
				query["operationName"] = operationName

		else:
			errors.append("Query was Null!")

		if errors == []:
			status, data = self.functions.sendRequest(
				endpoint,
				json.loads(self.textGet(self.headersEntry)),
				json.loads(self.textGet(self.cookiesEntry)),
				query,
				self.args.timeout
			)

			if status:
				self.responseStatus.configure(state = "normal")
				self.responseEntry.configure(state = "normal")

				self.responseStatus.delete(0, "end")
				self.textInsert(self.responseStatus, data[0])

				self.textClear(self.responseEntry)
				self.textInsert(self.responseEntry, json.dumps(data[1], indent = 2, ensure_ascii = False))

				self.responseStatus.configure(state = "disabled")
				self.responseEntry.configure(state = "disabled")
			else:
				messagebox.showerror("Error!", f"An error occured whilst sending query: `{data}`")
		else:
			messagebox.showerror("Error!", f"Several errors occured before sending query:\n\t`{'`\n\t`'.join(errors)}`")

	def saveResponse(self):
		path = filedialog.asksaveasfile(mode = "w", initialfile = "schema.json" if self.selectedQuery.get() == "introspection.graphql" else "response.json")

		if path:
			try:
				with path as out:
					out.write(json.dumps(json.loads(self.textGet(self.responseEntry)), indent = "\t", ensure_ascii = False))
			except json.JSONDecodeError:
				messagebox.showerror("Error!", "Could not serialize response as JSON")

	def copyResponse(self):
		self.root.clipboard_clear()
		self.root.clipboard_append(self.textGet(self.responseEntry))
		self.root.update()

	def loadCurl(self):
		try:
			curlVal = self.curlEntry.get("1.0", "end")

			try:
				self.endPointVariable.set(curlVal.split("'")[1].split("'")[0])
			except:
				pass

			if "--data-raw" in curlVal:
				curlVal, data = curlVal.split("--data-raw ")

				try:
					data = json.loads(data.replace("'", ""))
				except:
					data = {}

			curlVal = curlVal.split("' -H '")
			curlVal[0] = curlVal[0].split(" -H '")[1]
			curlVal[-1] = curlVal[-1].rstrip("'")

			headers = {k: v for k, v in [i.split(": ") for i in curlVal]}
			keys = copy.copy(headers).keys()
			headersToRemove = [
				"Accept-Encoding",
				"Cookie",
				"Content-Length",
				"DNT",
				"Sec-GPC",
			]

			cookie = SimpleCookie()
			cookie.load(headers["Cookie"])
			cookies = {k: v.value for k, v in cookie.items()}

			for key in keys:
				if key in headersToRemove:
					headers.pop(key)

			variables = data["variables"] if "variables" in (dataKeys := data.keys()) else {}

			self.textClear(self.cookiesEntry)
			self.textClear(self.headersEntry)
			self.textClear(self.variablesEntry)

			self.textInsert(self.cookiesEntry, json.dumps(cookies, indent = 2, ensure_ascii = False))
			self.textInsert(self.headersEntry, json.dumps(headers, indent = 2, ensure_ascii = False))
			self.textInsert(self.variablesEntry, json.dumps(variables, indent = 2, ensure_ascii = False))

			if "operationName" in dataKeys:
				self.operationNameVar.set(data["operationName"])

			if "query" in dataKeys:
				self.queryText = data["query"]
				self.selectedQuery.set("*FROM CURL")

			self.curlWindow.destroy()
		except Exception as error:
			messagebox.showerror("Error!", f"Could not parse curl command!\n{error}")

	def loadFromCurlWindow(self):
		self.curlWindow = Toplevel(self.root)
		self.curlWindow.geometry("700x410")
		self.curlWindow.resizable(False, False)
		self.curlWindow.title("Load from curl")
		self.curlWindow.grab_set()

		self.curlEntry = Text(self.curlWindow, width = 85, height = 20)
		self.curlEntry.pack(pady = 5, padx = 5)

		buttFrame = ttk.Frame(self.curlWindow)
		buttFrame.pack(pady = 10)

		button = ttk.Button(buttFrame, text = "Load", command = self.loadCurl)
		button.grid(column = 0, row = 0, padx = 5)

		clear = ttk.Button(buttFrame, text = "Clear", command = lambda : self.curlEntry.delete("1.0", "end"))
		clear.grid(column = 1, row = 0, padx = 5)

	def __init__(self):
		parser = argparse.ArgumentParser(description = f"gQuery {VER_STRING} GraphQL Querying Utility")
		#parser.add_argument("--queries", dest = "queries", action = "store", nargs = "?", default = "queries.json", const = "queries.json", type = str, help = "Queries File")
		parser.add_argument("--queriesdir", dest = "queriesDirectory", action = "store", nargs = "?", default = "Queries", const = "Queries", type = str, help = "Queries Directory")
		parser.add_argument("--timeout", dest = "timeout", action = "store", nargs = "?", default = 30, const = 30, type = int, help = "Requests Timeout")
		self.args = parser.parse_args()

		if not os.path.exists(self.args.queriesDirectory):
			os.makedirs(self.args.queriesDirectory)


		self.installLocation = "/".join(__file__.split("/")[:-1])
		self.queriesDir = f"{self.installLocation}/{self.args.queriesDirectory}"

		#if not os.path.exists(queriesFile := f"{self.args.queriesDirectory}/{self.args.queries}"):
			#with open(queriesFile, "w") as out:
				#json.dump(DEFAULT_QUERIES_FILE, out, indent = "\t")

		if not os.path.exists(ip := f"{self.queriesDir}/introspection.graphql"):
			with open(ip, "w") as out:
				out.write(DEFAULT_INTROSPECTION)

		print(f"gQuery {VER_STRING} located at: `{self.installLocation}`")

		self.textClear = lambda obj : obj.delete("0.0", "end")
		self.textInsert = lambda obj, data : obj.insert("end", data)
		self.textGet = lambda obj: obj.get("1.0", "end-1c")

		self.functions = Functions()
		self.queries = self.functions.getQueries(self.queriesDir)

		#DEFINE WINDOW
		self.root = Tk()
		self.style = ttk.Style()
		self.style.theme_use("clam")
		#print(self.style.theme_names())

		self.root.title(f"gQuery {VER_STRING}")
		self.root.resizable(False, False)
		self.root.geometry("1200x970")

		#LEFT FRAME (Text entry widgets)
		self.lFrame = ttk.Frame(self.root)
		self.lFrame.pack(side = "left", anchor = "n", pady = 10, padx = 5)
		self.rFrame = ttk.Frame(self.root)
		self.rFrame.pack(side = "right", anchor = "n", pady = 10, padx = 5)

		#COOKIES
		self.cookiesFrame = ttk.LabelFrame(self.lFrame, text = "Cookies:", padding = 1)
		self.cookiesFrame.pack(pady = 5)
		self.cookiesEntry = Text(self.cookiesFrame, height = 13, width = 60)
		self.cookiesEntry.pack(padx = 5, pady = 5, anchor = "s", side = "bottom")
		self.clearCookiesButton = ttk.Button(self.cookiesFrame, text = "Clear", command = lambda : self.textClear(self.cookiesEntry))
		self.clearCookiesButton.pack(anchor = "ne", padx = 5, pady = 5)

		#HEADERS
		self.headersFrame = ttk.LabelFrame(self.lFrame, text = "Headers:", padding = 1)
		self.headersFrame.pack(pady = 5)
		self.headersEntry = Text(self.headersFrame, height = 13, width = 60)
		self.headersEntry.pack(padx = 5, pady = 5, anchor = "s", side = "bottom")
		self.clearHeadersButton = ttk.Button(self.headersFrame, text = "Clear", command = lambda : self.textClear(self.headersEntry))
		self.clearHeadersButton.pack(anchor = "ne", padx = 5, pady = 5)

		#VARIABLES
		self.variablesFrame = ttk.LabelFrame(self.lFrame, text = "Variables:", padding = 1)
		self.variablesFrame.pack(pady = 5)
		self.variablesEntry = Text(self.variablesFrame, height = 13, width = 60)
		self.variablesEntry.pack(padx = 5, pady = 5, anchor = "s", side = "bottom")
		self.clearVariablesButton = ttk.Button(self.variablesFrame, text = "Clear", command = lambda : self.textClear(self.variablesEntry))
		self.clearVariablesButton.pack(anchor = "ne", padx = 5, pady = 5)

		#RIGHT FRAME (Controls and response)
		self.rFrame = ttk.Frame(self.root, width = 50)
		self.rFrame.pack(anchor = "nw", pady = 10)#padx = [0, 300])

		#CONTROLS
		self.controls = ttk.Frame(self.rFrame)
		self.controls.pack()

		self.endPointLabel = ttk.Label(self.controls, text = "Endpoint:")
		self.endPointLabel.grid(column = 1, row = 1, pady = 5, padx = 5, sticky = "w")

		self.endPointVariable = StringVar(self.root)
		self.endPointEntry = ttk.Entry(self.controls, width = 35, textvariable = self.endPointVariable)
		self.endPointEntry.grid(column = 1, row = 2, pady = 5, padx = 5)

		self.operationNameLabel = ttk.Label(self.controls, text = "Operation Name:")
		self.operationNameLabel.grid(column = 1, row = 3, pady = 5, padx = 5, sticky = "w")

		self.operationNameVar = StringVar(self.root)
		self.operationNameEntry = ttk.Entry(self.controls, width = 35, textvariable = self.operationNameVar)
		self.operationNameEntry.grid(column = 1, row = 4, pady = 5, padx = 5)

		self.selectedQuery = StringVar(self.root)

		self.queriesLabel = ttk.Label(self.controls, text = "Queries:")
		self.queriesLabel.grid(column = 2, row = 1, pady = 5, padx = 10, sticky = "w")

		self.queriesDropDown = ttk.OptionMenu(self.controls, self.selectedQuery, *[self.queries[0], self.queries])
		self.queriesDropDown.grid(column = 2, row = 2, pady = 5, padx = 10, sticky = "w")

		self.buttons = ttk.Frame(self.controls)
		self.buttons.grid(column = 2, row = 4, pady = 5, padx = 6, sticky = "w", columnspan = 3)


		self.loadFromCurlButton = ttk.Button(self.buttons, text = "Load From Curl", command = self.loadFromCurlWindow)
		self.loadFromCurlButton.pack(side = "left", padx = 5)

		self.sendRequestButton = ttk.Button(self.buttons, text = "Send", command = self.sendQuery)
		self.sendRequestButton.pack(side = "left", padx = 5)

		self.clearAllButton = ttk.Button(self.buttons, text = "Clear All", command = self.clearAll)
		self.clearAllButton.pack(side = "left", padx = 5)

		#RESPONSE
		self.response = ttk.Labelframe(self.rFrame, width = 50, text = "Response:", padding = 1)
		self.response.pack(anchor = "ne", pady = 5, padx = 10)

		self.responseControls = ttk.Frame(self.response)
		self.responseControls.pack(anchor = "ne", pady = 5)

		self.responseStatus = ttk.Entry(self.responseControls, width = 3, state = "disabled")
		self.responseStatus.pack(side = "right", padx = 5)

		self.responseLabel = ttk.Label(self.responseControls, text = "Status Code")
		self.responseLabel.pack(side = "right", padx = 5)

		self.responseSave = ttk.Button(self.responseControls, text = "Save", command = self.saveResponse)
		self.responseSave.pack(side = "right", padx = 5)

		self.responseCopy = ttk.Button(self.responseControls, text = "Copy", command = self.copyResponse)
		self.responseCopy.pack(side = "left", padx = 5)

		self.responseEntry = Text(self.response, height = 42, state = "disabled")
		self.responseEntry.pack(padx = 5, pady = 5, anchor = "s", side = "bottom")

		self.root.mainloop()

if __name__ == "__main__":
	if (platform := os.sys.platform) != "linux":
		print(f"Unsupported system: `{platform}`")
		exit()
	gQuery()
