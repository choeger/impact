package index

import (
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"os"
)

type Index map[LibraryName]Library

func DownloadIndex() Index {
	var master = "https://impact.modelica.org/impact_data.json"

	resp, err := http.Get(master)
	if err != nil {
		fmt.Println("Unable to locate index file at " + master)
		os.Exit(1)
	}
	defer resp.Body.Close()

	index := Index{}

	err = index.BuildIndex(resp.Body)
	if err != nil {
		fmt.Println("Error reading index: " + err.Error())
		os.Exit(2)
	}

	return index
}

func (index *Index) BuildIndexFromFile(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	return index.BuildIndex(file)
}

func (index *Index) BuildIndex(read io.Reader) error {
	data, err := ioutil.ReadAll(read)
	str := string(data)

	latest := Index{}
	if err == nil {
		err = json.Unmarshal([]byte(str), &latest)
	}
	for lib, v := range latest {
		v.Name = lib // Let the library know its name
		(*index)[lib] = v
	}
	return err
}

func (index *Index) Find(name LibraryName, version VersionString) (v Version, err error) {
	me, ok := (*index)[name]
	if !ok {
		err = MissingLibraryError{Name: name}
		return
	}
	v, ok = me.Versions[version]
	if !ok {
		err = MissingVersionError{Name: name, Version: version}
		return
	}
	return
}

func (index *Index) Dependencies(name LibraryName,
	version VersionString) (libs Libraries, err error) {
	myver, err := index.Find(name, version)
	if err != nil {
		return
	}

	libs = Libraries{name: myver}

	for _, dep := range myver.Dependencies {
		deps, lerr := index.Dependencies(dep.Name, dep.Version)
		if lerr != nil {
			return
		}
		for dn, dv := range deps {
			ev, exists := libs[dn]
			if exists {
				if dv.Equals(ev) {
					err = VersionConflictError{Name: dn, Existing: ev, Additional: dv}
					return
				}
			} else {
				libs[dn] = dv
			}
		}
	}
	return
}