import sys
import base64
import json
# urllib2 is now split into several urllib modules in python3
try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, HTTPError, Request


# This is (yet another) Python interface to the GitHub v3 API.
# There is no reason to invent our own here except that it is
# already done and does the minimum of what we need.  But if another
# better supported interface exists that provides all the same
# functionality, we should use it.

class GitHub(object):
    BASE = "https://api.github.com"
    def __init__(self, username=None, password=None, token=None):
        self.username = username
        self.password = password
        self.token = token
        self.pager = "?per_page=100"
    def _req(self, path, headers={}, raw=False, isurl=False, params=""):
        # Construct base URL
        if isurl:
            url = path
        else:
            url = self.BASE+path

        # Add pagination part
        url = url+self.pager

        # Add user params
        url = url+params

        # If we have an OAuth token, add it to the URL
        if self.token!=None:
            url = url+"&access_token="+str(self.token)

        # If we have a username and password, create the appropriate
        # Basic Authorization header
        if self.username!=None and self.password!=None:
            base64string = base64.encodestring("%s:%s" % (self.username,
                                                          self.password))
            base64string.replace("\n", "")
            headers["Authorization"] = "Basic %s" % (base64string,)

        # Formulate request
        # print "url = "+str(url)
        req = Request(url, headers=headers)

        # Get response
        response = urlopen(req)

        if raw:
            # If the request is for the raw response, return the
            # (file-like) response object
            return response
        else:
            # Convert reponse (which should be JSON) into a python dictionary
            # and return it
            try:
                ''.decode(encoding='utf8') # dummy to trigger TypeError
                return json.loads(response.read().decode(encoding='utf8'))
            except TypeError:  # Python 2.6 backward compatibility
                return json.loads(response.read())

    def getRepos(self, user):
        try:
            repos = self._req("/users/"+user+"/repos")
            return repos
        except Exception as e:
            print("Error fetching repositories: "+str(e))
            sys.exit(1)
    def getTags(self, user, repo):
        try:
            tags = self._req("/repos/"+user+"/"+repo+"/tags")
            return tags
        except Exception as e:
            print("Error accessing repository tags: "+str(e))
            sys.exit(1)
    def getContents(self, user, repo, ref):
        try:
            # https://api.github.com/repos/dietmarw/M_S_L/contents/?ref=release
            contents = self._req("/repos/"+user+"/"+repo+"/contents/", params="&ref="+ref)
            return contents
        except Exception as e:
            print("Error retrieving repo contents: "+str(e))
            sys.exit(1)
    def getRawFile(self, user, repo, tag, path):
        url = "https://raw.github.com/%s/%s/%s/%s" % (user, repo, tag, path)
        try:
            req = self._req(url, isurl=True, raw=True)
            return req
        except HTTPError as e:
            #print("Error trying to open %s: %s" % (url, str(e)))
            return None
    def getDownload(self, url):
        try:
            return self._req(url, isurl=True, raw=True)
        except Exception as e:
            print("Error downloading file: "+str(e))
            sys.exit(1)