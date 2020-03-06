# redmine.py -- a python library that allows working with
# redmine - a project management software
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Author: Alex Lourie <djay.il@gmail.com> @alourie
# Redmine: Copyright (C) 2006-2013  Jean-Philippe Lang

import os
import requests
from json import dumps, JSONDecodeError
from base64 import b64decode

class Redmine:

    def __init__(self, url=None, auth=None, b64_api_access_key=None):
        self.url = url
        self.session = requests.Session()
        self.session.auth = auth or (b64decode(b64_api_access_key), None)
        if not self.session.auth:
            raise Exception(
                "Error! No auth nor API access key for redmine were given!"
            )
        self.session.verify = False
        self.session.headers = {'content-type': 'application/json'}

    def get_project_url(self, project_id=None):
        if project_id:
            url = self.url + "/projects/%s.json" % project_id
        else:
            url = self.url + "/projects.json"
        return url

    def get_issue_url(self, issue_id=None):
        if issue_id:
            url = self.url + "/issues/%s.json" % issue_id
        else:
            url = self.url + "/issues.json"
        return url

    def get_time_entry_url(self, time_entry_id=None):
        ''' Get http://REDMINE_HOST/time_entries/[ISSUE_ID].xml url '''
        if time_entry_id:
            url = self.url + "/time_entries/%s.json" % time_entry_id
        else:
            url = self.url + "/time_entries.json"
        return url

    def getProject(self, project_id=None, name=None):
        if not project_id and not name:
            return None

        if project_id and name:
            raise TypeError("Please specify id or name, not both.")

        project_id = project_id or name
        r = self.session.get(self.get_project_url(project_id=project_id))
        return self.Project(r.json())

    def getProjects(self):
        r = self.session.get(self.get_project_url(), data=dumps({'limit': 999}))
        try:
            return [self.Project(data) for data in r.json()['projects']]
        except KeyError:
            raise TypeError(r.json()['errors']) 

    def getIssue(self, issue_id):
        r = self.session.get(self.get_issue_url(issue_id))
        return self.Issue(r.json())

    def getTimeEntry(self, time_entry_id):
        ''' Get a particular Time Entry. HTTP return code 200 ok, 404 error '''
        r = self.session.get(self.get_time_entry_url(time_entry_id))
        return self.TimeEntry(r.json())

    def getIssues(self, criteria=None):
        if criteria and not 'limit' in criteria:
            criteria.update({'limit': 100})
        elif not criteria:
            criteria = ({'limit': 100})
        r = self.session.get(self.get_issue_url(),
                       data=dumps(criteria))
        try:
            return [self.Issue(data) for data in r.json()['issues']]
        except KeyError:
            raise TypeError(r.json()['errors']) 

    def getTimeEntries(self, criteria=None):
        ''' Get Time Entries of a particular Issue filtered by criteria '''
        if criteria and not 'limit' in criteria:
            criteria.update({'limit': 100})
        elif not criteria:
            criteria = ({'limit': 100})
        r = self.session.get(self.get_time_entry_url(),
                       data=dumps(criteria))
        # r.json() will fail with a 403 response
        try:
            return [self.TimeEntry(data) for data in r.json()['time_entries']]
        except KeyError:
            raise TypeError(r.json()['errors']) 
        except JSONDecodeError:
            return self.TimeEntry({'message': '403 forbidden'})

    def updateIssue(self, issue_id, data):
        print("Updating issue {id} with data:{data}".format(
            id=issue_id,
            data=data,
        ))
        r = self.session.put(self.get_issue_url(issue_id), data=dumps(data))
        return r

    def createIssue(self, data):
        r = self.session.post(self.get_issue_url(), data=dumps(data))
        return r

    def createTimeEntry(self, data):
        ''' Creates a Time Entry attached to a given Issue or Project '''
        r = self.session.post(self.get_time_entry_url(), data=dumps(data))
        return r

    class RedmineObj(object):

        def __init__(self, data, objType):
            if not isinstance(data, dict):
                raise TypeError("Data must be dict!")
            self.raw_data = data
            self.objType = objType
            self.to_obj(data)

        def to_obj(self, data):
            if self.objType in data:
                self.__dict__.update(**data[self.objType])
            else:
                self.__dict__.update(**data)

        def __repr__(self):
            t = self.get_data()
            output = "Redmine %s object:\n" % self.objType
            output = output + "{\n"
            for k, v in t.items():
                output = output + "    '%s': '%s',\n" % (k, v)
            output = output + "}"
            return output

        def __getitem__(self, item):
            t = self.get_data()
            if item in t:
                return t[item]
            return None

        def get_data(self):
            ndata = self.__dict__.copy()
            del ndata['raw_data']
            return ndata

    class Project(RedmineObj):
        def __init__(self, data):
            super(Redmine.Project, self).__init__(data, 'project')

    class Issue(RedmineObj):
        def __init__(self, data):
            super(Redmine.Issue, self).__init__(data, 'issue')

    class TimeEntry(RedmineObj):
        def __init__(self, data):
            super(Redmine.TimeEntry, self).__init__(data, 'time_entry')
