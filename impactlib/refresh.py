import json
import os
import re

from impactlib.github import GitHub
from impactlib.semver import SemanticVersion
from impactlib import config

def extract_dependencies(fp):
    deps = {}
    contents = fp.read()
    contents = contents.replace("\n","")
    contents = contents.replace("\r","")
    pat = """([A-Za-z]\w*)\s*\(\s*version\s*=\s*"(\d+\.\d+)(\.\d+)?"\s*\)"""
    c = re.compile(pat)
    matches = re.findall(c, contents)
    for m in matches:
        if m[0]=="uses":
            continue
        deps[m[0]] = m[1]+m[2]
    ret = []
    for dep in deps:
        ret.append((dep, deps[dep]))
    return ret

def get_package_details(user, repo, tag, github, ver, verbose):
    """
    This function returns a tuple.

    The first element in the tuple is that path of the actual Modelica
    package.  This tells us what, after extracting the zipball, needs
    to be moved to the install path.

    The second element in the tuple is the list of dependencies.
    """
    root = github.getRawFile(user, repo, tag, "package.mo")
    if root!=None:
        deps = extract_dependencies(root)
        root.close()
        return (".", deps)
    elif verbose:
        print "Not in root directory"
    unver_dir = github.getRawFile(user, repo, tag, repo+"/package.mo")
    if unver_dir!=None:
        deps = extract_dependencies(unver_dir)
        unver_dir.close()
        return (repo, deps)
    elif verbose:
        print "Not in unversioned directory of the same name"
    ver_name = repo+" "+str(tag.replace("v",""))
    path = repo+"%20"+str(tag.replace("v", ""))+"/package.mo"
    ver_dir = github.getRawFile(user, repo, tag, path)
    if ver_dir!=None:
        deps = extract_dependencies(ver_dir)
        ver_dir.close()
        return (ver_name, deps)
    elif verbose:
        print "Not in versioned directory ("+ver_name+")"
    return (None, [])

def process_user(repo_data, user, github, verbose, tolerant, ignore_empty):
    # Get a list of repositories
    repos = github.getRepos(user)

    # Iterate over each repository
    for repo in repos:
        # Extract the repository name
        name = repo["name"]
        print "Repository: "+name

        # Initialize data for current repository
        data = {}

        # Pull out various pieces of information about the repository
        # and store it.
        data["description"] = repo["description"]

        # Prepare to extract all versions of this library
        data["versions"] = {}

        # Get the list of tags from GitHub
        tags = github.getTags(user, name)

        # Iterate over each tag
        for tag in tags:
            # Get the name of the tag
            tagname = tag["name"]
            if verbose:
                print "  Tag: "+tagname
            
            # Parse the tag to see if it is a semantic version number
            try:
                ver = SemanticVersion(tagname, tolerant=tolerant)
            except ValueError as e:
                if verbose:
                    print "Exception: "+str(e)
                continue

            # TODO: extract dependency information
            (path, deps) = get_package_details(user, name, tagname,
                                               github, ver, verbose)
            if path==None:
                print "Couldn't find Modelica package root"
                continue

            print "  Semantic version info: "+str(ver)
            print "    Path: "+str(path)
            print "    Dependencies: "+str(deps)

            # Create a data structure for information related to this version
            tagdata = ver.json()
            tagdata["zipball_url"] = tag["zipball_url"]
            tagdata["tarball_url"] = tag["tarball_url"]
            tagdata["path"] = path
            tagdata["dependencies"] = deps

            data["versions"][str(ver)] = tagdata

        if len(data["versions"])==0:
            print "  No useable version tags found"
            if ignore_empty:
                continue

        # Add data for this repository to master data structure
        repo_data[name] = data

def refresh(output, verbose, tolerant, ignore_empty):
    username = config.get("Impact", "username", None)
    password = config.get("Impact", "password", None)
    token = config.get("Impact", "token", None)

    if verbose:
        if username!=None:
            print "Using username: "+username+" to authenticate"
        if token!=None:
            print "Using API token to authenticate"

    # Setup connection to github
    github = GitHub(username=username, password=password,
                    token=token)

    # Initialize respository data.  This is what we are refreshing
    # and what we will store eventually.
    repo_data = {}

    # Process all 3rd party libraries
    process_user(repo_data, user="modelica-3rdparty", github=github,
                 verbose=verbose, tolerant=tolerant, ignore_empty=ignore_empty)

    # This gives the "modelica" user priority over "modelica-3rdparty"
    # in case of naming conflict
    process_user(repo_data, user="modelica", github=github, verbose=verbose,
                 tolerant=tolerant, ignore_empty=ignore_empty)
    
    # Write out repository data collected
    if output==None:
        print json.dumps(repo_data, indent=4)
    else:
        if verbose:
            print "Output file: "+output
        with open(output, "w") as fp:
            json.dump(repo_data, fp, indent=4)
    if verbose:
        print "Refresh completed"
